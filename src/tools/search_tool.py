import os
from langchain.tools import tool
from langchain_community.tools.tavily_search import TavilySearchResults
import json


@tool
def web_search(query: str) -> str:
    """
    Useful for searching the internet for current market trends, competitor prices, and reviews.
    Use this when the information is not available in the internal product catalog.
    """
    api_key = os.getenv("TAVILY_API_KEY")

    if api_key:
        try:
            search = TavilySearchResults(max_results=3)
            results = search.invoke(query)
            return json.dumps(results, indent=2)
        except Exception as e:
            return f"Error performing web search: {str(e)}"
    else:
        # Mock implementation if no API key
        print("Warning: TAVILY_API_KEY not found. Using mock search results.")
        return mock_search(query)


def mock_search(query: str) -> str:
    """Mock search results for testing without API key."""
    query_lower = query.lower()

    if "headphone" in query_lower:
        return json.dumps(
            [
                {
                    "url": "https://example.com/review1",
                    "content": "Sony WH-1000XM5 are the top noise cancelling headphones in 2024, priced around $348.",
                },
                {
                    "url": "https://example.com/market",
                    "content": "The wireless headphone market is trending towards longer battery life and multipoint connection.",
                },
            ]
        )
    elif "price" in query_lower:
        return json.dumps(
            [
                {
                    "url": "https://example.com/pricing",
                    "content": "Competitor prices for similar items have dropped by 5% this month due to seasonal sales.",
                }
            ]
        )
    else:
        return json.dumps(
            [
                {
                    "url": "https://example.com/general",
                    "content": f"Search results for '{query}' suggest high demand in this category.",
                }
            ]
        )
