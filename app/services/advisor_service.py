from app.services.classifier_service import classify_intent
from app.services.plan_service import get_active_plan_version


def process_question(
    question: str,
    plan_id: str | None = None,
    version: str | None = None,
):
    """
    Coordinate the processing of a user's insurance question.

    RAG, LLM and guardrail logic will be added in later phases.
    """

    # Step 1: Classify the user's question
    classification = classify_intent(question)

    intent = classification["intent"]
    confidence = classification["confidence"]

    # Step 2: Resolve policy version
    resolved_version = version

    if plan_id and not resolved_version:

        plan = get_active_plan_version(plan_id)

        if plan:
            resolved_version = plan.get("version")

    # Step 3: Return structured result
    return {
        "answer": (
            f"Question received and classified as: {intent}"
        ),
        "intent": intent,
        "confidence": confidence,
        "plan_id": plan_id,
        "version": resolved_version,
        "source_clauses": [],
    }