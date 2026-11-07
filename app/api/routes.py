from fastapi import APIRouter

from app.schemas import AskRequest, AskResponse, CompareRequest,CompareResponse
from app.services.plan_service import get_all_plans
from app.services.classifier_service import classify_intent
from app.services.advisor_service import process_question
from app.services.comparison_service import (
    generate_plan_comparison,
)

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

@router.post(
    "/compare",
    response_model=CompareResponse,
)
def compare_plans(
    request: CompareRequest,
):
    """
    Compare two insurance policies using
    grounded policy evidence.
    """

    result = generate_plan_comparison(
        question=request.question,

        plan_a_id=request.plan_a_id,
        plan_a_version=(
            request.plan_a_version
        ),

        plan_b_id=request.plan_b_id,
        plan_b_version=(
            request.plan_b_version
        ),

        category=request.category,
        top=request.top,
    )

    return CompareResponse(
    answer=result["answer"],
    summary=result["summary"],

    plan_a_id=result["plan_a_id"],
    plan_a_version=result[
        "plan_a_version"
    ],

    plan_b_id=result["plan_b_id"],
    plan_b_version=result[
        "plan_b_version"
    ],

    comparison_rows=result[
        "comparison_rows"
    ],

    sources_a=result["sources_a"],
    sources_b=result["sources_b"],

    status=result["status"],
)