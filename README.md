# Multi-Agent Investment Analyst

A research system where multiple AI agents work together to answer financial questions. You ask something, the system figures out which specialist should handle it, that specialist uses real tools to find the answer, and you watch the whole reasoning process happen live.

## What you can ask it

Stuff like:
- "What was Tesla's revenue last year?"
- "What's the latest news on Nvidia?"
- "What was Microsoft's Q1 revenue in 2024?"

The system pulls real financial data from SEC filings and recent news from the web. No making up numbers.

## How it works

There's an orchestrator that reads your question and decides which agent should answer it. Two agents are available:

- A **research agent** that handles news and market context (uses Tavily search)
- A **financial agent** that handles SEC filing data (uses the SEC's XBRL API)

Each agent has its own tools and its own focused system prompt, so they stay in their lane. The orchestrator just routes.

There's also a memory layer (ChromaDB) so the agents don't keep re-fetching the same data. If the financial agent looks up Tesla's revenue once, the next agent that needs it just reads from memory.

## What it's built with

- LangGraph for the agent orchestration
- Claude Sonnet 4.5 for the LLM
- FastAPI for the backend, with WebSockets so the frontend gets live reasoning updates
- React (Vite) for the frontend
- ChromaDB for memory
- SEC EDGAR XBRL API and Tavily for data
- Deployed on AWS EC2 (backend, behind Caddy for HTTPS) and Vercel (frontend)

## The live reasoning trace

This is the part I think is coolest. As the system works, every step gets streamed to the frontend over a WebSocket. You see the orchestrator make its routing decision, then watch the specialist call tools one by one, then see the final answer. It feels less like a black box and more like watching someone think.

## Running it yourself

Backend:
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# add ANTHROPIC_API_KEY and TAVILY_API_KEY to a .env file
uvicorn api:app --reload
```

Frontend:
```bash
cd frontend
npm install
npm run dev
```

## What's next

Right now the orchestrator picks one specialist per query. The next step is making it loop, so the orchestrator can call multiple specialists for one question and synthesize across them. I built a prototype of this and ran into some edge cases that need more thought, so it's parked for now.
