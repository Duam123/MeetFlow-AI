from langchain_core.prompts import ChatPromptTemplate

# Create a reusable prompt template
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a professional AI meeting assistant."),
    ("human", "Summarize this meeting: {meeting_details}")
])

# Pass dynamic data
formatted_prompt = prompt.invoke({
    "meeting_details": "Ali and Sara discussed the project deadline."
})

# Display the generated messages
for message in formatted_prompt.messages:
    print(message.type.upper(), ":", message.content)