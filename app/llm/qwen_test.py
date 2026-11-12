
import torch
import json

from transformers import AutoTokenizer, AutoModelForCausalLM

from app.meeting_intelligence.meeting_schema import MeetingSummary
from app.meeting_intelligence.evidence_validator import validate_evidence


# ==========================================
# 1. MODEL CONFIGURATION
# ==========================================

MODEL_NAME = "Qwen/Qwen2.5-0.5B-Instruct"

print("Loading Qwen model...")

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    dtype=torch.float32
)

model.eval()

print("Qwen model loaded successfully!")


# ==========================================
# 2. MEETING TRANSCRIPT
# ==========================================

meeting_text = """
Ali and Sara discussed the project deadline.

Ali will complete the frontend by Friday.

Sara will test the application next Monday,
after Ali completes the frontend.

The team agreed to prioritize frontend development first.

Testing may be delayed if frontend development
is not completed on time.

They still need to decide who will handle deployment.
"""


# ==========================================
# 3. SYSTEM INSTRUCTIONS
# ==========================================

system_prompt = """
You are MeetFlow AI, a professional meeting intelligence system.

Your task is to extract structured information from meeting transcripts.

STRICT RULES:

1. Only extract information explicitly supported by the transcript.
2. Never invent participants, tasks, owners, dates or decisions.
3. If an owner or deadline is missing, return null.
4. Evidence must be an exact sentence copied from the transcript.
5. Do not create evidence that does not exist.
6. Distinguish decisions from action items.
7. Identify risks only when a potential problem is mentioned.
8. Identify unresolved questions that remain unanswered.
9. Preserve relative deadlines such as Friday or Next Monday.
10. Do not convert relative deadlines into calendar dates.
11. Return valid JSON only.
12. Do not include Markdown or explanations.
"""


# ==========================================
# 4. USER PROMPT
# ==========================================

user_prompt = f"""
Analyze this meeting transcript and extract complete
meeting intelligence.

Return exactly this JSON structure:

{{
    "meeting_title": "string",
    "summary": "string",
    "participants": [],

    "decisions": [
        {{
            "content": "string",
            "evidence": "exact transcript sentence or null"
        }}
    ],

    "action_items": [
        {{
            "task": "string",
            "owner": "string or null",
            "deadline": "string or null",
            "dependencies": [],
            "evidence": "exact transcript sentence or null"
        }}
    ],

    "risks": [
        {{
            "content": "string",
            "evidence": "exact transcript sentence or null"
        }}
    ],

    "dependencies": [],

    "unresolved_questions": [
        {{
            "content": "string",
            "evidence": "exact transcript sentence or null"
        }}
    ]
}}

Meeting transcript:

{meeting_text}

Remember:
- Use null for missing information.
- Use empty lists when no information is available.
- Never invent exact calendar dates.
- Return JSON only.
"""


# ==========================================
# 5. CREATE CHAT MESSAGES
# ==========================================

messages = [
    {
        "role": "system",
        "content": system_prompt
    },
    {
        "role": "user",
        "content": user_prompt
    }
]


# ==========================================
# 6. APPLY CHAT TEMPLATE
# ==========================================

prompt = tokenizer.apply_chat_template(
    messages,
    tokenize=False,
    add_generation_prompt=True
)


# ==========================================
# 7. TOKENIZE INPUT
# ==========================================

inputs = tokenizer(
    prompt,
    return_tensors="pt"
)


# ==========================================
# 8. GENERATE AI RESPONSE
# ==========================================

print("\nMeetFlow AI is analyzing the meeting...")

with torch.no_grad():

    outputs = model.generate(
        **inputs,
        max_new_tokens=700,
        do_sample=False,
        pad_token_id=tokenizer.eos_token_id
    )


# ==========================================
# 9. DECODE RESPONSE
# ==========================================

generated_tokens = outputs[0][
    inputs["input_ids"].shape[1]:
]

response = tokenizer.decode(
    generated_tokens,
    skip_special_tokens=True
)

print("\nRAW QWEN RESPONSE:")
print(response)


# ==========================================
# 10. PARSE AND VALIDATE JSON
# ==========================================

try:

    clean_response = response.strip()

    # Remove Markdown code fences
    if clean_response.startswith("```"):

        clean_response = clean_response.removeprefix("```json")
        clean_response = clean_response.removeprefix("```")
        clean_response = clean_response.removesuffix("```").strip()

    # Convert JSON into Python dictionary
    extracted_data = json.loads(clean_response)

    # Validate using Pydantic
    meeting_summary = MeetingSummary.model_validate(
        extracted_data
    )

    print("\n" + "=" * 50)
    print("MEETFLOW AI - MEETING INTELLIGENCE REPORT")
    print("=" * 50)

    print(meeting_summary.model_dump_json(indent=4))


    # ==========================================
    # 11. VERIFY EXTRACTED EVIDENCE
    # ==========================================

    print("\n" + "=" * 50)
    print("EVIDENCE VERIFICATION")
    print("=" * 50)

    evidence_issues = validate_evidence(
        meeting_summary.model_dump(),
        meeting_text
    )

    if evidence_issues:

        print("\nEVIDENCE VERIFICATION WARNINGS:")

        for issue in evidence_issues:
            print("-", issue)

        print("\nSome extracted evidence needs review.")

    else:

        print("\nSUCCESS: All evidence matches the transcript!")


    # ==========================================
    # 12. FINAL STATUS
    # ==========================================

    print("\n" + "=" * 50)
    print("MEETFLOW AI PROCESS COMPLETED")
    print("=" * 50)

except json.JSONDecodeError as error:

    print("\nJSON PARSING FAILED:")
    print(error)

    print("\nThe model did not return valid JSON.")

except Exception as error:

    print("\nVALIDATION OR PROCESSING FAILED:")
    print(error)
