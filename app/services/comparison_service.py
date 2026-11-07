import json
import re
from typing import Any

from app.services.guardrail_service import validate_answer
from app.services.llm_service import generate_answer
from app.services.rag_service import (
    hybrid_search,
    load_system_prompt,
)


# ============================================================
# RETRIEVAL
# ============================================================

def retrieve_plan_evidence(
    question: str,
    plan_id: str,
    version: str,
    category: str | None = None,
    top: int = 3,
) -> list:
    """
    Retrieve relevant policy clauses for one
    specific plan and policy version.

    This function performs retrieval only.
    It does not call the chat LLM.
    """

    return hybrid_search(
        question=question,
        plan_id=plan_id,
        version=version,
        category=category,
        top=top,
    )


def retrieve_comparison_evidence(
    question: str,
    plan_a_id: str,
    plan_a_version: str,
    plan_b_id: str,
    plan_b_version: str,
    category: str | None = None,
    top: int = 3,
) -> dict:
    """
    Retrieve policy evidence independently
    for two plans.
    """

    plan_a_clauses = retrieve_plan_evidence(
        question=question,
        plan_id=plan_a_id,
        version=plan_a_version,
        category=category,
        top=top,
    )

    plan_b_clauses = retrieve_plan_evidence(
        question=question,
        plan_id=plan_b_id,
        version=plan_b_version,
        category=category,
        top=top,
    )

    return {
        "plan_a": {
            "plan_id": plan_a_id,
            "version": plan_a_version,
            "clauses": plan_a_clauses,
        },
        "plan_b": {
            "plan_id": plan_b_id,
            "version": plan_b_version,
            "clauses": plan_b_clauses,
        },
    }


# ============================================================
# CONTEXT BUILDING
# ============================================================

def _build_clause_block(
    clause: dict,
) -> str:
    """
    Convert one retrieved clause into a clear
    grounding block for the comparison prompt.
    """

    return (
        f"[Clause ID: {clause['clause_id']}]\n"
        f"Plan ID: {clause['plan_id']}\n"
        f"Version: {clause['version']}\n"
        f"Category: {clause['category']}\n"
        f"Section: {clause['section']}\n"
        f"Policy Text: {clause['text']}"
    )


def build_comparison_context(
    question: str,
    comparison_evidence: dict,
) -> dict:
    """
    Build grounded context for comparing two plans.

    This function does not call the LLM.
    """

    plan_a = comparison_evidence["plan_a"]
    plan_b = comparison_evidence["plan_b"]

    plan_a_blocks = [
        _build_clause_block(clause)
        for clause in plan_a["clauses"]
    ]

    plan_b_blocks = [
        _build_clause_block(clause)
        for clause in plan_b["clauses"]
    ]

    sources_a = list(
        dict.fromkeys(
            clause["clause_id"]
            for clause in plan_a["clauses"]
        )
    )

    sources_b = list(
        dict.fromkeys(
            clause["clause_id"]
            for clause in plan_b["clauses"]
        )
    )

    source_clause_ids = list(
        dict.fromkeys(
            sources_a + sources_b
        )
    )

    plan_a_context = "\n\n".join(
        plan_a_blocks
    )

    plan_b_context = "\n\n".join(
        plan_b_blocks
    )

    comparison_prompt = f"""
USER QUESTION:
{question}

PLAN A:
Plan ID: {plan_a["plan_id"]}
Version: {plan_a["version"]}

PLAN A POLICY EVIDENCE:
{plan_a_context}

PLAN B:
Plan ID: {plan_b["plan_id"]}
Version: {plan_b["version"]}

PLAN B POLICY EVIDENCE:
{plan_b_context}

COMPARISON INSTRUCTIONS:

Compare only the information contained in the
policy evidence above.

Do not invent benefits, exclusions, waiting periods,
limits, documents, or coverage.

Clearly explain the similarities and differences
between Plan A and Plan B.

If the evidence does not contain information for
one plan, write exactly:

"Not available in retrieved evidence"

Do not guarantee claim approval or coverage approval.

COMPARISON OUTPUT FORMAT:

Return valid JSON only.

Do not return Markdown.

Do not wrap the JSON in triple backticks or a
JSON code fence.

Use exactly this structure:

{{
  "summary": "short overall comparison",
  "rows": [
    {{
      "feature": "feature being compared",
      "plan_a": "what the evidence says for Plan A",
      "plan_b": "what the evidence says for Plan B",
      "difference": "main difference or similarity",
      "sources_a": ["Plan A clause IDs"],
      "sources_b": ["Plan B clause IDs"]
    }}
  ]
}}

OUTPUT RULES:

- The summary must be short and evidence-based.
- The rows value must be a JSON array.
- Every row must contain all six fields.
- Every source in sources_a must be a Plan A clause.
- Every source in sources_b must be a Plan B clause.
- Every source ID must come from the retrieved evidence.
- Use an empty source list only when the corresponding
  plan has no retrieved evidence for that feature.
- Return no text before or after the JSON object.
""".strip()

    return {
        "comparison_prompt": comparison_prompt,
        "plan_a": plan_a,
        "plan_b": plan_b,
        "sources_a": sources_a,
        "sources_b": sources_b,
        "source_clause_ids": source_clause_ids,
    }


