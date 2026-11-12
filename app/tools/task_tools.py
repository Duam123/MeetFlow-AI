
from datetime import date, datetime

from langchain_core.tools import tool

from app.database.meeting_store import (
    create_task,
    get_all_tasks,
    get_task,
    update_task,
)


# =========================================================
# CONSTANTS
# =========================================================

ALLOWED_PRIORITIES = [
    "Low",
    "Medium",
    "High",
    "Critical",
]

ALLOWED_STATUSES = [
    "Pending",
    "In Progress",
    "Completed",
    "Cancelled",
]


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def normalize_priority(priority):
    """
    Convert priority into the correct database format.
    Example: high -> High
    """

    if not priority:
        return "Medium"

    priority = str(priority).strip().lower()

    priority_map = {
        "low": "Low",
        "medium": "Medium",
        "high": "High",
        "critical": "Critical",
    }

    return priority_map.get(priority)


def normalize_status(status):
    """
    Normalize task status.
    """

    if not status:
        return "Pending"

    status = str(status).strip().lower()

    status_map = {
        "pending": "Pending",
        "in progress": "In Progress",
        "in_progress": "In Progress",
        "completed": "Completed",
        "complete": "Completed",
        "done": "Completed",
        "cancelled": "Cancelled",
        "canceled": "Cancelled",
    }

    return status_map.get(status)


def validate_date(date_value):
    """
    Validate ISO date format: YYYY-MM-DD
    """

    try:
        datetime.strptime(str(date_value), "%Y-%m-%d")
        return True

    except (ValueError, TypeError):
        return False


def validate_time(time_value):
    """
    Validate time format: HH:MM
    """

    try:
        datetime.strptime(str(time_value), "%H:%M")
        return True

    except (ValueError, TypeError):
        return False


def get_task_value(task, key, default=None):
    """
    Safely read values from database task records.
    """

    if not task:
        return default

    if isinstance(task, dict):
        return task.get(key, default)

    try:
        return task[key]

    except (KeyError, IndexError, TypeError):
        return default


# =========================================================
# TOOL 1: VIEW ALL TASKS
# =========================================================

@tool
def view_tasks() -> str:
    """
    Retrieve all tasks from the MeetFlow database.

    Use this tool when the user asks to:
    - View tasks
    - Show all tasks
    - Check pending tasks
    - See task deadlines
    - Review task assignments
    """

    try:

        tasks = get_all_tasks()

        if not tasks:
            return "No tasks found in MeetFlow."

        result = []

        for task in tasks:

            task_id = get_task_value(task, "task_id", "N/A")
            title = get_task_value(task, "title", "Untitled")
            assigned_to = get_task_value(
                task,
                "assigned_to",
                "Unassigned",
            )

            due_date = get_task_value(
                task,
                "due_date",
                "Not specified",
            )

            due_time = get_task_value(
                task,
                "due_time",
                "Not specified",
            )

            priority = get_task_value(
                task,
                "priority",
                "Medium",
            )

            status = get_task_value(
                task,
                "status",
                "Pending",
            )

            result.append(
                f"""
Task ID: {task_id}
Title: {title}
Assigned To: {assigned_to}
Due Date: {due_date}
Due Time: {due_time}
Priority: {priority}
Status: {status}
"""
            )

        return (
            f"Found {len(tasks)} task(s):\n\n"
            + "\n----------------------\n".join(result)
        )

    except Exception as error:

        return f"Error retrieving tasks: {str(error)}"


# =========================================================
# TOOL 2: CREATE NEW TASK
# =========================================================

@tool
def create_new_task(
    title: str,
    due_date: str,
    due_time: str,
    assigned_to: str = "",
    assigned_email: str = "",
    priority: str = "Medium",
    status: str = "Pending",
    reminder_minutes: int = 30,
    related_meeting_id: str = "",
) -> str:
    """
    Create a new task in the MeetFlow database.

    Required:
    - title
    - due_date in YYYY-MM-DD format
    - due_time in HH:MM format

    Optional:
    - assigned_to
    - assigned_email
    - priority: Low, Medium, High or Critical
    - status: Pending, In Progress, Completed or Cancelled
    - reminder_minutes
    - related_meeting_id
    """

    try:

        # ---------------------------------------------
        # TITLE VALIDATION
        # ---------------------------------------------

        if not title or not title.strip():

            return "Task title is required."

        title = title.strip()

        # ---------------------------------------------
        # DATE VALIDATION
        # ---------------------------------------------

        if not validate_date(due_date):

            return (
                "Invalid due date. "
                "Use YYYY-MM-DD format."
            )

        # ---------------------------------------------
        # TIME VALIDATION
        # ---------------------------------------------

        if not validate_time(due_time):

            return (
                "Invalid due time. "
                "Use HH:MM format."
            )

        # ---------------------------------------------
        # PRIORITY NORMALIZATION
        # ---------------------------------------------

        priority = normalize_priority(priority)

        if priority not in ALLOWED_PRIORITIES:

            return (
                "Invalid priority. "
                "Use Low, Medium, High or Critical."
            )

        # ---------------------------------------------
        # STATUS NORMALIZATION
        # ---------------------------------------------

        status = normalize_status(status)

        if status not in ALLOWED_STATUSES:

            return (
                "Invalid status. "
                "Use Pending, In Progress, "
                "Completed or Cancelled."
            )

        # ---------------------------------------------
        # REMINDER VALIDATION
        # ---------------------------------------------

        try:

            reminder_minutes = int(reminder_minutes)

        except (ValueError, TypeError):

            return "Reminder minutes must be a number."

        if reminder_minutes < 0:

            return "Reminder minutes cannot be negative."

        # ---------------------------------------------
        # CREATE TASK IN DATABASE
        # ---------------------------------------------

        task_id = create_task(
            title=title,
            due_date=due_date,
            due_time=due_time,
            assigned_to=assigned_to.strip(),
            assigned_email=assigned_email.strip(),
            priority=priority,
            status=status,
            reminder_minutes=reminder_minutes,
            related_meeting_id=related_meeting_id or None,
        )

        return (
            "Task created successfully!\n\n"
            f"Task ID: {task_id}\n"
            f"Title: {title}\n"
            f"Priority: {priority}\n"
            f"Due Date: {due_date}\n"
            f"Due Time: {due_time}\n"
            f"Status: {status}"
        )

    except Exception as error:

        return f"Error creating task: {str(error)}"


