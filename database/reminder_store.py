
import sqlite3
from pathlib import Path
from datetime import datetime


# ==========================================
# PROJECT PATHS
# ==========================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATABASE_FOLDER = PROJECT_ROOT / "database"

DATABASE_FOLDER.mkdir(parents=True, exist_ok=True)

DATABASE_PATH = DATABASE_FOLDER / "meetflow.db"


# ==========================================
# DATABASE CONNECTION
# ==========================================

def get_connection():
    """Create and return a SQLite database connection."""

    connection = sqlite3.connect(DATABASE_PATH)

    connection.row_factory = sqlite3.Row

    return connection


# ==========================================
# INITIALIZE DATABASE
# ==========================================

def initialize_database():
    """Create notification history table."""

    with get_connection() as connection:

        connection.execute("""
            CREATE TABLE IF NOT EXISTS notification_logs (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                notification_key TEXT UNIQUE NOT NULL,

                notification_type TEXT NOT NULL,

                reference_id TEXT NOT NULL,

                recipient_email TEXT,

                scheduled_for TEXT NOT NULL,

                status TEXT NOT NULL DEFAULT 'pending',

                attempts INTEGER DEFAULT 0,

                sent_at TEXT,

                last_error TEXT,

                created_at TEXT DEFAULT CURRENT_TIMESTAMP

            )
        """)

        connection.commit()


# ==========================================
# CHECK REMINDER EXISTENCE
# ==========================================

def reminder_exists(notification_key):
    """Check whether a reminder has already been sent."""

    with get_connection() as connection:

        record = connection.execute(
            """
            SELECT id
            FROM notification_logs
            WHERE notification_key = ?
            AND status = 'sent'
            """,
            (notification_key,)
        ).fetchone()

        return record is not None


# ==========================================
# CREATE REMINDER
# ==========================================

def create_reminder(
    notification_key,
    notification_type,
    reference_id,
    scheduled_for,
    recipient_email=None
):
    """Create a reminder if it does not already exist."""

    with get_connection() as connection:

        cursor = connection.execute(
            """
            INSERT OR IGNORE INTO notification_logs (

                notification_key,
                notification_type,
                reference_id,
                recipient_email,
                scheduled_for

            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                notification_key,
                notification_type,
                reference_id,
                recipient_email,
                scheduled_for
            )
        )

        connection.commit()

        return cursor.rowcount == 1


# ==========================================
# GET REMINDER STATUS
# ==========================================

def get_reminder_status(notification_key):
    """Get the current delivery status of a reminder."""

    with get_connection() as connection:

        record = connection.execute(
            """
            SELECT status
            FROM notification_logs
            WHERE notification_key = ?
            """,
            (notification_key,)
        ).fetchone()

        if record is None:
            return None

        return record["status"]


# ==========================================
# MARK REMINDER AS SENT
# ==========================================

def mark_reminder_sent(notification_key):
    """Mark a reminder as successfully sent."""

    with get_connection() as connection:

        connection.execute(
            """
            UPDATE notification_logs

            SET status = 'sent',

                attempts = attempts + 1,

                sent_at = ?,

                last_error = NULL

            WHERE notification_key = ?
            """,
            (
                datetime.now().isoformat(),
                notification_key
            )
        )

        connection.commit()


# ==========================================
# MARK REMINDER AS FAILED
# ==========================================

def mark_reminder_failed(notification_key, error):
    """Save failed delivery details."""

    with get_connection() as connection:

        connection.execute(
            """
            UPDATE notification_logs

            SET status = 'failed',

                attempts = attempts + 1,

                last_error = ?

            WHERE notification_key = ?
            """,
            (
                str(error),
                notification_key
            )
        )

        connection.commit()


# ==========================================
# GET NOTIFICATION HISTORY
# ==========================================

def get_notification_history():
    """Return all notification records."""

    with get_connection() as connection:

        records = connection.execute(
            """
            SELECT *
            FROM notification_logs
            ORDER BY created_at DESC
            """
        ).fetchall()

        return [dict(record) for record in records]


# ==========================================
# MAIN
# ==========================================

if __name__ == "__main__":

    initialize_database()

    print("MeetFlow AI database initialized!")

    print("Database location:", DATABASE_PATH)
