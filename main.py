from langchain_core.messages import HumanMessage
from src.agent import agent

print("=" * 60)
print("FIRST QUERY")
print("=" * 60)
result1 = agent.invoke({
    "messages": [HumanMessage(content="What was Tesla's revenue last year?")]
})
for msg in result1["messages"]:
    print(f"\n[{type(msg).__name__}]")
    if hasattr(msg, 'tool_calls') and msg.tool_calls:
        print(f"Tool calls: {[t['name'] for t in msg.tool_calls]}")
    if hasattr(msg, 'content'):
        print(str(msg.content)[:500])

print("\n" + "=" * 60)
print("SECOND QUERY")
print("=" * 60)
result2 = agent.invoke({
    "messages": [HumanMessage(content="Remind me what Tesla's revenue was??")]
})
for msg in result2["messages"]:
    print(f"\n[{type(msg).__name__}]")
    if hasattr(msg, 'tool_calls') and msg.tool_calls:
        print(f"Tool calls: {[t['name'] for t in msg.tool_calls]}")
    if hasattr(msg, 'content'):
        print(str(msg.content)[:500])