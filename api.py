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