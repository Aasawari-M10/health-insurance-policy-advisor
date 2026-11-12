import json
from pathlib import Path

from app.services.document_intelligence_service import (
    analyze_policy_document,
)

from app.services.policy_clause_extraction_service import (
    build_structured_clauses,
    extract_candidate_clauses,
    validate_document_scope,
    validate_structured_clauses,
)

from app.services.policy_document_service import (
    get_policy_document,
)


POLICY_DOCUMENTS = [
    {
        "document_path": (
            "policies/silver/v1/"
            "Silver_Health_Plan_v1.pdf"
        ),
        "plan_id": "PLAN001",
        "version": "v1",
    },
    {
        "document_path": (
            "policies/silver/v2/"
            "Silver_Health_Plan_v2.pdf"
        ),
        "plan_id": "PLAN001",
        "version": "v2",
    },
    {
        "document_path": (
            "policies/gold/v1/"
            "Gold_Health_Plan_v1.pdf"
        ),
        "plan_id": "PLAN002",
        "version": "v1",
    },
    {
        "document_path": (
            "policies/gold/v2/"
            "Gold_Health_Plan_v2.pdf"
        ),
        "plan_id": "PLAN002",
        "version": "v2",
    },
    {
        "document_path": (
            "policies/platinum/v1/"
            "Platinum_Health_Plan_v1.pdf"
        ),
        "plan_id": "PLAN003",
        "version": "v1",
    },
    {
        "document_path": (
            "policies/platinum/v2/"
            "Platinum_Health_Plan_v2.pdf"
        ),
        "plan_id": "PLAN003",
        "version": "v2",
    },
]


OUTPUT_PATH = Path(
    "app/data/policy_clauses_v2.jsonl"
)


def process_policy_document(
    document_path: str,
    expected_plan_id: str,
    expected_version: str,
) -> list[dict]:
    """
    Download, analyze, extract and validate one policy PDF.
    """

    print("\n" + "=" * 75)

    print(
        f"Processing: {document_path}"
    )

    print(
        f"Expected scope: "
        f"{expected_plan_id} / {expected_version}"
    )

    # 1. Download from Blob Storage
    pdf_bytes = get_policy_document(
        document_path
    )

    print(
        f"Downloaded: {len(pdf_bytes)} bytes"
    )

    # 2. Analyze the complete PDF
    analysis = analyze_policy_document(
        pdf_bytes
    )

    print(
        f"Pages analyzed: "
        f"{analysis['page_count']}"
    )

    if analysis["page_count"] < 3:
        raise ValueError(
            f"Only {analysis['page_count']} pages were "
            f"analyzed for {document_path}. "
            "Verify the Document Intelligence S0 tier "
            "and the Blob PDF."
        )

    # 3. Extract clause candidates
    candidates = extract_candidate_clauses(
        analysis
    )

    print(
        f"Candidate clauses: {len(candidates)}"
    )

    # 4. Add plan/version/category metadata
    structured_clauses = (
        build_structured_clauses(
            candidates
        )
    )

    print(
        f"Structured clauses: "
        f"{len(structured_clauses)}"
    )

    # 5. Validate individual records
    validation = validate_structured_clauses(
        structured_clauses
    )

    print(
        f"Valid clauses: "
        f"{validation['total_valid']}"
    )

    print(
        f"Invalid clauses: "
        f"{validation['total_invalid']}"
    )

    if not validation["valid"]:
        print(
            "\nValidation errors:"
        )

        for error in validation["errors"]:
            print(error)

        raise ValueError(
            f"Clause validation failed for "
            f"{document_path}."
        )

    # 6. Validate the complete document scope
    scope_validation = validate_document_scope(
        validation["valid_clauses"],
        expected_plan_id=expected_plan_id,
        expected_version=expected_version,
    )

    if not ["scope_valid"]:
        print(
            "\nDocument scope mismatches:"
        )

        for mismatch in (
            scope_validation["mismatches"]
        ):
            print(mismatch)

        raise ValueError(
            f"Document scope validation failed "
            f"for {document_path}."
        )

    print(
        "Document scope: VALID"
    )

    # Add source-document information for traceability.
    final_clauses = []

    for clause in validation["valid_clauses"]:
        final_clauses.append(
            {
                **clause,
                "source_document": document_path,
            }
        )

    return final_clauses


def validate_global_clause_ids(
    clauses: list[dict],
) -> None:
    """
    Ensure no clause ID is duplicated across the full dataset.
    """

    seen_ids = set()
    duplicate_ids = set()

    for clause in clauses:
        clause_id = clause["clause_id"]

        if clause_id in seen_ids:
            duplicate_ids.add(
                clause_id
            )

        seen_ids.add(
            clause_id
        )

    if duplicate_ids:
        raise ValueError(
            "Duplicate clause IDs were found across "
            f"the policy dataset: "
            f"{sorted(duplicate_ids)}"
        )


def write_jsonl(
    clauses: list[dict],
    output_path: Path,
) -> None:
    """
    Write validated clauses as JSON Lines.
    """

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with output_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        for clause in clauses:
            file.write(
                json.dumps(
                    clause,
                    ensure_ascii=False,
                )
            )

            file.write("\n")


def main():
    all_clauses = []

    for policy in POLICY_DOCUMENTS:
        policy_clauses = (
            process_policy_document(
                document_path=policy[
                    "document_path"
                ],
                expected_plan_id=policy[
                    "plan_id"
                ],
                expected_version=policy[
                    "version"
                ],
            )
        )

        all_clauses.extend(
            policy_clauses
        )

    validate_global_clause_ids(
        all_clauses
    )

    write_jsonl(
        clauses=all_clauses,
        output_path=OUTPUT_PATH,
    )

    print("\n" + "=" * 75)

    print(
        "POLICY CLAUSE GENERATION COMPLETE"
    )

    print(
        f"Total clauses: {len(all_clauses)}"
    )

    print(
        f"Output file: {OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()