from app.services.policy_summary_service import (
    summarize_policy_document,
)


DOCUMENT_PATH = (
    "policies/silver/v2/"
    "Silver_Health_Plan_v2.pdf"
)


print(
    "\nGenerating complete policy summary...\n"
)


result = summarize_policy_document(
    DOCUMENT_PATH
)


print(
    "========== POLICY SUMMARY ==========\n"
)

print(
    result["summary"]
)


print(
    "\n========== PROCESSING INFO =========="
)

print(
    f"Pages: {result['page_count']}"
)

print(
    f"Paragraphs: {result['paragraph_count']}"
)

print(
    f"Tables: {result['table_count']}"
)

print(
    f"Status: {result['status']}"
)