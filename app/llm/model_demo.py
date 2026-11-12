from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

# Hugging Face model ID
MODEL_NAME = "google/flan-t5-small"

print("Loading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

print("Loading AI model...")
model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)

print("Model loaded successfully!")

# Test input
meeting_text = """
Ali and Sara discussed the project deadline.
Ali will complete the frontend by Friday.
Sara will test the application next Monday.
"""

prompt = f"""
Summarize this meeting in simple English:

{meeting_text}
"""

# Convert text into model-readable tokens
inputs = tokenizer(prompt, return_tensors="pt", truncation=True)

# Generate response
outputs = model.generate(
    **inputs,
    max_new_tokens=100
)

# Convert generated tokens back into text
summary = tokenizer.decode(outputs[0], skip_special_tokens=True)

print("\nMEETING SUMMARY:")
print(summary)