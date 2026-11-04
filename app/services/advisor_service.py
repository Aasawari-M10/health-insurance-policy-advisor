from app.services.classifier_service import classify_intent
from app.services.plan_service import get_active_plan_version
from app.services.rag_service import retrieve_and_build_context
from app.services.llm_service import generate_answer
from app.services.guardrail_service import (
    validate_request,
    validate_retrieval,
    validate_answer,
)


def process_question(
    question: str,
    plan_id: str | None = None,
    version: str | None = None,
):
    """
    Coordinate the complete policy-advisor workflow.

    Flow:
    Question
        -> Intent classification
        -> Plan/version resolution
        -> Request guardrails
        -> Hybrid retrieval + RAG context
        -> Retrieval guardrails
        -> LLM generation
        -> Output guardrails
        -> Final response
    """

    # --------------------------------------------------
    # 1. Classify user intent
    # --------------------------------------------------

    classification = classify_intent(
        question
    )

    intent = classification["intent"]
    confidence = classification["confidence"]


    # --------------------------------------------------
    # 2. Resolve policy version
    # --------------------------------------------------

    resolved_version = version

    if plan_id and not resolved_version:

        plan = get_active_plan_version(
            plan_id
        )

        if plan:
            resolved_version = plan.get(
                "version"
            )


    # --------------------------------------------------
    # 3. PRE-RAG GUARDRAILS
    # --------------------------------------------------

    request_check = validate_request(
        question=question,
        plan_id=plan_id,
        version=resolved_version,
        intent=intent,
    )

    if not request_check["allowed"]:

        return {
            "answer": request_check["message"],
            "intent": intent,
            "confidence": confidence,
            "plan_id": plan_id,
            "version": resolved_version,
            "source_clauses": [],
        }


    # --------------------------------------------------
    # 4. RETRIEVE EVIDENCE + BUILD RAG CONTEXT
    # --------------------------------------------------

    rag_result = retrieve_and_build_context(
        question=question,
        intent=intent,
        plan_id=plan_id,
        version=resolved_version,
        top=3,
    )


    # --------------------------------------------------
    # 5. RETRIEVAL GUARDRAILS
    # --------------------------------------------------

    retrieval_check = validate_retrieval(
        clauses=rag_result[
            "retrieved_clauses"
        ],
        plan_id=plan_id,
        version=resolved_version,
    )

    if not retrieval_check["allowed"]:

        return {
            "answer": retrieval_check[
                "message"
            ],
            "intent": intent,
            "confidence": confidence,
            "plan_id": plan_id,
            "version": resolved_version,
            "source_clauses": [],
        }


    # --------------------------------------------------
    # 6. GENERATE GROUNDED ANSWER
    # --------------------------------------------------

    answer = generate_answer(
        system_prompt=rag_result[
            "system_prompt"
        ],
        grounded_prompt=rag_result[
            "grounded_prompt"
        ],
    )


    # --------------------------------------------------
    # 7. POST-LLM GUARDRAILS
    # --------------------------------------------------

    answer_check = validate_answer(
        answer=answer,
        source_clause_ids=rag_result[
            "source_clause_ids"
        ],
    )

    if not answer_check["allowed"]:

        return {
            "answer": (
                "I could not provide a verified "
                "policy answer from the available "
                "evidence. Please review the "
                "applicable policy wording or "
                "contact a human advisor."
            ),
            "intent": intent,
            "confidence": confidence,
            "plan_id": plan_id,
            "version": resolved_version,
            "source_clauses": rag_result[
                "source_clause_ids"
            ],
        }


    # --------------------------------------------------
    # 8. FINAL VALIDATED RESPONSE
    # --------------------------------------------------

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