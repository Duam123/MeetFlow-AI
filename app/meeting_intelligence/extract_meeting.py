
import json
import torch

from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from pydantic import BaseModel, Field, ValidationError


# 1. Define output schema
class MeetingSummary(BaseModel):

    meeting_title: str

    participants: list[str]

    action_items: list[str]


# 2. Load model
MODEL_NAME = "google/flan-t5-small"

print("Loading AI model...")

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)

model.eval()


# 3. Meeting conversation
meeting_text = """
Ali and Sara discussed the project deadline.
Ali will complete the frontend by Friday.
Sara will test the application next Monday.
"""


# 4. Create extraction prompt

prompt = f"""
Convert this meeting conversation into JSON.

Required keys:
meeting_title, participants, action_items.

Meeting:
{meeting_text}

Return a JSON object only.
"""



# 5. Generate AI output
inputs = tokenizer(
    prompt,
    return_tensors="pt",
    truncation=True
)

with torch.no_grad():
    outputs = model.generate(
    **inputs,
    max_new_tokens=150,
    do_sample=False
)
       
    

ai_response = tokenizer.decode(
    outputs[0],
    skip_special_tokens=True
)

print("\nRAW AI RESPONSE:")
print(ai_response)


# 6. Parse and validate output
try:

    extracted_data = json.loads(ai_response)

    meeting_summary = MeetingSummary.model_validate(
        extracted_data
    )

    print("\nVALIDATED MEETING INFORMATION:")
    print(meeting_summary.model_dump_json(indent=4))

except (json.JSONDecodeError, ValidationError) as error:

    print("\nOutput validation failed:")
    print(error)
