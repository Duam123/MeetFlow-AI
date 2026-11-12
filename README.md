
# MeetFlow AI

**An AI-powered Meeting and Task Management Assistant**

MeetFlow AI is an intelligent meeting and task management application built with Streamlit, LangChain, LangGraph, and a locally running Qwen language model. It helps users organize meetings, manage tasks, track reminders, and automate routine workflow operations through a conversational AI assistant.

## Features

- **AI Assistant:** Understands natural-language requests for meeting and task management.
- **Meeting Management:** Create, view, and update meeting records.
- **Task Management:** Create, view, and update tasks, including priority and status.
- **Human Approval Workflow:** Requires user approval before executing actions that modify records.
- **Email Reminders:** Sends Gmail notifications for upcoming meetings and tasks.
- **Reminder Scheduler:** Uses APScheduler to check scheduled reminders automatically.
- **Dashboard:** Displays an overview of meetings, tasks, and activity.
- **Analytics:** Provides a summary of meeting and task information.
- **SQLite Database:** Stores meeting, task, and notification records locally.
- **Gmail Integration:** Supports email notification functionality and unread-email tools.
- **Local LLM:** Uses Qwen2.5-0.5B-Instruct without requiring a paid AI API.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core application |
| Streamlit | User interface |
| LangChain | Tool integration |
| LangGraph | AI agent workflow |
| Qwen2.5-0.5B-Instruct | Local language model |
| SQLite | Database |
| Pandas | Excel data handling |
| APScheduler | Automated reminders |
| Gmail SMTP/IMAP | Email integration |

## How It Works

1. The user enters a request through the AI Assistant.
2. The local language model identifies the user's intent and extracts relevant information.
3. The agent maps the request to an available application tool.
4. Input validation checks the extracted information.
5. Read-only operations can execute directly.
6. Actions that create or update records are presented for user approval.
7. After approval, the selected tool performs the operation.
8. Meeting and task information is stored in SQLite.
9. The reminder scheduler checks due reminders and sends email notifications.

## Project Setup

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR-USERNAME/MeetFlow-AI.git
cd MeetFlow-AI
```

### 2. Create a Virtual Environment

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root directory.

Add your own Gmail configuration:

```env
GMAIL_ADDRESS=your_email@gmail.com
GMAIL_APP_PASSWORD=your_gmail_app_password
REMINDER_RECEIVER_EMAIL=your_email@gmail.com
```

**Important:** Use a Gmail App Password where required. Never upload your `.env` file or email credentials to GitHub.

### 5. Run the Application

```bash
streamlit run streamlit_app.py
```

The application will open in your browser.

## AI Agent Workflow

MeetFlow AI uses a tool-based agent workflow.

The application separates:

- Intent identification
- Tool selection
- Input validation
- Read-only tool execution
- Action approval
- Approved action execution
- Final response generation

This workflow helps prevent record-changing actions from being executed without user confirmation.

## Database

MeetFlow AI uses SQLite for local data storage.

The database stores:

- Meeting records
- Task records
- Notification history

The database is created and managed by the application.

## Email Reminder System

The reminder system uses APScheduler and Gmail integration.

It checks upcoming meeting and task reminders and sends notifications to the configured reminder receiver email address.

## Important Notes

- The application uses a local Qwen language model.
- Model files may need to be downloaded or configured before first use.
- Gmail credentials must be configured locally.
- The local SQLite database is not included in the public repository.
- The local language model may require clear instructions for complex requests.
- Record-changing actions require explicit approval.

## Future Improvements

- Improved natural-language understanding
- More advanced AI scheduling
- Calendar integrations
- Additional notification channels
- User authentication and role management
- Deployment to a cloud platform

## Author

**Dua Mirani**

Software Engineering Graduate

- Portfolio: https://dua-mirani-portfolio.vercel.app/
- LinkedIn: https://www.linkedin.com/in/dua-mirani-a4468025b/

---

*MeetFlow AI — Smarter Meetings, Better Task Management.*
