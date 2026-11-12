
import json
import re
from datetime import date, datetime, timedelta

from app.llm.local_llm import tokenizer, generator


# =========================================================
# ALLOWED INTENTS
# =========================================================

ALLOWED_INTENTS = {
    "view_meetings",
    "create_meeting",
    "update_meeting",
    "cancel_meeting",
    "view_tasks",
    "create_task",
    "update_task",
    "complete_task",
    "view_unread_emails",
    "analyze_unread_emails",
    "unknown",
}


# =========================================================
# TRUSTED INTENT TO TOOL MAPPING
# =========================================================

INTENT_TO_TOOL = {
    "view_meetings": "view_meetings",
    "create_meeting": "create_new_meeting",
    "update_meeting": "update_existing_meeting",
    "cancel_meeting": "update_existing_meeting",

    "view_tasks": "view_tasks",
    "create_task": "create_new_task",
    "update_task": "update_existing_task",
    "complete_task": "update_existing_task",

    "view_unread_emails": "get_unread_emails",
    "analyze_unread_emails": "analyze_unread_emails",
}


# =========================================================
# MUTATING INTENTS
# =========================================================

CONFIRMATION_INTENTS = {
    "create_meeting",
    "update_meeting",
    "cancel_meeting",
    "create_task",
    "update_task",
    "complete_task",
}


# =========================================================
# ALLOWED TOOL INPUT FIELDS
# =========================================================

ALLOWED_TOOL_FIELDS = {
    "view_meetings": set(),

    "create_meeting": {
        "title", "meeting_date", "start_time", "end_time",
        "participants", "participant_emails", "meeting_link",
        "agenda", "description", "reminder_minutes",
    },

    "update_meeting": {
        "meeting_id", "title", "meeting_date", "start_time",
        "end_time", "participants", "participant_emails",
        "meeting_link", "agenda", "description", "status",
        "reminder_minutes",
    },

    "cancel_meeting": {
        "meeting_id", "status",
    },

    "view_tasks": set(),

    "create_task": {
        "title", "description", "due_date", "due_time",
        "priority", "assigned_to", "assigned_email",
        "status", "reminder_minutes", "related_meeting_id",
    },

    "update_task": {
        "task_id", "title", "description", "due_date",
        "due_time", "priority", "assigned_to",
        "assigned_email", "status", "reminder_minutes",
        "related_meeting_id",
    },

    "complete_task": {
        "task_id", "status",
    },

    "view_unread_emails": {"limit"},
    "analyze_unread_emails": {"limit"},
    "unknown": set(),
}


# =========================================================
# JSON EXTRACTION
# =========================================================

def extract_json(text: str) -> dict:

    if not text:
        return {}

    text = text.strip()

    text = re.sub(
        r"```(?:json)?",
        "",
        text,
        flags=re.IGNORECASE,
    )

    text = text.replace("```", "").strip()

    try:
        result = json.loads(text)

        if isinstance(result, dict):
            return result

    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", text, re.DOTALL)

    if not match:
        return {}

    try:
        result = json.loads(match.group(0))

        if isinstance(result, dict):
            return result

    except json.JSONDecodeError:
        pass

    return {}


# =========================================================
# INPUT SANITIZATION
# =========================================================

def sanitize_tool_input(intent: str, tool_input: dict) -> dict:

    if not isinstance(tool_input, dict):
        return {}

    allowed_fields = ALLOWED_TOOL_FIELDS.get(intent, set())

    cleaned_input = {}

    for key, value in tool_input.items():

        if key not in allowed_fields:
            continue

        if value is None:
            continue

        if isinstance(value, str):
            value = value.strip()

            if not value:
                continue

        cleaned_input[key] = value

    return cleaned_input


# =========================================================
# DATE EXTRACTION
# =========================================================

def extract_meeting_date(user_message: str):

    message = user_message.lower()
    today = date.today()

    if re.search(r"\bday after tomorrow\b", message):
        return (today + timedelta(days=2)).isoformat()

    if re.search(r"\btomorrow\b", message):
        return (today + timedelta(days=1)).isoformat()

    if re.search(r"\btoday\b", message):
        return today.isoformat()

    explicit_date = re.search(
        r"\b(20\d{2})-(\d{2})-(\d{2})\b",
        message,
    )

    if explicit_date:
        try:
            return datetime.strptime(
                explicit_date.group(0),
                "%Y-%m-%d",
            ).strftime("%Y-%m-%d")
        except ValueError:
            return None

    return None


