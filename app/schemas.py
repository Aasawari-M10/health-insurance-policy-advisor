from typing import Optional,List

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=1,
        description="Insurance policy question asked by the user",
    )

    plan_id: Optional[str] = Field(
        default=None,
        description="Selected insurance plan ID",
    )

    version: Optional[str] = Field(
        default=None,
        description="Selected policy version",
    )


class AskResponse(BaseModel):
    answer: str
    intent: Optional[str] = None
    confidence: float | None = None
    plan_id: Optional[str] = None
    version: Optional[str] = None
    source_clauses: list[str] = []

class PlanResponse(BaseModel):
    plan_id: str
    plan_name: str
    version: str
    effective_date: str
    status: str

class CompareRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=1,
    )

    plan_a_id: str
    plan_a_version: str

    plan_b_id: str
    plan_b_version: str

    category: Optional[str] = None

    top: int = Field(
        default=3,
        ge=1,
        le=5,
    )


class ComparisonRow(BaseModel):
    feature: str
    plan_a: str
    plan_b: str
    difference: str
    sources_a: list[str]
    sources_b: list[str]


class CompareResponse(BaseModel):
    answer: str
    summary: str

    plan_a_id: str
    plan_a_version: str

    plan_b_id: str
    plan_b_version: str

    comparison_rows: list[ComparisonRow]

    sources_a: list[str]
    sources_b: list[str]

    status: str