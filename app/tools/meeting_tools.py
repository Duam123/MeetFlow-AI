
from datetime import date, datetime

from langchain_core.tools import tool

from app.database.meeting_store import (
    create_meeting,
    get_all_meetings,
    get_meeting,
    update_meeting,
)


@tool
def view_meetings() -> str:
    """Retrieve all meetings saved in the MeetFlow AI database."""

    meetings = get_all_meetings()

    if not meetings:
        return "No meetings found."

    return "\n\n".join(str(dict(meeting)) for meeting in meetings)


@tool
def create_new_meeting(
    title: str,
    meeting_date: str,
    start_time: str,
    end_time: str,
    participants: str = "",
    participant_emails: str = "",
    meeting_link: str = "",
    agenda: str = "",
    reminder_minutes: int = 15,
) -> str:
    """Create a meeting. Date format YYYY-MM-DD, time format HH:MM."""

    try:
        date.fromisoformat(meeting_date)

        start = datetime.strptime(start_time, "%H:%M")
        end = datetime.strptime(end_time, "%H:%M")

        if not title.strip():
            return "Error: Meeting title is required."

        if end <= start:
            return "Error: End time must be after start time."

        if reminder_minutes < 0:
            return "Error: Reminder cannot be negative."

        meeting_id = create_meeting(
            title=title,
            meeting_date=meeting_date,
            start_time=start_time,
            end_time=end_time,
            participants=participants,
            participant_emails=participant_emails,
            meeting_link=meeting_link,
            agenda=agenda,
            status="Scheduled",
            reminder_minutes=reminder_minutes,
        )

        return f"Meeting created successfully. ID: {meeting_id}"

    except ValueError:
        return "Invalid date or time format."
    except Exception as error:
        return f"Meeting creation failed: {error}"


@tool
def get_meeting_details(meeting_id: str) -> str:
    """Get details of a meeting using its ID."""

    meeting = get_meeting(meeting_id)

    if not meeting:
        return f"No meeting found with ID: {meeting_id}"

    return str(dict(meeting))


@tool
def update_existing_meeting(
    meeting_id: str,
    title: str,
    meeting_date: str,
    start_time: str,
    end_time: str,
    participants: str = "",
    participant_emails: str = "",
    meeting_link: str = "",
    agenda: str = "",
    reminder_minutes: int = 15,
) -> str:
    """Update an existing meeting using its ID."""

    try:
        date.fromisoformat(meeting_date)

        start = datetime.strptime(start_time, "%H:%M")
        end = datetime.strptime(end_time, "%H:%M")

        if not title.strip():
            return "Error: Meeting title is required."

        if end <= start:
            return "Error: End time must be after start time."

        if reminder_minutes < 0:
            return "Error: Reminder cannot be negative."

        existing = get_meeting(meeting_id)

        if not existing:
            return f"No meeting found with ID: {meeting_id}"

        update_meeting(
            meeting_id=meeting_id,
            title=title,
            meeting_date=meeting_date,
            start_time=start_time,
            end_time=end_time,
            participants=participants,
            participant_emails=participant_emails,
            meeting_link=meeting_link,
            agenda=agenda,
            status="Scheduled",
            reminder_minutes=reminder_minutes,
        )

        return f"Meeting updated successfully. ID: {meeting_id}"

    except ValueError:
        return "Invalid date or time format."
    except Exception as error:
        return f"Meeting update failed: {error}"


MEETING_TOOLS = [
    view_meetings,
    create_new_meeting,
    get_meeting_details,
    update_existing_meeting,
]
