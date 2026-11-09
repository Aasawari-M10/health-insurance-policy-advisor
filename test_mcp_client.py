import asyncio

from mcp import Client


MCP_URL = "http://127.0.0.1:8000/mcp"

async def main():
    async with Client(MCP_URL) as client:

        print("\nConnected to MCP server")

        # ------------------------------------------
        # List available MCP tools
        # ------------------------------------------

        tools_result = await client.list_tools()

        print("\nAvailable MCP tools:")

        for tool in tools_result.tools:
            print(f"- {tool.name}")

        print("\nTesting compare_policies:")

        comparison_result = await client.call_tool(
            "compare_policies",
            {
                "question": "Compare the waiting periods.",
                "plan_a_id": "PLAN001",
                "plan_a_version": "v2",
                "plan_b_id": "PLAN002",
                "plan_b_version": "v1",
                "category": "waiting_period",
                "top": 3,
            },
        )

        print(comparison_result)


if __name__ == "__main__":
    asyncio.run(main())
    