from app.services.policy_document_service import (
    get_policy_document,
)

from app.services.document_intelligence_service import (
    analyze_policy_document,
    prepare_policy_for_summary,
)


DOCUMENT_PATH = (
    "policies/silver/v2/"
    "Silver_Health_Plan_v2.pdf"
)


pdf_bytes = get_policy_document(
    DOCUMENT_PATH
)

print(
    f"PDF size: {len(pdf_bytes)} bytes"
)


result = analyze_policy_document(
    pdf_bytes
)
summary_content = prepare_policy_for_summary(
    result
)


print(
    "\n========== SUMMARY CONTENT ==========\n"
)

print(
    summary_content
)


print(
    "\n========== SUMMARY CONTENT STATS =========="
)

print(
    f"Characters: {len(summary_content)}"
)

print(
    f"Words: {len(summary_content.split())}"
)

print(
    f"Pages extracted: {result['page_count']}"
)

print(
    f"Paragraphs extracted: "
    f"{len(result['paragraphs'])}"
)

print(
    f"Tables extracted: "
    f"{len(result['tables'])}"
)


print("\n========== DOCUMENT TEXT ==========\n")

print(
    result["content"][:5000]
)