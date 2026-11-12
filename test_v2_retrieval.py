from app.services.rag_service import hybrid_search


TESTS = [
    {
        "question": "What is the room benefit?",
        "plan_id": "PLAN001",
        "version": "v2",
        "category": "benefit",
    },
    {
        "question": "What ICU expenses are covered?",
        "plan_id": "PLAN001",
        "version": "v2",
        "category": "benefit",
    },
    {
        "question": "What ambulance benefit is available?",
        "plan_id": "PLAN002",
        "version": "v2",
        "category": "benefit",
    },
    {
        "question": "What are the waiting periods?",
        "plan_id": "PLAN003",
        "version": "v2",
        "category": "waiting_period",
    },
    {
        "question": "What is excluded from this policy?",
        "plan_id": "PLAN002",
        "version": "v1",
        "category": "exclusion",
    },
    {
        "question": "What documents are required for hospitalization?",
        "plan_id": "PLAN003",
        "version": "v1",
        "category": "documentation",
    },
]


for test in TESTS:

    print("\n" + "=" * 80)

    print(
        f"{test['plan_id']} "
        f"{test['version']} | "
        f"{test['question']}"
    )

    results = hybrid_search(
        question=test["question"],
        plan_id=test["plan_id"],
        version=test["version"],
        category=test["category"],
        top=3,
    )

    for index, result in enumerate(
        results,
        start=1,
    ):
        print(f"\nResult {index}")

        print(
            "Clause:",
            result.get("clause_id")
        )

        print(
            "Section:",
            result.get("section")
        )

        print(
            "Category:",
            result.get("category")
        )

        print(
            "Text:",
            result.get("text")
        )