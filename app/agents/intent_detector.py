
from app.llm.structured_output import generate_structured_output


def detect_intent(user_message: str) -> str:
    """
    Detect user intent using the local Qwen LLM.
    """

    try:
        result = generate_structured_output(user_message)

        allowed_intents = [
            "view_meetings",
            "create_meeting",
            "update_meeting",
            "view_tasks",
            "create_task",
            "update_task",
            "unknown",
        ]

        intent = result.get("intent", "unknown")

        if intent not in allowed_intents:
            return "unknown"

        return intent

    except Exception as error:
        print(f"Intent detection error: {error}")
        return "unknown"
