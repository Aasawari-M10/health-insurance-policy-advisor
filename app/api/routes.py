from fastapi import APIRouter

from app.schemas import AskRequest, AskResponse
from app.services.plan_service import get_all_plans
from app.services.classifier_service import classify_intent
from app.services.advisor_service import process_question

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

    result = process_question(
        question=request.question,
        plan_id=request.plan_id,
        version=request.version,
    )

    return AskResponse(**result)