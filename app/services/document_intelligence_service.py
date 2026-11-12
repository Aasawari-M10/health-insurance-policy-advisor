import os

from dotenv import load_dotenv

load_dotenv()

from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest
from azure.core.credentials import AzureKeyCredential


DOCUMENT_INTELLIGENCE_ENDPOINT = os.getenv(
    "DOCUMENT_INTELLIGENCE_ENDPOINT"
)

DOCUMENT_INTELLIGENCE_KEY = os.getenv(
    "DOCUMENT_INTELLIGENCE_KEY"
)


def _get_document_client() -> DocumentIntelligenceClient:
    """
    Create the Azure Document Intelligence client.
    """

    if not DOCUMENT_INTELLIGENCE_ENDPOINT:
        raise ValueError(
            "DOCUMENT_INTELLIGENCE_ENDPOINT is not configured."
        )

    if not DOCUMENT_INTELLIGENCE_KEY:
        raise ValueError(
            "DOCUMENT_INTELLIGENCE_KEY is not configured."
        )

    return DocumentIntelligenceClient(
        endpoint=DOCUMENT_INTELLIGENCE_ENDPOINT,
        credential=AzureKeyCredential(
            DOCUMENT_INTELLIGENCE_KEY
        ),
    )


def analyze_policy_document(
    pdf_bytes: bytes,
) -> dict:
    """
    Extract complete text, paragraphs and tables
    from a policy PDF using Azure Document Intelligence.
    """

    if not pdf_bytes:
        raise ValueError(
            "Policy PDF is empty."
        )

    client = _get_document_client()

    poller = client.begin_analyze_document(
        model_id="prebuilt-layout",
        body=pdf_bytes,
        content_type="application/pdf",
    )

    result = poller.result()

    # Complete document text
    content = result.content or ""

    # Paragraphs
    paragraphs = []

    for paragraph_index, paragraph in enumerate(
        result.paragraphs or []
    ):
        page_numbers = []

        for region in paragraph.bounding_regions or []:
            if region.page_number:
                page_numbers.append(
                    region.page_number
                )

        paragraphs.append(
            {
                "paragraph_index": paragraph_index,
                "content": paragraph.content,
                "role": (
                    str(paragraph.role)
                    if paragraph.role
                    else None
                ),
                "page_numbers": sorted(
                    set(page_numbers)
                ),
            }
        )

    # Tables
    tables = []

    for table_index, table in enumerate(
        result.tables or []
    ):
        cells = []

        for cell in table.cells:
            cells.append(
                {
                    "row_index": cell.row_index,
                    "column_index": cell.column_index,
                    "content": cell.content,
                    "kind": (
                        str(cell.kind)
                        if cell.kind
                        else None
                    ),
                }
            )

        tables.append(
            {
                "table_index": table_index,
                "row_count": table.row_count,
                "column_count": table.column_count,
                "cells": cells,
            }
        )

    return {
        "content": content,
        "paragraphs": paragraphs,
        "tables": tables,
        "page_count": len(result.pages or []),
    }

def prepare_policy_for_summary(
    analysis: dict,
) -> str:
    """
    Convert Document Intelligence output into clean text
    suitable for whole-policy summarization.
    """

    if not analysis:
        raise ValueError(
            "Document analysis result is empty."
        )

    content = (
        analysis.get("content") or ""
    ).strip()

    if not content:
        raise ValueError(
            "No document text was extracted."
        )

    return content