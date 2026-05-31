from fastapi import FastAPI
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from src.agent import agent

app = FastAPI(title="Multi-Agent Investment Analyst")


# Request body schema - what the client must send
class ResearchRequest(BaseModel):
    question: str


# Response schema - what we send back
class ResearchResponse(BaseModel):
    answer: str


@app.get("/")
async def root():
    return {"status": "ok", "service": "Multi-Agent Investment Analyst"}


@app.post("/research", response_model=ResearchResponse)
async def research(request: ResearchRequest):
    """Run a research query through the multi-agent system."""
    result = await agent.ainvoke({
        "messages": [HumanMessage(content=request.question)]
    })

    # Last message is the final answer
    final_answer = result["messages"][-1].content

    return ResearchResponse(answer=final_answer)

from fastapi import WebSocket, WebSocketDisconnect


@app.websocket("/ws/research")
async def research_ws(websocket: WebSocket):
    """Stream agent reasoning live over WebSocket."""
    await websocket.accept()

    # Map internal node names to user-friendly labels
    NODE_LABELS = {
        "orchestrator": "Orchestrator",
        "research_agent": "Research Agent",
        "research_tools": "Research Tool",
        "financial_agent": "Financial Agent",
        "financial_tools": "Financial Tool",
    }

    try:
        data = await websocket.receive_json()
        question = data.get("question")

        if not question:
            await websocket.send_json({"type": "error", "content": "No question provided"})
            await websocket.close()
            return

        await websocket.send_json({
            "type": "status",
            "agent": "System",
            "message": f"Starting research"
        })

        async for event in agent.astream(
            {"messages": [HumanMessage(content=question)]},
            stream_mode="updates"
        ):
            for node_name, state_update in event.items():
                label = NODE_LABELS.get(node_name, node_name)
                messages = state_update.get("messages", [])

                if not messages:
                    continue

                last_msg = messages[-1]
                msg_type = type(last_msg).__name__

                # Format based on what happened
                if msg_type == "ToolMessage":
                    # A tool just ran
                    await websocket.send_json({
                        "type": "tool_result",
                        "agent": label,
                        "message": f"Tool returned data"
                    })
                elif hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
                    # Agent decided to call tools
                    tool_names = [tc["name"] for tc in last_msg.tool_calls]
                    await websocket.send_json({
                        "type": "tool_call",
                        "agent": label,
                        "message": f"Calling {', '.join(tool_names)}"
                    })
                else:
                    # Agent gave text output
                    content = last_msg.content if isinstance(last_msg.content, str) else str(last_msg.content)

                    # Orchestrator's "financial" or "research" is a routing decision
                    if node_name == "orchestrator":
                        await websocket.send_json({
                            "type": "routing",
                            "agent": label,
                            "message": f"Routing to {content} specialist"
                        })
                    else:
                        # This is the final answer from a specialist
                        await websocket.send_json({
                            "type": "final_answer",
                            "agent": label,
                            "message": content
                        })

        await websocket.send_json({"type": "complete", "agent": "System", "message": "Done"})
        await websocket.close()

    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        await websocket.send_json({"type": "error", "agent": "System", "message": str(e)})
        await websocket.close()