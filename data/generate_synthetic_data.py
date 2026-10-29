import csv
import json
import random
from pathlib import Path

random.seed(42)

OUTPUT_DIR = Path("data")
OUTPUT_DIR.mkdir(exist_ok=True)


# ---------------------------------------------------------
# 1. FICTIONAL PLANS
# ---------------------------------------------------------

plans = [
    {
        "plan_id": "PLAN001",
        "plan_name": "Silver Health Plan",
        "version": "v1",
        "effective_date": "2025-01-01",
        "status": "inactive",
    },
    {
        "plan_id": "PLAN001",
        "plan_name": "Silver Health Plan",
        "version": "v2",
        "effective_date": "2026-01-01",
        "status": "active",
    },
    {
        "plan_id": "PLAN002",
        "plan_name": "Gold Health Plan",
        "version": "v1",
        "effective_date": "2026-01-01",
        "status": "active",
    },
    {
        "plan_id": "PLAN003",
        "plan_name": "Platinum Health Plan",
        "version": "v1",
        "effective_date": "2026-01-01",
        "status": "active",
    },
]


# ---------------------------------------------------------
# 2. POLICY CONFIGURATION
# All values below are FICTIONAL.
# ---------------------------------------------------------

policy_config = {
    ("PLAN001", "v1"): {
        "prefix": "SILV1",
        "waiting_days": 120,
        "annual_limit": 100000,
        "room_limit": 3000,
    },
    ("PLAN001", "v2"): {
        "prefix": "SILV2",
        "waiting_days": 90,
        "annual_limit": 150000,
        "room_limit": 4500,
    },
    ("PLAN002", "v1"): {
        "prefix": "GOLDV1",
        "waiting_days": 60,
        "annual_limit": 300000,
        "room_limit": 7000,
    },
    ("PLAN003", "v1"): {
        "prefix": "PLATV1",
        "waiting_days": 30,
        "annual_limit": 500000,
        "room_limit": 10000,
    },
}


# ---------------------------------------------------------
# 3. POLICY CLAUSES
# ---------------------------------------------------------

def generate_policy_clauses():
    clauses = []

    for (plan_id, version), config in policy_config.items():
        prefix = config["prefix"]

        clauses.extend(
            [
                {
                    "clause_id": f"{prefix}-BEN-001",
                    "plan_id": plan_id,
                    "category": "benefit",
                    "section": "Hospitalization Benefits",
                    "text": (
                        "This fictional plan includes eligible inpatient "
                        "hospitalization benefits subject to the conditions "
                        "and limits stated in the policy."
                    ),
                    "version": version,
                },
                {
                    "clause_id": f"{prefix}-BEN-002",
                    "plan_id": plan_id,
                    "category": "benefit",
                    "section": "Room Benefits",
                    "text": (
                        f"This fictional plan provides eligible room expenses "
                        f"up to {config['room_limit']} synthetic currency units "
                        f"per day, subject to policy conditions."
                    ),
                    "version": version,
                },
                {
                    "clause_id": f"{prefix}-WAIT-001",
                    "plan_id": plan_id,
                    "category": "waiting_period",
                    "section": "Waiting Periods",
                    "text": (
                        f"Eligible planned procedures under this fictional "
                        f"policy are subject to a waiting period of "
                        f"{config['waiting_days']} days from the applicable "
                        f"policy start date."
                    ),
                    "version": version,
                },
                {
                    "clause_id": f"{prefix}-EXC-001",
                    "plan_id": plan_id,
                    "category": "exclusion",
                    "section": "General Exclusions",
                    "text": (
                        "Services classified as cosmetic-only procedures are "
                        "excluded under this fictional policy unless another "
                        "approved clause explicitly provides a benefit."
                    ),
                    "version": version,
                },
                {
                    "clause_id": f"{prefix}-DOC-001",
                    "plan_id": plan_id,
                    "category": "documentation",
                    "section": "Required Documentation",
                    "text": (
                        "For a planned procedure, this fictional policy "
                        "requires a completed request form, supporting procedure "
                        "documentation, and identification information."
                    ),
                    "version": version,
                },
                {
                    "clause_id": f"{prefix}-DOC-002",
                    "plan_id": plan_id,
                    "category": "documentation",
                    "section": "Hospitalization Documentation",
                    "text": (
                        "For hospitalization-related requests, the fictional "
                        "policy record requires the applicable request form "
                        "and supporting hospitalization documentation."
                    ),
                    "version": version,
                },
            ]
        )

    return clauses


