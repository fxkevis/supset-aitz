#!/usr/bin/env python3
"""Debug Telegram Search - Check if typing actually works"""

import asyncio
import sys
import time
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from navigation_manager import NavigationManager

async def debug_telegram_search():
    """Debug what happens when we type in Telegram search."""
    print("🔍 Debugging Telegram Search Typing...")
    print("=" * 50)
    
    nav = NavigationManager()
    
    if nav.connect_to_chrome():
        print("✅ Connected to Chrome")
        
        # Navigate to Telegram
        print("\n📱 Opening Telegram Web...")
        if nav.navigate_to_website("https://web.telegram.org"):
            await asyncio.sleep(5)
            
            # Find search box
            print("\n🔍 Finding search box...")
            search_selectors = [
                "input[type='search']",
                "input[placeholder*='Search']",
                "input[placeholder*='search']",
                "input[type='text']"
            ]
            
            search_box = nav.find_element_reliable(search_selectors, "search box")
            
            if search_box:
                print("✅ Found search box")
                
                # Check initial value
                initial_value = search_box.get_attribute("value") or ""
                print(f"📝 Initial search box value: '{initial_value}'")
                
                # Try typing
                print("\n⌨️  Attempting to type '@stroiteeleva'...")
                success = nav.type_text_reliable(search_box, "@stroiteeleva")
                
                if success:
                    # Wait a moment
                    await asyncio.sleep(2)
                    
                    # Check value after typing
                    after_value = search_box.get_attribute("value") or ""
                    print(f"📝 Search box value after typing: '{after_value}'")
                    
                    # Check if the value actually changed
                    if after_value == "@stroiteeleva":
                        print("✅ Typing worked correctly!")
                    elif after_value == initial_value:
                        print("❌ Typing failed - value unchanged")
                    else:
                        print(f"⚠️  Unexpected value: '{after_value}'")
                    
                    # Try alternative typing methods
                    print("\n🔧 Trying alternative typing methods...")
                    
                    # Method 1: Focus first, then type
                    try:
                        search_box.click()
                        await asyncio.sleep(1)
                        search_box.clear()
                        search_box.send_keys("@stroiteeleva")
                        await asyncio.sleep(2)
                        
                        focus_value = search_box.get_attribute("value") or ""
                        print(f"📝 After focus+type: '{focus_value}'")
                    except Exception as e:
                        print(f"❌ Focus method failed: {e}")
                    
                    # Method 2: JavaScript direct
                    try:
                        nav.driver.execute_script("arguments[0].value = '@stroiteeleva';", search_box)
                        nav.driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", search_box)
                        await asyncio.sleep(2)
                        
                        js_value = search_box.get_attribute("value") or ""
                        print(f"📝 After JavaScript: '{js_value}'")
                    except Exception as e:
                        print(f"❌ JavaScript method failed: {e}")
                    
                    # Method 3: Character by character
                    try:
                        search_box.clear()
                        for char in "@stroiteeleva":
                            search_box.send_keys(char)
                            await asyncio.sleep(0.1)
                        
                        char_value = search_box.get_attribute("value") or ""
                        print(f"📝 After char-by-char: '{char_value}'")
                    except Exception as e:
                        print(f"❌ Character method failed: {e}")
                    
                    # Now continue with the full workflow
                    print("\n👤 Step 3: Looking for contact in search results...")
                    await asyncio.sleep(3)  # Wait for search results
                    
                    # Look for contact
                    contact_selectors = [
                        f"//*[contains(text(), 'stroiteeleva')]",
                        f"//*[contains(text(), '@stroiteeleva')]", 
                        ".ListItem",
                        ".chat-item:first-child",
                        ".contact-item:first-child",
                        ".search-result:first-child"
                    ]
                    
                    contact = nav.find_element_reliable(contact_selectors, "contact @stroiteeleva")
                    
                    if contact:
                        print("✅ Found contact!")
                        
                        # Click on contact
                        print("🖱️  Clicking on contact...")
                        if nav.click_element_reliable(contact):
                            print("✅ Successfully clicked contact")
                            
                            # Wait for chat to open
                            await asyncio.sleep(5)
                            
                            # Look for message input
                            print("\n💬 Step 4: Looking for message input...")
                            message_selectors = [
                                "[role='textbox'][contenteditable='true']",
                                "div[contenteditable='true']",
                                "[role='textbox']",
                                "[placeholder*='Message']",
                                "[placeholder*='message']",
                                ".composer-input-wrapper",
                                ".composer-input",
                                "textarea"
                            ]
                            
                            message_input = nav.find_element_reliable(message_selectors, "message input")
                            
                            if message_input:
                                print("✅ Found message input!")
                                
                                # Type message
                                print("⌨️  Typing 'hello'...")
                                if nav.type_text_reliable(message_input, "hello"):
                                    print("✅ Successfully typed message")
                                    
                                    # Send message (press Enter)
                                    try:
                                        from selenium.webdriver.common.keys import Keys
                                        message_input.send_keys(Keys.ENTER)
                                        print("📤 Message sent!")
                                        print("🎉 Complete workflow successful!")
                                    except Exception as e:
                                        print(f"❌ Could not send message: {e}")
                                else:
                                    print("❌ Could not type message")
                            else:
                                print("❌ Could not find message input")
                        else:
                            print("❌ Could not click contact")
                    else:
                        print("❌ Could not find contact in search results")
                        
                        # Debug: show what elements are available
                        print("\n🔍 Debug: Available elements after search...")
                        try:
                            all_elements = nav.driver.find_elements("css selector", "*")
                            visible_elements = [elem for elem in all_elements if elem.is_displayed() and elem.text.strip()]
                            
                            print(f"Found {len(visible_elements)} visible elements with text")
                            for i, elem in enumerate(visible_elements[:10]):  # Show first 10
                                try:
                                    text = elem.text[:50]
                                    tag = elem.tag_name
                                    if "stroiteeleva" in text.lower():
                                        print(f"  🎯 {i+1}. {tag}: '{text}' (CONTAINS TARGET!)")
                                    else:
                                        print(f"  {i+1}. {tag}: '{text}'")
                                except:
                                    pass
                        except Exception as e:
                            print(f"Debug failed: {e}")
                
                else:
                    print("❌ Initial typing attempt failed")
            else:
                print("❌ Could not find search box")
        else:
            print("❌ Could not navigate to Telegram")
        
        nav.close()
    else:
        print("❌ Could not connect to Chrome")

if __name__ == "__main__":
    asyncio.run(debug_telegram_search())