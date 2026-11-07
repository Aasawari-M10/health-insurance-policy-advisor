import json
from pathlib import Path

from mcp.server import MCPServer


mcp = MCPServer(
    "Health Insurance Policy Tools"
)


PLANS_FILE = Path(
    "data/plans.csv"
)

POLICY_FILE = Path(
    "data/policy_clauses.jsonl"
)