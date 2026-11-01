import json
import os
from pathlib import Path

from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient


load_dotenv()


# --------------------------------------------------
# Configuration
# --------------------------------------------------

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

POLICY_FILE = Path(
    "data/policy_clauses.jsonl"
)


# --------------------------------------------------
# Validate configuration
# --------------------------------------------------

if not SEARCH_ENDPOINT:
    raise ValueError(
        "AZURE_SEARCH_ENDPOINT is missing."
    )

if not SEARCH_ADMIN_KEY:
    raise ValueError(
        "AZURE_SEARCH_ADMIN_KEY is missing."
    )

if not POLICY_FILE.exists():
    raise FileNotFoundError(
        f"Policy file not found: {POLICY_FILE}"
    )


# --------------------------------------------------
# Create SearchClient
# --------------------------------------------------

credential = AzureKeyCredential(
    SEARCH_ADMIN_KEY
)

search_client = SearchClient(
    endpoint=SEARCH_ENDPOINT,
    index_name=INDEX_NAME,
    credential=credential,
)


# --------------------------------------------------
# Load policy clauses
# --------------------------------------------------

def load_policy_clauses():

    documents = []

    with POLICY_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:

        for line_number, line in enumerate(
            file,
            start=1,
        ):

            line = line.strip()

            if not line:
                continue

            try:
                clause = json.loads(line)

            except json.JSONDecodeError as error:
                raise ValueError(
                    f"Invalid JSON on line "
                    f"{line_number}: {error}"
                )

            document = {
                "clause_id": clause["clause_id"],
                "plan_id": clause["plan_id"],
                "version": clause["version"],
                "category": clause["category"],
                "section": clause["section"],
                "text": clause["text"],
            }

            documents.append(document)

    return documents


# --------------------------------------------------
# Upload
# --------------------------------------------------

def upload_policy_clauses():

    documents = load_policy_clauses()

    if not documents:
        print(
            "No policy clauses found."
        )
        return

    print(
        f"Loaded {len(documents)} "
        f"policy clauses."
    )

    print(
        f"Uploading documents to "
        f"Azure AI Search index: "
        f"{INDEX_NAME}"
    )

    results = search_client.upload_documents(
        documents=documents
    )

    successful = 0
    failed = 0

    for result in results:

        if result.succeeded:
            successful += 1

        else:
            failed += 1

            print(
                f"Upload failed for "
                f"{result.key}: "
                f"{result.error_message}"
            )

    print("\nUpload completed.")

    print(
        f"Successful: {successful}"
    )

    print(
        f"Failed: {failed}"
    )


# --------------------------------------------------
# Run
# --------------------------------------------------

if __name__ == "__main__":
    upload_policy_clauses()