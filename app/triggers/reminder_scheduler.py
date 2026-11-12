
from datetime import datetime, timedelta
from html import escape
import time
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler

# SQLite database functions
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
# ENVIRONMENT CONFIGURATION
# ==================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

load_dotenv(PROJECT_ROOT / ".env")

REMINDER_RECEIVER_EMAIL = os.getenv(
    "REMINDER_RECEIVER_EMAIL", ""
).strip()


# ==================================================
# LOGGING CONFIGURATION
# ==================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)


# ==================================================
# EMAIL SERVICE
# ==================================================

email_service = EmailService()


# ==================================================
# DATA UTILITIES
# ==================================================

def get_value(record, key, default=None):
    """Safely retrieve a value from a SQLite record."""

    if record is None:
        return default

    if isinstance(record, dict):
        value = record.get(key, default)
    else:
        try:
            value = record[key]
        except (KeyError, IndexError, TypeError):
            return default

    return default if value is None else value


def combine_datetime(date_value, time_value):
    """Combine SQLite date and time values."""

    if date_value is None or time_value is None:
        return None

    date_text = str(date_value).strip()
    time_text = str(time_value).strip()

    if date_text.lower() in ("", "none", "nan", "nat"):
        return None

    if time_text.lower() in ("", "none", "nan", "nat"):
        return None

    try:
        # Handle date values containing a time component.
        date_text = date_text.replace("T", " ").split(" ")[0]

        return datetime.fromisoformat(
            f"{date_text}T{time_text}"
        )

    except (ValueError, TypeError):
        logger.warning(
            "Invalid date/time combination: %s %s",
            date_value,
            time_value
        )
        return None


def get_reminder_minutes(value, default=30):
    """Convert reminder minutes safely into an integer."""

    try:
        if value is None:
            return default

        return max(0, int(float(value)))

    except (ValueError, TypeError):
        return default


# ==================================================
# EMAIL TEMPLATE
# ==================================================

def create_email_template(
    notification_type,
    reference_id,
    message,
    reminder_time
):
    """Generate professional HTML and plain text emails."""

    safe_message = escape(str(message))
    safe_reference = escape(str(reference_id))

    notification_title = (
        notification_type.replace("_", " ").title()
    )

    html_body = f"""
    <html>
    <body style="
        font-family: Arial, sans-serif;
        background-color: #f4f5f9;
        padding: 25px;
    ">

        <div style="
            max-width: 600px;
            margin: auto;
            background: white;
            padding: 30px;
            border-radius: 10px;
        ">

            <h2 style="color: #4338ca;">
                MeetFlow AI
            </h2>

            <h3>{escape(notification_title)}</h3>

            <p>Hello,</p>

            <p>
                This is an automated notification
                from MeetFlow AI.
            </p>

            <p>
                <strong>Details:</strong>
                {safe_message}
            </p>

            <p>
                <strong>Reference ID:</strong>
                {safe_reference}
            </p>

            <p>
                <strong>Reminder Time:</strong>
                {escape(str(reminder_time))}
            </p>

            <hr>

            <p style="color: #777;">
                Intelligent Meeting & Task Automation
            </p>

        </div>

    </body>
    </html>
    """

    text_body = (
        f"MeetFlow AI Notification\n"
        f"Type: {notification_title}\n"
        f"Details: {message}\n"
        f"Reference ID: {reference_id}\n"
        f"Reminder Time: {reminder_time}"
    )

    return html_body, text_body


# ==================================================
# CENTRAL EMAIL NOTIFICATION SERVICE
# ==================================================

def register_reminder(
    notification_key,
    notification_type,
    reference_id,
    reminder_time,
    recipient_email=None,
    message=""
):
    """
    Send reminders to the central Gmail configured in .env.

    Successfully delivered notifications are not sent again.
    Failed notifications can be retried.
    """

    # Always route notifications to configured Gmail.
    recipient_email = REMINDER_RECEIVER_EMAIL

    if (
        not recipient_email
        or "@" not in recipient_email
        or "." not in recipient_email.split("@")[-1]
    ):
        logger.error(
            "REMINDER_RECEIVER_EMAIL is missing or invalid."
        )
        return

    try:

        # Create notification record if it does not exist.
        create_reminder(
            notification_key=notification_key,
            notification_type=notification_type,
            reference_id=reference_id,
            scheduled_for=reminder_time.isoformat(),
            recipient_email=recipient_email
        )

        # Check whether notification was already sent.
        status = get_reminder_status(notification_key)

        if status == "sent":
            logger.info(
                "Already delivered: %s",
                notification_key
            )
            return

        logger.info(
            "Processing notification: %s",
            notification_key
        )

        subject = (
            f"MeetFlow AI | "
            f"{notification_type.replace('_', ' ').title()}"
        )

        html_body, text_body = create_email_template(
            notification_type=notification_type,
            reference_id=reference_id,
            message=message,
            reminder_time=reminder_time
        )

        # Actual Gmail SMTP delivery.
        email_service.send_email(
            to_email=recipient_email,
            subject=subject,
            html_body=html_body,
            text_body=text_body
        )

        # Update database only after successful email delivery.
        mark_reminder_sent(notification_key)

        logger.info(
            "EMAIL SENT | %s | Recipient: %s",
            notification_key,
            recipient_email
        )

    except Exception as error:

        try:
            mark_reminder_failed(
                notification_key,
                error
            )
        except Exception:
            logger.exception(
                "Could not update failed notification status."
            )

        logger.exception(
            "EMAIL DELIVERY FAILED | %s",
            notification_key
        )


