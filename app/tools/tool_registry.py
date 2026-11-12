
from app.tools.meeting_tools import MEETING_TOOLS
from app.tools.task_tools import TASK_TOOLS
from app.tools.gmail_tools import GMAIL_TOOLS


# ==========================================
# ALL REGISTERED MEETFLOW AI TOOLS
# ==========================================

ALL_TOOLS = (
    MEETING_TOOLS
    + TASK_TOOLS
    + GMAIL_TOOLS
)


# ==========================================
# GET ALL TOOLS
# ==========================================

def get_all_tools():
    """Return all registered MeetFlow AI tools."""
    return ALL_TOOLS


# ==========================================
# TEST TOOL REGISTRY
# ==========================================

if __name__ == "__main__":

    print("\nMeetFlow AI - Registered Tools\n")

    for index, selected_tool in enumerate(
        ALL_TOOLS,
        start=1
    ):

        print(f"{index}. {selected_tool.name}")
        print(f"   {selected_tool.description}\n")

    print(
        f"Total registered tools: {len(ALL_TOOLS)}"
    )
