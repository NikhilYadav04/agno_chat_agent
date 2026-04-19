import re
import traceback
from typing import Any, AsyncGenerator, Dict, List

from agno.team import Team
from agno.team.team import TeamRunEvent
from agno.tools.mcp import MCPTools

from backend.config.settings import settings
from backend.models.output_schema import Output
from backend.services.agents import (
    build_researcher_agent,
    build_inventory_agent,
    build_directory_agent,
)
from backend.services.agents.llm_factory import get_fast_llm
from backend.utils.memory_utils import format_history_for_agent

# ─── MCP Server URL ───
_MCP_URL = (
    "https://pillbin-mcp-server-f7c6fyfcctgqb7ec.canadacentral-01.azurewebsites.net/mcp"
)

# ─── MCP Singleton ───────────────────────────────────────────────────────────
# One MCPTools connection is shared across all requests. Re-connects lazily
# if the Azure server drops the idle connection.
_mcp: MCPTools | None = None


async def get_mcp_tools() -> MCPTools:
    """Return the cached MCP connection, initializing it on first use."""
    global _mcp

    # If we have a cached connection, ensure it is still alive
    if _mcp is not None and getattr(_mcp, "initialized", False):
        try:
            alive = await _mcp.is_alive()
            if not alive:
                _mcp = None
        except Exception as e:
            print(f"[MCP] Cached connection dead, reconnecting... ({e})")
            _mcp = None

    if _mcp is None or not getattr(_mcp, "initialized", False):
        _mcp = MCPTools(transport="streamable-http", url=_MCP_URL)
        await _mcp.__aenter__()
    return _mcp


