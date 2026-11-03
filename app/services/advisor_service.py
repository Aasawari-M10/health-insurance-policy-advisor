from app.services.classifier_service import classify_intent
from app.services.plan_service import get_active_plan_version
from app.services.rag_service import retrieve_and_build_context
from app.services.llm_service import generate_answer


def process_question(
    question: str,
    plan_id: str | None = None,
    version: str | None = None,
):
    """
    Coordinate the end-to-end policy advisor workflow.
    """

    # 1. Intent classification
    classification = classify_intent(question)

    intent = classification["intent"]
    confidence = classification["confidence"]

    # 2. Resolve policy version
    resolved_version = version

    if plan_id and not resolved_version:
        plan = get_active_plan_version(plan_id)

        if plan:
            resolved_version = plan.get("version")

    # 3. Require plan
    if not plan_id:
        return {
            "answer": (
                "Please select an insurance plan "
                "before asking a policy question."
            ),
            "intent": intent,
            "confidence": confidence,
            "plan_id": None,
            "version": None,
            "source_clauses": [],
        }

    # 4. Require version
    if not resolved_version:
        return {
            "answer": (
                "I could not determine the applicable "
                "policy version."
            ),
            "intent": intent,
            "confidence": confidence,
            "plan_id": plan_id,
            "version": None,
            "source_clauses": [],
        }

    # 5. Temporary escalation handling
    if intent == "escalation":
        return {
            "answer": (
                "This request requires human review. "
                "I cannot guarantee claim approval or "
                "make a final coverage decision."
            ),
            "intent": intent,
            "confidence": confidence,
            "plan_id": plan_id,
            "version": resolved_version,
            "source_clauses": [],
        }

    # 6. Azure AI Search + RAG
    rag_result = retrieve_and_build_context(
        question=question,
        intent=intent,
        plan_id=plan_id,
        version=resolved_version,
        top=3,
    )

    # 7. No supporting evidence
    if not rag_result["source_clause_ids"]:
        return {
            "answer": (
                "I could not find supporting policy "
                "information for this question."
            ),
            "intent": intent,
            "confidence": confidence,
            "plan_id": plan_id,
            "version": resolved_version,
            "source_clauses": [],
        }

    # 8. Generate grounded answer
    answer = generate_answer(
        system_prompt=rag_result["system_prompt"],
        grounded_prompt=rag_result["grounded_prompt"],
    )

    # 9. Final API response
    return {
        "answer": answer,
        "intent": intent,
        "confidence": confidence,
        "plan_id": plan_id,
        "version": resolved_version,
        "source_clauses": rag_result[
            "source_clause_ids"
        ],
    }