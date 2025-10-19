#!/usr/bin/env python3
"""Test Telegram with @stroiteeleva"""

import asyncio
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from ultimate_agent import UltimateAIAgent

async def test_stroiteeleva():
    """Test Telegram messaging to @stroiteeleva."""
    print("📱 Testing Telegram with @stroiteeleva...")
    print("=" * 50)
    
    agent = UltimateAIAgent()
    await agent.initialize()
    
    try:
        # Connect to existing Chrome
        print("🔄 Connecting to your existing Chrome...")
        connected = await agent.try_connect_existing_chrome()
        
        if connected:
            agent.browser_started = True
            from selenium.webdriver.support.ui import WebDriverWait
            agent.wait = WebDriverWait(agent.browser.driver, 10)
            
            print("✅ Connected to your existing Chrome with all your logins!")
            
            # Navigate to Telegram
            print("\\n📱 Step 1: Opening Telegram Web...")
            agent.browser.driver.get("https://web.telegram.org")
            await asyncio.sleep(5)
            
            # Check what page we're on
            current_url = agent.browser.driver.current_url
            page_title = agent.browser.driver.title
            print(f"📍 Current URL: {current_url}")
            print(f"📄 Page title: {page_title}")
            
            # Check if we're logged in and look for search
            if "telegram" in current_url.lower():
                print("✅ Successfully opened Telegram Web")
                
                # Try different search selectors for new Telegram interface
                print("\\n🔍 Step 2: Looking for search functionality...")
                search_selectors = [
                    "input[type='search']",
                    "input[placeholder*='Search']",
                    "input[placeholder*='search']",
                    "[data-testid='search-input']",
                    ".search-input",
                    "input[type='text']",
                    "[contenteditable='true']",
                    ".composer-input",
                    "[role='textbox']"
                ]
                
                search_found = False
                for selector in search_selectors:
                    try:
                        search_elements = agent.browser.driver.find_elements("css selector", selector)
                        for search_input in search_elements:
                            if search_input.is_displayed() and search_input.is_enabled():
                                print(f"✅ Found search input with selector: {selector}")
                                
                                # Search for @stroiteeleva
                                print("🔍 Step 3: Searching for @stroiteeleva...")
                                search_input.clear()
                                search_input.send_keys("@stroiteeleva")
                                await asyncio.sleep(3)
                                
                                # Look for contact in results
                                print("👤 Step 4: Looking for @stroiteeleva in results...")
                                contact_selectors = [
                                    "//*[contains(text(), 'stroiteeleva')]",
                                    "//*[contains(text(), '@stroiteeleva')]",
                                    ".ListItem",
                                    ".chat-item",
                                    ".contact-item"
                                ]
                                
                                for contact_selector in contact_selectors:
                                    try:
                                        if contact_selector.startswith("//"):
                                            contacts = agent.browser.driver.find_elements("xpath", contact_selector)
                                        else:
                                            contacts = agent.browser.driver.find_elements("css selector", contact_selector)
                                        
                                        for contact in contacts:
                                            if contact.is_displayed() and "stroiteeleva" in contact.text.lower():
                                                print(f"✅ Found @stroiteeleva contact!")
                                                contact.click()
                                                await asyncio.sleep(3)
                                                
                                                # Look for message input
                                                print("💬 Step 5: Looking for message input...")
                                                message_selectors = [
                                                    "[role='textbox']",
                                                    "div[contenteditable='true']",
                                                    ".composer-input",
                                                    "[placeholder*='Message']",
                                                    "[placeholder*='message']",
                                                    "textarea",
                                                    ".message-input"
                                                ]
                                                
                                                for msg_selector in message_selectors:
                                                    try:
                                                        message_inputs = agent.browser.driver.find_elements("css selector", msg_selector)
                                                        for message_input in message_inputs:
                                                            if message_input.is_displayed() and message_input.is_enabled():
                                                                print(f"✅ Found message input!")
                                                                
                                                                # Type and send message
                                                                print("✍️ Step 6: Sending 'hello' message...")
                                                                message_input.clear()
                                                                message_input.send_keys("hello")
                                                                
                                                                # Press Enter to send
                                                                from selenium.webdriver.common.keys import Keys
                                                                message_input.send_keys(Keys.ENTER)
                                                                
                                                                print("🎉 Message sent successfully to @stroiteeleva!")
                                                                return
                                                    except Exception as e:
                                                        continue
                                                
                                                print("❌ Could not find message input")
                                                return
                                    except Exception as e:
                                        continue
                                
                                print("❌ Could not find @stroiteeleva in search results")
                                search_found = True
                                break
                    except Exception as e:
                        continue
                
                if not search_found:
                    print("❌ Could not find any search input")
                    print("💡 The Telegram interface may have changed or you need to log in")
            else:
                print("❌ Not on Telegram Web page")
                
        else:
            print("❌ Could not connect to existing Chrome")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
    
    finally:
        print("\\nℹ️  Keeping your Chrome open")

if __name__ == "__main__":
    asyncio.run(test_stroiteeleva())