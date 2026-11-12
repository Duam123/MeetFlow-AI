
import sqlite3
from pathlib import Path
from datetime import datetime
from uuid import uuid4


# ==========================================
# DATABASE PATH
# ==========================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATABASE_PATH = PROJECT_ROOT / "database" / "meetflow.db"

DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)


# ==========================================
# DATABASE CONNECTION
# ==========================================

def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


# ==========================================
# INITIALIZE MEETINGS AND TASKS TABLES
# ==========================================

def initialize_meeting_task_tables():

    with get_connection() as connection:

        connection.execute("""
            CREATE TABLE IF NOT EXISTS meetings (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                meeting_id TEXT UNIQUE NOT NULL,

                title TEXT NOT NULL,

                meeting_date TEXT NOT NULL,

                start_time TEXT NOT NULL,

                end_time TEXT NOT NULL,

                participants TEXT DEFAULT '',

                participant_emails TEXT DEFAULT '',

                meeting_link TEXT DEFAULT '',

                agenda TEXT DEFAULT '',

                status TEXT DEFAULT 'Scheduled',

                reminder_minutes INTEGER DEFAULT 15,

                created_at TEXT DEFAULT CURRENT_TIMESTAMP,

                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS tasks (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                task_id TEXT UNIQUE NOT NULL,

                title TEXT NOT NULL,

                assigned_to TEXT DEFAULT '',

                assigned_email TEXT DEFAULT '',

                due_date TEXT NOT NULL,

                due_time TEXT NOT NULL,

                priority TEXT DEFAULT 'Medium',

                status TEXT DEFAULT 'Pending',

                reminder_minutes INTEGER DEFAULT 30,

                related_meeting_id TEXT DEFAULT '',

                created_at TEXT DEFAULT CURRENT_TIMESTAMP,

                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        connection.commit()


# ==========================================
# MEETINGS - CREATE
# ==========================================

def create_meeting(
    title,
    meeting_date,
    start_time,
    end_time,
    participants="",
    participant_emails="",
    meeting_link="",
    agenda="",
    status="Scheduled",
    reminder_minutes=15
):

    meeting_id = f"M-{uuid4().hex[:8].upper()}"

    with get_connection() as connection:

        connection.execute("""
            INSERT INTO meetings (
                meeting_id,
                title,
                meeting_date,
                start_time,
                end_time,
                participants,
                participant_emails,
                meeting_link,
                agenda,
                status,
                reminder_minutes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            meeting_id,
            title,
            str(meeting_date),
            str(start_time),
            str(end_time),
            participants,
            participant_emails,
            meeting_link,
            agenda,
            status,
            reminder_minutes
        ))

    return meeting_id


# ==========================================
# MEETINGS - READ
# ==========================================

def get_all_meetings():

    with get_connection() as connection:

        records = connection.execute("""
            SELECT *
            FROM meetings
            ORDER BY meeting_date ASC, start_time ASC
        """).fetchall()

        return [dict(record) for record in records]


def get_meeting(meeting_id):

    with get_connection() as connection:

        record = connection.execute("""
            SELECT *
            FROM meetings
            WHERE meeting_id = ?
        """, (meeting_id,)).fetchone()

        return dict(record) if record else None


# ==========================================
# MEETINGS - UPDATE
# ==========================================

def update_meeting(
    meeting_id,
    title,
    meeting_date,
    start_time,
    end_time,
    participants="",
    participant_emails="",
    meeting_link="",
    agenda="",
    status="Scheduled",
    reminder_minutes=15
):

    with get_connection() as connection:

        cursor = connection.execute("""
            UPDATE meetings

            SET title = ?,
                meeting_date = ?,
                start_time = ?,
                end_time = ?,
                participants = ?,
                participant_emails = ?,
                meeting_link = ?,
                agenda = ?,
                status = ?,
                reminder_minutes = ?,
                updated_at = ?

            WHERE meeting_id = ?
        """, (
            title,
            str(meeting_date),
            str(start_time),
            str(end_time),
            participants,
            participant_emails,
            meeting_link,
            agenda,
            status,
            reminder_minutes,
            datetime.now().isoformat(),
            meeting_id
        ))

        return cursor.rowcount > 0


# ==========================================
# MEETINGS - DELETE
# ==========================================

def delete_meeting(meeting_id):

    with get_connection() as connection:

        cursor = connection.execute("""
            DELETE FROM meetings
            WHERE meeting_id = ?
        """, (meeting_id,))

        return cursor.rowcount > 0


# ==========================================
# TASKS - CREATE
# ==========================================

def create_task(
    title,
    due_date,
    due_time,
    assigned_to="",
    assigned_email="",
    priority="Medium",
    status="Pending",
    reminder_minutes=30,
    related_meeting_id=""
):

    task_id = f"T-{uuid4().hex[:8].upper()}"

    with get_connection() as connection:

        connection.execute("""
            INSERT INTO tasks (
                task_id,
                title,
                assigned_to,
                assigned_email,
                due_date,
                due_time,
                priority,
                status,
                reminder_minutes,
                related_meeting_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            task_id,
            title,
            assigned_to,
            assigned_email,
            str(due_date),
            str(due_time),
            priority,
            status,
            reminder_minutes,
            related_meeting_id
        ))

    return task_id


# ==========================================
# TASKS - READ
# ==========================================

def get_all_tasks():

    with get_connection() as connection:

        records = connection.execute("""
            SELECT *
            FROM tasks
            ORDER BY due_date ASC, due_time ASC
        """).fetchall()

        return [dict(record) for record in records]


def get_task(task_id):

    with get_connection() as connection:

        record = connection.execute("""
            SELECT *
            FROM tasks
            WHERE task_id = ?
        """, (task_id,)).fetchone()

        return dict(record) if record else None


# ==========================================
# TASKS - UPDATE
# ==========================================

def update_task(
    task_id,
    title,
    due_date,
    due_time,
    assigned_to="",
    assigned_email="",
    priority="Medium",
    status="Pending",
    reminder_minutes=30,
    related_meeting_id=""
):

    with get_connection() as connection:

        cursor = connection.execute("""
            UPDATE tasks

            SET title = ?,
                assigned_to = ?,
                assigned_email = ?,
                due_date = ?,
                due_time = ?,
                priority = ?,
                status = ?,
                reminder_minutes = ?,
                related_meeting_id = ?,
                updated_at = ?

            WHERE task_id = ?
        """, (
            title,
            assigned_to,
            assigned_email,
            str(due_date),
            str(due_time),
            priority,
            status,
            reminder_minutes,
            related_meeting_id,
            datetime.now().isoformat(),
            task_id
        ))

        return cursor.rowcount > 0


# ==========================================
# TASKS - DELETE
# ==========================================

def delete_task(task_id):

    with get_connection() as connection:

        cursor = connection.execute("""
            DELETE FROM tasks
            WHERE task_id = ?
        """, (task_id,))

        return cursor.rowcount > 0


# ==========================================
# INITIALIZE WHEN RUN DIRECTLY
# ==========================================

if __name__ == "__main__":

    initialize_meeting_task_tables()

    print("Meetings and Tasks tables initialized!")
    print("Database:", DATABASE_PATH)
