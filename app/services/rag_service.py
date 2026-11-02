import os

from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery

from app.services.embedding_service import generate_embedding


load_dotenv()


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