# =========================================================
# PREVENT INVENTED MEETING FIELDS
# =========================================================

def prevent_invented_meeting_fields(user_message, tool_input):

    message = user_message.lower()

    explicit_title = re.search(
        r"\b(?:title is|meeting title|titled|called|name it)\b",
        message,
    )

    if not explicit_title:
        tool_input.pop("title", None)

    time_pattern = (
        r"\b(?:[01]?\d|2[0-3])"
        r"(?::[0-5]\d)?\s*(?:a\.?m\.?|p\.?m\.?)\b"
        r"|\b(?:[01]\d|2[0-3]):[0-5]\d\b"
    )

    time_mentions = re.findall(
        time_pattern,
        message,
        flags=re.IGNORECASE,
    )

    explicit_end = re.search(
        r"\b(?:end(?:s)? at|ending at|until)\b",
        message,
    )

    if len(time_mentions) < 2 and not explicit_end:
        tool_input.pop("end_time", None)

    return tool_input


# =========================================================
# STATUS COMMAND OVERRIDES
# =========================================================

def apply_status_command(user_message, intent, tool_input):

    message = user_message.lower()

    if intent == "cancel_meeting":

        tool_input["status"] = "Cancelled"

    elif intent == "complete_task":

        tool_input["status"] = "Completed"

    elif intent == "update_task":

        if re.search(r"\bmark(?:ed)?\s+(?:the\s+)?task\s+.*\bcompleted\b", message):
            tool_input["status"] = "Completed"

    elif intent == "update_meeting":

        if re.search(r"\bmark(?:ed)?\s+(?:the\s+)?meeting\s+.*\bcompleted\b", message):
            tool_input["status"] = "Completed"

    return tool_input


# =========================================================
# GMAIL VALIDATION
# =========================================================

def validate_gmail_input(intent, tool_input):

    if intent not in {
        "view_unread_emails",
        "analyze_unread_emails",
    }:
        return tool_input

    limit = tool_input.get("limit", 5)

    if type(limit) is not int:
        limit = 5

    maximum = 10 if intent == "view_unread_emails" else 5

    tool_input["limit"] = max(1, min(limit, maximum))

    return tool_input


# =========================================================
# MAIN STRUCTURED OUTPUT GENERATOR
# =========================================================