# ---------------------------------------------------------
# 4. BENEFIT SCHEDULE
# ---------------------------------------------------------

def generate_benefit_schedule():
    rows = []

    for (plan_id, version), config in policy_config.items():
        rows.append(
            {
                "plan_id": plan_id,
                "version": version,
                "benefit_id": f"{config['prefix']}-BEN-HOSP",
                "limit_type": "annual",
                "synthetic_amount": config["annual_limit"],
                "waiting_days": config["waiting_days"],
            }
        )

    return rows


# ---------------------------------------------------------
# 5. FAQ DATA
# ---------------------------------------------------------

def generate_faqs():
    faqs = []

    for (plan_id, version), config in policy_config.items():
        prefix = config["prefix"]

        faqs.extend(
            [
                {
                    "faq_id": f"{prefix}-FAQ-001",
                    "plan_id": plan_id,
                    "version": version,
                    "question": "What documents are required for a planned procedure?",
                    "approved_answer": (
                        "The fictional policy requires the documents listed "
                        "in the applicable documentation clause."
                    ),
                    "supporting_clause_ids": [
                        f"{prefix}-DOC-001"
                    ],
                },
                {
                    "faq_id": f"{prefix}-FAQ-002",
                    "plan_id": plan_id,
                    "version": version,
                    "question": "Is there a waiting period for planned procedures?",
                    "approved_answer": (
                        f"The fictional policy specifies a "
                        f"{config['waiting_days']}-day waiting period for "
                        f"eligible planned procedures."
                    ),
                    "supporting_clause_ids": [
                        f"{prefix}-WAIT-001"
                    ],
                },
            ]
        )

    return faqs


# ---------------------------------------------------------
# 6. INTENT CLASSIFICATION DATA
# This will later be used for Hugging Face.
# ---------------------------------------------------------

intent_templates = {
    "benefit": [
        "What benefits are included in my plan?",
        "What does my policy cover?",
        "Is hospitalization covered?",
        "Does my plan include hospital benefits?",
        "What benefits can I use?",
        "Can you explain my hospitalization benefits?",
        "Is this treatment covered under my plan?",
        "What coverage does my policy provide?",
        "Does this plan provide inpatient benefits?",
        "Tell me about the benefits in my policy.",
    ],

    "waiting_period": [
        "What is the waiting period?",
        "How long do I need to wait?",
        "Is there a waiting period for a planned procedure?",
        "When can I use this benefit?",
        "How many days is the waiting period?",
        "Does my plan have a waiting period?",
        "When does this benefit become applicable?",
        "What waiting period applies to hospitalization?",
        "Do I need to wait before using this benefit?",
        "Explain the waiting period in my policy.",
    ],

    "exclusion": [
        "What is excluded from my policy?",
        "Is cosmetic treatment excluded?",
        "What does my plan not cover?",
        "Which treatments are excluded?",
        "Can you explain the policy exclusions?",
        "What services are not covered?",
        "Does my policy exclude cosmetic procedures?",
        "Tell me what is excluded from this plan.",
        "Are there treatments that this policy does not cover?",
        "What are the general exclusions in my policy?",
    ],

    "documentation": [
        "What documents do I need?",
        "Which documents are required for hospitalization?",
        "What papers should I submit?",
        "What documents are needed for a planned procedure?",
        "Which documents do I need to provide?",
        "Tell me the required documentation.",
        "What documentation is required by my policy?",
        "What should I submit for hospitalization?",
        "Which supporting documents are required?",
        "What documents should I provide with my request?",
    ],

    "escalation": [
        "Guarantee that my claim will be approved.",
        "Can you promise that my claim will be paid?",
        "Tell me for certain that the claim will be accepted.",
        "Guarantee my reimbursement.",
        "Can you approve my claim?",
        "Promise that this treatment will be approved.",
        "Confirm that I will definitely receive payment.",
        "Can you guarantee coverage for my claim?",
        "Tell me my claim will definitely be accepted.",
        "I need a guaranteed claim approval.",
    ],
}


