"""
Example usage of the SERP API tool.

This example demonstrates how to use the serp_api function to search Google
and process the results.

Note: You need to set SERPAPI_API_KEY environment variable before running this.
Get a free API key from https://serpapi.com/
"""

import asyncio
import sys
import os

# Add functions directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'functions'))

from serp_api import serp_api


async def example_basic_search():
    """Example 1: Basic search"""
    print("=" * 60)
    print("Example 1: Basic Search")
    print("=" * 60)
    
    result = await serp_api(query="Python programming tutorials", num_results=5)
    
    if result.get("status") == "success":
        print(f"\nSearch Query: {result['query']}")
        print(f"Found {len(result['organic_results'])} results:\n")
        
        for item in result["organic_results"]:
            print(f"{item['position']}. {item['title']}")
            print(f"   URL: {item['link']}")
            print(f"   {item['snippet'][:100]}...")
            print()
    else:
        print(f"❌ Error: {result.get('error')}")


async def example_with_location():
    """Example 2: Search with location"""
    print("=" * 60)
    print("Example 2: Search with Location")
    print("=" * 60)
    
    result = await serp_api(
        query="restaurants near me",
        location="San Francisco, CA",
        num_results=3
    )
    
    if result.get("status") == "success":
        print(f"\nSearch Query: {result['query']}")
        print(f"Location: San Francisco, CA")
        print(f"\nTop {len(result['organic_results'])} results:\n")
        
        for item in result["organic_results"]:
            print(f"• {item['title']}")
            print(f"  {item['link']}\n")
    else:
        print(f"❌ Error: {result.get('error')}")


async def example_knowledge_graph():
    """Example 3: Get knowledge graph information"""
    print("=" * 60)
    print("Example 3: Knowledge Graph")
    print("=" * 60)
    
    result = await serp_api(query="Albert Einstein", num_results=1)
    
    if result.get("status") == "success":
        if "knowledge_graph" in result:
            kg = result["knowledge_graph"]
            print("\n📚 Knowledge Graph:")
            print(f"Title: {kg.get('title', 'N/A')}")
            print(f"Type: {kg.get('type', 'N/A')}")
            if 'description' in kg:
                print(f"Description: {kg['description'][:200]}...")
        else:
            print("\nNo knowledge graph available for this query")
    else:
        print(f"❌ Error: {result.get('error')}")


async def example_related_searches():
    """Example 4: Get related searches"""
    print("=" * 60)
    print("Example 4: Related Searches")
    print("=" * 60)
    
    result = await serp_api(query="machine learning", num_results=1)
    
    if result.get("status") == "success":
        if "related_searches" in result:
            print("\n🔍 Related Searches:")
            for related in result["related_searches"][:5]:
                print(f"  • {related['query']}")
        else:
            print("\nNo related searches available")
    else:
        print(f"❌ Error: {result.get('error')}")


async def main():
    """Run all examples"""
    print("\n")
    print("🚀 SERP API Examples")
    print("=" * 60)
    
    # Check if API key is set
    if not os.getenv("SERPAPI_API_KEY"):
        print("\n⚠️  Warning: SERPAPI_API_KEY not set!")
        print("\nTo run these examples:")
        print("1. Get a free API key from https://serpapi.com/")
        print("2. Set it in your .env file or environment:")
        print("   export SERPAPI_API_KEY=your_key_here")
        print("\nRunning basic validation test instead...\n")
        
        # Run a validation test
        result = await serp_api(query="")
        print(f"Validation test: {result.get('error')}")
        return
    
    # Run all examples
    try:
        await example_basic_search()
        print("\n")
        
        await example_with_location()
        print("\n")
        
        await example_knowledge_graph()
        print("\n")
        
        await example_related_searches()
        print("\n")
        
        print("=" * 60)
        print("✅ All examples completed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")


if __name__ == "__main__":
    asyncio.run(main())
