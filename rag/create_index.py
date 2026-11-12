import os

from dotenv import load_dotenv

from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import ResourceNotFoundError

from azure.search.documents.indexes import (
    SearchIndexClient,
)

from azure.search.documents.indexes.models import (
    HnswAlgorithmConfiguration,
    SearchField,
    SearchFieldDataType,
    SearchIndex,
    SearchableField,
    SimpleField,
    VectorSearch,
    VectorSearchProfile,
)


load_dotenv()


SEARCH_ENDPOINT = os.getenv(
    "AZURE_SEARCH_ENDPOINT"
)

SEARCH_ADMIN_KEY = os.getenv(
    "AZURE_SEARCH_ADMIN_KEY"
)

INDEX_NAME = "policy-index-v2"


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


# --------------------------------------------------
# Vector search configuration
# --------------------------------------------------

vector_search = VectorSearch(
    algorithms=[
        HnswAlgorithmConfiguration(
            name="policy-hnsw"
        )
    ],

    profiles=[
        VectorSearchProfile(
            name="policy-vector-profile",
            algorithm_configuration_name="policy-hnsw",
        )
    ],
)


# --------------------------------------------------
# Index fields
# --------------------------------------------------

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

    SearchField(
        name="content_vector",
        type=SearchFieldDataType.Collection(
            SearchFieldDataType.Single
        ),
        searchable=True,
        vector_search_dimensions=1536,
        vector_search_profile_name=(
            "policy-vector-profile"
        ),
    ),
]


policy_index = SearchIndex(
    name=INDEX_NAME,
    fields=fields,
    vector_search=vector_search,
)


def create_policy_index():

    # Development only:
    # recreate the index so the schema includes
    # the vector field.

    try:

        index_client.delete_index(
            INDEX_NAME
        )

        print(
            f"Deleted existing index: "
            f"{INDEX_NAME}"
        )

    except ResourceNotFoundError:

        print(
            "Existing index not found."
        )

    result = index_client.create_index(
        policy_index
    )

    print(
        f"Vector index created successfully: "
        f"{result.name}"
    )


if __name__ == "__main__":
    create_policy_index()