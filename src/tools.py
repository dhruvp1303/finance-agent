import os
import requests
from langchain_core.tools import tool
from tavily import TavilyClient
from dotenv import load_dotenv

load_dotenv()

tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
#hey
SEC_HEADERS = {
    "User-Agent": "Dhruv Patel dhruvp1303@gmail.com"
}


@tool
def search_web(query: str) -> str:
    """Search the web for recent news, analyst opinions, and market commentary.
    Use this for finding current information about a company, industry trends,
    or anything not in SEC filings."""
    results = tavily_client.search(query, max_results=5)
    return str(results)


@tool
def get_sec_filings(ticker: str, filing_type: str = "10-K") -> str:
    """Fetch the most recent SEC filing for a given company ticker.
    Use this to get official financial data, earnings, debt, and risk disclosures.
    filing_type can be '10-K' (annual), '10-Q' (quarterly), or '8-K' (current events)."""

    # Step 1: Get the CIK number for the ticker
    ticker_url = "https://www.sec.gov/files/company_tickers.json"
    ticker_data = requests.get(ticker_url, headers=SEC_HEADERS).json()

    cik = None
    for item in ticker_data.values():
        if item["ticker"] == ticker.upper():
            cik = str(item["cik_str"]).zfill(10)
            break

    if not cik:
        return f"Could not find CIK for ticker {ticker}"

    # Step 2: Get the list of filings for that CIK
    filings_url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    filings_data = requests.get(filings_url, headers=SEC_HEADERS).json()

    # Step 3: Find the most recent filing of the requested type
    recent = filings_data["filings"]["recent"]
    for i, form in enumerate(recent["form"]):
        if form == filing_type:
            accession = recent["accessionNumber"][i].replace("-", "")
            primary_doc = recent["primaryDocument"][i]
            filing_url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession}/{primary_doc}"
            return f"Found {filing_type} for {ticker}: {filing_url}"

    return f"No {filing_type} found for {ticker}"