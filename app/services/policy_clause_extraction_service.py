import re
from typing import Any

PLAN_PREFIX_MAP = {
    "SILV": {
        "plan_id": "PLAN001",
        "plan_name": "Silver Health Plan",
    },
    "GOLDV": {
        "plan_id": "PLAN002",
        "plan_name": "Gold Health Plan",
    },
    "PLATV": {
        "plan_id": "PLAN003",
        "plan_name": "Platinum Health Plan",
    },
}


CATEGORY_CODE_MAP = {
    "ELG": "eligibility",
    "LIM": "limit",
    "BEN": "benefit",
    "ADD": "additional_benefit",
    "WAIT": "waiting_period",
    "EXC": "exclusion",
    "DOC": "documentation",
    "RUL": "rule",
}
CLAUSE_HEADING_PATTERN = re.compile(
    r"^(?P<clause_id>"
    r"(?:SILV|GOLDV|PLATV)\d+"
    r"-[A-Z]+-\d+"
    r")"
    r"\s*(?:-|–|—|:)\s*"
    r"(?P<section>.+)$",
    flags=re.IGNORECASE,
)
CLAUSE_ID_METADATA_PATTERN = re.compile(
    r"^(?P<plan_prefix>SILV|GOLDV|PLATV)"
    r"(?P<version_number>\d+)"
    r"-(?P<category_code>[A-Z]+)"
    r"-(?P<sequence>\d+)$",
    flags=re.IGNORECASE,
)

IGNORED_PARAGRAPH_ROLES = {
    "paragraphrole.page_header",
    "paragraphrole.page_footer",
    "paragraphrole.page_number",
    "paragraphrole.title",
}


IGNORED_TEXT_VALUES = {
    "synthetic capstone data",
    (
        "not a real insurance product. for demonstration, "
        "development, retrieval, and evaluation only."
    ),
}
VALID_PLAN_VERSIONS = {
    "PLAN001": {"v1", "v2"},
    "PLAN002": {"v1", "v2"},
    "PLAN003": {"v1", "v2"},
}


VALID_CATEGORIES = {
    "eligibility",
    "limit",
    "benefit",
    "additional_benefit",
    "waiting_period",
    "exclusion",
    "documentation",
    "rule",
}


EXPECTED_PLAN_PREFIX = {
    "PLAN001": "SILV",
    "PLAN002": "GOLDV",
    "PLAN003": "PLATV",
}

def derive_clause_metadata(
    clause_id: str,
) -> dict:
    """
    Derive plan, version and category metadata
    from a validated clause ID.
    """

    normalized_id = _normalize_clause_id(
        clause_id
    )

    match = CLAUSE_ID_METADATA_PATTERN.match(
        normalized_id
    )

    if not match:
        raise ValueError(
            f"Unsupported clause ID: {normalized_id}"
        )

    plan_prefix = (
        match.group("plan_prefix").upper()
    )

    category_code = (
        match.group("category_code").upper()
    )

    version_number = (
        match.group("version_number")
    )

    plan_metadata = PLAN_PREFIX_MAP.get(
        plan_prefix
    )

    if not plan_metadata:
        raise ValueError(
            f"Unknown plan prefix: {plan_prefix}"
        )

    category = CATEGORY_CODE_MAP.get(
        category_code
    )

    if not category:
        raise ValueError(
            f"Unknown clause category: "
            f"{category_code}"
        )

    return {
        "plan_id": plan_metadata["plan_id"],
        "plan_name": plan_metadata["plan_name"],
        "version": f"v{version_number}",
        "category": category,
    }
def _normalize_role(
    value: Any,
) -> str:
    """
    Normalize the Document Intelligence paragraph role.
    """

    if value is None:
        return ""

    return str(value).strip().lower()

def deduplicate_candidate_clauses(
    candidates: list[dict],
) -> list:
    """
    Remove duplicate clause IDs.

    If the same clause is extracted more than once,
    retain the candidate containing more useful text.
    """

    candidates_by_id = {}

    for candidate in candidates:

        clause_id = _normalize_clause_id(
            candidate.get("clause_id")
        )

        section = _clean_text(
            candidate.get("section")
        )

        text = _clean_text(
            candidate.get("text")
        )

        if not clause_id:
            continue

        if not section:
            continue

        if not text:
            continue

        clean_candidate = {
            "clause_id": clause_id,
            "section": section,
            "text": text,
        }

        existing_candidate = (
            candidates_by_id.get(
                clause_id
            )
        )

        if not existing_candidate:
            candidates_by_id[
                clause_id
            ] = clean_candidate

            continue

        # Keep the more complete extraction.
        if len(text) > len(
            existing_candidate["text"]
        ):
            candidates_by_id[
                clause_id
            ] = clean_candidate

    return list(
        candidates_by_id.values()
    )
