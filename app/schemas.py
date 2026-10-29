from typing import Optional

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
    plan_id: Optional[str] = None
    version: Optional[str] = None
    source_clauses: list[str] = []