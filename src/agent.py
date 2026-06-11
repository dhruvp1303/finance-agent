import os
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from src.state import AgentState
from src.tools import search_web , get_financial_metric, recall_from_memory

load_dotenv()

llm = ChatAnthropic(model="claude-sonnet-4-5")


research_tools = [search_web,recall_from_memory]
research_llm = llm.bind_tools(research_tools)

financial_tools = [get_financial_metric, recall_from_memory]
financial_llm = llm.bind_tools(financial_tools)




ORCHESTRATOR_PROMPT = """You are a routing orchestrator for a financial research system.

Read the user's question and decide which specialist should handle it:
- "research" — for news, market commentary, analyst opinions, recent events
- "financial" — for specific financial numbers from SEC filings (revenue, net income, assets, etc.)

Respond with ONLY one word: either "research" or "financial". No explanation, no punctuation."""

#xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

RESEARCH_PROMPT = """You are a research specialist focused on news, market events, and analyst commentary.

You have two tools:
- recall_from_memory: Check past findings first. Pass the ticker symbol when relevant.
- search_web: Find recent news and market info.

IMPORTANT RULES:
1. Call tools ONE AT A TIME, not in parallel.
2. First call recall_from_memory and WAIT for the result.
3. If memory has relevant data, USE IT directly. Do NOT call search_web again to "verify" or "get more recent" info.
4. Only call search_web if memory returns nothing relevant.

Cite sources. Be concise and factual."""

#xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
FINANCIAL_PROMPT = """You are a financial data specialist focused on SEC filings.

You have two tools:
- recall_from_memory: Check past findings first. Pass the ticker symbol when relevant.
- get_financial_metric: Get precise financial numbers from SEC XBRL data.

IMPORTANT RULES:
1. Call tools ONE AT A TIME, not in parallel.
2. First call recall_from_memory and WAIT for the result.
3. If memory has relevant data, USE IT directly. Do NOT call get_financial_metric again to "verify."
4. Only call get_financial_metric if memory returns nothing relevant.

Use exact figures from filings. Never invent numbers."""

#xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# endregion

# region Agents
def orchestrator_node(state: AgentState):
    messages = [SystemMessage(content=ORCHESTRATOR_PROMPT)] + state["messages"]
    response = llm.invoke(messages)
    specialist = response.content.strip().lower()
    return {"current_step": specialist, "messages": [response]}


def research_agent_node(state: AgentState):
    # Strip any old SystemMessages, use only our prompt
    non_system = [m for m in state["messages"] if not isinstance(m, SystemMessage)]
    messages = [SystemMessage(content=RESEARCH_PROMPT)] + non_system
    response = research_llm.invoke(messages)
    return {"messages": [response]}


def financial_agent_node(state: AgentState):
    # Strip any old SystemMessages, use only our prompt
    non_system = [m for m in state["messages"] if not isinstance(m, SystemMessage)]
    messages = [SystemMessage(content=FINANCIAL_PROMPT)] + non_system
    response = financial_llm.invoke(messages)
    return {"messages": [response]}
# endregion

# region Edges
def route_to_specialist(state: AgentState):
    if state["current_step"] == "financial":
        return "financial_agent"
    return "research_agent"

def research_should_continue(state: AgentState):
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "research_tools"
    return END

def financial_should_continue(state: AgentState):
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "financial_tools"
    return END


#endregion

#region Tool Nodes
research_tool_node = ToolNode(research_tools)
financial_tool_node = ToolNode(financial_tools)

#endregion

def build_agent():
    graph = StateGraph(AgentState)
# This is the updated graph structure. There are 3 agents ( Orc, Research, Financial), 2 Tool Nodes (research tools, financial tools)
# There are 5 edges, 3 conditional edges and 2 normal. Conditional edges dont just only route to ONE node but more than one or END, normal edges ALWAYS route to another node    
# Full Explanation : The agent system gets invoked by main.py and since the entry point is orc, it will send the state to the orc agent which will add the orc prompt and send that to the LLM to respond with one word (research or financial) to se saved under "current_step" in the state. Then since the edge from the orc node is to "route_to_specialist" that route function will run and will either call the research agent node or the finaicial agent node. The respective node will run which will send the state to the LLM with the tools and the LLM will choose what tool to call and add that to the messages. That node is now done and according to the graph, the edge is to the router function either "research_should_continue" or "financial_should_continue" which would see if the last message is a tool call by the LLM and if it is, it will call the respective tool node. When the tool node is done, the edges automatically send it back to either the reseach agent node or the finaicial agent node which would decide to keep going or END.This would end the whole agent graph  
    
    
    
    graph.add_node("orchestrator", orchestrator_node)
    graph.add_node("research_agent", research_agent_node)
    graph.add_node("financial_agent", financial_agent_node)
    graph.add_node("research_tools", research_tool_node)
    graph.add_node("financial_tools", financial_tool_node)

    graph.set_entry_point("orchestrator")

    graph.add_conditional_edges("orchestrator", route_to_specialist)
   
    graph.add_conditional_edges("research_agent", research_should_continue)
    graph.add_edge("research_tools", "research_agent")
   
    graph.add_conditional_edges("financial_agent", financial_should_continue)
    graph.add_edge("financial_tools", "financial_agent")

    return graph.compile()


agent = build_agent()