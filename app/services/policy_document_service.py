from azure.core.exceptions import ResourceNotFoundError

from app.services.blob_service import container_client


def list_policy_documents() -> list:
    """
    Return all PDF policy documents available in Blob Storage.
    """
    documents = []

    for blob in container_client.list_blobs():
        if blob.name.lower().endswith(".pdf"):
            documents.append(blob.name)

    return documents


def get_policy_document(filename: str) -> bytes:
    """
    Download a policy PDF from Blob Storage and return it as bytes.
    """
    if not filename:
        raise ValueError("Policy document filename is required.")

    # Basic protection against selecting an unintended blob/path.
    available_documents = list_policy_documents()

    if filename not in available_documents:
        raise FileNotFoundError(
            f"Policy document '{filename}' was not found."
        )

    try:
        blob_client = container_client.get_blob_client(filename)
        return blob_client.download_blob().readall()

    except ResourceNotFoundError as exc:
        raise FileNotFoundError(
            f"Policy document '{filename}' was not found."
        ) from exc