from app.services.classifier_service import classify_intent
from app.services.plan_service import get_active_plan_version


def process_question(question: str, plan_id: str | None = None, version: str | None = None):
    """
    Coordinate the processing of a user's insurance question.

    RAG, LLM and guardrail logic will be added in later phases.
    """

    intent = classify_intent(question)

    resolved_version = version

    if plan_id and not resolved_version:
        plan = get_active_plan_version(plan_id)

        if plan:
            resolved_version = plan.get("version")

    return {
        "answer": f"Question received and classified as: {intent}",
        "intent": intent,
        "plan_id": plan_id,
        "version": resolved_version,
        "source_clauses": [],
    }