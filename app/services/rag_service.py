import os

from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery

from app.services.embedding_service import generate_embedding
from pathlib import Path


load_dotenv()

SYSTEM_PROMPT_PATH = Path(
    "app/prompts/system_prompt.txt"
)

SEARCH_ENDPOINT = os.getenv(
    "AZURE_SEARCH_ENDPOINT"
)

SEARCH_ADMIN_KEY = os.getenv(
    "AZURE_SEARCH_ADMIN_KEY"
)

INDEX_NAME = os.getenv(
    "AZURE_SEARCH_INDEX_NAME",
    "policy-index",
)


if not SEARCH_ENDPOINT:
    raise ValueError(
        "AZURE_SEARCH_ENDPOINT is missing."
    )

if not SEARCH_ADMIN_KEY:
    raise ValueError(
        "AZURE_SEARCH_ADMIN_KEY is missing."
    )


search_client = SearchClient(
    endpoint=SEARCH_ENDPOINT,
    index_name=INDEX_NAME,
    credential=AzureKeyCredential(
        SEARCH_ADMIN_KEY
    ),
)


def keyword_search(
    question: str,
    plan_id: str,
    version: str,
    category: str | None = None,
    top: int = 3,
):
    """
    Search policy clauses using Azure AI Search
    keyword retrieval.

    Results are restricted to the selected
    fictional plan and policy version.
    """

    filters = [
        f"plan_id eq '{plan_id}'",
        f"version eq '{version}'",
    ]

    if category:
        filters.append(
            f"category eq '{category}'"
        )

    filter_expression = " and ".join(
        filters
    )

    results = search_client.search(
        search_text=question,
        filter=filter_expression,
        top=top,
        select=[
            "clause_id",
            "plan_id",
            "version",
            "category",
            "section",
            "text",
        ],
    )

    clauses = []

    for result in results:

        clauses.append(
            {
                "clause_id":
                    result["clause_id"],

                "plan_id":
                    result["plan_id"],

                "version":
                    result["version"],

                "category":
                    result["category"],

                "section":
                    result["section"],

                "text":
                    result["text"],

                "score":
                    result.get(
                        "@search.score"
                    ),
            }
        )

    return clauses

def vector_search(
    question: str,
    plan_id: str,
    version: str,
    category: str | None = None,
    top: int = 3,
):
    """
    Retrieve policy clauses using semantic vector search.
    """

    # Convert the user question into the same
    # embedding space used for policy clauses.
    query_vector = generate_embedding(question)

    filters = [
        f"plan_id eq '{plan_id}'",
        f"version eq '{version}'",
    ]

    if category:
        filters.append(
            f"category eq '{category}'"
        )

    filter_expression = " and ".join(filters)

    vector_query = VectorizedQuery(
        vector=query_vector,
        k_nearest_neighbors=top,
        fields="content_vector",
    )

    results = search_client.search(
        search_text=None,
        vector_queries=[vector_query],
        filter=filter_expression,
        top=top,
        select=[
            "clause_id",
            "plan_id",
            "version",
            "category",
            "section",
            "text",
        ],
    )

    clauses = []

    for result in results:
        clauses.append(
            {
                "clause_id": result["clause_id"],
                "plan_id": result["plan_id"],
                "version": result["version"],
                "category": result["category"],
                "section": result["section"],
                "text": result["text"],
                "score": result.get(
                    "@search.score"
                ),
            }
        )

    return clauses

def hybrid_search(
    question: str,
    plan_id: str,
    version: str,
    category: str | None = None,
    top: int = 3,
):
    """
    Retrieve policy clauses using both
    keyword and vector search.
    """

    # Create semantic representation
    # of the user's question.
    query_vector = generate_embedding(
        question
    )

    filters = [
        f"plan_id eq '{plan_id}'",
        f"version eq '{version}'",
    ]

    if category:
        filters.append(
            f"category eq '{category}'"
        )

    filter_expression = " and ".join(
        filters
    )

    vector_query = VectorizedQuery(
        vector=query_vector,
        k_nearest_neighbors=top,
        fields="content_vector",
    )

    results = search_client.search(
        search_text=question,
        vector_queries=[
            vector_query
        ],
        filter=filter_expression,
        top=top,
        select=[
            "clause_id",
            "plan_id",
            "version",
            "category",
            "section",
            "text",
        ],
    )

    clauses = []

    for result in results:

        clauses.append(
            {
                "clause_id":
                    result["clause_id"],

                "plan_id":
                    result["plan_id"],

                "version":
                    result["version"],

                "category":
                    result["category"],

                "section":
                    result["section"],

                "text":
                    result["text"],

                "score":
                    result.get(
                        "@search.score"
                    ),
            }
        )

    return clauses

def load_system_prompt() -> str:
    """
    Load reusable system instructions
    for grounded policy responses.
    """

    if not SYSTEM_PROMPT_PATH.exists():
        raise FileNotFoundError(
            f"System prompt not found: "
            f"{SYSTEM_PROMPT_PATH}"
        )

    return SYSTEM_PROMPT_PATH.read_text(
        encoding="utf-8"
    ).strip()

def build_rag_context(
    question: str,
    intent: str,
    plan_id: str,
    version: str,
    clauses: list[dict],
) -> dict:
    """
    Build grounded context for the LLM.

    This function does NOT call the LLM.
    """

    system_prompt = load_system_prompt()

    clause_blocks = []

    source_clause_ids = []

    for clause in clauses:

        clause_id = clause["clause_id"]

        source_clause_ids.append(
            clause_id
        )

        block = (
            f"[Clause ID: {clause_id}]\n"
            f"Section: {clause['section']}\n"
            f"Category: {clause['category']}\n"
            f"Policy Text: {clause['text']}"
        )

        clause_blocks.append(block)

    policy_context = "\n\n".join(
        clause_blocks
    )

    grounded_prompt = f"""
USER QUESTION:
{question}

DETECTED INTENT:
{intent}

PLAN ID:
{plan_id}

POLICY VERSION:
{version}

RETRIEVED POLICY CONTEXT:
{policy_context}
""".strip()

    return {
        "system_prompt": system_prompt,
        "grounded_prompt": grounded_prompt,
        "source_clause_ids": source_clause_ids,
        "retrieved_clauses": clauses,
    }

def retrieve_and_build_context(
    question: str,
    intent: str,
    plan_id: str,
    version: str,
    top: int = 3,
) -> dict:
    """
    Retrieve relevant policy clauses and
    prepare grounded RAG context.
    """

    clauses = hybrid_search(
        question=question,
        plan_id=plan_id,
        version=version,
        category=intent,
        top=top,
    )

    return build_rag_context(
        question=question,
        intent=intent,
        plan_id=plan_id,
        version=version,
        clauses=clauses,
    )