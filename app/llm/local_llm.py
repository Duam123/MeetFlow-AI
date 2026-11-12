
import torch

from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    pipeline,
)

# ==========================================
# MODEL CONFIGURATION
# ==========================================

MODEL_NAME = "Qwen/Qwen2.5-0.5B-Instruct"

# ==========================================
# LOAD TOKENIZER
# ==========================================

tokenizer = AutoTokenizer.from_pretrained(
    MODEL_NAME,
    local_files_only=True,
)

# Ensure padding token is available
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

# ==========================================
# LOAD MODEL
# ==========================================

model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    local_files_only=True,
    dtype=torch.float32,
    low_cpu_mem_usage=True,
)

model.eval()

# ==========================================
# TEXT GENERATION PIPELINE
# ==========================================

generator = pipeline(
    "text-generation",
    model=model,
    tokenizer=tokenizer,
    device=-1,
)

# ==========================================
# GENERATE RESPONSE
# ==========================================

def generate_response(user_message: str) -> str:
    """Generate a response using the shared local Qwen model."""

    messages = [
        {
            "role": "system",
            "content": (
                "You are MeetFlow AI, a helpful and professional "
                "meeting, task management and email intelligence assistant. "
                "Respond clearly, accurately and professionally. "
                "Never invent information."
            ),
        },
        {
            "role": "user",
            "content": user_message,
        },
    ]

    prompt = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )

    output = generator(
        prompt,
        max_new_tokens=250,
        do_sample=False,
        return_full_text=False,
        pad_token_id=tokenizer.eos_token_id,
    )

    return output[0]["generated_text"].strip()
