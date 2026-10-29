from fastapi import APIRouter

from app.schemas import AskRequest, AskResponse
from app.services.plan_service import get_all_plans
from app.services.classifier_service import classify_intent


router = APIRouter()


@router.get("/health")
def health_check():
    return {
        "status": "healthy"
    }


@router.get("/plans")
def get_plans():
    return get_all_plans()


@router.post("/ask", response_model=AskResponse)
def ask_question(request: AskRequest):

    intent = classify_intent(request.question)

    return AskResponse(
        answer=f"Question received: {request.question}",
        intent=intent,
        plan_id=request.plan_id,
        version=request.version,
        source_clauses=[],
    )