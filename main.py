from langchain_core.messages import HumanMessage
from src.agent import agent

# First question
print("=" * 60)
print("FIRST QUERY")
print("=" * 60)
question1 = "What was Tesla's revenue last year?"
result1 = agent.invoke({
    "messages": [HumanMessage(content=question1)]
})
print(result1["messages"][-1].content)

# Second question, related
print("\n" + "=" * 60)
print("SECOND QUERY (should use memory)")
print("=" * 60)
question2 = "Remind me what Tesla's revenue was?"
result2 = agent.invoke({
    "messages": [HumanMessage(content=question2)]
})
print(result2["messages"][-1].content)