def retrieve_and_build_comparison(
    question: str,
    plan_a_id: str,
    plan_a_version: str,
    plan_b_id: str,
    plan_b_version: str,
    category: str | None = None,
    top: int = 3,
) -> dict:
    """
    Retrieve evidence for two plans and build
    the grounded comparison context.
    """

    evidence = retrieve_comparison_evidence(
        question=question,
        plan_a_id=plan_a_id,
        plan_a_version=plan_a_version,
        plan_b_id=plan_b_id,
        plan_b_version=plan_b_version,
        category=category,
        top=top,
    )

    return build_comparison_context(
        question=question,
        comparison_evidence=evidence,
    )


# ============================================================
# EVIDENCE VALIDATION
# ============================================================

def validate_comparison_evidence(
    comparison: dict,
) -> dict:
    """
    Confirm that evidence on each side belongs to
    the requested plan and version.
    """

    plan_a = comparison["plan_a"]
    plan_b = comparison["plan_b"]

    plan_a_id = plan_a["plan_id"]
    plan_a_version = plan_a["version"]

    plan_b_id = plan_b["plan_id"]
    plan_b_version = plan_b["version"]

    valid_a = []
    invalid_a = []

    valid_b = []
    invalid_b = []

    for clause in plan_a["clauses"]:
        if (
            clause.get("plan_id") == plan_a_id
            and clause.get("version") == plan_a_version
        ):
            valid_a.append(clause)
        else:
            invalid_a.append(clause)

    for clause in plan_b["clauses"]:
        if (
            clause.get("plan_id") == plan_b_id
            and clause.get("version") == plan_b_version
        ):
            valid_b.append(clause)
        else:
            invalid_b.append(clause)

    sources_a = list(
        dict.fromkeys(
            clause["clause_id"]
            for clause in valid_a
        )
    )

    sources_b = list(
        dict.fromkeys(
            clause["clause_id"]
            for clause in valid_b
        )
    )

    if not valid_a or not valid_b:
        return {
            "allowed": False,
            "reason": (
                "insufficient_comparison_evidence"
            ),
            "sources_a": sources_a,
            "sources_b": sources_b,
            "invalid_a": invalid_a,
            "invalid_b": invalid_b,
        }

    if invalid_a or invalid_b:
        return {
            "allowed": False,
            "reason": "comparison_scope_mismatch",
            "sources_a": sources_a,
            "sources_b": sources_b,
            "invalid_a": invalid_a,
            "invalid_b": invalid_b,
        }

    return {
        "allowed": True,
        "reason": None,
        "sources_a": sources_a,
        "sources_b": sources_b,
        "invalid_a": [],
        "invalid_b": [],
    }


# ============================================================
# STRUCTURED OUTPUT PARSING
# ============================================================

def _remove_json_code_fence(
    answer: str,
) -> str:
    """
    Remove an accidental Markdown JSON code fence.
    """

    cleaned = answer.strip()

    cleaned = re.sub(
        r"^```(?:json)?\s*",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )

    cleaned = re.sub(
        r"\s*```$",
        "",
        cleaned,
    )

    return cleaned.strip()


