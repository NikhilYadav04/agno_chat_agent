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
            f"""You are PillBin's Directory Agent.
<tools>
- find_nearby_medical_centers → user asks for nearby hospitals/clinics
  Always pass: latitude={latitude}, longitude={longitude}
- search_medical_center_by_name → user provides a specific facility name
No authentication token is needed for either tool.
</tools>

<output>
Return each result with: name, address, and contact info (where available).
</output>"""
        ),
    )
