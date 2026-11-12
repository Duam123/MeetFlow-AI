
import logging
import os
from datetime import datetime, timedelta
from html import escape
from pathlib import Path
from threading import RLock

from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv

from app.database.meeting_store import (
    initialize_meeting_task_tables,
    get_all_meetings,
    get_all_tasks,
)
from app.database.reminder_store import (
    initialize_database,
    create_reminder,
    get_reminder_status,
    mark_reminder_sent,
    mark_reminder_failed,
)
from app.email.email_service import EmailService


# ==================================================
# CONFIGURATION
# ==================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

REMINDER_RECEIVER_EMAIL = os.getenv(
    "REMINDER_RECEIVER_EMAIL", ""
).strip()

CHECK_INTERVAL_SECONDS = 30

logger = logging.getLogger("meetflow.reminders")

email_service = EmailService()

_scheduler = None
_scheduler_lock = RLock()


# ==================================================
# DATE AND TIME HELPERS
# ==================================================

def parse_datetime(date_value, time_value):
    """Convert database date and time values into datetime."""

    if not date_value or not time_value:
        return None

    try:
        date_text = str(date_value).strip()
        time_text = str(time_value).strip()

        return datetime.fromisoformat(
            f"{date_text}T{time_text}"
        )

    except (ValueError, TypeError):
        logger.exception(
            "Invalid date/time: %s %s",
            date_value,
            time_value,
        )
        return None


def normalize_status(value):
    return str(value or "").strip().lower()


def is_valid_email(value):
    if not value or not isinstance(value, str):
        return False

    value = value.strip()

    return (
        "@" in value
        and "." in value.rsplit("@", 1)[-1]
    )


# ==================================================
# EMAIL TEMPLATE
# ==================================================

def create_email_template(
    notification_type,
    reference_id,
    message,
    reminder_time,
):
    title = notification_type.replace(
        "_", " "
    ).title()

    safe_title = escape(title)
    safe_message = escape(str(message))
    safe_reference = escape(str(reference_id))
    safe_time = escape(str(reminder_time))

    html_body = f"""
    <!DOCTYPE html>
    <html>
    <body style="
        margin:0;
        padding:30px;
        background:#f4f5fb;
        font-family:Arial,sans-serif;
    ">
        <div style="
            max-width:620px;
            margin:auto;
            background:white;
            border-radius:14px;
            padding:32px;
            border:1px solid #e8eaf2;
        ">
            <h2 style="color:#4338ca;">
                MeetFlow AI
            </h2>

            <h3>{safe_title}</h3>

            <p>Hello,</p>

            <p>
                This is an automated notification
                from MeetFlow AI.
            </p>

            <div style="
                background:#f5f6ff;
                padding:18px;
                border-radius:10px;
            ">
                <p><b>Details:</b> {safe_message}</p>
                <p><b>Reference:</b> {safe_reference}</p>
                <p><b>Reminder:</b> {safe_time}</p>
            </div>

            <p style="color:#777;font-size:13px;">
                Intelligent Meeting & Task Automation
            </p>
        </div>
    </body>
    </html>
    """

    text_body = (
        f"MeetFlow AI - {title}\n"
        f"Details: {message}\n"
        f"Reference: {reference_id}\n"
        f"Reminder: {reminder_time}"
    )

    return html_body, text_body


# ==================================================
# EMAIL DELIVERY
# ==================================================

def register_reminder(
    notification_key,
    notification_type,
    reference_id,
    reminder_time,
    message,
):
    """
    Send notification to the central email address
    configured in .env.

    Participant and assigned emails are intentionally
    not used as notification recipients.
    """

    recipient = REMINDER_RECEIVER_EMAIL

    if not is_valid_email(recipient):
        logger.error(
            "REMINDER_RECEIVER_EMAIL is missing or invalid."
        )
        return False

    # Never send a previously successful notification again.
    status = get_reminder_status(notification_key)

    if status == "sent":
        return True

    # Save notification record before attempting delivery.
    create_reminder(
        notification_key=notification_key,
        notification_type=notification_type,
        reference_id=reference_id,
        scheduled_for=reminder_time.isoformat(),
        recipient_email=recipient,
    )

    try:
        html_body, text_body = create_email_template(
            notification_type=notification_type,
            reference_id=reference_id,
            message=message,
            reminder_time=reminder_time,
        )

        email_service.send_email(
            to_email=recipient,
            subject=f"MeetFlow AI | {notification_type.replace('_', ' ').title()}",
            html_body=html_body,
            text_body=text_body,
        )

        mark_reminder_sent(notification_key)

        logger.info(
            "Reminder delivered: %s",
            notification_key,
        )

        return True

    except Exception as error:
        mark_reminder_failed(
            notification_key,
            error,
        )

        logger.exception(
            "Reminder delivery failed: %s",
            notification_key,
        )

        return False


