import os
from pathlib import Path

from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv


load_dotenv()


STORAGE_CONNECTION_STRING = os.getenv(
    "AZURE_STORAGE_CONNECTION_STRING"
)

CONTAINER_NAME = os.getenv(
    "AZURE_STORAGE_CONTAINER_NAME",
    "policy-documents",
)


if not STORAGE_CONNECTION_STRING:
    raise ValueError(
        "AZURE_STORAGE_CONNECTION_STRING is missing."
    )


blob_service_client = (
    BlobServiceClient.from_connection_string(
        STORAGE_CONNECTION_STRING
    )
)


container_client = (
    blob_service_client.get_container_client(
        CONTAINER_NAME
    )
)


def list_policy_files() -> list:
    """
    List files stored in the policy container.
    """

    return [
        blob.name
        for blob in container_client.list_blobs()
    ]


def upload_policy_file(
    local_file_path: str,
    blob_name: str | None = None,
) -> str:
    """
    Upload one policy source file
    to Azure Blob Storage.
    """

    file_path = Path(local_file_path)

    if not file_path.exists():
        raise FileNotFoundError(
            f"File not found: {local_file_path}"
        )

    if blob_name is None:
        blob_name = file_path.name

    blob_client = (
        container_client.get_blob_client(
            blob_name
        )
    )

    with file_path.open("rb") as data:
        blob_client.upload_blob(
            data,
            overwrite=True,
        )

    return blob_name


def download_policy_file(
    blob_name: str,
) -> bytes:
    """
    Download one policy source file
    from Azure Blob Storage.
    """

    blob_client = (
        container_client.get_blob_client(
            blob_name
        )
    )

    downloader = blob_client.download_blob()

    return downloader.readall()