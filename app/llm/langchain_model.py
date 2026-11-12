
import torch

from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableLambda

MODEL_NAME = "google/flan-t5-small"

print("Loading Hugging Face model...")

# 1. Load tokenizer
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

# 2. Load model
model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)
model.eval()

print("Model loaded successfully!")


# 3. Define model generation function
def generate_response(prompt_value):

    prompt_text = prompt_value.to_string()

    inputs = tokenizer(
        prompt_text,
        return_tensors="pt",
        truncation=True
    )

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=100
        )

    response = tokenizer.decode(
        outputs[0],
        skip_special_tokens=True
    )

    return response


# 4. Create LangChain prompt
prompt = PromptTemplate.from_template(
    """
    You are a professional AI meeting assistant.

    Summarize this meeting in simple English:

    {meeting_details}
    """
)


# 5. Convert Python function into LangChain Runnable
llm = RunnableLambda(generate_response)


# 6. Connect prompt and model
chain = prompt | llm


# 7. Meeting information
meeting = """
Ali and Sara discussed the project deadline.
Ali will complete the frontend by Friday.
Sara will test the application next Monday.
"""


# 8. Generate summary
print("\nGenerating meeting summary...")

response = chain.invoke({
    "meeting_details": meeting
})

print("\nMEETING SUMMARY:")
print(response)
