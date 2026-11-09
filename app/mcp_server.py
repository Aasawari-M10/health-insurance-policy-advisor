from mcp.server import MCPServer

from app.services.rag_service import retrieve_and_build_context
from app.services.comparison_service import generate_plan_comparison
from app.services.policy_document_service import (
    list_policy_documents,
)

mcp = MCPServer(
    "HealthInsurancePolicyAdvisorMCP"
)


@mcp.tool()
def search_policy(
    question: str,
    intent: str,
    plan_id: str,
    version: str,
    top: int = 3,
) -> dict:
    """
    Search health insurance policy clauses and return grounded
    policy context for a specific plan and policy version.

    Use this tool when policy information is required, such as
    benefits, exclusions, waiting periods, documentation,
    hospitalization benefits, or room benefits.
    """

    return retrieve_and_build_context(
        question=question,
        intent=intent,
        plan_id=plan_id,
        version=version,
        top=top,
    )

@mcp.tool()
def compare_policies(
    question: str,
    plan_a_id: str,
    plan_a_version: str,
    plan_b_id: str,
    plan_b_version: str,
    category: str | None = None,
    top: int = 3,
) -> dict:
    """
    Compare two health insurance policies or policy versions.

    Use this tool when the user wants to compare two plans,
    compare different versions of plans, or understand
    differences in benefits, waiting periods, exclusions,
    documentation requirements, or other policy features.
    """

    return generate_plan_comparison(
        question=question,
        plan_a_id=plan_a_id,
        plan_a_version=plan_a_version,
        plan_b_id=plan_b_id,
        plan_b_version=plan_b_version,
        category=category,
        top=top,
    )

@mcp.tool()
def get_policy_documents() -> list[str]:
    """
    List the policy PDF documents currently available
    in the Health Insurance Policy Advisor.

    Use this tool when the user wants to find or view
    an original policy document.
    """

    return list_policy_documents()