def _finalize_candidate(
    current_clause: dict | None,
) -> dict | None:
    """
    Convert the current working clause into a clean candidate.
    """

    if not current_clause:
        return None

    clause_text = _clean_text(
        " ".join(
            current_clause.get(
                "text_parts",
                [],
            )
        )
    )

    if not clause_text:
        return None

    return {
        "clause_id": current_clause["clause_id"],
        "section": current_clause["section"],
        "text": clause_text,
    }
def _clean_text(value: Any) -> str:
    """
    Convert extracted values into normalized text.
    """

    if value is None:
        return ""

    text = str(value)

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


def _normalize_clause_id(
    clause_id: str,
) -> str:
    """
    Normalize clause IDs to uppercase.
    """

    return _clean_text(
        clause_id
    ).upper()


def extract_candidate_clauses(
    analysis: dict,
) -> list[dict]:
    """
    Convert Document Intelligence paragraphs into clean
    candidate policy clauses.

    The parser:
    - detects clause headings,
    - ignores page headers, footers and page numbers,
    - stops at unrelated section headings,
    - prevents table content from leaking into clauses,
    - removes duplicate clause IDs.
    """

    if not analysis:
        raise ValueError(
            "Document analysis result is empty."
        )

    paragraphs = (
        analysis.get("paragraphs")
        or []
    )

    if not paragraphs:
        raise ValueError(
            "No document paragraphs were extracted."
        )

    extracted_candidates = []
    current_clause = None

    for paragraph in paragraphs:

        paragraph_text = _clean_text(
            paragraph.get("content")
        )

        paragraph_role = _normalize_role(
            paragraph.get("role")
        )

        if not paragraph_text:
            continue

        # ---------------------------------------------
        # Ignore page-level content
        # ---------------------------------------------

        if paragraph_role in IGNORED_PARAGRAPH_ROLES:
            continue

        if (
            paragraph_text.lower()
            in IGNORED_TEXT_VALUES
        ):
            continue

        # ---------------------------------------------
        # Detect a clause heading
        # ---------------------------------------------

        heading_match = (
            CLAUSE_HEADING_PATTERN.match(
                paragraph_text
            )
        )

        if heading_match:

            completed_clause = (
                _finalize_candidate(
                    current_clause
                )
            )

            if completed_clause:
                extracted_candidates.append(
                    completed_clause
                )

            current_clause = {
                "clause_id": (
                    _normalize_clause_id(
                        heading_match.group(
                            "clause_id"
                        )
                    )
                ),
                "section": _clean_text(
                    heading_match.group(
                        "section"
                    )
                ),
                "text_parts": [],
            }

            continue

        # ---------------------------------------------
        # Stop the active clause when a normal section
        # heading begins.
        #
        # Example:
        # SILV2-LIM-002
        # clause text...
        # 1.2 Core Benefit Schedule  ← stop here
        # ---------------------------------------------

                # ---------------------------------------------
        # Stop the active clause when a normal section
        # heading begins.
        # ---------------------------------------------

        if (
            paragraph_role
            == "paragraphrole.section_heading"
        ):
            completed_clause = _finalize_candidate(
                current_clause
            )

            if completed_clause:
                extracted_candidates.append(
                    completed_clause
                )

            current_clause = None
            continue

        # ---------------------------------------------
        # Add regular paragraph text to active clause
        # ---------------------------------------------

        if current_clause:
            current_clause[
                "text_parts"
            ].append(
                paragraph_text
            )

    # Save the final active clause.
    completed_clause = _finalize_candidate(
        current_clause
    )

    if completed_clause:
        extracted_candidates.append(
            completed_clause
        )

    return deduplicate_candidate_clauses(
        extracted_candidates
    )
def build_structured_clauses(
    candidates: list[dict],
) -> list[dict]:
    """
    Convert extracted clause candidates into
    structured RAG-ready records.
    """

    structured_clauses = []

    for candidate in candidates:

        clause_id = _normalize_clause_id(
            candidate.get("clause_id")
        )

        section = _clean_text(
            candidate.get("section")
        )

        text = _clean_text(
            candidate.get("text")
        )

        if not clause_id:
            continue

        if not section:
            continue

        if not text:
            continue

        if len(text.split()) < 5:
            continue

        metadata = derive_clause_metadata(
            clause_id
        )

        structured_clauses.append(
            {
                "clause_id": clause_id,
                "plan_id": metadata["plan_id"],
                "plan_name": metadata["plan_name"],
                "category": metadata["category"],
                "section": section,
                "text": text,
                "version": metadata["version"],
            }
        )

    return structured_clauses
