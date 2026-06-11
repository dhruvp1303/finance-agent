import os
import requests
from langchain_core.tools import tool
from tavily import TavilyClient
from dotenv import load_dotenv
from src.memory import add_to_memory
from src.memory import search_memory, add_to_memory


load_dotenv()

tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

SEC_HEADERS = {
    "User-Agent": "Dhruv Patel dhruvp1303@gmail.com"
}


@tool
def search_web(query: str) -> str:
    """Search the web for recent news, analyst opinions, and market commentary.
    Use this for finding current information about a company, industry trends,
    or anything not in SEC filings."""
    results = tavily_client.search(
        query,
        max_results=3,
        search_depth="basic",
        include_answer=True
    )

    output = ""
    if results.get("answer"):
        output += f"Summary: {results['answer']}\n\n"

    output += "Sources:\n"
    for r in results.get("results", []):
        output += f"- {r['title']}\n  {r['url']}\n  {r['content'][:300]}...\n\n"

    
    add_to_memory(
        text=output,
        source="web_search",
        metadata={"query": query}
    )

    return output






@tool
def get_financial_metric(ticker: str, metric: str = "Revenues", period: str = "FY") -> str:
    """Get historical financial data for a company from SEC XBRL filings.

    period options:
    - 'FY' = annual data (from 10-K filings)
    - 'Q1', 'Q2', 'Q3', 'Q4' = quarterly data (from 10-Q filings)

    Common metric names:
    - 'Revenues' or 'RevenueFromContractWithCustomerExcludingAssessedTax' for revenue
    - 'NetIncomeLoss' for net income
    - 'Assets' for total assets
    - 'Liabilities' for total liabilities
    - 'StockholdersEquity' for equity
    - 'CashAndCashEquivalentsAtCarryingValue' for cash
    """

    ticker_url = "https://www.sec.gov/files/company_tickers.json"
    ticker_data = requests.get(ticker_url, headers=SEC_HEADERS).json()

    cik = None
    for item in ticker_data.values():
        if item["ticker"] == ticker.upper():
            cik = str(item["cik_str"]).zfill(10)
            break

    if not cik:
        return f"Could not find CIK for ticker {ticker}"

    if metric.lower() in ["revenue", "revenues"]:
        metrics_to_try = ["RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues"]
    else:
        metrics_to_try = [metric]

    all_values = []
    used_metric = None

    # which filing type to look for based on period
    is_annual = period.upper() == "FY"
    form_type = "10-K" if is_annual else "10-Q"

    for m in metrics_to_try:
        url = f"https://data.sec.gov/api/xbrl/companyconcept/CIK{cik}/us-gaap/{m}.json"
        response = requests.get(url, headers=SEC_HEADERS)

        if response.status_code != 200:
            continue

        data = response.json()
        if "units" not in data or "USD" not in data["units"]:
            continue

        for item in data["units"]["USD"]:
            if item.get("form") != form_type:
                continue
            if item.get("fp") != period.upper():
                continue

            try:
                from datetime import datetime
                end = datetime.fromisoformat(item["end"])
                if "start" in item:
                    start = datetime.fromisoformat(item["start"])
                    days = (end - start).days
                    # Annual: ~365 days, Quarterly: ~90 days
                    if is_annual and 0 < days < 350:
                        continue
                    if not is_annual and (days < 60 or days > 120):
                        continue
            except (KeyError, ValueError):
                continue

            all_values.append(item)

        if all_values:
            used_metric = m
            break

    if not all_values:
        return f"No {period} data found for {metric} on {ticker}"

    seen_dates = {}
    for item in all_values:
        key = item["end"]
        if key not in seen_dates or item["filed"] > seen_dates[key]["filed"]:
            seen_dates[key] = item

    sorted_values = sorted(seen_dates.values(), key=lambda x: x["end"], reverse=True)

    output = f"{ticker} - {used_metric} ({period} / {form_type} filings):\n"
    for item in sorted_values[:5]:
        value_billions = item["val"] / 1_000_000_000
        output += f"  Period ending {item['end']}: ${value_billions:,.2f}B (filed {item['filed']})\n"

    add_to_memory(
        text=output,
        source="sec_xbrl",
        metadata={"ticker": ticker, "metric": used_metric, "period": period}
    )

    return output
    
    
    return output





@tool
def recall_from_memory(query: str, ticker: str = None) -> str:
    """Search past findings stored in memory. Use this BEFORE calling other tools
    to check if relevant information has already been gathered in this session.

    query: what you're looking for
    ticker: optional, pass the ticker symbol to narrow results to that company only
    """
    return search_memory(query, ticker=ticker)