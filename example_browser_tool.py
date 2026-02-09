"""
Example usage of the Browser Tool.

This example demonstrates how to use the browser_tool function to automate
web browsing tasks.

Note: You need to set OPENAI_API_KEY environment variable before running this.
"""

import asyncio
import sys
import os

# Add functions directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'functions'))

from browser_tool import browser_tool


async def example_simple_task():
    """Example 1: Simple one-shot task"""
    print("=" * 60)
    print("Example 1: Simple Task (run_task_and_wait)")
    print("=" * 60)
    
    # Start a session
    print("\n1. Starting browser session...")
    session_response = await browser_tool(action="start_session")
    
    if session_response.get("status") != "success":
        print(f"❌ Failed to start session: {session_response}")
        return
    
    session_id = session_response["session_id"]
    print(f"✓ Session started: {session_id}")
    
    # Run a task and wait for completion
    print("\n2. Running task...")
    task = "Go to https://example.com and get the heading text"
    result = await browser_tool(
        action="run_task_and_wait",
        session_id=session_id,
        task=task,
        timeout_seconds=60
    )
    
    print(f"\nTask Status: {result.get('status')}")
    if result.get("status") == "completed":
        print(f"✓ Task completed successfully")
        print(f"Result: {result.get('result', 'No result')[:200]}...")
    else:
        print(f"Result: {result}")
    
    # Clean up
    print("\n3. Closing session...")
    await browser_tool(action="stop_session", session_id=session_id)
    print("✓ Session closed")


async def example_background_task():
    """Example 2: Background task with status polling"""
    print("\n" + "=" * 60)
    print("Example 2: Background Task (run_task + get_status)")
    print("=" * 60)
    
    # Start a session
    print("\n1. Starting browser session...")
    session_response = await browser_tool(action="start_session")
    
    if session_response.get("status") != "success":
        print(f"❌ Failed to start session: {session_response}")
        return
    
    session_id = session_response["session_id"]
    print(f"✓ Session started: {session_id}")
    
    # Start task in background
    print("\n2. Starting background task...")
    task = "Go to https://www.python.org and find the latest Python version"
    result = await browser_tool(
        action="run_task",
        session_id=session_id,
        task=task
    )
    
    print(f"Task Status: {result.get('status')}")
    
    # Poll for status
    print("\n3. Polling for task completion...")
    for i in range(10):  # Poll up to 10 times
        await asyncio.sleep(3)  # Wait 3 seconds between polls
        
        status = await browser_tool(
            action="get_status",
            session_id=session_id
        )
        
        print(f"   Poll {i+1}: {status.get('status')}")
        
        if status.get("status") in ["completed", "failed", "stopped"]:
            break
    
    # Get the result
    print("\n4. Getting final result...")
    final_result = await browser_tool(
        action="get_result",
        session_id=session_id
    )
    
    print(f"Final Status: {final_result.get('status')}")
    if final_result.get("status") == "completed":
        print(f"✓ Result: {final_result.get('result', 'No result')[:200]}...")
    
    # Clean up
    print("\n5. Closing session...")
    await browser_tool(action="stop_session", session_id=session_id)
    print("✓ Session closed")


async def main():
    """Run all examples"""
    print("\n")
    print("🌐 Browser Tool Examples")
    print("=" * 60)
    
    # Check if API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("\n⚠️  Warning: OPENAI_API_KEY not set!")
        print("\nTo run these examples:")
        print("1. Get an API key from https://platform.openai.com/api-keys")
        print("2. Set it in your .env file or environment:")
        print("   export OPENAI_API_KEY=your_key_here")
        print("\n❌ Cannot run browser examples without API key.")
        return
    
    # Run examples
    try:
        # Example 1: Simple task
        await example_simple_task()
        
        # Wait a bit between examples
        await asyncio.sleep(2)
        
        # Example 2: Background task
        await example_background_task()
        
        print("\n" + "=" * 60)
        print("✅ All examples completed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
