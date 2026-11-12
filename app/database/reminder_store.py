
import sqlite3
from pathlib import Path
from datetime import datetime


# Project paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATABASE_FOLDER = PROJECT_ROOT / "database"

DATABASE_FOLDER.mkdir(parents=True, exist_ok=True)

DATABASE_PATH = DATABASE_FOLDER / "meetflow.db"


def get_connection():
    """Create a database connection."""

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    return connection


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


def reminder_exists(notification_key):
    """Check whether a reminder already exists."""

    with get_connection() as connection:

        result = connection.execute(
            """
            SELECT id
            FROM notification_logs
            WHERE notification_key = ?
            AND status = 'sent'
            """,
            (notification_key,)
        ).fetchone()

        return result is not None


def create_reminder(
    notification_key,
    notification_type,
    reference_id,
    scheduled_for,
    recipient_email=None
):
    """Save a reminder if it does not already exist."""

    with get_connection() as connection:

        cursor = connection.execute(
            """
            INSERT OR IGNORE INTO notification_logs
            (
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


def mark_reminder_sent(notification_key):
    """Mark reminder as successfully sent."""

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
            (str(error), notification_key)
        )

        connection.commit()


def get_notification_history():

    with get_connection() as connection:

        records = connection.execute(
            """
            SELECT *
            FROM notification_logs
            ORDER BY created_at DESC
            """
        ).fetchall()

        return [dict(record) for record in records]


if __name__ == "__main__":

    initialize_database()

    print("MeetFlow AI database initialized!")

    print("Database location:", DATABASE_PATH)

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

