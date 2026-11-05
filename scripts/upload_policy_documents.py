
from pathlib import Path

from app.services.blob_service import upload_policy_file


# ------------------------------------------------------------
# Policy documents to upload
# ------------------------------------------------------------
# LEFT  = local file in repository
# RIGHT = destination path in Azure Blob Storage
#
# Change the local filenames below if your actual
# PDF filenames are different.

POLICY_DOCUMENTS = [
    (
        "data/documents/Silver_Health_Plan_v1.pdf",
        "policies/silver/v1/Silver_Health_Plan_v1.pdf",
    ),
    (
        "data/documents/Silver_Health_Plan_v2.pdf",
        "policies/silver/v2/Silver_Health_Plan_v2.pdf",
    ),
    (
        "data/documents/Gold_Health_Plan_v1.pdf",
        "policies/gold/v1/Gold_Health_Plan_v1.pdf",
    ),
    (
        "data/documents/Platinum_Health_Plan_v1.pdf",
        "policies/platinum/v1/Platinum_Health_Plan_v1.pdf",
    ),
]


def upload_policy_documents() -> None:
    """
    Upload original policy PDF documents
    to Azure Blob Storage.
    """

    uploaded = 0
    skipped = 0

    print("Uploading policy documents...")
    print("=" * 60)

    for local_path, blob_path in POLICY_DOCUMENTS:

        file_path = Path(local_path)

        if not file_path.exists():
            print(
                f"SKIPPED: {local_path} "
                "(file not found)"
            )

            skipped += 1
            continue

        try:
            uploaded_blob = upload_policy_file(
                local_file_path=local_path,
                blob_name=blob_path,
            )

            print(
                f"UPLOADED: {uploaded_blob}"
            )

            uploaded += 1

        except Exception as exc:
            print(
                f"FAILED: {local_path}"
            )
            print(
                f"Reason: {exc}"
            )

            skipped += 1

    print()
    print("=" * 60)
    print("Upload complete")
    print(f"Uploaded: {uploaded}")
    print(f"Skipped/Failed: {skipped}")


if __name__ == "__main__":
    upload_policy_documents()