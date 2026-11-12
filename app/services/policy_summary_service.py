from app.services.document_intelligence_service import (
    analyze_policy_document,
    prepare_policy_for_summary,
)

from app.services.policy_document_service import (
    get_policy_document,
)

# IMPORTANT:
# Use the same generate_answer import that your
# existing comparison/advisor service already uses.
from app.services.llm_service import generate_answer


def summarize_policy_document(
    document_path: str,
) -> dict:
    """
    Generate a complete summary of the selected policy PDF
    using Document Intelligence + the existing Foundry LLM.
    """

    if not document_path.strip():
        raise ValueError(
            "Policy document path is required."
        )

    # 1. Download original PDF from Blob Storage
    pdf_bytes = get_policy_document(
        document_path
    )

    # 2. Extract complete PDF content
    analysis = analyze_policy_document(
        pdf_bytes
    )

    # 3. Prepare extracted content
    policy_content = prepare_policy_for_summary(
        analysis
    )

    # 4. Build grounded summarization prompt
    summary_prompt = f"""
You are summarizing a fictional health insurance policy.

Use ONLY the policy document content provided below.

Create a concise, structured policy summary.

Do not produce long paragraphs.

Use the following exact structure.


## Policy Overview

Create a Markdown table:

| Field | Value |
|---|---|
| Plan Name | value |
| Plan ID | value |
| Version | value |
| Effective Date | value |
| Status | value |
| Annual Hospitalization Limit | value |


## Key Benefits

Create a Markdown table:

| Benefit | Coverage / Limit |
|---|---|
| Hospitalization | value |
| Room Expenses | value |
| ICU Expenses | value |
| Ground Ambulance | value |
| Pre-Hospitalization | value |
| Post-Hospitalization | value |
| Maternity | value |

Only include benefits supported by the document.


## Waiting Periods

Create a Markdown table:

| Waiting Period Type | Duration |
|---|---|
| value | value |

Include every important waiting period found in the policy.


## Major Exclusions

Use short bullet points.

Maximum 6 bullets.

Each bullet must contain one exclusion only.


## Required Documentation

Use short bullet points.

Include only documents explicitly supported by the policy.


## Claims and Authorization Process

Use a numbered list.

Keep every step to one sentence.


## Important Policy Conditions

Use short bullet points.

Maximum 5 bullets.


## Key Takeaways

Provide exactly 5 short bullet points containing the most
important information a policyholder should understand.


RULES:

1. Use only information contained in the supplied document.

2. Never invent benefits, limits, waiting periods,
   exclusions or documentation requirements.

3. Preserve numerical amounts and durations exactly.

4. Do not write long paragraphs.

5. Prefer tables for structured numerical information.

6. Prefer bullet points for conditions, exclusions and documents.

7. Keep each bullet concise.

8. Do not provide medical advice.

9. Clearly state that the policy is fictional.

10. If information for a field is unavailable, write:
    "Not specified in the policy."


POLICY DOCUMENT:

{policy_content}
"""

    system_prompt = """
You are a grounded health insurance policy summarization assistant.

Your responsibility is to explain policy documents accurately
and clearly using only the supplied document.

Never invent policy information.
"""

    summary = generate_answer(
        system_prompt=system_prompt,
        grounded_prompt=summary_prompt,
    )

    return {
        "summary": summary,
        "document_path": document_path,
        "page_count": analysis["page_count"],
        "paragraph_count": len(
            analysis["paragraphs"]
        ),
        "table_count": len(
            analysis["tables"]
        ),
        "status": "document_intelligence_summary",
    }