def generate_structured_output(user_message: str) -> dict:

    if not isinstance(user_message, str) or not user_message.strip():

        return {
            "intent": "unknown",
            "tool_name": None,
            "tool_input": {},
            "requires_confirmation": False,
        }

    current_date = date.today().isoformat()

    # -----------------------------------------------------
    # SYSTEM PROMPT
    # -----------------------------------------------------

    system_prompt = f"""
You are MeetFlow AI intent detection engine.

Return ONLY valid JSON.

CURRENT DATE: {current_date}

AVAILABLE INTENTS:

view_meetings
create_meeting
update_meeting
cancel_meeting
view_tasks
create_task
update_task
complete_task
view_unread_emails
analyze_unread_emails
unknown

GENERAL RULES:

1. Never invent information.
2. Never invent IDs.
3. Never invent titles, dates or times.
4. Return only explicitly provided fields.
5. Use unknown if request is unclear.
6. Never generate tool names.

MEETINGS:

Show meetings = view_meetings.
Create meeting = create_meeting.
Update meeting = update_meeting.
Cancel meeting = cancel_meeting.

For cancel_meeting extract meeting_id only.

For update_meeting extract meeting_id and only requested changes.

TASKS:

Show tasks = view_tasks.
Create task = create_task.
Update task = update_task.
Mark task completed = complete_task.

For complete_task extract task_id only.

For update_task extract task_id and only requested changes.

Extract only explicitly provided:
title, due_date, due_time, priority, assigned_to,
assigned_email, status, reminder_minutes, related_meeting_id.

For task completion use status Completed.

For meeting cancellation use status Cancelled.

DATES:

Tomorrow = current date + 1 day.
Today = current date.
Day after tomorrow = current date + 2 days.

Date format YYYY-MM-DD.

TIMES:

Use 24-hour format.
3 PM = 15:00.
4 PM = 16:00.
10 AM = 10:00.

GMAIL:

List unread emails = view_unread_emails.
Analyze unread emails = analyze_unread_emails.

Return this JSON structure:

{{
    "intent": "allowed_intent",
    "tool_input": {{}}
}}

EXAMPLES:

User: Show my meetings.
{{"intent":"view_meetings","tool_input":{{}}}}

User: Show my tasks.
{{"intent":"view_tasks","tool_input":{{}}}}

User: Cancel meeting M-12345678.
{{"intent":"cancel_meeting","tool_input":{{"meeting_id":"M-12345678"}}}}

User: Mark task T-12345678 as completed.
{{"intent":"complete_task","tool_input":{{"task_id":"T-12345678"}}}}

User: Change task T-12345678 priority to High.
{{"intent":"update_task","tool_input":{{"task_id":"T-12345678","priority":"High"}}}}

User: Change meeting M-12345678 to 4 PM.
{{"intent":"update_meeting","tool_input":{{"meeting_id":"M-12345678","start_time":"16:00"}}}}

User: Create a meeting tomorrow at 3 PM.
{{"intent":"create_meeting","tool_input":{{"meeting_date":"tomorrow","start_time":"15:00"}}}}

User: Show my unread emails.
{{"intent":"view_unread_emails","tool_input":{{"limit":5}}}}

User: Analyze my unread emails.
{{"intent":"analyze_unread_emails","tool_input":{{"limit":3}}}}
"""

    # -----------------------------------------------------
    # BUILD PROMPT
    # -----------------------------------------------------

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]

    prompt = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )

    # -----------------------------------------------------
    # LOCAL QWEN GENERATION
    # -----------------------------------------------------

    output = generator(
        prompt,
        max_new_tokens=300,
        do_sample=False,
        return_full_text=False,
        pad_token_id=tokenizer.eos_token_id,
    )

    generated_text = output[0]["generated_text"].strip()

    # -----------------------------------------------------
    # EXTRACT JSON
    # -----------------------------------------------------

    result = extract_json(generated_text)

    if not result:
        return {
            "intent": "unknown",
            "tool_name": None,
            "tool_input": {},
            "requires_confirmation": False,
        }

    # -----------------------------------------------------
    # VALIDATE INTENT
    # -----------------------------------------------------

    intent = result.get("intent", "unknown")

    if intent not in ALLOWED_INTENTS:
        intent = "unknown"

    tool_input = result.get("tool_input", {})

    if not isinstance(tool_input, dict):
        tool_input = {}

    # -----------------------------------------------------
    # SANITIZE
    # -----------------------------------------------------

    tool_input = sanitize_tool_input(intent, tool_input)

    # -----------------------------------------------------
    # DETERMINISTIC DATE
    # -----------------------------------------------------

    if intent in {"create_meeting", "update_meeting"}:

        extracted_date = extract_meeting_date(user_message)

        if extracted_date:
            tool_input["meeting_date"] = extracted_date

        tool_input = prevent_invented_meeting_fields(
            user_message,
            tool_input,
        )

    if intent in {"create_task", "update_task"}:

        extracted_date = extract_meeting_date(user_message)

        if extracted_date and re.search(
            r"\b(?:due|deadline|by|tomorrow|today)\b",
            user_message.lower(),
        ):
            tool_input["due_date"] = extracted_date

    # -----------------------------------------------------
    # APPLY STATUS COMMANDS
    # -----------------------------------------------------

    tool_input = apply_status_command(
        user_message,
        intent,
        tool_input,
    )

    # -----------------------------------------------------
    # GMAIL VALIDATION
    # -----------------------------------------------------

    tool_input = validate_gmail_input(
        intent,
        tool_input,
    )

    # -----------------------------------------------------
    # TRUSTED TOOL SELECTION
    # -----------------------------------------------------

    tool_name = INTENT_TO_TOOL.get(intent)

    # -----------------------------------------------------
    # CONFIRMATION
    # -----------------------------------------------------

    requires_confirmation = intent in CONFIRMATION_INTENTS

    return {
        "intent": intent,
        "tool_name": tool_name,
        "tool_input": tool_input,
        "requires_confirmation": requires_confirmation,
    }
