# serp_api

Google search results using SerpAPI. Use this tool to get structured search results from Google including organic results, knowledge graphs, answer boxes, and related searches.

---

## Integrating in a skill or agent

- **Tool name:** `serp_api`  
  Register or attach the async function `serp_api` (from `serp_api.py`) as a tool. The tool name your agent/skill uses should be **serp_api**.

- **API Key Required:**  
  You need a SerpAPI API key. Get one free at [https://serpapi.com/](https://serpapi.com/) (100 free searches/month). Set it as an environment variable `SERPAPI_API_KEY`.

- **Simple usage:**  
  Call the function with a search query and optionally specify the number of results, location, language, and safe search settings.

---

## Parameters

All parameters are passed directly to the function:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| **query** | string | Yes | - | The search query string (e.g., "Python programming", "weather in Paris") |
| **num_results** | integer | No | 10 | Number of results to return (1-100) |
| **location** | string | No | None | Location for localized results (e.g., "United States", "New York, NY") |
| **language** | string | No | "en" | Language code for results (e.g., "en", "es", "fr") |
| **safe_search** | boolean | No | False | Enable safe search filtering |

---

## Response Structure

The function returns a dictionary with the following structure:

```python
{
    "status": "success",  # or "error"
    "query": "your search query",
    "organic_results": [
        {
            "position": 1,
            "title": "Page Title",
            "link": "https://example.com",
            "displayed_link": "example.com",
            "snippet": "Description snippet...",
            "date": "2 days ago"  # if available
        },
        # ... more results
    ],
    "knowledge_graph": {
        # Knowledge graph data if available
        "title": "...",
        "type": "...",
        "description": "...",
        # ... more fields
    },
    "answer_box": {
        # Answer box data if available
        "answer": "...",
        "snippet": "...",
        # ... more fields
    },
    "related_searches": [
        {
            "query": "related search term",
            "link": "https://google.com/search?q=..."
        },
        # ... more related searches
    ],
    "related_questions": [
        {
            "question": "People also ask question",
            "snippet": "Answer snippet",
            "title": "Source title",
            "link": "https://example.com"
        },
        # ... more questions
    ],
    "search_metadata": {
        "id": "search_id",
        "status": "Success",
        "created_at": "timestamp",
        "processed_at": "timestamp",
        "total_time_taken": 1.23
    }
}
```

On error, the response will be:
```python
{
    "status": "error",
    "error": "Error message describing what went wrong"
}
```

---

## Example Usage

### Basic search

```python
import asyncio
from serp_api import serp_api

# Async usage
async def search():
    result = await serp_api(query="Python programming tutorials")
    
    if result.get("status") == "success":
        print(f"Found {len(result['organic_results'])} results")
        for item in result["organic_results"]:
            print(f"{item['position']}. {item['title']}")
            print(f"   {item['link']}")
            print(f"   {item['snippet']}")
            print()
    else:
        print(f"Error: {result.get('error')}")

asyncio.run(search())
```

### Search with location and language

```python
result = await serp_api(
    query="restaurants near me",
    location="New York, NY",
    language="en",
    num_results=5
)
```

### Synchronous usage

```python
from serp_api import serp_api_sync

result = serp_api_sync(query="climate change", num_results=20)
```

### Using in an agent

```python
# Register the tool
agent.register_tool("serp_api", serp_api)

# Agent can now use it
# "Search for recent news about AI safety"
# The agent will call: serp_api(query="AI safety news 2024", num_results=10)
```

---

## Setup Instructions

1. **Install dependencies:**
   ```bash
   pip install google-search-results python-dotenv
   ```

2. **Get a SerpAPI key:**
   - Sign up at [https://serpapi.com/](https://serpapi.com/)
   - Get your API key from the dashboard
   - Free tier includes 100 searches per month

3. **Set environment variable:**
   
   Create a `.env` file in your project root:
   ```env
   SERPAPI_API_KEY=your_api_key_here
   ```
   
   Or set it directly:
   ```bash
   export SERPAPI_API_KEY=your_api_key_here
   ```

---

## Common Use Cases

- **Research:** Find information, articles, and resources on any topic
- **Competitive analysis:** See what content ranks for specific keywords
- **Content discovery:** Find trending topics and related searches
- **Fact checking:** Get diverse sources for verification
- **Local search:** Find businesses, restaurants, services by location
- **News monitoring:** Track recent news and updates on topics
- **Academic research:** Find papers, articles, and educational resources

---

## Tips

- Be specific with queries for better results
- Use `location` parameter for location-specific searches
- Use `num_results` to limit API usage (you have a monthly quota)
- Check the `knowledge_graph` for quick facts and summaries
- Check `answer_box` for direct answers to questions
- Use `related_searches` to discover related topics
- Handle errors gracefully - API key issues are the most common

---

## Error Handling

Common errors and solutions:

| Error | Solution |
|-------|----------|
| "SERPAPI_API_KEY environment variable not set" | Set your API key in `.env` file or environment |
| "serpapi package not installed" | Run `pip install google-search-results` |
| "Query cannot be empty" | Provide a non-empty search query |
| "num_results must be between 1 and 100" | Use a valid number between 1 and 100 |
| API quota exceeded | Wait for quota reset or upgrade your SerpAPI plan |

---

## Notes

- This tool uses the SerpAPI service, which acts as a proxy to Google Search
- SerpAPI handles all the complexity of scraping and parsing Google results
- The free tier is suitable for development and light usage
- For production use with high volume, consider a paid plan
- Results are returned in real-time from Google's actual search results
- The tool is async-first but includes a synchronous wrapper for compatibility
