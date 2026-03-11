from agno.agent import Agent
from backend.services.agents.llm_factory import get_fast_llm

# MCP tool names that belong to this agent's domain
INVENTORY_TOOL_NAMES = {
    "get_medicines",
    "get_inventory_summary_stats",
    "get_expiry_analytics",
    "check_medicine_stock",
    "get_deleted_medicine_history",
}


def build_inventory_agent(mcp_tools) -> Agent:
    """
    Inventory & Health Agent — handles private, authenticated user data
    via the PillBin MCP server. Uses the cheap fast model.
    """
    return Agent(
        name="Inventory Agent",
        role="Fetch and analyze personal prescriptions, inventory stats, and medication expiry data via MCP.",
        model=get_fast_llm(),
        tools=[mcp_tools],
        tool_call_limit=2,
        retries=1,
        instructions=(
            "Extract the JWT token from the user's message and use it for all authenticated MCP calls. "
            "Never guess or fabricate data — always fetch from MCP. "
            "Return data clearly and accurately."
        ),
    )
