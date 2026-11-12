
from app.meeting_intelligence.meeting_schema import MeetingSummary

meeting_data = {
    "meeting_title": "Project Planning Meeting",

    "summary": "Ali and Sara discussed frontend development and testing.",

    "participants": ["Ali", "Sara"],

    "decisions": [
        {
            "content": "Frontend development will be prioritized.",
            "evidence": "We will prioritize frontend development first."
        }
    ],

   
  "action_items": [
    {
        "task": "Complete frontend development",
        "owner": "Ali",
        "deadline": "Friday",
        "dependencies": [],
        "evidence": "Ali will complete the frontend by Friday."
    },
    {
        "task": "Test the application",
        "owner": "Sara",
        "deadline": "Next Monday",
        "dependencies": [
            "Complete frontend development"
        ],
        "evidence": "Sara will test the application next Monday."
    }
],

    "risks": [
        {
            "content": "Testing could be delayed.",
            "evidence": "Testing may be delayed if frontend is incomplete."
        }
    ],

    "dependencies": [],

    "unresolved_questions": [
        {
            "content": "Who will handle deployment?",
            "evidence": "We still need to decide who will handle deployment."
        }
    ]
}

meeting = MeetingSummary.model_validate(meeting_data)

print("\nMEETING INTELLIGENCE REPORT")
print(meeting.model_dump_json(indent=4))

print("\nSUCCESS: Evidence-based schema validation completed!")