# ==================================================
# MEETING REMINDERS
# ==================================================

def process_meeting_reminders(current_time):
    meetings = get_all_meetings()

    processed = 0

    for meeting in meetings:

        meeting_id = meeting.get("meeting_id")
        title = meeting.get("title", "Untitled Meeting")

        if not meeting_id:
            continue

        if normalize_status(meeting.get("status")) != "scheduled":
            continue

        meeting_start = parse_datetime(
            meeting.get("meeting_date"),
            meeting.get("start_time"),
        )

        if meeting_start is None:
            continue

        reminder_minutes = int(
            meeting.get("reminder_minutes") or 15
        )

        if reminder_minutes <= 0:
            continue

        reminder_time = meeting_start - timedelta(
            minutes=reminder_minutes
        )

        # Only process inside the reminder window.
        if reminder_time <= current_time <= meeting_start:

            success = register_reminder(
                notification_key=f"meeting:{meeting_id}:reminder",
                notification_type="meeting_reminder",
                reference_id=meeting_id,
                reminder_time=reminder_time,
                message=title,
            )

            if success:
                processed += 1

    return processed


# ==================================================
# TASK REMINDERS
# ==================================================

def process_task_reminders(current_time):
    tasks = get_all_tasks()

    processed = 0

    for task in tasks:

        task_id = task.get("task_id")
        title = task.get("title", "Untitled Task")

        if not task_id:
            continue

        status = normalize_status(task.get("status"))

        if status not in ("pending", "in progress", "in-progress"):
            continue

        due_datetime = parse_datetime(
            task.get("due_date"),
            task.get("due_time"),
        )

        if due_datetime is None:
            continue

        reminder_minutes = int(
            task.get("reminder_minutes") or 30
        )

        reminder_time = due_datetime - timedelta(
            minutes=reminder_minutes
        )

        # Upcoming task reminder.
        if reminder_time <= current_time <= due_datetime:

            success = register_reminder(
                notification_key=f"task:{task_id}:reminder",
                notification_type="task_reminder",
                reference_id=task_id,
                reminder_time=reminder_time,
                message=title,
            )

            if success:
                processed += 1

        # One overdue notification per task.
        elif current_time > due_datetime:

            success = register_reminder(
                notification_key=f"task:{task_id}:overdue",
                notification_type="task_overdue",
                reference_id=task_id,
                reminder_time=due_datetime,
                message=f"{title} is overdue.",
            )

            if success:
                processed += 1

    return processed


# ==================================================
# MAIN REMINDER CHECK
# ==================================================

def check_reminders(current_time=None):
    """Read SQLite records and process due notifications."""

    if current_time is None:
        current_time = datetime.now()

    try:
        meeting_count = process_meeting_reminders(
            current_time
        )

        task_count = process_task_reminders(
            current_time
        )

        logger.info(
            "Reminder check completed | Meetings: %s | Tasks: %s",
            meeting_count,
            task_count,
        )

        return {
            "success": True,
            "meeting_notifications": meeting_count,
            "task_notifications": task_count,
            "checked_at": current_time.isoformat(),
        }

    except Exception:
        logger.exception(
            "Unexpected error during reminder check."
        )

        return {
            "success": False,
            "meeting_notifications": 0,
            "task_notifications": 0,
        }


# ==================================================
# BACKGROUND SCHEDULER
# ==================================================

def start_background_scheduler():
    """
    Start one background scheduler instance.

    Safe to call repeatedly from Streamlit.
    """

    global _scheduler

    with _scheduler_lock:

        if _scheduler and _scheduler.running:
            return _scheduler

        initialize_meeting_task_tables()
        initialize_database()

        if not is_valid_email(REMINDER_RECEIVER_EMAIL):
            logger.warning(
                "Reminder scheduler not started: "
                "configure REMINDER_RECEIVER_EMAIL in .env"
            )
            return None

        scheduler = BackgroundScheduler(
            timezone="Asia/Karachi"
        )

        scheduler.add_job(
            check_reminders,
            trigger="interval",
            seconds=CHECK_INTERVAL_SECONDS,
            id="meetflow_reminder_monitor",
            max_instances=1,
            coalesce=True,
            replace_existing=True,
        )

        scheduler.start()

        _scheduler = scheduler

        logger.info(
            "MeetFlow AI reminder scheduler started."
        )

        # Run an initial check immediately.
        check_reminders()

        return _scheduler


def stop_background_scheduler():
    global _scheduler

    with _scheduler_lock:

        if _scheduler and _scheduler.running:
            _scheduler.shutdown(wait=False)

        _scheduler = None

        logger.info(
            "MeetFlow AI reminder scheduler stopped."
        )


# ==================================================
# MANUAL TEST
# ==================================================

if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )

    start_background_scheduler()

    try:
        import time

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        stop_background_scheduler()
