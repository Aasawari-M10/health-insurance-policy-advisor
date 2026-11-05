from pathlib import Path

from app.services.blob_service import (
    upload_policy_file,
)


SOURCE_FILES = [
    (
        "data/policy_clauses.jsonl",
        "structured/policy_clauses.jsonl",
    ),
    (
        "data/plans.csv",
        "structured/plans.csv",
    ),
    (
        "data/benefit_schedule.csv",
        "structured/benefit_schedule.csv",
    ),
]


def upload_sources() -> None:
    uploaded = 0
    skipped = 0

    for local_path, blob_name in SOURCE_FILES:
        file_path = Path(local_path)

        if not file_path.exists():
            print(
                f"Skipped missing file: {local_path}"
            )

            skipped += 1
            continue

        result = upload_policy_file(
            local_file_path=local_path,
            blob_name=blob_name,
        )

        print(f"Uploaded: {result}")

        uploaded += 1

    print()
    print(f"Uploaded files: {uploaded}")
    print(f"Skipped files: {skipped}")


if __name__ == "__main__":
    upload_sources()