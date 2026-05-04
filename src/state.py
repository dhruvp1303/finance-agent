from typing import TypedDict, Annotated, Optional
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    # Core
    session_id: str
    query: str
    messages: Annotated[list, add_messages]
    current_step: str
    loop_count: int
    max_loops: int

    # Company
    ticker: str
    company_name: str
    sector: str
    market_cap: float

    # Research outputs
    news_articles: list
    sec_filings: dict
    insider_trades: list
    earnings_sentiment: str

    # Financial metrics
    valuation_metrics: dict
    peer_comparison: dict

    # Analysis
    insights: list
    risk_rating: str
    confidence_score: int
    recommendation: str
    price_target: float

    # Memo
    draft_memo: str
    critique_feedback: list
    final_memo: str

    # Meta
    sources: list
    tokens_used: int
    error_log: list