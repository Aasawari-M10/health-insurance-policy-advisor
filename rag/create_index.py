import os

from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchFieldDataType,
    SearchIndex,
    SearchableField,
    SimpleField,
)


load_dotenv()


SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
SEARCH_ADMIN_KEY = os.getenv("AZURE_SEARCH_ADMIN_KEY")
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


credential = AzureKeyCredential(
    SEARCH_ADMIN_KEY
)


index_client = SearchIndexClient(
    endpoint=SEARCH_ENDPOINT,
    credential=credential,
)


fields = [
    SimpleField(
        name="clause_id",
        type=SearchFieldDataType.String,
        key=True,
        filterable=True,
    ),

    SimpleField(
        name="plan_id",
        type=SearchFieldDataType.String,
        filterable=True,
        facetable=True,
    ),

    SimpleField(
        name="version",
        type=SearchFieldDataType.String,
        filterable=True,
        facetable=True,
    ),

    SimpleField(
        name="category",
        type=SearchFieldDataType.String,
        filterable=True,
        facetable=True,
    ),

    SearchableField(
        name="section",
        type=SearchFieldDataType.String,
        searchable=True,
        filterable=True,
    ),

    SearchableField(
        name="text",
        type=SearchFieldDataType.String,
        searchable=True,
    ),
]


policy_index = SearchIndex(
    name=INDEX_NAME,
    fields=fields,
)


def create_policy_index():

    print(
        f"Creating Azure AI Search index: "
        f"{INDEX_NAME}"
    )

    result = index_client.create_or_update_index(
        policy_index
    )

    print(
        f"Index created successfully: "
        f"{result.name}"
    )


if __name__ == "__main__":
    create_policy_index()