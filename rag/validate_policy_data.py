import json
from pathlib import Path


POLICY_FILE = Path("data/policy_clauses.jsonl")


REQUIRED_FIELDS = {
    "clause_id",
    "plan_id",
    "category",
    "section",
    "text",
    "version",
}


VALID_CATEGORIES = {
    "benefit",
    "waiting_period",
    "exclusion",
    "documentation",
}


def load_policy_clauses():

    if not POLICY_FILE.exists():
        raise FileNotFoundError(
            f"Policy file not found: {POLICY_FILE}"
        )

    clauses = []

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
                    f"Invalid JSON at line "
                    f"{line_number}: {error}"
                )

            clauses.append(clause)

    return clauses


def validate_required_fields(clauses):

    errors = []

    for index, clause in enumerate(
        clauses,
        start=1,
    ):

        missing = (
            REQUIRED_FIELDS
            - set(clause.keys())
        )

        if missing:

            errors.append(
                f"Record {index} missing: "
                f"{sorted(missing)}"
            )

    return errors


def validate_categories(clauses):

    errors = []

    for clause in clauses:

        category = clause.get("category")

        if category not in VALID_CATEGORIES:

            errors.append(
                f"{clause.get('clause_id')} "
                f"has invalid category: "
                f"{category}"
            )

    return errors


def validate_duplicate_clause_ids(clauses):

    seen = set()
    duplicates = set()

    for clause in clauses:

        clause_id = clause["clause_id"]

        if clause_id in seen:
            duplicates.add(clause_id)

        seen.add(clause_id)

    return sorted(duplicates)


def validate_empty_text(clauses):

    errors = []

    for clause in clauses:

        text = str(
            clause.get(
                "text",
                "",
            )
        ).strip()

        if not text:

            errors.append(
                clause.get(
                    "clause_id",
                    "UNKNOWN",
                )
            )

    return errors


def show_summary(clauses):

    print("\nPolicy Knowledge Summary")
    print("=" * 40)

    print(
        f"Total clauses: {len(clauses)}"
    )

    plans = sorted(
        set(
            clause["plan_id"]
            for clause in clauses
        )
    )

    versions = sorted(
        set(
            clause["version"]
            for clause in clauses
        )
    )

    categories = sorted(
        set(
            clause["category"]
            for clause in clauses
        )
    )

    print(
        f"Plans: {plans}"
    )

    print(
        f"Versions: {versions}"
    )

    print(
        f"Categories: {categories}"
    )

    print("\nClauses by category:")

    for category in categories:

        count = sum(
            1
            for clause in clauses
            if clause["category"]
            == category
        )

        print(
            f"{category}: {count}"
        )


def main():

    clauses = load_policy_clauses()

    print(
        f"Loaded {len(clauses)} "
        f"policy clauses."
    )

    errors = []

    errors.extend(
        validate_required_fields(
            clauses
        )
    )

    errors.extend(
        validate_categories(
            clauses
        )
    )

    empty_text = (
        validate_empty_text(
            clauses
        )
    )

    if empty_text:

        errors.append(
            "Empty clause text found in: "
            + ", ".join(empty_text)
        )

    duplicates = (
        validate_duplicate_clause_ids(
            clauses
        )
    )

    if duplicates:

        errors.append(
            "Duplicate clause IDs: "
            + ", ".join(duplicates)
        )

    if errors:

        print(
            "\nValidation FAILED"
        )

        for error in errors:

            print(
                f"- {error}"
            )

        raise SystemExit(1)

    print(
        "\nPolicy data validation PASSED."
    )

    show_summary(clauses)


if __name__ == "__main__":
    main()