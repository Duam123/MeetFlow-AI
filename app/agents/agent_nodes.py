
from app.llm.structured_output import generate_structured_output
from app.tools.tool_registry import get_all_tools
from app.agents.action_validator import validate_action_input

from app.database.meeting_store import get_task, get_meeting


# =========================================================
# ACCESS RULES
# =========================================================

READ_ONLY_INTENTS = {
    "view_meetings",
    "view_tasks",
    "view_unread_emails",
    "analyze_unread_emails",
}

APPROVAL_REQUIRED_TOOLS = {
    "create_new_meeting",
    "update_existing_meeting",
    "create_new_task",
    "update_existing_task",
}

UPDATE_INTENTS = {
    "update_task",
    "update_meeting",
    "complete_task",
    "cancel_meeting",
}

INTENT_TO_UPDATE_TYPE = {
    "update_task": "update_task",
    "complete_task": "update_task",
    "update_meeting": "update_meeting",
    "cancel_meeting": "update_meeting",
}

EXPECTED_TOOLS = {
    "update_task": "update_existing_task",
    "complete_task": "update_existing_task",
    "update_meeting": "update_existing_meeting",
    "cancel_meeting": "update_existing_meeting",
}


# =========================================================
# DATABASE FIELDS
# =========================================================

TASK_FIELDS = [
    "title",
    "due_date",
    "due_time",
    "assigned_to",
    "assigned_email",
    "priority",
    "status",
    "reminder_minutes",
    "related_meeting_id",
]

MEETING_FIELDS = [
    "title",
    "meeting_date",
    "start_time",
    "end_time",
    "participants",
    "participant_emails",
    "meeting_link",
    "agenda",
    "status",
    "reminder_minutes",
]


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def get_tool_map():
    return {
        tool.name: tool
        for tool in get_all_tools()
    }


def get_tool_input(state):
    value = state.get("tool_input")

    if isinstance(value, dict):
        return value.copy()

    return {}


def get_record_value(record, field, default=None):

    if isinstance(record, dict):
        return record.get(field, default)

    try:
        return record[field]
    except (KeyError, TypeError, IndexError):
        return default


# =========================================================
# PARTIAL UPDATE PREPARATION
# =========================================================

def prepare_partial_update(intent, tool_input):
    """
    Fetch existing record and merge only requested changes.
    This function does not modify the database.
    """

    update_type = INTENT_TO_UPDATE_TYPE.get(intent)

    # -----------------------------------------------------
    # TASK UPDATE / COMPLETION
    # -----------------------------------------------------

    if update_type == "update_task":

        task_id = tool_input.get("task_id")

        if not task_id:
            raise ValueError(
                "Please provide the Task ID."
            )

        existing_record = get_task(task_id)

        if not existing_record:
            raise ValueError(
                f"No task found with ID: {task_id}"
            )

        merged_input = {
            field: get_record_value(existing_record, field)
            for field in TASK_FIELDS
        }

        merged_input["task_id"] = task_id

        # Apply only the requested changes.
        for field in TASK_FIELDS:

            if field in tool_input:
                merged_input[field] = tool_input[field]

        # Completion command.
        if intent == "complete_task":
            merged_input["status"] = "Completed"

        return merged_input

    # -----------------------------------------------------
    # MEETING UPDATE / CANCELLATION
    # -----------------------------------------------------

    if update_type == "update_meeting":

        meeting_id = tool_input.get("meeting_id")

        if not meeting_id:
            raise ValueError(
                "Please provide the Meeting ID."
            )

        existing_record = get_meeting(meeting_id)

        if not existing_record:
            raise ValueError(
                f"No meeting found with ID: {meeting_id}"
            )

        merged_input = {
            field: get_record_value(existing_record, field)
            for field in MEETING_FIELDS
        }

        merged_input["meeting_id"] = meeting_id

        # Apply only the requested changes.
        for field in MEETING_FIELDS:

            if field in tool_input:
                merged_input[field] = tool_input[field]

        # Cancellation command.
        if intent == "cancel_meeting":
            merged_input["status"] = "Cancelled"

        return merged_input

    raise ValueError("Unsupported update operation.")


# =========================================================
# NODE 1: INTENT DETECTION
# =========================================================

def intent_detection_node(state):

    user_message = state.get("user_message", "").strip()

    if not user_message:
        return {
            "error": "Please enter a message.",
            "final_response": "Please enter a message.",
        }

    try:

        result = generate_structured_output(user_message)

        if not isinstance(result, dict):
            raise ValueError("Invalid structured output.")

        return {
            "intent": result.get("intent", "unknown"),
            "agent_domain": result.get("agent_domain"),
            "tool_name": result.get("tool_name"),
            "tool_input": result.get("tool_input") or {},
            "requires_confirmation": False,
            "approved": False,
            "pending_action": None,
            "validation_result": None,
            "tool_result": None,
            "final_response": None,
            "error": None,
            "observations": [],
            "iteration_count": 0,
        }

    except Exception as exc:

        print(f"Intent detection error: {exc}")

        return {
            "error": "Intent detection failed.",
            "final_response": (
                "I could not understand the request. Please try again."
            ),
        }


# =========================================================
# NODE 2: TOOL SELECTION AND VALIDATION
# =========================================================

