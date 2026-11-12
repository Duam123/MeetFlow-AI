
import sys
import json
from pathlib import Path

# --------------------------------------------------
# PROJECT CONFIGURATION
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.llm.local_llm import generate_response
from app.tools.gmail_tools import get_gmail_tools


# --------------------------------------------------
# EMAIL REACT AGENT
# --------------------------------------------------

class EmailReActAgent:

    def __init__(self, max_iterations=3):

        self.max_iterations = max_iterations

        # Register available Gmail tools
        self.tools = {
            registered_tool.name: registered_tool
            for registered_tool in get_gmail_tools()
        }

        print("\nGmail tools registered successfully!")

        for name in self.tools:
            print(" -", name)

    # --------------------------------------------------
    # INTENT DETECTION
    # --------------------------------------------------

    def detect_intent(self, message):

        text = message.lower()

        analyze_keywords = [
            "analyze",
            "analyse",
            "summarize",
            "summary",
            "classify",
            "explain my emails",
            "email analysis",
            "important emails",
            "priority emails"
        ]

        check_keywords = [
            "check",
            "read",
            "show",
            "fetch",
            "get",
            "unread",
            "inbox",
            "emails",
            "email"
        ]

        if any(word in text for word in analyze_keywords):
            return "analyze_unread_emails"

        if any(word in text for word in check_keywords):
            return "get_unread_emails"

        return None

    # --------------------------------------------------
    # JSON EXTRACTION
    # --------------------------------------------------

    def extract_json(self, response):

        if isinstance(response, dict):
            return response

        response = str(response).strip()

        if "```json" in response:
            response = response.split("```json", 1)[1]
            response = response.split("```", 1)[0]

        elif "```" in response:
            response = response.split("```", 1)[1]
            response = response.split("```", 1)[0]

        start = response.find("{")
        end = response.rfind("}")

        if start == -1 or end == -1:
            return None

        try:
            return json.loads(response[start:end + 1])

        except json.JSONDecodeError:
            return None

    # --------------------------------------------------
    # LLM REASONING
    # --------------------------------------------------

    def reason(self, user_message):

        prompt = f"""
You are MeetFlow AI, an intelligent Gmail assistant.

Available tools:

1. get_unread_emails
   Retrieves unread emails from Gmail.

2. analyze_unread_emails
   Analyzes and summarizes unread emails.

Rules:

- If the user wants to read, check or display emails,
  select get_unread_emails.

- If the user wants analysis, summaries or classification,
  select analyze_unread_emails.

- For greetings or unrelated questions, respond directly.

- Never invent email information.

Return ONLY valid JSON.

Tool response example:
{{
    "action": "tool",
    "tool_name": "get_unread_emails",
    "tool_input": {{
        "limit": 5
    }}
}}

Final response example:
{{
    "action": "final",
    "response": "Hello! How can I help you?"
}}

User message:
{user_message}
"""

        try:

            response = generate_response(prompt)

            decision = self.extract_json(response)

            if isinstance(decision, dict):

                action = decision.get("action")

                if action == "final":
                    return decision

                if action == "tool":

                    tool_name = decision.get("tool_name")

                    if tool_name in self.tools:

                        return {
                            "action": "tool",
                            "tool_name": tool_name,
                            "tool_input": decision.get(
                                "tool_input", {}
                            )
                        }

        except Exception as error:

            print("LLM reasoning error:", error)

        # Reliable fallback
        detected_tool = self.detect_intent(user_message)

        if detected_tool:

            return {
                "action": "tool",
                "tool_name": detected_tool,
                "tool_input": {
                    "limit": 5
                }
            }

        return {
            "action": "final",
            "response": (
                "Hello! I am MeetFlow AI. "
                "I can check and analyze your Gmail inbox."
            )
        }

    # --------------------------------------------------
    # TOOL EXECUTION
    # --------------------------------------------------

    def execute_tool(self, tool_name, tool_input=None):

        if tool_name not in self.tools:

            return json.dumps({
                "success": False,
                "error": f"Tool {tool_name} is not registered."
            })

        tool_input = tool_input or {}

        try:

            limit = int(tool_input.get("limit", 5))

            limit = max(1, min(limit, 5))

            print(f"\nExecuting {tool_name}...")
            print(f"Email limit: {limit}")

            result = self.tools[tool_name].invoke({
                "limit": limit
            })

            # Normalize tool result
            if isinstance(result, dict):
                return json.dumps(result, ensure_ascii=False)

            return str(result)

        except Exception as error:

            return json.dumps({
                "success": False,
                "error": str(error)
            }, ensure_ascii=False)

    # --------------------------------------------------
    # FORMAT EMAIL RESULTS
    # --------------------------------------------------

    def format_results(self, observations):

        if not observations:

            return "No email operation was performed."

        output = []

        for item in observations:

            try:

                raw_result = item["result"]

                if isinstance(raw_result, dict):
                    data = raw_result
                else:
                    data = json.loads(str(raw_result))

                if not isinstance(data, dict):

                    output.append(str(raw_result))
                    continue

                if data.get("success") is False:

                    output.append(
                        "Email operation failed: "
                        + str(data.get("error", "Unknown error"))
                    )

                    continue

                tool_name = item["tool"]

                # --------------------------------------
                # UNREAD EMAIL RESULTS
                # --------------------------------------

                if tool_name == "get_unread_emails":

                    emails = data.get("emails", [])

                    output.append(
                        f"Unread emails found: {data.get('total_emails', len(emails))}"
                    )

                    if not emails:

                        output.append(
                            "Your inbox has no unread emails."
                        )

                    for email in emails:

                        output.append(
                            f"\nEmail #{email.get('email_number', '')}"
                            f"\nFrom: {email.get('sender', 'Unknown')}"
                            f"\nSubject: {email.get('subject', 'No subject')}"
                            f"\nDate: {email.get('date', 'Unknown')}"
                            f"\nPreview: {email.get('body_preview', 'No preview available')}"
                            "\n" + "-" * 45
                        )

                # --------------------------------------
                # EMAIL ANALYSIS RESULTS
                # --------------------------------------

                elif tool_name == "analyze_unread_emails":

                    results = data.get("results", [])

                    output.append(
                        f"Emails analyzed: {data.get('total_analyzed', len(results))}"
                    )

                    if not results:

                        output.append("No unread emails available for analysis.")

                    for email in results:

                        analysis = email.get("analysis", {})

                        if not isinstance(analysis, dict):
                            analysis = {
                                "summary": str(analysis)
                            }

                        output.append(
                            f"\nSubject: {email.get('subject', 'No subject')}"
                            f"\nSender: {email.get('sender', 'Unknown')}"
                            f"\nCategory: {analysis.get('category', 'Unknown')}"
                            f"\nPriority: {analysis.get('priority', 'Unknown')}"
                            f"\nSummary: {analysis.get('summary', 'Not available')}"
                            "\n" + "-" * 45
                        )

            except (json.JSONDecodeError, TypeError, AttributeError) as error:

                output.append(
                    f"Could not format tool result: {error}\n"
                    f"Raw result: {item['result']}"
                )

        return "\n".join(output)

    # --------------------------------------------------
    # MAIN REACT LOOP
    # --------------------------------------------------

    def run(self, user_message):

        print("\nMeetFlow AI is thinking...\n")

        observations = []

        for iteration in range(self.max_iterations):

            print(f"Reasoning Step: {iteration + 1}")

            decision = self.reason(user_message)

            # ------------------------------------------
            # FINAL RESPONSE
            # ------------------------------------------

            if decision["action"] == "final":

                response = decision.get(
                    "response",
                    "How can I help you?"
                )

                print("\nMeetFlow AI:")
                print(response)

                return response

            # ------------------------------------------
            # TOOL ACTION
            # ------------------------------------------

            tool_name = decision.get("tool_name")

            tool_input = decision.get("tool_input", {})

            if tool_name not in self.tools:

                print("Invalid tool selected. Applying fallback...")

                tool_name = self.detect_intent(user_message)

                if not tool_name:

                    return "I could not understand your request."

            print("Selected Tool:", tool_name)
            print("Executing tool...\n")

            observation = self.execute_tool(
                tool_name,
                tool_input
            )

            observations.append({
                "tool": tool_name,
                "result": observation
            })

            print("Tool execution completed.")

            # Validate tool result
            try:

                parsed_result = json.loads(observation)

                if parsed_result.get("success") is False:

                    error_message = (
                        "Email operation failed: "
                        + str(parsed_result.get("error", "Unknown error"))
                    )

                    print("\nMeetFlow AI:")
                    print(error_message)

                    return error_message

            except (json.JSONDecodeError, AttributeError, TypeError):
                pass

            # Read-only tool: format and return results
            final_response = self.format_results(observations)

            print("\nMeetFlow AI:")
            print(final_response)

            return final_response

        return self.format_results(observations)


# --------------------------------------------------
# TERMINAL APPLICATION
# --------------------------------------------------

if __name__ == "__main__":

    agent = EmailReActAgent()

    print("\n" + "=" * 60)
    print("       MEETFLOW AI - EMAIL REACT AGENT")
    print("=" * 60)

    print("Gmail AI Assistant is ready!")
    print("Type 'exit' to close the agent.")

    while True:

        try:

            user_input = input("\nYou: ").strip()

            if user_input.lower() in ["exit", "quit"]:

                print("\nMeetFlow AI stopped.")
                break

            if not user_input:
                continue

            # Run agent and display returned response
            response = agent.run(user_input)

            # Additional protection against empty responses
            if not response:

                print("\nMeetFlow AI:")
                print("I could not generate a response.")

        except KeyboardInterrupt:

            print("\n\nMeetFlow AI stopped.")
            break

        except Exception as error:

            print("\nApplication Error:", str(error))
