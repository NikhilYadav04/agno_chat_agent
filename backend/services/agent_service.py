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


async def stream_agent_response(
    token: str,
    user_message: str,
    recent_history: List[Dict[str, Any]],
    agent_message_id: str = None,
) -> AsyncGenerator[str, None]:
    """
    Streams the Team response chunk by chunk.

    Flow:
      1. Build history context string from recent_history.
      2. Open a single shared MCP context manager.
      3. Build the 3 specialist agents and the coordinating Team lead.
      4. Stream team.arun() and yield chunks.
      5. Prune user memories after each run.
    """
    # 1. Build history block
    history_text = format_history_for_agent(recent_history)

    history_block = ""
    if history_text:
        history_block = f"\n\n## Recent Conversation History\n{history_text}"

    # 2. Open a single shared MCP connection for the entire run
    mcp = MCPTools(transport="streamable-http", url=_MCP_URL)
    async with mcp as mcp_tools:

        # 3. Build specialist agents
        researcher = build_researcher_agent(token)
        inventory  = build_inventory_agent(mcp_tools)
        directory  = build_directory_agent(mcp_tools)

        # Enable deep debug on all sub-agents
        researcher.debug_mode = True
        inventory.debug_mode  = True
        directory.debug_mode  = True

        # Build the coordinating Team lead (cheap gpt-4o-mini)
        team = Team(
            name="PillBin Team",
            members=[researcher, inventory, directory],
            model=get_fast_llm(),
            #mode=TeamMode.coordinate,       # Delegate + synthesize (default)
            stream_member_events=False,      # Keep the frontend stream clean
            output_schema=Output,            # Enforce Pydantic schema on final answer
            tool_call_limit=3,
            retries=2,
            debug_mode=True,                 # Full team-level debug logs
            debug_level=2,                   # Maximum verbosity (prompts + tool calls)
            instructions=f"""You are the PillBin front-desk coordinator.{history_block}

If the conversation history above is sufficient to answer the query, answer directly — do NOT delegate to any agent.

Otherwise, delegate based on the query intent:
- Personal prescriptions / medication inventory / expiry dates / deleted meds / stock → Inventory Agent
- Nearby clinics / hospitals / medical facility search / pharmacy locations → Directory Agent
- Medical knowledge / symptoms / general health / diagnoses / uploaded reports / documents / knowledge base / lab results → Researcher Agent
- Multi-domain queries → Delegate to multiple agents and synthesise their answers.

If the query mentions a "report", "document", "lab result", "test result", or "knowledge base" — ALWAYS route to Researcher Agent, NOT Inventory Agent.

Always compose a single, concise, cohesive final response. Never fabricate personal data. Recommend a clinician for clinical decisions.

IMPORTANT: You MUST use the exact ID '{agent_message_id}' for the 'id' field in your final JSON Output schema response.""",
        )

        # 4. Stream the Team response
        full_response_obj = None
        full_response_str = ""
        try:
            async for event in team.arun(
                user_message, stream=True, stream_events=True
            ):
                if event.event == TeamRunEvent.run_content:
                    content = event.content
                    if content:
                        if isinstance(content, str):
                            # Intermediate text — log only, do NOT stream to client
                            full_response_str += content
                            print(f"[Agent intermediate]: {content}", end="", flush=True)
                        else:
                            # Final Pydantic Output object — serialise and yield to client
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
                            target = args.get("member_id") or args.get("member") or args.get("agent_id") or args.get("agent")
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
                            target = args.get("member_id") or args.get("member") or args.get("agent_id") or args.get("agent")
                            if target:
                                step += f" (Delegating to: **{target}**)"
                    except Exception:
                        pass
                    step += "\n"
                    print(step)

                elif event.event == TeamRunEvent.run_completed:
                    # Fallback: if structured output only arrives at run_completed
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
                # --- Error Handling ---
                elif event.event == TeamRunEvent.run_error:
                    error_msg = getattr(event, "error", str(event))
                    print(f"\n❌ [Team Run Error]: {error_msg}")
                    # Enforce consistent Pydantic JSON stream output
                    err_out = Output(id=agent_message_id or "error-id", message=f"Error: {error_msg}", confidence=0.0)
                    yield err_out.model_dump_json()

                elif event.event == TeamRunEvent.tool_call_error:
                    tool_name = "Unknown tool"
                    if hasattr(event, "tool"):
                        tool_name = getattr(event.tool, "tool_name", tool_name)
                    error_msg = getattr(event, "error", str(event))
                    print(f"\n❌ [Tool Call Error] in {tool_name}: {error_msg}")
                    err_out = Output(id=agent_message_id or "error-id", message=f"Tool error in {tool_name}: {error_msg}", confidence=0.0)
                    yield err_out.model_dump_json()

        except BaseException as e:
            if hasattr(e, "exceptions"):
                for sub in e.exceptions:
                    print(f"[Sub-exception]: {type(sub).__name__}: {sub}")
                    traceback.print_exception(type(sub), sub, sub.__traceback__)
            else:
                print(f"[Team error]: {type(e).__name__}: {e}")
                traceback.print_exc()
            
            # Send consistent JSON error to frontend before raising
            err_out = Output(id=agent_message_id or "error-id", message=f"An unexpected error occurred: {str(e)}", confidence=0.0)
            yield err_out.model_dump_json()
            raise
