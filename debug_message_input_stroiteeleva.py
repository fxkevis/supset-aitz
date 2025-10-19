#!/usr/bin/env python3
"""Debug Message Input for @stroiteeleva Chat"""

import asyncio
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from ultimate_agent import UltimateAIAgent

async def debug_message_input_stroiteeleva():
    """Debug message input after opening @stroiteeleva chat."""
    print("🔍 Debugging Message Input for @stroiteeleva...")
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
            
            # Navigate to Telegram and search
            print("\\n📱 Opening Telegram and searching for @stroiteeleva...")
            agent.browser.driver.get("https://web.telegram.org")
            await asyncio.sleep(5)
            
            # Search for @stroiteeleva
            search_input = agent.browser.driver.find_element("css selector", "input[placeholder*='Search']")
            search_input.clear()
            search_input.send_keys("@stroiteeleva")
            await asyncio.sleep(3)
            
            # Click on contact
            contact = agent.browser.driver.find_element("xpath", "//*[contains(text(), 'stroiteeleva')]")
            contact.click()
            await asyncio.sleep(5)
            
            print("✅ Opened chat with @stroiteeleva")
            print("\\n🔍 Analyzing all input elements...")
            
            # Find all input elements
            inputs = agent.browser.driver.find_elements("tag name", "input")
            print(f"Found {len(inputs)} input elements:")
            
            for i, inp in enumerate(inputs):
                try:
                    placeholder = inp.get_attribute("placeholder") or "No placeholder"
                    input_type = inp.get_attribute("type") or "text"
                    class_name = inp.get_attribute("class") or "No class"
                    visible = inp.is_displayed()
                    enabled = inp.is_enabled()
                    print(f"  {i+1}. Type: {input_type}, Placeholder: '{placeholder}', Visible: {visible}, Enabled: {enabled}")
                except Exception as e:
                    print(f"  {i+1}. Error reading input: {e}")
            
            print("\\n🔍 Analyzing contenteditable elements...")
            editables = agent.browser.driver.find_elements("css selector", "[contenteditable='true']")
            print(f"Found {len(editables)} contenteditable elements:")
            
            for i, edit in enumerate(editables):
                try:
                    tag = edit.tag_name
                    class_name = edit.get_attribute("class") or "No class"
                    visible = edit.is_displayed()
                    enabled = edit.is_enabled()
                    text = edit.text[:50] if edit.text else "No text"
                    print(f"  {i+1}. Tag: {tag}, Visible: {visible}, Enabled: {enabled}, Text: '{text}'")
                    print(f"      Class: {class_name}")
                except Exception as e:
                    print(f"  {i+1}. Error reading editable: {e}")
            
            print("\\n🔍 Analyzing textarea elements...")
            textareas = agent.browser.driver.find_elements("tag name", "textarea")
            print(f"Found {len(textareas)} textarea elements:")
            
            for i, textarea in enumerate(textareas):
                try:
                    placeholder = textarea.get_attribute("placeholder") or "No placeholder"
                    class_name = textarea.get_attribute("class") or "No class"
                    visible = textarea.is_displayed()
                    enabled = textarea.is_enabled()
                    print(f"  {i+1}. Placeholder: '{placeholder}', Visible: {visible}, Enabled: {enabled}")
                    print(f"      Class: {class_name}")
                except Exception as e:
                    print(f"  {i+1}. Error reading textarea: {e}")
            
            print("\\n🔍 Testing specific selectors...")
            test_selectors = [
                "[role='textbox']",
                "div[contenteditable='true']",
                ".composer-input",
                "[placeholder*='Message']",
                "[placeholder*='message']",
                "[data-testid='message-input']",
                ".message-input",
                ".input-message-input"
            ]
            
            for selector in test_selectors:
                try:
                    elements = agent.browser.driver.find_elements("css selector", selector)
                    if elements:
                        print(f"✅ Found {len(elements)} elements with selector: {selector}")
                        for elem in elements:
                            visible = elem.is_displayed()
                            enabled = elem.is_enabled()
                            print(f"    - Visible: {visible}, Enabled: {enabled}")
                            if visible and enabled:
                                print(f"    🎯 THIS ONE SHOULD WORK!")
                except Exception as e:
                    print(f"❌ Error with selector {selector}: {e}")
            
        else:
            print("❌ Could not connect to existing Chrome")
            
    except Exception as e:
        print(f"❌ Debug failed: {e}")
    
    finally:
        print("\\nℹ️  Debug complete - keeping Chrome open")

if __name__ == "__main__":
    asyncio.run(debug_message_input_stroiteeleva())