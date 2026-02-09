"""
SERP API tool for Google search results.

Simple function to query Google search results using SerpAPI service.
Returns structured search results including organic results, knowledge graph, and more.
"""

import os
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()


async def serp_api(
    query: str,
    num_results: Optional[int] = 10,
    location: Optional[str] = None,
    language: Optional[str] = "en",
    safe_search: Optional[bool] = False,
) -> Dict[str, Any]:
    """
    Search Google using SerpAPI and return structured results.

    Args:
        query: The search query string.
        num_results: Number of results to return (default: 10, max: 100).
        location: Optional location for localized results (e.g., "United States", "New York").
        language: Language code for results (default: "en").
        safe_search: Enable safe search filtering (default: False).

    Returns:
        Dict with search results including:
        - organic_results: List of organic search results
        - knowledge_graph: Knowledge graph data if available
        - answer_box: Answer box data if available
        - related_searches: Related search queries
        - search_metadata: Metadata about the search
        - error: Error message if the search failed

    Example:
        result = await serp_api(query="Python programming", num_results=5)
        for item in result.get("organic_results", []):
            print(f"{item['title']}: {item['link']}")
    """
    try:
        # Validate inputs first
        if not query or not query.strip():
            return {"error": "Query cannot be empty", "status": "error"}

        if num_results and (num_results < 1 or num_results > 100):
            return {"error": "num_results must be between 1 and 100", "status": "error"}

        # Check for API key
        api_key = os.getenv("SERPAPI_API_KEY")
        if not api_key:
            return {
                "error": "SERPAPI_API_KEY environment variable not set. Get your API key from https://serpapi.com/",
                "status": "error"
            }

        # Import serpapi (only if needed)
        try:
            from serpapi import GoogleSearch
        except ImportError:
            return {
                "error": "serpapi package not installed. Install it with: pip install google-search-results",
                "status": "error"
            }

        # Build search parameters
        params = {
            "q": query.strip(),
            "api_key": api_key,
            "num": num_results or 10,
            "hl": language or "en",
        }

        if location:
            params["location"] = location

        if safe_search:
            params["safe"] = "active"

        # Perform the search
        search = GoogleSearch(params)
        results = search.get_dict()

        # Check for API errors
        if "error" in results:
            return {
                "error": results["error"],
                "status": "error"
            }

        # Extract and structure the results
        response = {
            "status": "success",
            "query": query,
            "organic_results": [],
            "search_metadata": results.get("search_metadata", {}),
        }

        # Extract organic results
        if "organic_results" in results:
            for result in results["organic_results"]:
                response["organic_results"].append({
                    "position": result.get("position"),
                    "title": result.get("title"),
                    "link": result.get("link"),
                    "displayed_link": result.get("displayed_link"),
                    "snippet": result.get("snippet"),
                    "date": result.get("date"),
                })

        # Add knowledge graph if available
        if "knowledge_graph" in results:
            response["knowledge_graph"] = results["knowledge_graph"]

        # Add answer box if available
        if "answer_box" in results:
            response["answer_box"] = results["answer_box"]

        # Add related searches if available
        if "related_searches" in results:
            response["related_searches"] = [
                {"query": item.get("query"), "link": item.get("link")}
                for item in results["related_searches"]
            ]

        # Add people also ask if available
        if "related_questions" in results:
            response["related_questions"] = [
                {
                    "question": item.get("question"),
                    "snippet": item.get("snippet"),
                    "title": item.get("title"),
                    "link": item.get("link"),
                }
                for item in results["related_questions"]
            ]

        return response

    except Exception as e:
        return {
            "error": f"An error occurred: {str(e)}",
            "status": "error"
        }


# Synchronous wrapper for compatibility
def serp_api_sync(
    query: str,
    num_results: Optional[int] = 10,
    location: Optional[str] = None,
    language: Optional[str] = "en",
    safe_search: Optional[bool] = False,
) -> Dict[str, Any]:
    """
    Synchronous version of serp_api.
    
    For use in non-async contexts. See serp_api() for full documentation.
    """
    import asyncio
    
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(
        serp_api(
            query=query,
            num_results=num_results,
            location=location,
            language=language,
            safe_search=safe_search,
        )
    )