def validate_structured_clauses(
    clauses: list[dict],
) -> dict:
    """
    Validate extracted clauses before they are written
    to JSONL or sent for embedding.
    """

    valid_clauses = []
    errors = []

    seen_clause_ids = set()

    for clause in clauses:

        clause_id = _clean_text(
            clause.get("clause_id")
        ).upper()

        plan_id = _clean_text(
            clause.get("plan_id")
        )

        version = _clean_text(
            clause.get("version")
        ).lower()

        category = _clean_text(
            clause.get("category")
        ).lower()

        section = _clean_text(
            clause.get("section")
        )

        text = _clean_text(
            clause.get("text")
        )

        clause_errors = []

        # -----------------------------------------
        # Required fields
        # -----------------------------------------

        if not clause_id:
            clause_errors.append(
                "missing_clause_id"
            )

        if not plan_id:
            clause_errors.append(
                "missing_plan_id"
            )

        if not version:
            clause_errors.append(
                "missing_version"
            )

        if not category:
            clause_errors.append(
                "missing_category"
            )

        if not section:
            clause_errors.append(
                "missing_section"
            )

        if not text:
            clause_errors.append(
                "missing_text"
            )

        # -----------------------------------------
        # Duplicate clause IDs
        # -----------------------------------------

        if clause_id in seen_clause_ids:
            clause_errors.append(
                "duplicate_clause_id"
            )

        # -----------------------------------------
        # Plan validation
        # -----------------------------------------

        if plan_id not in VALID_PLAN_VERSIONS:
            clause_errors.append(
                "invalid_plan_id"
            )

        # -----------------------------------------
        # Version validation
        # -----------------------------------------

        elif (
            version
            not in VALID_PLAN_VERSIONS[plan_id]
        ):
            clause_errors.append(
                "invalid_version"
            )

        # -----------------------------------------
        # Category validation
        # -----------------------------------------

        if (
            category
            not in VALID_CATEGORIES
        ):
            clause_errors.append(
                "invalid_category"
            )

        # -----------------------------------------
        # Clause prefix ↔ plan validation
        # -----------------------------------------

        expected_prefix = (
            EXPECTED_PLAN_PREFIX.get(plan_id)
        )

        if (
            expected_prefix
            and not clause_id.startswith(
                expected_prefix
            )
        ):
            clause_errors.append(
                "plan_prefix_mismatch"
            )

        # -----------------------------------------
        # Clause ID ↔ version validation
        #
        # SILV2-* must be version v2
        # GOLDV1-* must be version v1
        # -----------------------------------------

        metadata_match = (
            CLAUSE_ID_METADATA_PATTERN.match(
                clause_id
            )
        )

        if metadata_match:

            id_version = (
                "v"
                + metadata_match.group(
                    "version_number"
                )
            )

            if id_version != version:
                clause_errors.append(
                    "clause_version_mismatch"
                )

        else:
            clause_errors.append(
                "invalid_clause_id_format"
            )

        # -----------------------------------------
        # Text quality
        # -----------------------------------------

        if text and len(
            text.split()
        ) < 5:
            clause_errors.append(
                "clause_text_too_short"
            )

        # -----------------------------------------
        # Final decision
        # -----------------------------------------

        if clause_errors:

            errors.append(
                {
                    "clause_id": clause_id,
                    "errors": clause_errors,
                }
            )

            continue

        seen_clause_ids.add(
            clause_id
        )

        valid_clauses.append(
            {
                **clause,
                "clause_id": clause_id,
                "plan_id": plan_id,
                "version": version,
                "category": category,
                "section": section,
                "text": text,
            }
        )

    return {
        "valid": not errors,
        "valid_clauses": valid_clauses,
        "errors": errors,
        "total_received": len(clauses),
        "total_valid": len(valid_clauses),
        "total_invalid": len(errors),
    }

def validate_document_scope(
    clauses: list[dict],
    expected_plan_id: str,
    expected_version: str,
) -> dict:

    mismatches = []

    for clause in clauses:

        if (
            clause.get("plan_id")
            != expected_plan_id
        ):
            mismatches.append(
                {
                    "clause_id": clause.get(
                        "clause_id"
                    ),
                    "reason": "wrong_plan",
                }
            )

        if (
            clause.get("version")
            != expected_version
        ):
            mismatches.append(
                {
                    "clause_id": clause.get(
                        "clause_id"
                    ),
                    "reason": "wrong_version",
                }
            )

    return {
        "valid": not mismatches,
        "mismatches": mismatches,
    }
