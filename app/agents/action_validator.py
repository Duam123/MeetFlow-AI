
import re
from datetime import datetime


# =========================================================
# REQUIRED FIELDS
# =========================================================

REQUIRED_FIELDS = {
    "create_meeting": [
        "title",
        "meeting_date",
        "start_time",
        "end_time",
    ],

    "update_meeting": [
        "meeting_id",
    ],

    "cancel_meeting": [
        "meeting_id",
    ],

    "create_task": [
        "title",
        "due_date",
        "due_time",
    ],

    "update_task": [
        "task_id",
    ],

    "complete_task": [
        "task_id",
    ],
}


# =========================================================
# ALLOWED UPDATE FIELDS
# =========================================================

MEETING_UPDATE_FIELDS = {
    "title",
    "meeting_date",
    "start_time",
    "end_time",
    "participants",
    "participant_emails",
    "meeting_link",
    "agenda",
    "description",
    "status",
    "reminder_minutes",
}

TASK_UPDATE_FIELDS = {
    "title",
    "due_date",
    "due_time",
    "assigned_to",
    "assigned_email",
    "priority",
    "status",
    "reminder_minutes",
    "related_meeting_id",
    "description",
}

ALLOWED_PRIORITIES = {
    "low",
    "medium",
    "high",
    "critical",
}

ALLOWED_TASK_STATUSES = {
    "pending",
    "in progress",
    "completed",
    "cancelled",
}

ALLOWED_MEETING_STATUSES = {
    "scheduled",
    "completed",
    "cancelled",
}


# =========================================================
# VALIDATION HELPERS
# =========================================================

def is_valid_date(value):

    if not isinstance(value, str):
        return False

    try:

        parsed = datetime.strptime(
            value,
            "%Y-%m-%d",
        )

        return parsed.strftime("%Y-%m-%d") == value

    except ValueError:
        return False


def is_valid_time(value):

    if not isinstance(value, str):
        return False

    return bool(
        re.fullmatch(
            r"(?:[01]\d|2[0-3]):[0-5]\d",
            value,
        )
    )


def is_valid_title(value):

    return (
        isinstance(value, str)
        and bool(value.strip())
        and len(value.strip()) <= 200
    )


def is_valid_id(value):

    return (
        isinstance(value, str)
        and bool(value.strip())
        and len(value.strip()) <= 100
    )


def validate_reminder(value):

    if isinstance(value, bool):
        return False

    try:

        number = int(value)

        if str(value).strip() != str(number):
            return False

        return 0 <= number <= 10080

    except (ValueError, TypeError):
        return False


def validation_error(message, missing_fields=None):

    return {
        "valid": False,
        "missing_fields": missing_fields or [],
        "error": message,
    }


def validation_success():

    return {
        "valid": True,
        "missing_fields": [],
        "error": None,
    }


# =========================================================
# MAIN VALIDATOR
# =========================================================

