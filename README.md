# WowBits Getting Started Kit

A collection of reusable tools and functions for building AI agents and skills with WowBits. This kit provides ready-to-use functions that can be integrated into your AI agents to extend their capabilities.

## 🚀 Features

This kit includes the following tools:

### 1. Browser Tool
Automate web browsers with session management. Control a real browser to perform tasks, navigate websites, and extract information.

**Use cases:**
- Web scraping and data extraction
- Automated testing
- Form filling and submission
- Website navigation and interaction

[📖 Browser Tool Documentation](functions/browser_tool.md)

### 2. SERP API Tool
Get Google search results programmatically using SerpAPI. Access organic results, knowledge graphs, answer boxes, and related searches.

**Use cases:**
- Research and information gathering
- Competitive analysis
- Content discovery
- Fact checking and verification
- Local business search
- News monitoring

[📖 SERP API Documentation](functions/serp_api.md)

## 📦 Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/PankajMoolrajani/wowbits-getting-started-kit.git
   cd wowbits-getting-started-kit
   ```

2. **Install dependencies:**
   ```bash
   pip install -r functions/requirements.txt
   ```

3. **Set up environment variables:**
   
   Create a `.env` file in the root directory:
   ```env
   # For Browser Tool (if needed)
   OPENAI_API_KEY=your_openai_api_key_here
   
   # For SERP API Tool
   SERPAPI_API_KEY=your_serpapi_key_here
   ```

## 🎯 Quick Start

### Try the Examples

The repository includes ready-to-run example scripts:

```bash
# Run SERP API examples
python3 example_serp_api.py

# Run Browser Tool examples
python3 example_browser_tool.py
```

### Using the Browser Tool

```python
import asyncio
from functions.browser_tool import browser_tool

async def main():
    # Start a browser session
    session = await browser_tool(action="start_session")
    session_id = session["session_id"]
    
    # Run a task
    result = await browser_tool(
        action="run_task_and_wait",
        session_id=session_id,
        task="Go to python.org and get the latest Python version"
    )
    
    print(result)
    
    # Clean up
    await browser_tool(action="stop_session", session_id=session_id)

asyncio.run(main())
```

### Using the SERP API Tool

```python
import asyncio
from functions.serp_api import serp_api

async def main():
    # Search Google
    result = await serp_api(
        query="Python programming tutorials",
        num_results=5
    )
    
    if result["status"] == "success":
        for item in result["organic_results"]:
            print(f"{item['title']}: {item['link']}")
    else:
        print(f"Error: {result['error']}")

asyncio.run(main())
```

## 🛠️ Available Functions

### Browser Tool

**Function:** `browser_tool(action, session_id=None, task=None, instruction=None, timeout_seconds=None)`

**Actions:**
- `start_session` - Start a new browser session
- `run_task_and_wait` - Run a task and wait for completion (recommended)
- `run_task` - Run a task in the background
- `get_status` - Get current task status
- `get_result` - Get task result
- `pause` / `resume` - Control task execution
- `add_instruction` / `update_task` - Modify running tasks
- `stop` - Stop current task
- `stop_session` - Clean up and close browser

### SERP API Tool

**Function:** `serp_api(query, num_results=10, location=None, language="en", safe_search=False)`

**Parameters:**
- `query` (required) - Search query string
- `num_results` - Number of results (1-100, default: 10)
- `location` - Location for localized results
- `language` - Language code (default: "en")
- `safe_search` - Enable safe search (default: False)

**Returns:**
- `organic_results` - List of search results
- `knowledge_graph` - Knowledge graph data (if available)
- `answer_box` - Direct answer (if available)
- `related_searches` - Related search queries
- `related_questions` - "People also ask" questions

## 📚 Documentation

Each tool has detailed documentation in the `functions/` directory:

- [Browser Tool Documentation](functions/browser_tool.md) - Complete guide for browser automation
- [SERP API Documentation](functions/serp_api.md) - Complete guide for Google search

## 🔑 API Keys

### OpenAI API Key (for Browser Tool)
Get your API key from [OpenAI Platform](https://platform.openai.com/api-keys)

### SerpAPI Key (for SERP Tool)
Get your API key from [SerpAPI](https://serpapi.com/) - Free tier includes 100 searches/month

## 🏗️ Project Structure

```
wowbits-getting-started-kit/
├── functions/               # Reusable tool functions
│   ├── browser_tool.py     # Browser automation tool
│   ├── browser_tool.md     # Browser tool documentation
│   ├── serp_api.py         # Google search tool
│   ├── serp_api.md         # SERP API documentation
│   └── requirements.txt    # Python dependencies
├── agent_runner/           # Agent execution environment
├── agent_studio/           # Agent configuration
├── data/                   # Data storage
├── example_browser_tool.py # Browser tool usage examples
├── example_serp_api.py     # SERP API usage examples
└── README.md              # This file
```

## 🤝 Contributing

Contributions are welcome! To add a new tool:

1. Create your tool as `functions/your_tool.py`
2. Add documentation as `functions/your_tool.md`
3. Update `functions/requirements.txt` if needed
4. Add usage examples in the documentation
5. Submit a pull request

## 📝 Best Practices

### For Browser Tool
- Always call `stop_session` when done to clean up resources
- Use `run_task_and_wait` for single tasks (simplest approach)
- Provide clear, step-by-step instructions in tasks
- Handle timeouts gracefully

### For SERP API Tool
- Be mindful of your API quota (100 free searches/month)
- Use specific queries for better results
- Leverage `location` parameter for local searches
- Check `knowledge_graph` and `answer_box` for quick answers
- Handle errors gracefully (especially API key issues)

## ❓ Troubleshooting

### Common Issues

**Browser Tool:**
- "Session not found" - Make sure you use the correct session_id from start_session
- Timeout errors - Increase timeout_seconds or check your task complexity
- Browser crashes - Ensure you have sufficient system resources

**SERP API Tool:**
- "SERPAPI_API_KEY not set" - Set the environment variable in your `.env` file
- "serpapi package not installed" - Run `pip install google-search-results`
- Quota exceeded - Wait for monthly reset or upgrade your plan

## 📄 License

This project is part of the WowBits ecosystem. Please check individual tool licenses and third-party API terms of service.

## 🔗 Resources

- [WowBits Documentation](https://wowbits.ai/docs)
- [SerpAPI Documentation](https://serpapi.com/docs)
- [Browser-Use Documentation](https://github.com/browser-use/browser-use)

## 💬 Support

For questions and support:
- Open an issue in this repository
- Check the individual tool documentation
- Visit [WowBits Community](https://wowbits.ai/community)

---

**Made with ❤️ for the WowBits community**
