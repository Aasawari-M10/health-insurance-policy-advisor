import re


GUARANTEE_PATTERNS = [
    r"\bguarantee\b",
    r"\bguaranteed\b",
    r"\bdefinitely approved\b",
    r"\bguarantee approval\b",
    r"\bclaim will be approved\b",
    r"\bwill my claim be approved\b",
]


def asks_for_guarantee(
    question: str,
) -> bool:

    question = question.lower().strip()

    return any(
        re.search(pattern, question)
        for pattern in GUARANTEE_PATTERNS
    )


def validate_request(
    question: str,
    plan_id: str | None,
    version: str | None,
    intent: str,
) -> dict:

    if not question.strip():
        return {
            "allowed": False,
            "reason": "empty_question",
            "message": "Please enter a policy question.",
        }

    if not plan_id:
        return {
            "allowed": False,
            "reason": "missing_plan",
            "message": (
                "Please select an insurance plan "
                "before asking a policy question."
            ),
        }

    if not version:
        return {
            "allowed": False,
            "reason": "missing_version",
            "message": (
                "I could not determine the applicable "
                "policy version."
            ),
        }

    if (
        intent == "escalation"
        or asks_for_guarantee(question)
    ):
        return {
            "allowed": False,
            "reason": "human_review",
            "message": (
                "This request requires human review. "
                "I can explain the available policy "
                "wording, but I cannot guarantee claim "
                "or coverage approval."
            ),
        }

    return {
        "allowed": True,
        "reason": None,
        "message": None,
    }

def validate_retrieval(
    clauses: list[dict],
    plan_id: str,
    version: str,
) -> dict:

    if not clauses:
        return {
            "allowed": False,
            "reason": "no_evidence",
            "message": (
                "I could not find supporting policy "
                "information for this question."
            ),
        }

    valid_clauses = [
        clause
        for clause in clauses
        if (
            clause.get("plan_id") == plan_id
            and clause.get("version") == version
        )
    ]

    if not valid_clauses:
        return {
            "allowed": False,
            "reason": "evidence_scope_mismatch",
            "message": (
                "The retrieved evidence does not match "
                "the selected plan and policy version."
            ),
        }

    return {
        "allowed": True,
        "reason": None,
        "message": None,
        "clauses": valid_clauses,
    }

def validate_citations(
    answer: str,
    allowed_clause_ids: list[str],
) -> dict:

    cited_ids = set(
        re.findall(
            r"\b[A-Z0-9]+-[A-Z]+-\d+\b",
            answer,
        )
    )

    allowed_ids = set(
        allowed_clause_ids
    )

    invalid_ids = cited_ids - allowed_ids

    if invalid_ids:
        return {
            "allowed": False,
            "reason": "invalid_citation",
            "invalid_ids": sorted(invalid_ids),
        }

    return {
        "allowed": True,
        "reason": None,
        "invalid_ids": [],
    }
UNSAFE_OUTPUT_PATTERNS = [
    r"\byour claim will definitely be approved\b",
    r"\bclaim approval is guaranteed\b",
    r"\bcoverage is guaranteed\b",
]


def validate_answer(
    answer: str,
    source_clause_ids: list[str],
) -> dict:

    normalized = answer.lower()

    for pattern in UNSAFE_OUTPUT_PATTERNS:
        if re.search(pattern, normalized):

            return {
                "allowed": False,
                "reason": "approval_guarantee",
                "message": (
                    "The generated answer contained "
                    "an unsupported approval guarantee."
                ),
            }

    citations = validate_citations(
        answer=answer,
        allowed_clause_ids=source_clause_ids,
    )

    if not citations["allowed"]:
        return {
            "allowed": False,
            "reason": "invalid_citation",
            "message": (
                "The generated answer referenced "
                "policy evidence that was not retrieved."
            ),
        }

    return {
        "allowed": True,
        "reason": None,
        "message": None,
    }