def parse_structured_comparison(
    answer: str,
) -> dict:
    """
    Parse and validate the basic JSON structure
    returned by the LLM.
    """

    cleaned_answer = _remove_json_code_fence(
        answer
    )

    parsed = json.loads(
        cleaned_answer
    )

    if not isinstance(parsed, dict):
        raise ValueError(
            "Comparison output must be a JSON object."
        )

    summary = parsed.get(
        "summary"
    )

    rows = parsed.get(
        "rows"
    )

    if not isinstance(summary, str):
        raise ValueError(
            "Comparison summary must be a string."
        )

    if not isinstance(rows, list):
        raise ValueError(
            "Comparison rows must be a list."
        )

    required_fields = {
        "feature",
        "plan_a",
        "plan_b",
        "difference",
        "sources_a",
        "sources_b",
    }

    normalized_rows = []

    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(
                f"Comparison row {index} "
                "must be an object."
            )

        missing_fields = (
            required_fields - row.keys()
        )

        if missing_fields:
            raise ValueError(
                f"Comparison row {index} is missing: "
                f"{sorted(missing_fields)}"
            )

        if not isinstance(
            row["sources_a"],
            list,
        ):
            raise ValueError(
                f"Row {index} sources_a "
                "must be a list."
            )

        if not isinstance(
            row["sources_b"],
            list,
        ):
            raise ValueError(
                f"Row {index} sources_b "
                "must be a list."
            )

        normalized_rows.append(
            {
                "feature": str(
                    row["feature"]
                ).strip(),
                "plan_a": str(
                    row["plan_a"]
                ).strip(),
                "plan_b": str(
                    row["plan_b"]
                ).strip(),
                "difference": str(
                    row["difference"]
                ).strip(),
                "sources_a": [
                    str(source).strip()
                    for source in row[
                        "sources_a"
                    ]
                ],
                "sources_b": [
                    str(source).strip()
                    for source in row[
                        "sources_b"
                    ]
                ],
            }
        )

    return {
        "summary": summary.strip(),
        "rows": normalized_rows,
    }


def validate_comparison_rows(
    rows: list[dict],
    sources_a: list[str],
    sources_b: list[str],
) -> dict:
    """
    Verify that every row cites only clauses retrieved
    for the correct side of the comparison.
    """

    allowed_a = set(sources_a)
    allowed_b = set(sources_b)

    invalid_sources_a = set()
    invalid_sources_b = set()

    for row in rows:
        row_sources_a = set(
            row.get(
                "sources_a",
                [],
            )
        )

        row_sources_b = set(
            row.get(
                "sources_b",
                [],
            )
        )

        invalid_sources_a.update(
            row_sources_a - allowed_a
        )

        invalid_sources_b.update(
            row_sources_b - allowed_b
        )

    if (
        invalid_sources_a
        or invalid_sources_b
    ):
        return {
            "allowed": False,
            "reason": (
                "invalid_comparison_citation"
            ),
            "invalid_sources_a": sorted(
                invalid_sources_a
            ),
            "invalid_sources_b": sorted(
                invalid_sources_b
            ),
        }

    return {
        "allowed": True,
        "reason": None,
        "invalid_sources_a": [],
        "invalid_sources_b": [],
    }


# ============================================================
# RESPONSE HELPERS
# ============================================================

def _comparison_response(
    *,
    answer: str,
    summary: str,
    comparison_rows: list[dict],
    plan_a_id: str,
    plan_a_version: str,
    plan_b_id: str,
    plan_b_version: str,
    sources_a: list[str],
    sources_b: list[str],
    status: str,
) -> dict:
    """
    Create a consistent comparison response for every
    success and failure path.
    """

    return {
        "answer": answer,
        "summary": summary,
        "comparison_rows": comparison_rows,
        "plan_a_id": plan_a_id,
        "plan_a_version": plan_a_version,
        "plan_b_id": plan_b_id,
        "plan_b_version": plan_b_version,
        "sources_a": sources_a,
        "sources_b": sources_b,
        "source_clause_ids": list(
            dict.fromkeys(
                sources_a + sources_b
            )
        ),
        "status": status,
    }


# ============================================================
# MAIN COMPARISON WORKFLOW
# ============================================================

