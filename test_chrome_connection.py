#!/usr/bin/env python3
"""Test Chrome connection for AI Agent"""

import asyncio
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from ultimate_agent import UltimateAIAgent

async def test_chrome_connection():
    """Test if we can connect to existing Chrome."""
    print("🧪 Testing connection to your existing Chrome...")
    print("=" * 50)
    
    agent = UltimateAIAgent()
    
    try:
        # Initialize the agent first
        await agent.initialize()
        
        # Then try to connect
        await agent.start_authorized_browser()
        
        if agent.browser_started:
            print("✅ SUCCESS! Connected to your existing Chrome")
            
            # Get current tab info
            current_url = agent.browser.get_current_url()
            title = agent.browser.get_page_title()
            
            print(f"📍 Current tab URL: {current_url}")
            print(f"📄 Current tab title: {title}")
            print(f"🔢 Total tabs: {len(agent.browser.driver.window_handles)}")
            
            print("\n🎉 Your existing Chrome is ready for the AI agent!")
            
        else:
            print("❌ FAILED to connect to existing Chrome")
            
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if agent.browser_started and agent.browser:
            # Don't close the browser - it's the user's existing Chrome
            print("ℹ️  Keeping your Chrome open")
        
    print("\n" + "=" * 50)
    print("Test complete!")

if __name__ == "__main__":
    asyncio.run(test_chrome_connection())