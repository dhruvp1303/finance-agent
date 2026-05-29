import chromadb
from chromadb.config import Settings

# Create a persistent client that saves to disk
client = chromadb.PersistentClient(
    path="./chroma_db",
    settings=Settings(anonymized_telemetry=False)
)

# Get or create a collection (like a table in a database)
collection = client.get_or_create_collection(
    name="agent_memory",
    metadata={"description": "Stores findings from agent tool calls"}
)


def add_to_memory(text: str, source: str, metadata: dict = None) -> str:
    """Store a piece of text in memory.

    text: the actual content to remember
    source: where it came from (e.g. 'sec_filing', 'web_search')
    metadata: extra info like ticker, date, filing_type
    """
    if metadata is None:
        metadata = {}

    metadata["source"] = source

    # ChromaDB needs a unique ID per entry
    doc_id = f"{source}_{collection.count()}"

    collection.add(
        documents=[text],
        metadatas=[metadata],
        ids=[doc_id]
    )

    return f"Stored in memory: {doc_id}"


def search_memory(query: str, n_results: int = 3, ticker: str = None) -> str:
    """Search memory for relevant past findings.

    query: what to search for in plain English
    n_results: how many matches to return
    ticker: optional ticker filter to only return relevant memories
    """
    if collection.count() == 0:
        return "Memory is empty. No past findings to recall."

    # Build the filter if ticker provided
    where_filter = {"ticker": ticker} if ticker else None

    results = collection.query(
        query_texts=[query],
        n_results=min(n_results, collection.count()),
        where=where_filter
    )

    if not results["documents"] or not results["documents"][0]:
        return f"No relevant memories found for {ticker or query}."

    output = f"Found {len(results['documents'][0])} relevant memories:\n\n"
    for i, doc in enumerate(results["documents"][0]):
        meta = results["metadatas"][0][i]
        output += f"[{i+1}] Source: {meta.get('source', 'unknown')}\n"
        if "ticker" in meta:
            output += f"    Ticker: {meta['ticker']}\n"
        output += f"    Content: {doc[:1500]}...\n\n"

    return output


def clear_memory():
    """Wipe all memory. Useful between test runs."""
    global collection
    client.delete_collection(name="agent_memory")
    collection = client.get_or_create_collection(name="agent_memory")
    return "Memory cleared."