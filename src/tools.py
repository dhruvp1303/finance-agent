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

    # Store in memory for future recall
    add_to_memory(
        text=output,
        source="web_search",
        metadata={"query": query}
    )

    return output





@tool
def get_financial_metric(ticker: str, metric: str = "Revenues") -> str:
    """Get historical financial data for a company from SEC XBRL filings.
    Returns the most recent annual values for the requested metric.

    Common metric names:
    - 'Revenues' for revenue (will also try newer tags automatically)
    - 'NetIncomeLoss' for net income
    - 'Assets' for total assets
    - 'Liabilities' for total liabilities
    - 'StockholdersEquity' for equity
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

    # If asking for revenue, try multiple known tags
    if metric.lower() in ["revenue", "revenues"]:
        metrics_to_try = ["RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues"]
    else:
        metrics_to_try = [metric]

    all_annual_values = []
    used_metric = None

    for m in metrics_to_try:
        url = f"https://data.sec.gov/api/xbrl/companyconcept/CIK{cik}/us-gaap/{m}.json"
        response = requests.get(url, headers=SEC_HEADERS)

        if response.status_code != 200:
            continue

        data = response.json()
        if "units" not in data or "USD" not in data["units"]:
            continue

        # Only true annual values: form is 10-K, fiscal period is FY, AND the duration is ~365 days
        for item in data["units"]["USD"]:
            if item.get("form") != "10-K" or item.get("fp") != "FY":
                continue
            # Filter for full-year duration by checking start/end dates
            try:
                from datetime import datetime
                end = datetime.fromisoformat(item["end"])
                # Balance sheet items (Assets, Liabilities) have no "start" or start = end
                # Income statement items (Revenue, NetIncome) have a period
                if "start" in item:
                    start = datetime.fromisoformat(item["start"])
                    days = (end - start).days
                    # Accept either a full year (income statement) or a snapshot (balance sheet)
                    if 0 < days < 350:  # skip quarters
                        continue
            except (KeyError, ValueError):
                continue

            all_annual_values.append(item)

        if all_annual_values:
            used_metric = m
            break

    if not all_annual_values:
        return f"No annual 10-K data found for {metric} on {ticker}"

    # Dedupe by end date, keep latest filed version
    seen_dates = {}
    for item in all_annual_values:
        key = item["end"]
        if key not in seen_dates or item["filed"] > seen_dates[key]["filed"]:
            seen_dates[key] = item

    annual_values = sorted(seen_dates.values(), key=lambda x: x["end"], reverse=True)

    output = f"{ticker} - {used_metric} (Annual / 10-K filings):\n"
    for item in annual_values[:5]:
        value_billions = item["val"] / 1_000_000_000
        output += f"  Fiscal year ending {item['end']}: ${value_billions:,.2f}B (filed {item['filed']})\n"

    # Store in memory
    add_to_memory(
        text=output,
        source="sec_xbrl",
        metadata={"ticker": ticker, "metric": used_metric}
    )

    return output
    
    
    return output




@tool
@tool
def recall_from_memory(query: str, ticker: str = None) -> str:
    """Search past findings stored in memory. Use this BEFORE calling other tools
    to check if relevant information has already been gathered in this session.

    query: what you're looking for
    ticker: optional, pass the ticker symbol to narrow results to that company only
    """
    return search_memory(query, ticker=ticker)