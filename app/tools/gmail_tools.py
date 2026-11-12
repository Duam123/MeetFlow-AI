
import sys
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from langchain_core.tools import tool
from app.email.gmail_client import GmailClient
from app.email.email_analyzer import analyze_email


@tool
def get_unread_emails(limit: int = 5) -> str:
    """Retrieve unread emails from the connected Gmail inbox."""

    limit = max(1, min(int(limit), 10))
    gmail = GmailClient()

    try:
        gmail.connect()
        emails = gmail.fetch_unread_emails(limit=limit)

        results = []

        for index, item in enumerate(emails, start=1):
            results.append({
                "email_number": index,
                "sender": item.get("from", ""),
                "subject": item.get("subject", ""),
                "date": item.get("date", ""),
                "body_preview": item.get("body", "")[:500]
            })

        return json.dumps({
            "success": True,
            "total_emails": len(results),
            "emails": results
        }, ensure_ascii=False, indent=2)

    except Exception as error:
        return json.dumps({
            "success": False,
            "error": str(error)
        }, ensure_ascii=False)

    finally:
        try:
            gmail.disconnect()
        except Exception:
            pass


@tool
def analyze_unread_emails(limit: int = 3) -> str:
    """Analyze unread Gmail emails using the local Qwen LLM."""

    limit = max(1, min(int(limit), 5))
    gmail = GmailClient()

    try:
        gmail.connect()
        emails = gmail.fetch_unread_emails(limit=limit)

        results = []

        for item in emails:
            analysis = analyze_email(item)

            results.append({
                "sender": analysis.get("sender"),
                "subject": analysis.get("subject"),
                "analysis": analysis.get("analysis"),
                "success": analysis.get("success")
            })

        return json.dumps({
            "success": True,
            "total_analyzed": len(results),
            "results": results
        }, ensure_ascii=False, indent=2)

    except Exception as error:
        return json.dumps({
            "success": False,
            "error": str(error)
        }, ensure_ascii=False)

    finally:
        try:
            gmail.disconnect()
        except Exception:
            pass


GMAIL_TOOLS = [
    get_unread_emails,
    analyze_unread_emails
]


def get_gmail_tools():
    return GMAIL_TOOLS


if __name__ == "__main__":
    print("\nMEETFLOW AI - GMAIL TOOL REGISTRY")
    print("=" * 50)

    for registered_tool in get_gmail_tools():
        print("Tool:", registered_tool.name)
        print("Description:", registered_tool.description)
        print("-" * 50)

    print("Total Gmail tools:", len(GMAIL_TOOLS))
