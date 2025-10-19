#!/usr/bin/env python3
"""Test Telegram with Fixed Navigation"""

import asyncio
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from ultimate_agent import UltimateAIAgent

async def test_telegram_fixed():
    """Test Telegram with proper tab handling."""
    print("📱 Testing Telegram with Fixed Navigation...")
    print("=" * 50)
    
    agent = UltimateAIAgent()
    await agent.initialize()
    
    try:
        # Connect to existing Chrome
        print("🔄 Connecting to your existing Chrome...")
        connected = await agent.try_connect_existing_chrome()
        
        if connected:
            agent.browser_started = True
            agent.wait = agent.browser.driver  # Fix wait object
            from selenium.webdriver.support.ui import WebDriverWait
            agent.wait = WebDriverWait(agent.browser.driver, 10)
            
            print("✅ Connected to your existing Chrome with all your logins!")
            
            # Show current tabs
            print(f"📊 Current tabs: {len(agent.browser.driver.window_handles)}")
            
            # Navigate to Telegram
            print("\\n📱 Step 1: Opening Telegram Web...")
            agent.browser.driver.get("https://web.telegram.org")
            await asyncio.sleep(5)
            
            # Check what page we're on
            current_url = agent.browser.driver.current_url
            page_title = agent.browser.driver.title
            print(f"📍 Current URL: {current_url}")
            print(f"📄 Page title: {page_title}")
            
            # Check if we're logged in
            if "telegram" in current_url.lower():
                print("✅ Successfully opened Telegram Web")
                
                # Look for search box
                print("\\n🔍 Step 2: Looking for search box...")
                try:
                    search_input = agent.browser.driver.find_element("css selector", "input[type='search']")
                    if search_input.is_displayed():
                        print("✅ Found search box!")
                        
                        # Search for Kikita
                        print("🔍 Step 3: Searching for Kikita...")
                        search_input.clear()
                        search_input.send_keys("Kikita")
                        await asyncio.sleep(3)
                        
                        # Look for contact
                        print("👤 Step 4: Looking for contact...")
                        try:
                            contact = agent.browser.driver.find_element("xpath", "//*[contains(text(), 'Kikita')]")
                            if contact.is_displayed():
                                print("✅ Found Kikita contact!")
                                contact.click()
                                await asyncio.sleep(3)
                                
                                # Look for message input
                                print("💬 Step 5: Looking for message input...")
                                try:
                                    message_input = agent.browser.driver.find_element("css selector", "[role='textbox']")
                                    if message_input.is_displayed():
                                        print("✅ Found message input!")
                                        
                                        # Type and send message
                                        print("✍️ Step 6: Sending message...")
                                        message_input.clear()
                                        message_input.send_keys("hello")
                                        
                                        # Press Enter to send
                                        from selenium.webdriver.common.keys import Keys
                                        message_input.send_keys(Keys.ENTER)
                                        
                                        print("🎉 Message sent successfully!")
                                    else:
                                        print("❌ Message input not visible")
                                except Exception as e:
                                    print(f"❌ Could not find message input: {e}")
                            else:
                                print("❌ Kikita contact not visible")
                        except Exception as e:
                            print(f"❌ Could not find Kikita contact: {e}")
                    else:
                        print("❌ Search box not visible")
                except Exception as e:
                    print(f"❌ Could not find search box: {e}")
                    print("💡 You may need to log in to Telegram Web first")
            else:
                print("❌ Not on Telegram Web page")
                print("💡 Navigation may have failed")
            
        else:
            print("❌ Could not connect to existing Chrome")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
    
    finally:
        print("\\nℹ️  Keeping your Chrome open")

if __name__ == "__main__":
    asyncio.run(test_telegram_fixed())