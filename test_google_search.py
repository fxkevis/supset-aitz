#!/usr/bin/env python3
"""Test Google Search with Existing Chrome Connection"""

import asyncio
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from ultimate_agent import UltimateAIAgent

async def test_google_search():
    """Test Google search using existing Chrome connection."""
    print("🔍 Testing Google Search with Existing Chrome...")
    print("=" * 50)
    
    agent = UltimateAIAgent()
    await agent.initialize()
    
    try:
        # Try to connect to existing Chrome first
        print("🔄 Connecting to your existing Chrome...")
        connected = await agent.try_connect_existing_chrome()
        
        if connected:
            agent.browser_started = True
            print("✅ Connected to your existing Chrome with all your logins!")
            
            # Navigate to Google
            print("\\n🌐 Step 1: Opening Google...")
            agent.browser.driver.get("https://www.google.com")
            await asyncio.sleep(2)
            
            # Find search box
            print("🔍 Step 2: Finding search box...")
            search_box = agent.browser.driver.find_element("name", "q")
            
            # Type search query
            print("⌨️  Step 3: Typing search query...")
            search_box.clear()
            search_box.send_keys("AI browser automation")
            
            # Press Enter to search
            print("🔍 Step 4: Executing search...")
            search_box.submit()
            await asyncio.sleep(3)
            
            # Get results
            print("📊 Step 5: Getting search results...")
            current_url = agent.browser.driver.current_url
            page_title = agent.browser.driver.title
            
            print(f"✅ Search completed!")
            print(f"📍 Current URL: {current_url}")
            print(f"📄 Page title: {page_title}")
            
            # Count results
            try:
                results = agent.browser.driver.find_elements("css selector", "h3")
                print(f"🔢 Found {len(results)} search result headings")
                
                # Show first few results
                for i, result in enumerate(results[:3]):
                    try:
                        text = result.text[:100]
                        print(f"  {i+1}. {text}...")
                    except:
                        pass
                        
            except Exception as e:
                print(f"⚠️  Could not count results: {e}")
            
        else:
            print("❌ Could not connect to existing Chrome")
            print("💡 Please run: ./setup_chrome_for_agent.sh")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
    
    finally:
        print("\\nℹ️  Keeping your Chrome open")
        # Don't close the browser

if __name__ == "__main__":
    asyncio.run(test_google_search())