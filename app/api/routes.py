from fastapi import APIRouter


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


@router.post("/ask")
def ask_question():
    return {
        "message": "Ask endpoint is ready. Business logic will be added later."
    }