def validate_action_input(intent, tool_input):

    if not isinstance(tool_input, dict):

        return validation_error(
            "Tool input must be a dictionary."
        )

    if intent not in REQUIRED_FIELDS:

        return validation_error(
            f"Unsupported intent: {intent}"
        )

    # -----------------------------------------------------
    # REQUIRED FIELDS
    # -----------------------------------------------------

    missing_fields = []

    for field in REQUIRED_FIELDS[intent]:

        value = tool_input.get(field)

        if value is None or (
            isinstance(value, str) and not value.strip()
        ):
            missing_fields.append(field)

    if missing_fields:

        return validation_error(
            "Some required information is missing.",
            missing_fields,
        )

    # -----------------------------------------------------
    # SELECT ALLOWED FIELDS
    # -----------------------------------------------------

    if intent in {
        "create_meeting",
        "update_meeting",
        "cancel_meeting",
    }:

        allowed_fields = (
            MEETING_UPDATE_FIELDS
            | {"meeting_id"}
        )

    elif intent in {
        "create_task",
        "update_task",
        "complete_task",
    }:

        allowed_fields = (
            TASK_UPDATE_FIELDS
            | {"task_id"}
        )

    else:
        allowed_fields = set()

    unknown_fields = (
        set(tool_input.keys()) - allowed_fields
    )

    if unknown_fields:

        return validation_error(
            "Unsupported fields: "
            + ", ".join(sorted(unknown_fields))
        )

    # -----------------------------------------------------
    # ID VALIDATION
    # -----------------------------------------------------

    if "meeting_id" in tool_input:

        if not is_valid_id(tool_input["meeting_id"]):

            return validation_error(
                "Invalid meeting ID."
            )

    if "task_id" in tool_input:

        if not is_valid_id(tool_input["task_id"]):

            return validation_error(
                "Invalid task ID."
            )

    # -----------------------------------------------------
    # TITLE VALIDATION
    # -----------------------------------------------------

    if "title" in tool_input:

        if not is_valid_title(tool_input["title"]):

            return validation_error(
                "Title must contain 1 to 200 characters."
            )

    # -----------------------------------------------------
    # DATE VALIDATION
    # -----------------------------------------------------

    date_fields = [
        "meeting_date",
        "due_date",
    ]

    for field in date_fields:

        if field in tool_input:

            if not is_valid_date(tool_input[field]):

                return validation_error(
                    f"Invalid {field}. Use YYYY-MM-DD format."
                )

    # -----------------------------------------------------
    # TIME VALIDATION
    # -----------------------------------------------------

    time_fields = [
        "start_time",
        "end_time",
        "due_time",
    ]

    for field in time_fields:

        if field in tool_input:

            if not is_valid_time(tool_input[field]):

                return validation_error(
                    f"Invalid {field}. Use HH:MM format."
                )

    # -----------------------------------------------------
    # MEETING TIME RANGE
    # -----------------------------------------------------

    if (
        "start_time" in tool_input
        and "end_time" in tool_input
    ):

        start = tool_input["start_time"]
        end = tool_input["end_time"]

        if start >= end:

            return validation_error(
                "Meeting end time must be after start time."
            )

    # -----------------------------------------------------
    # PRIORITY VALIDATION
    # -----------------------------------------------------

    if "priority" in tool_input:

        priority = str(
            tool_input["priority"]
        ).strip().lower()

        if priority not in ALLOWED_PRIORITIES:

            return validation_error(
                "Invalid priority. Use Low, Medium, High or Critical."
            )

    # -----------------------------------------------------
    # TASK STATUS VALIDATION
    # -----------------------------------------------------

    if (
        "status" in tool_input
        and intent in {
            "create_task",
            "update_task",
            "complete_task",
        }
    ):

        status = str(
            tool_input["status"]
        ).strip().lower()

        if status not in ALLOWED_TASK_STATUSES:

            return validation_error(
                "Invalid task status. Use Pending, In Progress, "
                "Completed or Cancelled."
            )

    # -----------------------------------------------------
    # MEETING STATUS VALIDATION
    # -----------------------------------------------------

    if (
        "status" in tool_input
        and intent in {
            "create_meeting",
            "update_meeting",
            "cancel_meeting",
        }
    ):

        status = str(
            tool_input["status"]
        ).strip().lower()

        if status not in ALLOWED_MEETING_STATUSES:

            return validation_error(
                "Invalid meeting status. Use Scheduled, "
                "Completed or Cancelled."
            )

    # -----------------------------------------------------
    # REMINDER VALIDATION
    # -----------------------------------------------------

    if "reminder_minutes" in tool_input:

        if not validate_reminder(
            tool_input["reminder_minutes"]
        ):

            return validation_error(
                "Reminder minutes must be between 0 and 10080."
            )

    # -----------------------------------------------------
    # SUCCESS
    # -----------------------------------------------------

    return validation_success()