async def stream_agent_response(
    token: str,
    user_message: str,
    recent_history: List[Dict[str, Any]],
    agent_message_id: str = None,
    jwt_token: str = "",
    latitude: str = "",
    longitude: str = "",
) -> AsyncGenerator[str, None]:
    history_text = format_history_for_agent(recent_history)

    history_block = ""
    if history_text:
        history_block = f"\n\n## Recent Conversation History\n{history_text}"

    mcp_tools = await get_mcp_tools()

    researcher = build_researcher_agent(token)
    inventory = build_inventory_agent(mcp_tools, jwt_token)
    directory = build_directory_agent(mcp_tools, latitude=latitude, longitude=longitude)

    team = Team(
        name="PillBin Team",
        members=[researcher, inventory, directory],
        model=get_fast_llm(),
        stream_member_events=False,
        output_schema=Output,
        tool_call_limit=3,
        retries=2,
        debug_mode=False,
        instructions="""
<role>
You are PillBin's front-desk coordinator. Your job is to route user queries
to the right specialist agent, synthesise their responses, and return a
single structured reply conforming to the output schema provided.
You never fabricate data.
</role>

<identity_constraints>
- NEVER ask the user for a token, JWT, or login credentials.
  Authentication is handled automatically by the system.
- NEVER fabricate personal data (medicines, inventory, lab values, etc.)
- ALWAYS recommend a clinician for any clinical decision.
- ALWAYS use the exact value '{agent_message_id}' for the `id` field.
</identity_constraints>

<step_1_check_history>
Check whether {history_block} already contains enough information
to answer the query completely.
- If YES → answer directly. Do NOT delegate to any agent.
- If NO  → proceed to Step 2.
</step_1_check_history>

<step_2_routing>
Route based on the PRIMARY intent of the query. Apply rules IN ORDER:

1. INVENTORY AGENT
   Triggers: personal prescriptions, medication inventory, expiry dates,
   deleted meds, stock levels.
   ⚠ Do NOT route here for reports, documents, or lab results.

2. DIRECTORY AGENT
   Triggers: nearby clinics, hospitals, pharmacies, medical facility search,
   location queries.

3. RESEARCHER AGENT
   Triggers: medical knowledge, symptoms, personal health questions,
   diagnoses, uploaded reports, documents, lab results, test results,
   knowledge base queries.
   ⚠ ANY mention of "report", "document", "lab result", "test result",
   or "knowledge base" → ALWAYS route here, never to Inventory Agent.

4. MULTIPLE AGENTS
   When a query spans more than one domain, delegate to all relevant agents
   and synthesise their answers into one cohesive reply.
</step_2_routing>

<step_3_output>
Set `isTable = true` when the response contains ANY of:
  medical data · statistics · lab values · medication lists ·
  inventory summaries · medical centre lists · comparative information

When isTable = true  → `message` is a 1–2 sentence summary only.
When isTable = false → `message` carries the full answer;
                       tableColumns and tableRows must be empty.
</step_3_output>
""",
    )

    full_response_obj = None
    full_response_str = ""
    try:
        async for event in team.arun(user_message, stream=True, stream_events=True):
            if event.event == TeamRunEvent.run_content:
                content = event.content
                if content:
                    if isinstance(content, str):
                        full_response_str += content
                        print(f"[Agent intermediate]: {content}", end="", flush=True)
                    else:
                        full_response_obj = content
                        json_str = (
                            content.model_dump_json()
                            if hasattr(content, "model_dump_json")
                            else str(content)
                        )
                        print(f"\n✅ Final Output: {json_str}")
                        yield json_str

            elif event.event == TeamRunEvent.tool_call_started:
                tool_name = event.tool.tool_name
                step = f"\n⚙️ Calling tool: **{tool_name}**"
                try:
                    args = event.tool.tool_args
                    if args and isinstance(args, dict):
                        target = (
                            args.get("member_id")
                            or args.get("member")
                            or args.get("agent_id")
                            or args.get("agent")
                        )
                        if target:
                            step += f" (Delegating to: **{target}**)"
                except Exception:
                    pass
                step += "...\n"
                print(step)

            elif event.event == TeamRunEvent.tool_call_completed:
                tool_name = event.tool.tool_name
                step = f"✅ Tool done: **{tool_name}**"
                try:
                    args = event.tool.tool_args
                    if args and isinstance(args, dict):
                        target = (
                            args.get("member_id")
                            or args.get("member")
                            or args.get("agent_id")
                            or args.get("agent")
                        )
                        if target:
                            step += f" (Delegating to: **{target}**)"
                except Exception:
                    pass
                step += "\n"
                print(step)

            elif event.event == TeamRunEvent.run_completed:
                if not full_response_obj and not full_response_str and event.content:
                    c = event.content
                    if isinstance(c, str):
                        full_response_str = c
                        yield c
                    else:
                        full_response_obj = c
                        yield (
                            c.model_dump_json()
                            if hasattr(c, "model_dump_json")
                            else str(c)
                        )

            elif event.event == TeamRunEvent.run_error:
                error_msg = getattr(event, "error", str(event))
                print(f"\n❌ [Team Run Error]: {error_msg}")
                err_out = Output(
                    id=agent_message_id or "error-id",
                    message=f"Error: {error_msg}",
                    confidence=0.0,
                )
                yield err_out.model_dump_json()

            elif event.event == TeamRunEvent.tool_call_error:
                tool_name = "Unknown tool"
                if hasattr(event, "tool"):
                    tool_name = getattr(event.tool, "tool_name", tool_name)
                error_msg = getattr(event, "error", str(event))
                print(f"\n❌ [Tool Call Error] in {tool_name}: {error_msg}")
                err_out = Output(
                    id=agent_message_id or "error-id",
                    message=f"Tool error in {tool_name}: {error_msg}",
                    confidence=0.0,
                )
                yield err_out.model_dump_json()

    except BaseException as e:
        if hasattr(e, "exceptions"):
            for sub in e.exceptions:
                print(f"[Sub-exception]: {type(sub).__name__}: {sub}")
                traceback.print_exception(type(sub), sub, sub.__traceback__)
        else:
            print(f"[Team error]: {type(e).__name__}: {e}")
            traceback.print_exc()

        err_out = Output(
            id=agent_message_id or "error-id",
            message=f"An unexpected error occurred: {str(e)}",
            confidence=0.0,
        )
        yield err_out.model_dump_json()
        raise
