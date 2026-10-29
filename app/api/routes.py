from fastapi import APIRouter

from app.schemas import AskRequest, AskResponse


router = APIRouter()


@router.get("/health")
def health_check():
    return {
        "status": "healthy"
    }


@router.get("/plans")
def get_plans():
    return {
        "message": "Plans endpoint is ready. Business logic will be added later."
    }


@router.post("/ask", response_model=AskResponse)
def ask_question(request: AskRequest):
    return AskResponse(
        answer=f"Question received: {request.question}",
        intent=None,
        plan_id=request.plan_id,
        version=request.version,
        source_clauses=[],
    )