
from typing import TypedDict, Optional, Any


class MeetFlowState(TypedDict):
    """
    Shared state for the unified MeetFlow AI Agent.

    Supports:
    - Meetings management
    - Tasks management
    - Gmail operations
    - ReAct agent workflow
    - Action validation and confirmation
    """

    # User request
    user_message: str

    # Intent detection
    intent: Optional[str]
    agent_domain: Optional[str]

    # Tool selection and execution
    tool_name: Optional[str]
    tool_input: Optional[dict]
    tool_result: Optional[Any]

    # Agent response
    final_response: Optional[str]

    # Action safety
    requires_confirmation: bool
    approved: bool
    validation_result: Optional[dict]
    pending_action: Optional[dict]

    # ReAct workflow tracking
    observations: list[str]
    iteration_count: int

    # Error handling
    error: Optional[str]
