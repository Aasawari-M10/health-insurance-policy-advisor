import json
from pathlib import Path


POLICY_FILE = Path(
    "data/policy_clauses.jsonl"
)


def load_clauses():

    clauses = []

    with POLICY_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:

        for line in file:

            if line.strip():

                clauses.append(
                    json.loads(line)
                )

    return clauses


def retrieve_clauses(
    plan_id: str,
    version: str,
    category: str,
):

    clauses = load_clauses()

    results = [
        clause
        for clause in clauses
        if (
            clause["plan_id"]
            == plan_id
            and
            clause["version"]
            == version
            and
            clause["category"]
            == category
        )
    ]

    return results


if __name__ == "__main__":

    results = retrieve_clauses(
        plan_id="PLAN001",
        version="v2",
        category="documentation",
    )

    print(
        f"Found {len(results)} "
        f"matching clauses.\n"
    )

    for clause in results:

        print(
            "Clause:",
            clause["clause_id"],
        )

        print(
            "Section:",
            clause["section"],
        )

        print(
            "Text:",
            clause["text"],
        )

        print("-" * 50)