# ==================================================
# MEETING REMINDER PROCESSOR
# ==================================================

def process_meeting_reminders(meetings, current_time):
    """Check SQLite meetings and trigger their reminders."""

    for meeting in meetings:

        status = str(
            get_value(meeting, "status", "")
        ).strip().lower()

        if status != "scheduled":
            continue

        meeting_id = get_value(meeting, "meeting_id")

        if not meeting_id:
            continue

        meeting_title = get_value(
            meeting,
            "title",
            "Untitled Meeting"
        )

        meeting_start = combine_datetime(
            get_value(meeting, "meeting_date"),
            get_value(meeting, "start_time")
        )

        if meeting_start is None:
            continue

        reminder_minutes = get_reminder_minutes(
            get_value(meeting, "reminder_minutes"),
            default=15
        )

        reminder_time = (
            meeting_start - timedelta(minutes=reminder_minutes)
        )

        # Trigger anytime inside the reminder window.
        if reminder_time <= current_time <= meeting_start:

            register_reminder(
                notification_key=f"meeting:{meeting_id}:reminder",
                notification_type="meeting_reminder",
                reference_id=meeting_id,
                reminder_time=reminder_time,
                recipient_email=get_value(
                    meeting,
                    "participant_emails"
                ),
                message=meeting_title
            )


# ==================================================
# TASK REMINDER PROCESSOR
# ==================================================

def process_task_reminders(tasks, current_time):
    """Check SQLite tasks and trigger reminders or overdue alerts."""

    for task in tasks:

        task_status = str(
            get_value(task, "status", "pending")
        ).strip().lower()

        # Completed and cancelled tasks need no reminders.
        if task_status in ("completed", "cancelled"):
            continue

        task_id = get_value(task, "task_id")

        if not task_id:
            continue

        task_title = get_value(
            task,
            "title",
            "Untitled Task"
        )

        due_datetime = combine_datetime(
            get_value(task, "due_date"),
            get_value(task, "due_time")
        )

        if due_datetime is None:
            continue

        reminder_minutes = get_reminder_minutes(
            get_value(task, "reminder_minutes"),
            default=30
        )

        reminder_time = (
            due_datetime - timedelta(minutes=reminder_minutes)
        )

        # ------------------------------------------
        # UPCOMING TASK REMINDER
        # ------------------------------------------

        if reminder_time <= current_time <= due_datetime:

            register_reminder(
                notification_key=f"task:{task_id}:reminder",
                notification_type="task_reminder",
                reference_id=task_id,
                reminder_time=reminder_time,
                recipient_email=get_value(
                    task,
                    "assigned_email"
                ),
                message=task_title
            )

        # ------------------------------------------
        # OVERDUE TASK ALERT
        # ------------------------------------------

        elif current_time > due_datetime:

            register_reminder(
                notification_key=f"task:{task_id}:overdue",
                notification_type="task_overdue",
                reference_id=task_id,
                reminder_time=due_datetime,
                recipient_email=get_value(
                    task,
                    "assigned_email"
                ),
                message=(
                    f"{task_title} - "
                    f"This task is overdue."
                )
            )


# ==================================================
# MAIN REMINDER MONITOR
# ==================================================

def check_reminders(current_time=None):
    """
    Read meetings and tasks directly from SQLite.

    This keeps the scheduler synchronized with the Streamlit
    application.
    """

    if current_time is None:
        current_time = datetime.now()

    try:

        meetings = get_all_meetings() or []
        tasks = get_all_tasks() or []

        logger.info(
            "Checking SQLite records | Meetings: %s | Tasks: %s",
            len(meetings),
            len(tasks)
        )

        process_meeting_reminders(
            meetings,
            current_time
        )

        process_task_reminders(
            tasks,
            current_time
        )

    except Exception:

        logger.exception(
            "Reminder monitoring cycle failed."
        )


# ==================================================
# BACKGROUND SCHEDULER
# ==================================================

def start_scheduler():
    """Start MeetFlow AI automatic reminder monitoring."""

    initialize_database()
    initialize_meeting_task_tables()

    if not REMINDER_RECEIVER_EMAIL:

        logger.error(
            "Configure REMINDER_RECEIVER_EMAIL in your .env file."
        )
        return

    scheduler = BackgroundScheduler()

    scheduler.add_job(
        check_reminders,
        trigger="interval",
        seconds=30,
        id="meetflow_reminder_monitor",
        max_instances=1,
        coalesce=True,
        replace_existing=True
    )

    scheduler.start()

    logger.info("=" * 55)
    logger.info("MEETFLOW AI REMINDER ENGINE")
    logger.info("Status: RUNNING")
    logger.info("Data Source: SQLite")
    logger.info("Check Interval: Every 30 seconds")
    logger.info("Delivery: Gmail SMTP")
    logger.info(
        "Reminder Receiver: %s",
        REMINDER_RECEIVER_EMAIL
    )
    logger.info("Press CTRL+C to stop")
    logger.info("=" * 55)

    # First monitoring cycle.
    check_reminders()

    try:

        while True:
            time.sleep(1)

    except KeyboardInterrupt:

        scheduler.shutdown(wait=False)

        logger.info(
            "MeetFlow AI Reminder Engine stopped."
        )


# ==================================================
# APPLICATION ENTRY POINT
# ==================================================

if __name__ == "__main__":
    start_scheduler()
