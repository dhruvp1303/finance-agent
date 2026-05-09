import os
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from src.state import AgentState
from src.tools import search_web, get_sec_filings

load_dotenv()

# The LLM
llm = ChatAnthropic(model="claude-sonnet-4-6")

# Tell the LLM about the tools
tools = [search_web, get_sec_filings]
llm_with_tools = llm.bind_tools(tools)


# Node 1: The agent brain
def agent_node(state: AgentState):
    messages = state["messages"]
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