def generate_plan_comparison(
    question: str,
    plan_a_id: str,
    plan_a_version: str,
    plan_b_id: str,
    plan_b_version: str,
    category: str | None = None,
    top: int = 3,
) -> dict:
    """
    Generate a grounded, structured and validated
    comparison between two policies.
    """

    # --------------------------------------------------
    # 1. Validate request
    # --------------------------------------------------

    if not question.strip():
        return _comparison_response(
            answer=(
                "Please enter a comparison question."
            ),
            summary="",
            comparison_rows=[],
            plan_a_id=plan_a_id,
            plan_a_version=plan_a_version,
            plan_b_id=plan_b_id,
            plan_b_version=plan_b_version,
            sources_a=[],
            sources_b=[],
            status="invalid_question",
        )

    if (
        plan_a_id == plan_b_id
        and plan_a_version == plan_b_version
    ):
        return _comparison_response(
            answer=(
                "Please select two different policies "
                "for comparison."
            ),
            summary="",
            comparison_rows=[],
            plan_a_id=plan_a_id,
            plan_a_version=plan_a_version,
            plan_b_id=plan_b_id,
            plan_b_version=plan_b_version,
            sources_a=[],
            sources_b=[],
            status="invalid_comparison",
        )

    # --------------------------------------------------
    # 2. Retrieve and build context
    # --------------------------------------------------

    comparison = retrieve_and_build_comparison(
        question=question,
        plan_a_id=plan_a_id,
        plan_a_version=plan_a_version,
        plan_b_id=plan_b_id,
        plan_b_version=plan_b_version,
        category=category,
        top=top,
    )

    # --------------------------------------------------
    # 3. Validate retrieved evidence
    # --------------------------------------------------

    evidence_check = validate_comparison_evidence(
        comparison
    )

    sources_a = evidence_check[
        "sources_a"
    ]

    sources_b = evidence_check[
        "sources_b"
    ]

    source_clause_ids = list(
        dict.fromkeys(
            sources_a + sources_b
        )
    )

    if not evidence_check["allowed"]:
        return _comparison_response(
            answer=(
                "I could not find enough verified "
                "policy evidence to compare these "
                "two plans."
            ),
            summary="",
            comparison_rows=[],
            plan_a_id=plan_a_id,
            plan_a_version=plan_a_version,
            plan_b_id=plan_b_id,
            plan_b_version=plan_b_version,
            sources_a=sources_a,
            sources_b=sources_b,
            status=evidence_check[
                "reason"
            ],
        )

    # --------------------------------------------------
    # 4. Generate structured comparison
    # --------------------------------------------------

    system_prompt = load_system_prompt()

    raw_answer = generate_answer(
        system_prompt=system_prompt,
        grounded_prompt=comparison[
            "comparison_prompt"
        ],
    )

    # --------------------------------------------------
    # 5. Parse returned JSON
    # --------------------------------------------------

    try:
        structured_comparison = (
            parse_structured_comparison(
                raw_answer
            )
        )

    except (
        json.JSONDecodeError,
        ValueError,
    ):
        return _comparison_response(
            answer=(
                "The comparison could not be "
                "converted into structured data."
            ),
            summary="",
            comparison_rows=[],
            plan_a_id=plan_a_id,
            plan_a_version=plan_a_version,
            plan_b_id=plan_b_id,
            plan_b_version=plan_b_version,
            sources_a=sources_a,
            sources_b=sources_b,
            status=(
                "invalid_comparison_format"
            ),
        )

    summary = structured_comparison[
        "summary"
    ]

    comparison_rows = (
        structured_comparison["rows"]
    )

    if not comparison_rows:
        return _comparison_response(
            answer=(
                "No structured comparison rows "
                "were generated from the evidence."
            ),
            summary=summary,
            comparison_rows=[],
            plan_a_id=plan_a_id,
            plan_a_version=plan_a_version,
            plan_b_id=plan_b_id,
            plan_b_version=plan_b_version,
            sources_a=sources_a,
            sources_b=sources_b,
            status=(
                "insufficient_comparison_rows"
            ),
        )

    # --------------------------------------------------
    # 6. Validate row citations by plan
    # --------------------------------------------------

    row_check = validate_comparison_rows(
        rows=comparison_rows,
        sources_a=sources_a,
        sources_b=sources_b,
    )

    if not row_check["allowed"]:
        return _comparison_response(
            answer=(
                "The comparison contained policy "
                "citations that were not part of "
                "the retrieved evidence."
            ),
            summary="",
            comparison_rows=[],
            plan_a_id=plan_a_id,
            plan_a_version=plan_a_version,
            plan_b_id=plan_b_id,
            plan_b_version=plan_b_version,
            sources_a=sources_a,
            sources_b=sources_b,
            status="guardrail_blocked",
        )

    # --------------------------------------------------
    # 7. Reuse general output guardrails
    # --------------------------------------------------

    guardrail_text = json.dumps(
        structured_comparison,
        ensure_ascii=False,
    )

    answer_check = validate_answer(
        answer=guardrail_text,
        source_clause_ids=source_clause_ids,
    )

    if not answer_check["allowed"]:
        return _comparison_response(
            answer=(
                "I could not provide a verified "
                "comparison from the available "
                "policy evidence."
            ),
            summary="",
            comparison_rows=[],
            plan_a_id=plan_a_id,
            plan_a_version=plan_a_version,
            plan_b_id=plan_b_id,
            plan_b_version=plan_b_version,
            sources_a=sources_a,
            sources_b=sources_b,
            status="guardrail_blocked",
        )

    # --------------------------------------------------
    # 8. Return table-ready response
    # --------------------------------------------------

    return _comparison_response(
        answer=summary,
        summary=summary,
        comparison_rows=comparison_rows,
        plan_a_id=plan_a_id,
        plan_a_version=plan_a_version,
        plan_b_id=plan_b_id,
        plan_b_version=plan_b_version,
        sources_a=sources_a,
        sources_b=sources_b,
        status="grounded_comparison",
    )