# =========================================================
# TOOL 3: GET TASK DETAILS
# =========================================================

@tool
def get_task_details(task_id: str) -> str:
    """
    Retrieve complete information about a specific task.

    Use this tool when the user asks about a particular
    task or provides a task ID.
    """

    try:

        if not task_id or not task_id.strip():

            return "Please provide a valid task ID."

        task = get_task(task_id.strip())

        if not task:

            return f"No task found with ID: {task_id}"

        return f"""
Task Details

Task ID: {get_task_value(task, 'task_id', 'N/A')}
Title: {get_task_value(task, 'title', 'N/A')}
Assigned To: {get_task_value(task, 'assigned_to', 'Unassigned')}
Assigned Email: {get_task_value(task, 'assigned_email', 'N/A')}
Due Date: {get_task_value(task, 'due_date', 'N/A')}
Due Time: {get_task_value(task, 'due_time', 'N/A')}
Priority: {get_task_value(task, 'priority', 'Medium')}
Status: {get_task_value(task, 'status', 'Pending')}
Reminder Minutes: {get_task_value(task, 'reminder_minutes', 30)}
Related Meeting ID: {get_task_value(task, 'related_meeting_id', 'None')}
"""

    except Exception as error:

        return f"Error retrieving task details: {str(error)}"


# =========================================================
# TOOL 4: UPDATE EXISTING TASK
# =========================================================

@tool
def update_existing_task(
    task_id: str,
    title: str,
    due_date: str,
    due_time: str,
    assigned_to: str = "",
    assigned_email: str = "",
    priority: str = "Medium",
    status: str = "Pending",
    reminder_minutes: int = 30,
    related_meeting_id: str = "",
) -> str:
    """
    Update an existing task.

    Requires the complete task information:
    - task_id
    - title
    - due_date
    - due_time

    Optional fields:
    - assigned_to
    - assigned_email
    - priority
    - status
    - reminder_minutes
    - related_meeting_id
    """

    try:

        # ---------------------------------------------
        # TASK ID VALIDATION
        # ---------------------------------------------

        if not task_id or not task_id.strip():

            return "Task ID is required."

        task_id = task_id.strip()

        existing_task = get_task(task_id)

        if not existing_task:

            return f"No task found with ID: {task_id}"

        # ---------------------------------------------
        # TITLE VALIDATION
        # ---------------------------------------------

        if not title or not title.strip():

            return "Task title is required."

        title = title.strip()

        # ---------------------------------------------
        # DATE VALIDATION
        # ---------------------------------------------

        if not validate_date(due_date):

            return (
                "Invalid due date. "
                "Use YYYY-MM-DD format."
            )

        # ---------------------------------------------
        # TIME VALIDATION
        # ---------------------------------------------

        if not validate_time(due_time):

            return (
                "Invalid due time. "
                "Use HH:MM format."
            )

        # ---------------------------------------------
        # PRIORITY NORMALIZATION
        # ---------------------------------------------

        priority = normalize_priority(priority)

        if priority not in ALLOWED_PRIORITIES:

            return (
                "Invalid priority. "
                "Use Low, Medium, High or Critical."
            )

        # ---------------------------------------------
        # STATUS NORMALIZATION
        # ---------------------------------------------

        status = normalize_status(status)

        if status not in ALLOWED_STATUSES:

            return (
                "Invalid status. "
                "Use Pending, In Progress, "
                "Completed or Cancelled."
            )

        # ---------------------------------------------
        # REMINDER VALIDATION
        # ---------------------------------------------

        try:

            reminder_minutes = int(reminder_minutes)

        except (ValueError, TypeError):

            return "Reminder minutes must be a number."

        if reminder_minutes < 0:

            return "Reminder minutes cannot be negative."

        # ---------------------------------------------
        # UPDATE DATABASE
        # ---------------------------------------------

        update_task(
            task_id=task_id,
            title=title,
            due_date=due_date,
            due_time=due_time,
            assigned_to=assigned_to.strip(),
            assigned_email=assigned_email.strip(),
            priority=priority,
            status=status,
            reminder_minutes=reminder_minutes,
            related_meeting_id=related_meeting_id or None,
        )

        return (
            "Task updated successfully!\n\n"
            f"Task ID: {task_id}\n"
            f"Title: {title}\n"
            f"Priority: {priority}\n"
            f"Due Date: {due_date}\n"
            f"Due Time: {due_time}\n"
            f"Status: {status}"
        )

    except Exception as error:

        return f"Error updating task: {str(error)}"


# =========================================================
# TASK TOOL REGISTRY
# =========================================================

TASK_TOOLS = [
    view_tasks,
    create_new_task,
    get_task_details,
    update_existing_task,
]