def tool_selection_node(state):

    intent = state.get("intent")
    tool_name = state.get("tool_name")
    tool_input = get_tool_input(state)

    tool_map = get_tool_map()

    if not tool_name:
        return {
            "error": "No suitable tool was selected.",
            "final_response": (
                "I could not find a suitable action."
            ),
        }

    if tool_name not in tool_map:
        return {
            "error": f"Tool is not registered: {tool_name}",
            "final_response": (
                f"The requested tool '{tool_name}' is unavailable."
            ),
        }

    # -----------------------------------------------------
    # READ-ONLY OPERATIONS
    # -----------------------------------------------------

    if intent in READ_ONLY_INTENTS:

        return {
            "requires_confirmation": False,
            "approved": False,
            "pending_action": None,
            "validation_result": {
                "valid": True,
                "missing_fields": [],
                "error": None,
            },
            "error": None,
        }

    # -----------------------------------------------------
    # MUTATION PERMISSION CHECK
    # -----------------------------------------------------

    if tool_name not in APPROVAL_REQUIRED_TOOLS:

        return {
            "error": (
                f"Tool '{tool_name}' is not allowed "
                "in the approval workflow."
            ),
            "final_response": (
                "This action is not currently supported."
            ),
        }

    expected_tool = EXPECTED_TOOLS.get(intent)

    if expected_tool and tool_name != expected_tool:

        return {
            "error": "Selected tool does not match the requested action.",
            "final_response": (
                "I could not safely prepare this action."
            ),
        }

    # -----------------------------------------------------
    # INITIAL VALIDATION
    # -----------------------------------------------------

    validation_result = validate_action_input(
        intent,
        tool_input,
    )

    if not validation_result.get("valid"):

        return {
            "validation_result": validation_result,
            "requires_confirmation": False,
            "approved": False,
            "pending_action": None,
            "error": None,
        }

    # -----------------------------------------------------
    # PARTIAL UPDATE PREPARATION
    # -----------------------------------------------------

    if intent in UPDATE_INTENTS:

        try:

            merged_input = prepare_partial_update(
                intent,
                tool_input,
            )

            validation_intent = INTENT_TO_UPDATE_TYPE[intent]

            merged_validation = validate_action_input(
                validation_intent,
                merged_input,
            )

            if not merged_validation.get("valid"):

                return {
                    "validation_result": merged_validation,
                    "requires_confirmation": False,
                    "approved": False,
                    "pending_action": None,
                    "error": None,
                }

            tool_input = merged_input

        except Exception as exc:

            return {
                "error": str(exc),
                "final_response": str(exc),
                "requires_confirmation": False,
                "pending_action": None,
                "approved": False,
            }

    # -----------------------------------------------------
    # CREATE APPROVAL REQUEST
    # -----------------------------------------------------

    pending_action = {
        "intent": intent,
        "tool_name": tool_name,
        "tool_input": tool_input.copy(),
    }

    return {
        "tool_input": tool_input,
        "validation_result": {
            "valid": True,
            "missing_fields": [],
            "error": None,
        },
        "requires_confirmation": True,
        "approved": False,
        "pending_action": pending_action,
        "error": None,
    }


# =========================================================
# NODE 3: TOOL EXECUTION
# =========================================================

def tool_execution_node(state):

    if state.get("requires_confirmation"):

        return {
            "error": "This action is waiting for user approval.",
            "tool_result": None,
        }

    intent = state.get("intent")
    tool_name = state.get("tool_name")

    # Never execute mutations automatically.
    if intent not in READ_ONLY_INTENTS:

        return {
            "error": "This operation requires approval.",
            "tool_result": None,
        }

    try:

        tool_map = get_tool_map()
        selected_tool = tool_map.get(tool_name)

        if selected_tool is None:
            raise ValueError(
                f"Tool not found: {tool_name}"
            )

        tool_result = selected_tool.invoke(
            get_tool_input(state)
        )

        observations = list(
            state.get("observations") or []
        )

        observations.append({
            "tool": tool_name,
            "result": str(tool_result),
        })

        return {
            "tool_result": tool_result,
            "observations": observations,
            "iteration_count": (
                state.get("iteration_count", 0) + 1
            ),
            "error": None,
        }

    except Exception as exc:

        print(f"Tool execution error: {exc}")

        return {
            "error": f"Tool execution failed: {exc}",
            "tool_result": None,
        }


# =========================================================
# NODE 4: RESPONSE GENERATION
# =========================================================

def response_node(state):

    error = state.get("error")

    if error:
        return {
            "final_response": str(error),
        }

    intent = state.get("intent")

    if not intent or intent == "unknown":

        return {
            "final_response": (
                "I can help you manage meetings, tasks, "
                "and email-related information."
            ),
        }

    # -----------------------------------------------------
    # VALIDATION FEEDBACK
    # -----------------------------------------------------

    validation = state.get("validation_result") or {}

    if not validation.get("valid", False):

        missing_fields = validation.get("missing_fields") or []
        validation_error = validation.get("error")

        if missing_fields:

            return {
                "final_response": (
                    "I need some additional information.\n\n"
                    "Missing information: "
                    + ", ".join(missing_fields)
                ),
            }

        return {
            "final_response": (
                validation_error
                or "Please check the information and try again."
            ),
        }

    # -----------------------------------------------------
    # APPROVAL MESSAGE
    # -----------------------------------------------------

    if state.get("requires_confirmation"):

        pending = state.get("pending_action") or {}

        action_messages = {
            "complete_task": "Complete this task",
            "cancel_meeting": "Cancel this meeting",
            "update_task": "Update this task",
            "update_meeting": "Update this meeting",
            "create_task": "Create this task",
            "create_meeting": "Create this meeting",
        }

        action_text = action_messages.get(
            pending.get("intent", intent),
            "Execute this action",
        )

        return {
            "final_response": (
                f"{action_text}?\n\n"
                "Please review the details and approve or reject."
            ),
        }

    # -----------------------------------------------------
    # TOOL RESULT
    # -----------------------------------------------------

    tool_result = state.get("tool_result")

    if tool_result is not None:

        return {
            "final_response": str(tool_result),
        }

    return {
        "final_response": "Your request has been processed.",
    }
