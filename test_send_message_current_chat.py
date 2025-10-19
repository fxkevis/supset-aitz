#!/usr/bin/env python3
"""Send message to current open chat"""

import asyncio
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from ultimate_agent import UltimateAIAgent

async def test_send_message_current_chat():
    """Send message to currently open chat."""
    print("💬 Testing Message Send to Current Chat...")
    print("=" * 50)
    
    agent = UltimateAIAgent()
    await agent.initialize()
    
    try:
        # Connect to existing Chrome
        connected = await agent.try_connect_existing_chrome()
        
        if connected:
            agent.browser_started = True
            from selenium.webdriver.support.ui import WebDriverWait
            agent.wait = WebDriverWait(agent.browser.driver, 10)
            
            print("✅ Connected to your existing Chrome")
            
            # Check current page
            current_url = agent.browser.driver.current_url
            page_title = agent.browser.driver.title
            print(f"📍 Current URL: {current_url}")
            print(f"📄 Page title: {page_title}")
            
            if "telegram" in current_url.lower():
                print("✅ Already on Telegram Web")
                
                print("\\n🔍 Looking for message input in current chat...")
                
                # Try all possible message input selectors
                message_selectors = [
                    "div[contenteditable='true'][data-testid='message-input']",
                    "div[contenteditable='true']",
                    "[role='textbox']",
                    ".composer-input",
                    "[placeholder*='Message']",
                    "[placeholder*='message']",
                    "textarea",
                    ".message-input",
                    ".input-message-input",
                    "[data-testid='message-input']"
                ]
                
                message_sent = False
                for selector in message_selectors:
                    try:
                        message_inputs = agent.browser.driver.find_elements("css selector", selector)
                        print(f"🔍 Trying selector: {selector} - found {len(message_inputs)} elements")
                        
                        for message_input in message_inputs:
                            try:
                                if message_input.is_displayed() and message_input.is_enabled():
                                    print(f"✅ Found working message input!")
                                    
                                    # Clear and type message
                                    print("✍️ Typing 'hello' message...")
                                    message_input.clear()
                                    message_input.send_keys("hello")
                                    
                                    # Wait a moment
                                    await asyncio.sleep(1)
                                    
                                    # Try to send with Enter
                                    print("📤 Sending message...")
                                    from selenium.webdriver.common.keys import Keys
                                    message_input.send_keys(Keys.ENTER)
                                    
                                    print("🎉 Message sent successfully!")
                                    message_sent = True
                                    break
                            except Exception as e:
                                print(f"⚠️  Element not usable: {e}")
                                continue
                        
                        if message_sent:
                            break
                            
                    except Exception as e:
                        print(f"❌ Selector {selector} failed: {e}")
                        continue
                
                if not message_sent:
                    print("❌ Could not find working message input")
                    
                    # Debug: show all elements that might be message inputs
                    print("\\n🔍 Debug: All contenteditable elements:")
                    editables = agent.browser.driver.find_elements("css selector", "[contenteditable='true']")
                    for i, edit in enumerate(editables):
                        try:
                            visible = edit.is_displayed()
                            enabled = edit.is_enabled()
                            tag = edit.tag_name
                            class_name = edit.get_attribute("class") or "No class"
                            print(f"  {i+1}. {tag} - Visible: {visible}, Enabled: {enabled}")
                            print(f"      Class: {class_name}")
                        except Exception as e:
                            print(f"  {i+1}. Error: {e}")
            else:
                print("❌ Not on Telegram Web")
                
        else:
            print("❌ Could not connect to existing Chrome")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
    
    finally:
        print("\\nℹ️  Keeping your Chrome open")

if __name__ == "__main__":
    asyncio.run(test_send_message_current_chat())