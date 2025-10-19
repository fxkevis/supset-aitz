#!/usr/bin/env python3
"""Make message input visible and send message"""

import asyncio
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from ultimate_agent import UltimateAIAgent

async def test_make_input_visible():
    """Make message input visible and send message."""
    print("👁️ Making Message Input Visible...")
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
                print("✅ On Telegram Web")
                
                # Try to scroll to bottom to make message input visible
                print("\\n📜 Scrolling to bottom to reveal message input...")
                agent.browser.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                await asyncio.sleep(2)
                
                # Try clicking on the page to focus it
                print("🖱️ Clicking on page to focus...")
                try:
                    body = agent.browser.driver.find_element("tag name", "body")
                    body.click()
                    await asyncio.sleep(1)
                except:
                    pass
                
                # Look for message input again
                print("\\n🔍 Looking for message input after scrolling...")
                
                message_selectors = [
                    "div[contenteditable='true']",
                    "[role='textbox']"
                ]
                
                for selector in message_selectors:
                    try:
                        message_inputs = agent.browser.driver.find_elements("css selector", selector)
                        print(f"🔍 Selector {selector}: found {len(message_inputs)} elements")
                        
                        for i, message_input in enumerate(message_inputs):
                            try:
                                visible = message_input.is_displayed()
                                enabled = message_input.is_enabled()
                                location = message_input.location
                                size = message_input.size
                                
                                print(f"  Element {i+1}: Visible={visible}, Enabled={enabled}")
                                print(f"    Location: {location}, Size: {size}")
                                
                                if enabled:  # Try even if not visible
                                    print(f"  🎯 Trying to use element {i+1}...")
                                    
                                    # Try to scroll to element
                                    agent.browser.driver.execute_script("arguments[0].scrollIntoView(true);", message_input)
                                    await asyncio.sleep(1)
                                    
                                    # Try to click to focus
                                    try:
                                        message_input.click()
                                        await asyncio.sleep(1)
                                    except:
                                        pass
                                    
                                    # Try to type
                                    try:
                                        message_input.clear()
                                        message_input.send_keys("hello")
                                        print("  ✅ Successfully typed 'hello'!")
                                        
                                        # Try to send
                                        from selenium.webdriver.common.keys import Keys
                                        message_input.send_keys(Keys.ENTER)
                                        print("  📤 Sent message!")
                                        
                                        print("🎉 Message sent successfully!")
                                        return
                                        
                                    except Exception as e:
                                        print(f"  ❌ Could not type: {e}")
                                        
                            except Exception as e:
                                print(f"  ❌ Error with element {i+1}: {e}")
                                
                    except Exception as e:
                        print(f"❌ Selector {selector} failed: {e}")
                
                # If still not working, try alternative approach
                print("\\n🔧 Trying alternative approach...")
                try:
                    # Try to find and click on message area
                    message_area_selectors = [
                        ".composer",
                        ".message-compose",
                        ".input-wrapper",
                        "[data-testid='composer']"
                    ]
                    
                    for selector in message_area_selectors:
                        try:
                            areas = agent.browser.driver.find_elements("css selector", selector)
                            if areas:
                                print(f"Found message area with {selector}")
                                areas[0].click()
                                await asyncio.sleep(1)
                                break
                        except:
                            continue
                    
                    # Try typing directly with JavaScript
                    print("🔧 Trying JavaScript approach...")
                    script = """
                    var editables = document.querySelectorAll('[contenteditable="true"]');
                    for (var i = 0; i < editables.length; i++) {
                        if (editables[i].offsetParent !== null) {  // Check if visible
                            editables[i].focus();
                            editables[i].textContent = 'hello';
                            
                            // Trigger Enter key
                            var event = new KeyboardEvent('keydown', {
                                key: 'Enter',
                                code: 'Enter',
                                keyCode: 13,
                                which: 13,
                                bubbles: true
                            });
                            editables[i].dispatchEvent(event);
                            return 'Message sent via JavaScript!';
                        }
                    }
                    return 'No visible contenteditable found';
                    """
                    
                    result = agent.browser.driver.execute_script(script)
                    print(f"JavaScript result: {result}")
                    
                    if "sent" in result.lower():
                        print("🎉 Message sent via JavaScript!")
                    else:
                        print("❌ JavaScript approach also failed")
                        
                except Exception as e:
                    print(f"❌ Alternative approach failed: {e}")
                    
            else:
                print("❌ Not on Telegram Web")
                
        else:
            print("❌ Could not connect to existing Chrome")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
    
    finally:
        print("\\nℹ️  Keeping your Chrome open")

if __name__ == "__main__":
    asyncio.run(test_make_input_visible())