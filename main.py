from langchain_core.messages import HumanMessage
from src.agent import agent

# Try a question
question = "Compare Microsoft and Google's revenue for the last 3 years"
result = agent.invoke({
    "messages": [HumanMessage(content=question)]
})

# Print every message in the conversation
for msg in result["messages"]:
    print(f"\n--- {type(msg).__name__} ---")
    print(msg.content if hasattr(msg, 'content') else msg)
    if hasattr(msg, 'tool_calls') and msg.tool_calls:
        print(f"Tool calls: {msg.tool_calls}")