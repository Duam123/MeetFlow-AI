
from langgraph.graph import StateGraph, START, END

from app.agents.agent_state import MeetFlowState

from app.agents.agent_nodes import (
    intent_detection_node,
    tool_selection_node,
    tool_execution_node,
    response_node,
)

from app.tools.tool_registry import get_all_tools


# =========================================================
# TOOL CONFIGURATION
# =========================================================

# Only these state-changing tools can execute after approval.
# Add another mutation tool here only after implementing
# its validation and approval workflow.

APPROVAL_REQUIRED_TOOLS = {
    "create_new_meeting",
    "update_existing_meeting",
    "create_new_task",
    "update_existing_task",
}


# =========================================================
# GRAPH ROUTING
# =========================================================

def route_after_selection(state: MeetFlowState) -> str:
    """Decide whether a request can execute immediately."""

    if state.get("error"):
        return "response"

    if not state.get("tool_name"):
        return "response"

    # Mutating actions must wait for user approval.
    if state.get("requires_confirmation"):
        return "response"

    return "execute"


# =========================================================
# BUILD AGENT GRAPH
# =========================================================

def build_agent_graph():
    """Build and compile the MeetFlow AI agent."""

    workflow = StateGraph(MeetFlowState)

    workflow.add_node("detect_intent", intent_detection_node)
    workflow.add_node("select_tool", tool_selection_node)
    workflow.add_node("execute_tool", tool_execution_node)
    workflow.add_node("generate_response", response_node)

    workflow.add_edge(START, "detect_intent")
    workflow.add_edge("detect_intent", "select_tool")

    workflow.add_conditional_edges(
        "select_tool",
        route_after_selection,
        {
            "execute": "execute_tool",
            "response": "generate_response",
        },
    )

    workflow.add_edge("execute_tool", "generate_response")
    workflow.add_edge("generate_response", END)

    return workflow.compile()


# Compile once when the application starts.
meetflow_agent = build_agent_graph()


# =========================================================
# INITIAL AGENT STATE
# =========================================================

def create_initial_state(user_message: str) -> dict:
    """Create a clean state for every new user request."""

    return {
        "user_message": user_message,

        "intent": None,
        "agent_domain": None,

        "tool_name": None,
        "tool_input": {},
        "tool_result": None,

        "final_response": None,

        "requires_confirmation": False,
        "approved": False,
        "validation_result": None,
        "pending_action": None,

        "observations": [],
        "iteration_count": 0,

        "error": None,
    }


# =========================================================
# RUN AGENT
# =========================================================

def run_agent(user_message: str) -> dict:
    """Run a new user request through the agent graph."""

    initial_state = create_initial_state(user_message)

    return meetflow_agent.invoke(initial_state)


# =========================================================
# APPROVE PENDING ACTION
# =========================================================

def approve_pending_action(agent_result: dict) -> dict:
    """
    Execute the exact action previously prepared by the agent.

    Important:
    - Does not call the LLM again.
    - Does not reinterpret the original message.
    - Executes only an approved, registered mutation tool.
    """

    result = dict(agent_result or {})

    if not result.get("requires_confirmation"):
        result["error"] = "There is no action waiting for approval."
        result["final_response"] = result["error"]
        return result

    pending = result.get("pending_action")

    if not isinstance(pending, dict):
        result["error"] = "Pending action is missing or invalid."
        result["final_response"] = result["error"]
        return result

    # Support the standard pending-action structure.
    tool_name = (
        pending.get("tool_name")
        or result.get("tool_name")
    )

    tool_input = (
        pending.get("tool_input")
        or pending.get("input")
        or pending.get("arguments")
        or result.get("tool_input")
    )

    if not tool_name or not isinstance(tool_input, dict):
        result["error"] = "The pending action does not contain valid tool arguments."
        result["final_response"] = result["error"]
        return result

    if tool_name not in APPROVAL_REQUIRED_TOOLS:
        result["error"] = f"Approval is not permitted for tool: {tool_name}"
        result["final_response"] = result["error"]
        return result

    # Verify that the approved action matches the prepared action.
    original_tool_name = result.get("tool_name")

    if original_tool_name and original_tool_name != tool_name:
        result["error"] = "The pending tool does not match the selected tool."
        result["final_response"] = result["error"]
        return result

    original_input = result.get("tool_input") or {}

    if original_input and original_input != tool_input:
        result["error"] = "The pending arguments do not match the prepared action."
        result["final_response"] = result["error"]
        return result

    # Find the exact registered LangChain tool.
    registered_tools = get_all_tools()

    tool_map = {
        tool.name: tool
        for tool in registered_tools
    }

    selected_tool = tool_map.get(tool_name)

    if selected_tool is None:
        result["error"] = f"Registered tool not found: {tool_name}"
        result["final_response"] = result["error"]
        return result

    # Execute only after the explicit approval call.
    try:
        tool_result = selected_tool.invoke(tool_input)

        result["tool_result"] = tool_result
        result["approved"] = True
        result["requires_confirmation"] = False
        result["pending_action"] = None
        result["error"] = None

        result["final_response"] = (
            f"Action approved and executed successfully.\n\n"
            f"Tool: {tool_name}\n"
            f"Result: {tool_result}"
        )

    except Exception as exc:
        result["approved"] = True
        result["error"] = str(exc)
        result["final_response"] = (
            f"The action was approved, but execution failed: {exc}"
        )

    return result


# =========================================================
# REJECT PENDING ACTION
# =========================================================

def reject_pending_action(agent_result: dict) -> dict:
    """Reject a pending action without executing it."""

    result = dict(agent_result or {})

    result["approved"] = False
    result["requires_confirmation"] = False
    result["pending_action"] = None

    result["final_response"] = (
        "Action rejected. No changes were made."
    )

    result["error"] = None

    return result