def generate_intent_dataset(samples_per_intent=100):
    rows = []

    for intent, templates in intent_templates.items():
        for i in range(samples_per_intent):
            base = random.choice(templates)

            variations = [
                base,
                base.lower(),
                f"Please tell me, {base.lower()}",
                f"Can you tell me {base.lower()}",
                f"I want to know: {base}",
            ]

            question = random.choice(variations)

            rows.append(
                {
                    "query_id": f"INT-{intent.upper()}-{i + 1:03d}",
                    "customer_question": question,
                    "intent": intent,
                }
            )

    random.shuffle(rows)

    return rows


# ---------------------------------------------------------
# 7. EVALUATION QUESTIONS
# Kept separate from training questions.
# ---------------------------------------------------------

evaluation_questions = [
    {
        "query_id": "EVAL-001",
        "customer_question": "Which supporting papers are required for my planned procedure?",
        "expected_intent": "documentation",
        "expected_behavior": "answer",
    },
    {
        "query_id": "EVAL-002",
        "customer_question": "How long must I wait before an eligible planned procedure?",
        "expected_intent": "waiting_period",
        "expected_behavior": "answer",
    },
    {
        "query_id": "EVAL-003",
        "customer_question": "Which services does the policy specifically leave out?",
        "expected_intent": "exclusion",
        "expected_behavior": "answer",
    },
    {
        "query_id": "EVAL-004",
        "customer_question": "Explain the hospitalization benefits available under the plan.",
        "expected_intent": "benefit",
        "expected_behavior": "answer",
    },
    {
        "query_id": "EVAL-005",
        "customer_question": "Promise me that my claim will definitely be accepted.",
        "expected_intent": "escalation",
        "expected_behavior": "safe_response",
    },
]


# ---------------------------------------------------------
# FILE WRITERS
# ---------------------------------------------------------

def write_csv(filename, rows, fieldnames):
    path = OUTPUT_DIR / filename

    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(rows)


def write_jsonl(filename, rows):
    path = OUTPUT_DIR / filename

    with path.open("w", encoding="utf-8") as file:
        for row in rows:
            file.write(
                json.dumps(row, ensure_ascii=False) + "\n"
            )


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

def main():
    policy_clauses = generate_policy_clauses()
    benefit_schedule = generate_benefit_schedule()
    faqs = generate_faqs()
    intent_data = generate_intent_dataset(
        samples_per_intent=100
    )

    write_csv(
        "plans.csv",
        plans,
        [
            "plan_id",
            "plan_name",
            "version",
            "effective_date",
            "status",
        ],
    )

    write_jsonl(
        "policy_clauses.jsonl",
        policy_clauses,
    )

    write_csv(
        "benefit_schedule.csv",
        benefit_schedule,
        [
            "plan_id",
            "version",
            "benefit_id",
            "limit_type",
            "synthetic_amount",
            "waiting_days",
        ],
    )

    write_jsonl(
        "faq.jsonl",
        faqs,
    )

    write_csv(
        "intent_training.csv",
        intent_data,
        [
            "query_id",
            "customer_question",
            "intent",
        ],
    )

    write_csv(
        "test_questions.csv",
        evaluation_questions,
        [
            "query_id",
            "customer_question",
            "expected_intent",
            "expected_behavior",
        ],
    )

    print("Synthetic data generated successfully.")
    print(f"Plans: {len(plans)}")
    print(f"Policy clauses: {len(policy_clauses)}")
    print(f"Benefit records: {len(benefit_schedule)}")
    print(f"FAQs: {len(faqs)}")
    print(f"Intent training examples: {len(intent_data)}")
    print(
        f"Evaluation questions: "
        f"{len(evaluation_questions)}"
    )


if __name__ == "__main__":
    main()