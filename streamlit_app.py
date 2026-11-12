
import sys
from pathlib import Path
from datetime import date, time

import pandas as pd
import streamlit as st


# =========================================================
# PROJECT PATH
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# =========================================================
# AGENT IMPORTS
# =========================================================

from app.agents.agent_graph import (
    run_agent,
    approve_pending_action,
    reject_pending_action,
)


# =========================================================
# DATABASE IMPORTS
# =========================================================

from app.database.meeting_store import (
    initialize_meeting_task_tables,
    create_meeting,
    get_all_meetings,
    get_meeting,
    update_meeting,
    delete_meeting,
    create_task,
    get_all_tasks,
    get_task,
    update_task,
    delete_task,
)

from app.database.reminder_store import (
    initialize_database,
    get_notification_history,
)


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="MeetFlow AI",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# DATABASE INITIALIZATION
# =========================================================

initialize_meeting_task_tables()
initialize_database()


# =========================================================
# BACKGROUND REMINDER SCHEDULER
# =========================================================

@st.cache_resource
def initialize_meetflow_scheduler():

    try:
        from app.reminders.reminder_engine import (
            start_background_scheduler,
        )

        return start_background_scheduler()

    except Exception as error:
        print(f"MeetFlow Scheduler Error: {error}")
        return None


meetflow_scheduler = initialize_meetflow_scheduler()

if meetflow_scheduler is None:

    st.warning(
        "Reminder scheduler could not start. "
        "Please check the terminal."
    )


# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown(
    """
    <style>

    @import url(
        'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap'
    );

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .stApp {
        background: #f7f8fc;
    }

    [data-testid="stSidebar"] {
        background: #10172a;
    }

    [data-testid="stSidebar"] * {
        color: white !important;
    }

    .main-title {
        font-size: 32px;
        font-weight: 800;
        color: #17213b;
        margin-bottom: 4px;
    }

    .sub-title {
        color: #77819a;
        font-size: 14px;
        margin-bottom: 25px;
    }

    .metric-card {
        background: white;
        padding: 22px;
        border-radius: 14px;
        border: 1px solid #e9ebf3;
        box-shadow: 0 3px 12px rgba(20,30,60,.04);
    }

    .metric-label {
        color: #7b8499;
        font-size: 13px;
        font-weight: 600;
    }

    .metric-value {
        color: #17213b;
        font-size: 28px;
        font-weight: 800;
        margin-top: 8px;
    }

    .section-heading {
        color: #17213b;
        font-size: 19px;
        font-weight: 700;
        margin-top: 15px;
        margin-bottom: 12px;
    }

    .agent-card {
        background: white;
        border: 1px solid #e9ebf3;
        border-radius: 14px;
        padding: 18px;
        margin-bottom: 10px;
    }

    div.stButton > button {
        border-radius: 9px;
        font-weight: 600;
        min-height: 40px;
    }

    div[data-testid="stForm"] {
        background: white;
        padding: 20px;
        border: 1px solid #e9ebf3;
        border-radius: 14px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# DATA HELPERS
# =========================================================

def load_meetings():

    try:
        return get_all_meetings() or []

    except Exception as error:
        st.error(f"Could not load meetings: {error}")
        return []


def load_tasks():

    try:
        return get_all_tasks() or []

    except Exception as error:
        st.error(f"Could not load tasks: {error}")
        return []


def load_notifications():

    try:
        return get_notification_history() or []

    except Exception as error:
        st.error(f"Could not load notifications: {error}")
        return []


def get_value(record, key, default=""):

    if record is None:
        return default

    if isinstance(record, dict):
        value = record.get(key, default)

    else:
        try:
            value = record[key]

        except (KeyError, IndexError, TypeError):
            value = default

    return default if value is None else value


def parse_date(value):

    if isinstance(value, date):
        return value

    try:
        return date.fromisoformat(str(value)[:10])

    except (ValueError, TypeError):
        return date.today()


def parse_time(value):

    if isinstance(value, time):
        return value

    try:
        return time.fromisoformat(str(value))

    except (ValueError, TypeError):
        return time(9, 0)


def metric_card(label, value):

    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_title(title):

    st.markdown(
        f'<div class="section-heading">{title}</div>',
        unsafe_allow_html=True,
    )


def show_dataframe(rows):

    if rows:

        st.dataframe(
            pd.DataFrame(rows),
            use_container_width=True,
            hide_index=True,
        )

    else:
        st.info("No records available.")


# =========================================================
# SESSION STATE
# =========================================================

if "meetflow_chat_history" not in st.session_state:
    st.session_state.meetflow_chat_history = []

if "meetflow_last_agent_result" not in st.session_state:
    st.session_state.meetflow_last_agent_result = None


# =========================================================
# SIDEBAR NAVIGATION
# =========================================================

with st.sidebar:

    st.markdown("# 📅 MeetFlow AI")

    st.caption(
        "Intelligent Meeting & Task Automation"
    )

    st.divider()

    selected_page = st.radio(
        "NAVIGATION",
        [
            "Dashboard",
            "Meetings",
            "Tasks",
            "Reminders",
            "Analytics",
            "AI Assistant",
            "Settings",
        ],
        key="meetflow_navigation",
    )

    st.divider()

    st.caption("MeetFlow AI")
    st.caption("Meeting productivity workspace")


# =========================================================
# DASHBOARD
# =========================================================

if selected_page == "Dashboard":

    st.markdown(
        '<div class="main-title">Dashboard</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="sub-title">Your meetings, tasks and automation overview.</div>',
        unsafe_allow_html=True,
    )

    meetings = load_meetings()
    tasks = load_tasks()
    notifications = load_notifications()

    pending_tasks = sum(
        str(get_value(t, "status", "Pending")).lower() == "pending"
        for t in tasks
    )

    sent_notifications = sum(
        str(get_value(n, "status", "")).lower() == "sent"
        for n in notifications
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        metric_card("Total Meetings", len(meetings))

    with c2:
        metric_card("Total Tasks", len(tasks))

    with c3:
        metric_card("Pending Tasks", pending_tasks)

    with c4:
        metric_card("Emails Sent", sent_notifications)

    st.write("")

    left, right = st.columns(2)

    with left:

        section_title("📅 Recent Meetings")

        recent_meetings = sorted(
            meetings,
            key=lambda x: str(get_value(x, "meeting_date", "")),
            reverse=True,
        )[:5]

        show_dataframe([
            {
                "Meeting": get_value(m, "title"),
                "Date": get_value(m, "meeting_date"),
                "Start": get_value(m, "start_time"),
                "Status": get_value(m, "status"),
            }
            for m in recent_meetings
        ])

    with right:

        section_title("✅ Recent Tasks")

        recent_tasks = sorted(
            tasks,
            key=lambda x: str(get_value(x, "due_date", "")),
        )[:5]

        show_dataframe([
            {
                "Task": get_value(t, "title"),
                "Assigned To": get_value(t, "assigned_to"),
                "Due Date": get_value(t, "due_date"),
                "Priority": get_value(t, "priority"),
                "Status": get_value(t, "status"),
            }
            for t in recent_tasks
        ])

    st.write("")

    section_title("🤖 Automation Overview")

    a1, a2, a3 = st.columns(3)

    with a1:
        st.info(
            "📧 Email Notifications\n\nSMTP email service configured."
        )

    with a2:
        st.info(
            "⏰ Reminder Engine\n\nAPScheduler reminder system."
        )

    with a3:
        st.info(
            "🗄️ Database\n\nSQLite data storage active."
        )


# =========================================================
# MEETINGS
# =========================================================

elif selected_page == "Meetings":

    st.markdown(
        '<div class="main-title">Meeting Management</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="sub-title">Create, manage, update and organize your meetings.</div>',
        unsafe_allow_html=True,
    )

    meetings = load_meetings()

    total = len(meetings)

    scheduled = sum(
        str(get_value(m, "status", "")).lower() == "scheduled"
        for m in meetings
    )

    completed = sum(
        str(get_value(m, "status", "")).lower() == "completed"
        for m in meetings
    )

    c1, c2, c3 = st.columns(3)

    with c1:
        metric_card("Total Meetings", total)

    with c2:
        metric_card("Scheduled", scheduled)

    with c3:
        metric_card("Completed", completed)

    st.write("")

    create_tab, manage_tab = st.tabs(
        ["➕ Create Meeting", "📋 Manage Meetings"]
    )

    # CREATE MEETING

    with create_tab:

        section_title("Create a New Meeting")

        with st.form("create_meeting_form"):

            title = st.text_input("Meeting Title")

            col1, col2 = st.columns(2)

            with col1:

                meeting_date = st.date_input(
                    "Meeting Date",
                    value=date.today(),
                )

                start_time = st.time_input(
                    "Start Time",
                    value=time(10, 0),
                )

                participants = st.text_input(
                    "Participants",
                    placeholder="Ali, Sara, Ahmed",
                )

                participant_emails = st.text_input(
                    "Participant Emails",
                    placeholder="ali@example.com, sara@example.com",
                )

            with col2:

                end_time = st.time_input(
                    "End Time",
                    value=time(11, 0),
                )

                meeting_link = st.text_input(
                    "Meeting Link",
                    placeholder="https://meet.google.com/...",
                )

                status = st.selectbox(
                    "Status",
                    ["Scheduled", "Completed", "Cancelled"],
                )

                reminder_minutes = st.number_input(
                    "Reminder Before Meeting (minutes)",
                    min_value=0,
                    max_value=10080,
                    value=30,
                )

            agenda = st.text_area("Meeting Agenda")

            submitted = st.form_submit_button(
                "Create Meeting",
                use_container_width=True,
            )

            if submitted:

                if not title.strip():

                    st.error("Meeting title is required.")

                elif end_time <= start_time:

                    st.error(
                        "End time must be later than start time."
                    )

                else:

                    try:

                        meeting_id = create_meeting(
                            title=title.strip(),
                            meeting_date=meeting_date.isoformat(),
                            start_time=start_time.strftime("%H:%M"),
                            end_time=end_time.strftime("%H:%M"),
                            participants=participants.strip(),
                            participant_emails=participant_emails.strip(),
                            meeting_link=meeting_link.strip(),
                            agenda=agenda.strip(),
                            status=status,
                            reminder_minutes=int(reminder_minutes),
                        )

                        st.success(
                            f"Meeting created successfully! ID: {meeting_id}"
                        )

                        st.rerun()

                    except Exception as error:
                        st.error(f"Could not create meeting: {error}")

    # MANAGE MEETINGS

    with manage_tab:

        section_title("All Meetings")

        meetings = load_meetings()

        if not meetings:

            st.info("No meetings available.")

        else:

            meeting_options = {
                f"{get_value(m, 'title')} ({get_value(m, 'meeting_id')})":
                get_value(m, "meeting_id")
                for m in meetings
            }

            selected_label = st.selectbox(
                "Select Meeting",
                list(meeting_options.keys()),
            )

            selected_id = meeting_options[selected_label]

            selected_meeting = get_meeting(selected_id)

            if selected_meeting:

                with st.expander(
                    "✏️ Edit Selected Meeting",
                    expanded=True,
                ):

                    with st.form("edit_meeting_form"):

                        edit_title = st.text_input(
                            "Meeting Title",
                            value=get_value(selected_meeting, "title"),
                        )

                        col1, col2 = st.columns(2)

                        with col1:

                            edit_date = st.date_input(
                                "Meeting Date",
                                value=parse_date(
                                    get_value(
                                        selected_meeting,
                                        "meeting_date",
                                    )
                                ),
                                key="edit_meeting_date",
                            )

                            edit_start = st.time_input(
                                "Start Time",
                                value=parse_time(
                                    get_value(
                                        selected_meeting,
                                        "start_time",
                                    )
                                ),
                                key="edit_meeting_start",
                            )

                            edit_participants = st.text_input(
                                "Participants",
                                value=get_value(
                                    selected_meeting,
                                    "participants",
                                ),
                            )

                            edit_emails = st.text_input(
                                "Participant Emails",
                                value=get_value(
                                    selected_meeting,
                                    "participant_emails",
                                ),
                            )

                        with col2:

                            edit_end = st.time_input(
                                "End Time",
                                value=parse_time(
                                    get_value(
                                        selected_meeting,
                                        "end_time",
                                    )
                                ),
                                key="edit_meeting_end",
                            )

                            edit_link = st.text_input(
                                "Meeting Link",
                                value=get_value(
                                    selected_meeting,
                                    "meeting_link",
                                ),
                            )

                            status_options = [
                                "Scheduled",
                                "Completed",
                                "Cancelled",
                            ]

                            current_status = get_value(
                                selected_meeting,
                                "status",
                                "Scheduled",
                            )

                            if current_status not in status_options:
                                current_status = "Scheduled"

                            edit_status = st.selectbox(
                                "Status",
                                status_options,
                                index=status_options.index(current_status),
                            )

                            edit_reminder = st.number_input(
                                "Reminder Minutes",
                                min_value=0,
                                max_value=10080,
                                value=int(
                                    get_value(
                                        selected_meeting,
                                        "reminder_minutes",
                                        30,
                                    )
                                ),
                            )

                        edit_agenda = st.text_area(
                            "Agenda",
                            value=get_value(
                                selected_meeting,
                                "agenda",
                            ),
                        )

                        update_clicked = st.form_submit_button(
                            "Save Changes",
                            use_container_width=True,
                        )

                        if update_clicked:

                            if not edit_title.strip():

                                st.error("Meeting title is required.")

                            elif edit_end <= edit_start:

                                st.error(
                                    "End time must be later than start time."
                                )

                            else:

                                try:

                                    update_meeting(
                                        meeting_id=selected_id,
                                        title=edit_title.strip(),
                                        meeting_date=edit_date.isoformat(),
                                        start_time=edit_start.strftime("%H:%M"),
                                        end_time=edit_end.strftime("%H:%M"),
                                        participants=edit_participants.strip(),
                                        participant_emails=edit_emails.strip(),
                                        meeting_link=edit_link.strip(),
                                        agenda=edit_agenda.strip(),
                                        status=edit_status,
                                        reminder_minutes=int(edit_reminder),
                                    )

                                    st.success("Meeting updated successfully!")
                                    st.rerun()

                                except Exception as error:
                                    st.error(f"Update failed: {error}")

                with st.expander("🗑️ Delete Selected Meeting"):

                    confirm_delete = st.checkbox(
                        "I confirm that I want to delete this meeting.",
                        key=f"confirm_meeting_{selected_id}",
                    )

                    if st.button(
                        "Delete Meeting",
                        disabled=not confirm_delete,
                        key=f"delete_meeting_{selected_id}",
                    ):

                        try:

                            delete_meeting(selected_id)

                            st.success("Meeting deleted successfully!")
                            st.rerun()

                        except Exception as error:
                            st.error(f"Delete failed: {error}")

            section_title("Meeting Overview")

            show_dataframe([
                {
                    "Meeting ID": get_value(m, "meeting_id"),
                    "Title": get_value(m, "title"),
                    "Date": get_value(m, "meeting_date"),
                    "Start": get_value(m, "start_time"),
                    "End": get_value(m, "end_time"),
                    "Status": get_value(m, "status"),
                }
                for m in meetings
            ])


# =========================================================
# TASKS
# =========================================================

elif selected_page == "Tasks":

    st.markdown(
        '<div class="main-title">Task Management</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="sub-title">Organize assignments, deadlines and task progress.</div>',
        unsafe_allow_html=True,
    )

    tasks = load_tasks()

    total_tasks = len(tasks)

    pending_tasks = sum(
        str(get_value(t, "status", "")).lower() == "pending"
        for t in tasks
    )

    in_progress_tasks = sum(
        str(get_value(t, "status", "")).lower() == "in progress"
        for t in tasks
    )

    completed_tasks = sum(
        str(get_value(t, "status", "")).lower() == "completed"
        for t in tasks
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        metric_card("Total Tasks", total_tasks)

    with c2:
        metric_card("Pending", pending_tasks)

    with c3:
        metric_card("In Progress", in_progress_tasks)

    with c4:
        metric_card("Completed", completed_tasks)

    st.write("")

    create_tab, manage_tab = st.tabs(
        ["➕ Create Task", "📋 Manage Tasks"]
    )

    # CREATE TASK

    with create_tab:

        section_title("Create a New Task")

        available_meetings = load_meetings()

        meeting_options = {
            "No related meeting": ""
        }

        for meeting in available_meetings:

            meeting_id = get_value(meeting, "meeting_id")
            meeting_title = get_value(meeting, "title")

            if meeting_id:

                meeting_options[
                    f"{meeting_title} ({meeting_id})"
                ] = meeting_id

        with st.form("create_task_form"):

            task_title = st.text_input("Task Title")

            col1, col2 = st.columns(2)

            with col1:

                assigned_to = st.text_input(
                    "Assigned To",
                    placeholder="Team member name",
                )

                assigned_email = st.text_input(
                    "Assigned Email",
                    placeholder="member@example.com",
                )

                due_date = st.date_input(
                    "Due Date",
                    value=date.today(),
                )

            with col2:

                due_time = st.time_input(
                    "Due Time",
                    value=time(17, 0),
                )

                priority = st.selectbox(
                    "Priority",
                    ["Low", "Medium", "High", "Critical"],
                    index=1,
                )

                task_status = st.selectbox(
                    "Task Status",
                    ["Pending", "In Progress", "Completed"],
                )

            task_reminder = st.number_input(
                "Reminder Before Deadline (minutes)",
                min_value=0,
                max_value=10080,
                value=30,
            )

            related_meeting_label = st.selectbox(
                "Related Meeting",
                list(meeting_options.keys()),
            )

            related_meeting_id = meeting_options[
                related_meeting_label
            ]

            task_submitted = st.form_submit_button(
                "Create Task",
                use_container_width=True,
            )

            if task_submitted:

                if not task_title.strip():

                    st.error("Task title is required.")

                else:

                    try:

                        task_id = create_task(
                            title=task_title.strip(),
                            due_date=due_date.isoformat(),
                            due_time=due_time.strftime("%H:%M"),
                            assigned_to=assigned_to.strip(),
                            assigned_email=assigned_email.strip(),
                            priority=priority,
                            status=task_status,
                            reminder_minutes=int(task_reminder),
                            related_meeting_id=related_meeting_id,
                        )

                        st.success(
                            f"Task created successfully! ID: {task_id}"
                        )

                        st.rerun()

                    except Exception as error:
                        st.error(f"Could not create task: {error}")

    # MANAGE TASKS

    with manage_tab:

        section_title("All Tasks")

        tasks = load_tasks()

        if not tasks:

            st.info("No tasks available.")

        else:

            task_options = {
                f"{get_value(t, 'title')} ({get_value(t, 'task_id')})":
                get_value(t, "task_id")
                for t in tasks
            }

            selected_task_label = st.selectbox(
                "Select Task",
                list(task_options.keys()),
            )

            selected_task_id = task_options[selected_task_label]

            selected_task = get_task(selected_task_id)

            if selected_task:

                with st.expander(
                    "✏️ Edit Selected Task",
                    expanded=True,
                ):

                    with st.form("edit_task_form"):

                        edit_task_title = st.text_input(
                            "Task Title",
                            value=get_value(selected_task, "title"),
                        )

                        col1, col2 = st.columns(2)

                        with col1:

                            edit_assigned_to = st.text_input(
                                "Assigned To",
                                value=get_value(
                                    selected_task,
                                    "assigned_to",
                                ),
                            )

                            edit_assigned_email = st.text_input(
                                "Assigned Email",
                                value=get_value(
                                    selected_task,
                                    "assigned_email",
                                ),
                            )

                            edit_due_date = st.date_input(
                                "Due Date",
                                value=parse_date(
                                    get_value(
                                        selected_task,
                                        "due_date",
                                    )
                                ),
                                key="edit_task_due_date",
                            )

                            edit_due_time = st.time_input(
                                "Due Time",
                                value=parse_time(
                                    get_value(
                                        selected_task,
                                        "due_time",
                                    )
                                ),
                                key="edit_task_due_time",
                            )

                        with col2:

                            priority_options = [
                                "Low",
                                "Medium",
                                "High",
                                "Critical",
                            ]

                            current_priority = get_value(
                                selected_task,
                                "priority",
                                "Medium",
                            )

                            if current_priority not in priority_options:
                                current_priority = "Medium"

                            edit_priority = st.selectbox(
                                "Priority",
                                priority_options,
                                index=priority_options.index(current_priority),
                            )

                            status_options = [
                                "Pending",
                                "In Progress",
                                "Completed",
                            ]

                            current_status = get_value(
                                selected_task,
                                "status",
                                "Pending",
                            )

                            if current_status not in status_options:
                                current_status = "Pending"

                            edit_task_status = st.selectbox(
                                "Task Status",
                                status_options,
                                index=status_options.index(current_status),
                            )

                            edit_task_reminder = st.number_input(
                                "Reminder Minutes",
                                min_value=0,
                                max_value=10080,
                                value=int(
                                    get_value(
                                        selected_task,
                                        "reminder_minutes",
                                        30,
                                    )
                                ),
                            )

                            current_related_id = get_value(
                                selected_task,
                                "related_meeting_id",
                            )

                            edit_meeting_options = {
                                "No related meeting": ""
                            }

                            for meeting in load_meetings():

                                mid = get_value(meeting, "meeting_id")
                                mtitle = get_value(meeting, "title")

                                if mid:

                                    edit_meeting_options[
                                        f"{mtitle} ({mid})"
                                    ] = mid

                            related_labels = list(
                                edit_meeting_options.keys()
                            )

                            selected_related_label = next(
                                (
                                    label
                                    for label, mid in edit_meeting_options.items()
                                    if str(mid) == str(current_related_id)
                                ),
                                "No related meeting",
                            )

                            edit_related_label = st.selectbox(
                                "Related Meeting",
                                related_labels,
                                index=related_labels.index(
                                    selected_related_label
                                ),
                            )

                            edit_related_id = edit_meeting_options[
                                edit_related_label
                            ]

                        save_task = st.form_submit_button(
                            "Save Task Changes",
                            use_container_width=True,
                        )

                        if save_task:

                            if not edit_task_title.strip():

                                st.error("Task title is required.")

                            else:

                                try:

                                    update_task(
                                        task_id=selected_task_id,
                                        title=edit_task_title.strip(),
                                        due_date=edit_due_date.isoformat(),
                                        due_time=edit_due_time.strftime("%H:%M"),
                                        assigned_to=edit_assigned_to.strip(),
                                        assigned_email=edit_assigned_email.strip(),
                                        priority=edit_priority,
                                        status=edit_task_status,
                                        reminder_minutes=int(edit_task_reminder),
                                        related_meeting_id=edit_related_id,
                                    )

                                    st.success("Task updated successfully!")
                                    st.rerun()

                                except Exception as error:
                                    st.error(f"Task update failed: {error}")

                with st.expander("🗑️ Delete Selected Task"):

                    confirm_delete = st.checkbox(
                        "I confirm that I want to delete this task.",
                        key=f"confirm_task_{selected_task_id}",
                    )

                    if st.button(
                        "Delete Task",
                        disabled=not confirm_delete,
                        key=f"delete_task_{selected_task_id}",
                    ):

                        try:

                            delete_task(selected_task_id)

                            st.success("Task deleted successfully!")
                            st.rerun()

                        except Exception as error:
                            st.error(f"Task deletion failed: {error}")

            section_title("Task Overview")

            show_dataframe([
                {
                    "Task ID": get_value(t, "task_id"),
                    "Task": get_value(t, "title"),
                    "Assigned To": get_value(t, "assigned_to"),
                    "Due Date": get_value(t, "due_date"),
                    "Due Time": get_value(t, "due_time"),
                    "Priority": get_value(t, "priority"),
                    "Status": get_value(t, "status"),
                }
                for t in tasks
            ])


# =========================================================
# REMINDERS
# =========================================================

elif selected_page == "Reminders":

    st.markdown(
        '<div class="main-title">Notification History</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="sub-title">Track email reminder delivery and notification status.</div>',
        unsafe_allow_html=True,
    )

    notifications = load_notifications()

    if notifications:

        notification_df = pd.DataFrame(notifications)

        st.dataframe(
            notification_df,
            use_container_width=True,
            hide_index=True,
        )

        sent = sum(
            str(get_value(n, "status")).lower() == "sent"
            for n in notifications
        )

        failed = sum(
            str(get_value(n, "status")).lower() == "failed"
            for n in notifications
        )

        c1, c2, c3 = st.columns(3)

        with c1:
            metric_card("Total Notifications", len(notifications))

        with c2:
            metric_card("Sent", sent)

        with c3:
            metric_card("Failed", failed)

    else:

        st.info("No notification history available yet.")


# =========================================================
# ANALYTICS
# =========================================================

elif selected_page == "Analytics":

    st.markdown(
        '<div class="main-title">Analytics</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="sub-title">Understand meeting activity and task performance.</div>',
        unsafe_allow_html=True,
    )

    meetings = load_meetings()
    tasks = load_tasks()
    notifications = load_notifications()

    col1, col2 = st.columns(2)

    with col1:

        section_title("Task Status Distribution")

        if tasks:

            status_counts = {}

            for task in tasks:

                status = get_value(task, "status", "Pending")

                status_counts[status] = (
                    status_counts.get(status, 0) + 1
                )

            status_df = pd.DataFrame({
                "Status": list(status_counts.keys()),
                "Count": list(status_counts.values()),
            })

            st.bar_chart(status_df.set_index("Status"))

        else:
            st.info("No task data available.")

    with col2:

        section_title("Meeting Status Distribution")

        if meetings:

            meeting_status_counts = {}

            for meeting in meetings:

                status = get_value(
                    meeting,
                    "status",
                    "Scheduled",
                )

                meeting_status_counts[status] = (
                    meeting_status_counts.get(status, 0) + 1
                )

            meeting_status_df = pd.DataFrame({
                "Status": list(meeting_status_counts.keys()),
                "Count": list(meeting_status_counts.values()),
            })

            st.bar_chart(
                meeting_status_df.set_index("Status")
            )

        else:
            st.info("No meeting data available.")

    st.write("")

    section_title("Notification Performance")

    if notifications:

        notification_counts = {}

        for item in notifications:

            status = get_value(item, "status", "unknown")

            notification_counts[status] = (
                notification_counts.get(status, 0) + 1
            )

        notification_df = pd.DataFrame({
            "Status": list(notification_counts.keys()),
            "Count": list(notification_counts.values()),
        })

        st.bar_chart(
            notification_df.set_index("Status")
        )

    else:
        st.info("No notification data available.")


# =========================================================
# AI ASSISTANT
# =========================================================

elif selected_page == "AI Assistant":

    st.markdown(
        '<div class="main-title">MeetFlow AI Assistant</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="sub-title">Your intelligent meeting and task automation assistant.</div>',
        unsafe_allow_html=True,
    )

    # -----------------------------------------------------
    # AGENT CARDS
    # -----------------------------------------------------

    agent_col1, agent_col2, agent_col3 = st.columns(3)

    with agent_col1:

        st.markdown(
            """
            <div class="agent-card">
                <h4>📅 Meeting Agent</h4>
                <p>Meeting information and scheduling.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with agent_col2:

        st.markdown(
            """
            <div class="agent-card">
                <h4>✅ Task Agent</h4>
                <p>Task management and deadlines.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with agent_col3:

        st.markdown(
            """
            <div class="agent-card">
                <h4>📧 Gmail Agent</h4>
                <p>Email retrieval and analysis.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.divider()

    # -----------------------------------------------------
    # CHAT HISTORY
    # -----------------------------------------------------

    section_title("💬 Chat with MeetFlow")

    for message in st.session_state.meetflow_chat_history:

        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # -----------------------------------------------------
    # CHAT INPUT
    # -----------------------------------------------------

    user_prompt = st.chat_input(
        "Ask MeetFlow about meetings, tasks or emails..."
    )

    if user_prompt:

        st.session_state.meetflow_chat_history.append({
            "role": "user",
            "content": user_prompt,
        })

        with st.spinner("MeetFlow AI is processing your request..."):

            try:

                result = run_agent(user_prompt)

                st.session_state.meetflow_last_agent_result = result

                response_text = result.get(
                    "final_response",
                    "Your request has been processed."
                )

                st.session_state.meetflow_chat_history.append({
                    "role": "assistant",
                    "content": str(response_text),
                })

            except Exception as error:

                st.session_state.meetflow_last_agent_result = None

                st.session_state.meetflow_chat_history.append({
                    "role": "assistant",
                    "content": f"Agent execution failed: {error}",
                })

        st.rerun()

    # -----------------------------------------------------
    # APPROVAL INTERFACE
    # -----------------------------------------------------

    agent_result = st.session_state.meetflow_last_agent_result

    if isinstance(agent_result, dict):

        if agent_result.get("requires_confirmation"):

            pending = agent_result.get("pending_action") or {}

            st.divider()

            st.subheader("🔐 Action Requires Your Approval")

            st.warning(
                "MeetFlow AI has prepared an action. "
                "Review the details before execution."
            )

            st.markdown(
                f"**Action:** {pending.get('intent', 'Unknown')}"
            )

            st.markdown(
                f"**Tool:** {pending.get('tool_name', 'Unknown')}"
            )

            st.markdown("**Action Details:**")

            st.json(
                pending.get("tool_input", {})
            )

            approve_col, reject_col = st.columns(2)

            with approve_col:

                approve_clicked = st.button(
                    "✅ Approve Action",
                    type="primary",
                    use_container_width=True,
                    key="meetflow_approve_action",
                )

            with reject_col:

                reject_clicked = st.button(
                    "❌ Reject Action",
                    use_container_width=True,
                    key="meetflow_reject_action",
                )

            # APPROVE

            if approve_clicked:

                with st.spinner("Executing approved action..."):

                    try:

                        updated_result = approve_pending_action(
                            agent_result
                        )

                        st.session_state.meetflow_last_agent_result = (
                            updated_result
                        )

                        st.session_state.meetflow_chat_history.append({
                            "role": "assistant",
                            "content": updated_result.get(
                                "final_response",
                                "Action execution completed."
                            ),
                        })

                    except Exception as error:

                        st.session_state.meetflow_chat_history.append({
                            "role": "assistant",
                            "content": f"Approval execution failed: {error}",
                        })

                        st.session_state.meetflow_last_agent_result = {
                            **agent_result,
                            "error": str(error),
                        }

                st.rerun()

            # REJECT

            if reject_clicked:

                updated_result = reject_pending_action(
                    agent_result
                )

                st.session_state.meetflow_last_agent_result = (
                    updated_result
                )

                st.session_state.meetflow_chat_history.append({
                    "role": "assistant",
                    "content": updated_result.get(
                        "final_response",
                        "Action rejected."
                    ),
                })

                st.rerun()

        # -------------------------------------------------
        # EXECUTION STATUS
        # -------------------------------------------------

        st.divider()

        section_title("🔎 Latest Agent Execution")

        col1, col2, col3 = st.columns(3)

        with col1:

            st.metric(
                "Intent",
                str(agent_result.get("intent") or "N/A"),
            )

        with col2:

            st.metric(
                "Iterations",
                agent_result.get("iteration_count", 0),
            )

        with col3:

            if agent_result.get("requires_confirmation"):
                action_status = "Pending Approval"

            elif agent_result.get("approved") and not agent_result.get("error"):
                action_status = "Executed"

            elif agent_result.get("final_response") == (
                "Action rejected. No changes were made."
            ):
                action_status = "Rejected"

            elif agent_result.get("error"):
                action_status = "Failed"

            else:
                action_status = "Processed"

            st.metric(
                "Action Status",
                action_status,
            )

        if agent_result.get("error"):
            st.error(agent_result["error"])

        if agent_result.get("approved") and not agent_result.get("error"):
            st.success("Approved action executed successfully.")

        with st.expander("View Complete Execution Result"):
            st.json(agent_result)

    # -----------------------------------------------------
    # CLEAR CONVERSATION
    # -----------------------------------------------------

    st.divider()

    if st.button(
        "🗑️ Clear Conversation",
        key="meetflow_clear_chat",
    ):

        st.session_state.meetflow_chat_history = []
        st.session_state.meetflow_last_agent_result = None

        st.rerun()

    st.caption(
        "Meeting and task modifications require explicit user approval."
    )


# =========================================================
# SETTINGS
# =========================================================

elif selected_page == "Settings":

    st.markdown(
        '<div class="main-title">Settings</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="sub-title">MeetFlow AI configuration and system information.</div>',
        unsafe_allow_html=True,
    )

    st.subheader("System Information")

    st.write("**Application:** MeetFlow AI")
    st.write("**Database:** SQLite")
    st.write("**LLM:** Qwen2.5-0.5B-Instruct (Local)")
    st.write("**Agent Framework:** LangChain + LangGraph")
    st.write("**Scheduler:** APScheduler")
    st.write("**Email Service:** Gmail SMTP / IMAP")

    st.divider()

    st.subheader("Email Reminder Configuration")

    st.info(
        "Email credentials are managed securely through your local .env file. "
        "Never share your Gmail App Password."
    )

    st.divider()

    st.subheader("AI Agent Configuration")

    st.write("Local model: Qwen2.5-0.5B-Instruct")
    st.write("Agent orchestration: LangGraph")
    st.write("Tool integration: LangChain")

    st.caption(
        "MeetFlow AI uses a local language model and connected application tools."
    )
