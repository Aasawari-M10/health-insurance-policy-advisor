from app.services.document_intelligence_service import (
    analyze_policy_document,
)

from app.services.policy_clause_extraction_service import (
    extract_candidate_clauses,
    build_structured_clauses,
    validate_structured_clauses,
    validate_document_scope,
)

from app.services.policy_document_service import (
    get_policy_document,
)


DOCUMENT_PATH = (
    "policies/gold/v2/"
    "Gold_Health_Plan_v2.pdf"
)


print(
    "\nDownloading policy from Blob Storage..."
)

pdf_bytes = get_policy_document(
    DOCUMENT_PATH
)


print(
    "Analyzing policy with Document Intelligence..."
)

analysis = analyze_policy_document(
    pdf_bytes
)



print(
    "Extracting candidate clauses..."
)

clauses = extract_candidate_clauses(
    analysis
)
structured_clauses = build_structured_clauses(
    clauses
)


print(
    f"\nStructured clauses: "
    f"{len(structured_clauses)}"
)


for clause in structured_clauses:
    # print("\n-----------structured--------------\n")
    print(
        "\n"
        + "=" * 70
    )

    print(
        f"Clause ID: {clause['clause_id']}"
    )

    print(
        f"Plan: {clause['plan_name']}"
    )

    print(
        f"Plan ID: {clause['plan_id']}"
    )

    print(
        f"Version: {clause['version']}"
    )

    print(
        f"Category: {clause['category']}"
    )

    print(
        f"Section: {clause['section']}"
    )

    print(
        f"Text: {clause['text']}"
    )

print(
    f"\nCandidate clauses extracted: "
    f"{len(clauses)}"
)

validation = validate_structured_clauses(
    structured_clauses
)


print(
    "\n========== VALIDATION =========="
)

print(
    f"Received: "
    f"{validation['total_received']}"
)

print(
    f"Valid: "
    f"{validation['total_valid']}"
)

print(
    f"Invalid: "
    f"{validation['total_invalid']}"
)


if validation["errors"]:

    print(
        "\nValidation errors:"
    )

    for error in validation["errors"]:
        print(error)
scope_validation = validate_document_scope(
    validation["valid_clauses"],
    expected_plan_id="PLAN002",
    expected_version="v2",
)


print(
    "\n========== DOCUMENT SCOPE =========="
)

print(
    f"Scope valid: "
    f"{scope_validation['valid']}"
)


if scope_validation["mismatches"]:
    for mismatch in (
        scope_validation["mismatches"]
    ):
        print(mismatch)
# for index, clause in enumerate(
#     clauses,
#     start=1,
# ):
#     print(
#         "\n"
#         + "=" * 70
#     )

#     print(
#         f"Candidate {index}"
#     )

#     print(
#         f"Clause ID: "
#         f"{clause['clause_id']}"
#     )

#     print(
#         f"Section: "
#         f"{clause['section']}"
#     )

#     print(
#         f"Text: "
#         f"{clause['text']}"
#     )

from collections import Counter


category_counts = Counter(
    clause["category"]
    for clause in structured_clauses
)


print(
    "\n========== CATEGORY COUNTS =========="
)

for category, count in sorted(
    category_counts.items()
):
    print(
        f"{category}: {count}"
    )


clause_ids = [
    clause["clause_id"]
    for clause in structured_clauses
]


print(
    "\n========== DUPLICATE CHECK =========="
)

print(
    f"Total clause records: "
    f"{len(clause_ids)}"
)

print(
    f"Unique clause IDs: "
    f"{len(set(clause_ids))}"
)