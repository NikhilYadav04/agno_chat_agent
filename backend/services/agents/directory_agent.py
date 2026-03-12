from agno.agent import Agent
from backend.services.agents.llm_factory import get_fast_llm


def build_directory_agent(mcp_tools, latitude: str = "", longitude: str = "") -> Agent:
    """
    Facility Directory Agent — handles medical center lookups.
    No JWT authentication required for these tools.
    Uses the cheap fast model.
    """
    return Agent(
        name="Directory Agent",
        role="Find nearby medical facilities or search for centers by name.",
        model=get_fast_llm(),
        tools=[mcp_tools],
        tool_call_limit=2,
        retries=1,
        instructions=(
            "You help users find medical facilities. "
            "Use `find_nearby_medical_centers` when the user asks for nearby hospitals or clinics. "
            "Use `search_medical_center_by_name` when the user provides a specific name. "
            f"When calling `find_nearby_medical_centers`, always include the user's "
            f"latitude ({latitude}) and longitude ({longitude}) in the tool arguments "
            "to find results near the user. "
            "No authentication token is needed for these tools. "
            "Return results clearly with name, address, and contact info where available."
        ),
    )
