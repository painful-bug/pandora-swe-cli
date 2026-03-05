import os
from langchain.tools import tool

_tavily_available = False
_tavily_client = None

try:
    from tavily import TavilyClient
    api_key = os.getenv("TAVILY_API_KEY")
    if api_key:
        _tavily_client = TavilyClient(api_key=api_key)
        _tavily_available = True
except ImportError:
    pass


@tool
def web_search(query: str, max_results: int = 5) -> str:
    """Search the web for information. Returns relevant results for the query."""
    if not _tavily_available or not _tavily_client:
        return "Web search is not available. Set TAVILY_API_KEY in .env and install tavily-python."

    try:
        results = _tavily_client.search(query, max_results=max_results)
        output_parts = []
        for r in results.get("results", []):
            output_parts.append(f"**{r.get('title', 'No title')}**\n{r.get('url', '')}\n{r.get('content', '')}\n")
        return "\n---\n".join(output_parts) or "No results found."
    except Exception as e:
        return f"Search error: {e}"


def get_search_tools() -> list:
    if _tavily_available:
        return [web_search]
    return []
