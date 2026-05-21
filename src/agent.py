import os
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from src.state import AgentState
from src.tools import search_web, get_sec_filings

load_dotenv()

# The LLM
llm = ChatAnthropic(model="claude-sonnet-4-5")

# Tell the LLM about the tools
tools = [search_web, get_sec_filings]
llm_with_tools = llm.bind_tools(tools)


SYSTEM_PROMPT = """You are a financial research assistant.

You have access to two tools:
- search_web: for recent news, analyst commentary, market updates
- get_sec_filings: for official SEC filings (10-K, 10-Q, 8-K)

Rules:
1. Always use tools to get real data. Never invent financial figures.
2. If a tool returns only a URL without content, tell the user to visit the link rather than fabricating numbers.
3. Cite your sources by including URLs in your final answer.
4. Be concise and factual."""


# Node 1: The agent brain
def agent_node(state: AgentState):
    messages = state["messages"]
    # Add system prompt as the first message if not already there
    if not messages or not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}


# Node 2: The tool executor
tool_node = ToolNode(tools)


# Conditional edge: should we call a tool or are we done?
def should_continue(state: AgentState):
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tools"
    return END


# Build the graph
def build_agent():
    graph = StateGraph(AgentState)

    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)

    graph.set_entry_point("agent")

    graph.add_conditional_edges("agent", should_continue)
    graph.add_edge("tools", "agent")

    return graph.compile()


agent = build_agent()