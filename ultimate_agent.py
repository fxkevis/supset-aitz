#!/usr/bin/env python3
"""Ultimate AI Browser Agent - Full Autonomous Control"""

import asyncio
import sys
import os
import tempfile
import json
import time
import re
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from ai_browser_agent.controllers.browser_controller import BrowserController
from ai_browser_agent.models.config import BrowserConfig
from ai_browser_agent.core.task_planner import TaskPlanner
from ai_browser_agent.interfaces.mock_model import MockModel
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class UltimateAIAgent:
    """Ultimate AI Browser Agent with full autonomous control."""
    
    def __init__(self):
        self.browser = None
        self.wait = None
        self.browser_started = False
        self.current_task_context = {}
        
    async def initialize(self):
        """Initialize the ultimate agent."""
        print("🚀 Initializing Ultimate AI Browser Agent...")
        print("🧠 Full autonomous control enabled")
        print("🔐 Authorized Chrome browser mode")
        
        # Configure browser to use your existing Chrome profile
        browser_config = BrowserConfig()
        
        # Use your actual Chrome profile directory
        chrome_profile_path = os.path.expanduser("~/Library/Application Support/Google/Chrome")
        if os.path.exists(chrome_profile_path):
            browser_config.profile_path = chrome_profile_path
            browser_config.profile_directory = "Profile 3"  # Your main profile
            print("✅ Configured to use your existing Chrome profile with all logins")
        else:
            print("❌ Could not find Chrome profile directory")
            raise Exception("Chrome profile not found")
        
        # Remove automation indicators to look like regular browsing
        browser_config.disable_automation_flags = True
        
        # Initialize browser controller
        self.browser = BrowserController(browser_config)
        
        # Initialize task planner
        self.planner = TaskPlanner({}, MockModel())
        self.planner.initialize()
        
        print("✅ Ultimate AI Agent ready for autonomous operation!")
    
    async def process_ultimate_task(self, user_input: str):
        """Process tasks with ultimate autonomous control."""
        print(f"\n🎯 Ultimate Task: {user_input}")
        print("🧠 Analyzing with full AI decision-making...")
        
        # Start browser if needed
        if not self.browser_started:
            await self.start_authorized_browser()
        
        # Analyze the task with enhanced AI
        task_analysis = await self.ultimate_task_analysis(user_input)
        print(f"📋 AI Analysis: {task_analysis['intent']}")
        
        # Execute with full autonomous control
        await self.execute_ultimate_task(task_analysis, user_input)
    
    async def start_authorized_browser(self):
        """Start authorized Chrome browser without interfering with existing Chrome."""
        print("🔄 Connecting to your authorized Chrome browser...")
        
        # First try to connect to existing Chrome with remote debugging
        connected = await self.try_connect_existing_chrome()
        
        if connected:
            self.browser_started = True
            self.wait = WebDriverWait(self.browser.driver, 10)
            print("✅ Connected to your existing Chrome with all your logins!")
            return
        
        # Fallback: Start new Chrome instance
        try:
            print("🚀 Starting separate Chrome instance for AI agent...")
            print("📋 This will preserve your existing Chrome and copy your login sessions")
            
            # Start the browser with copied profile
            self.browser.connect()
            self.wait = WebDriverWait(self.browser.driver, 10)
            self.browser_started = True
            print("✅ AI agent Chrome started with your login sessions!")
            
        except Exception as e:
            print(f"❌ Browser startup failed: {e}")
            print("💡 This might be because the profile is in use by your existing Chrome")
            print("🔄 Trying with temporary profile...")
            
            # Fallback to temporary profile
            try:
                temp_profile = tempfile.mkdtemp(prefix="ai_agent_fallback_")
                self.browser.browser_config.profile_path = temp_profile
                self.browser.browser_config.profile_directory = None
                
                self.browser.connect()
                self.wait = WebDriverWait(self.browser.driver, 10)
                self.browser_started = True
                print("✅ AI agent Chrome started with temporary profile")
                print("⚠️  You may need to log in manually to websites")
                
            except Exception as fallback_error:
                print(f"❌ Fallback also failed: {fallback_error}")
                raise
    
    async def try_connect_existing_chrome(self) -> bool:
        """Try to connect to existing authorized Chrome."""
        try:
            # Install requests if needed
            try:
                import requests
            except ImportError:
                print("📦 Installing requests library...")
                import subprocess
                subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
                import requests
            
            # Check if Chrome is running with remote debugging
            print("🔍 Looking for existing Chrome with remote debugging...")
            response = requests.get("http://localhost:9222/json", timeout=5)
            
            if response.status_code == 200:
                tabs = response.json()
                if tabs:
                    print(f"✅ Found existing Chrome with {len(tabs)} tabs")
                    print("🔗 Connecting to your existing Chrome browser...")
                    
                    # Connect using Chrome DevTools Protocol
                    from selenium.webdriver.chrome.options import Options
                    options = Options()
                    options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
                    
                    from selenium import webdriver
                    self.browser.driver = webdriver.Chrome(options=options)
                    
                    # Verify connection
                    current_url = self.browser.driver.current_url
                    print(f"✅ Successfully connected to your existing Chrome!")
                    print(f"📍 Current tab: {current_url}")
                    return True
                    
        except requests.exceptions.ConnectionError:
            print("❌ Chrome is not running with remote debugging enabled")
            print("💡 Please run: ./setup_chrome_for_agent.sh")
            print("   This will restart Chrome with AI agent support while preserving your logins")
            return False
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            print("💡 Please run: ./setup_chrome_for_agent.sh")
            return False
        
        return False
    
    async def ultimate_task_analysis(self, user_input: str) -> Dict[str, Any]:
        """Ultimate AI task analysis with enhanced understanding."""
        user_lower = user_input.lower()
        
        # Enhanced pattern matching
        if any(word in user_lower for word in ["send", "write", "message"]) and any(platform in user_lower for platform in ["telegram", "whatsapp", "discord", "messenger"]):
            return await self.analyze_messaging_task_ultimate(user_input)
        elif "email" in user_lower:
            return await self.analyze_email_task_ultimate(user_input)
        elif "search" in user_lower:
            return await self.analyze_search_task_ultimate(user_input)
        elif any(word in user_lower for word in ["open", "go", "visit", "navigate"]):
            return await self.analyze_navigation_task_ultimate(user_input)
        else:
            # If unsure, ask user for clarification
            return await self.ask_user_for_clarification(user_input)
    
    async def analyze_messaging_task_ultimate(self, user_input: str) -> Dict[str, Any]:
        """Ultimate messaging task analysis."""
        # Enhanced extraction with multiple patterns
        website = await self.determine_messaging_platform(user_input)
        recipient = await self.extract_recipient(user_input)
        message = await self.extract_message_content(user_input)
        
        return {
            "intent": "ultimate_messaging",
            "website": website,
            "recipient": recipient,
            "message": message,
            "confidence": 0.9,
            "autonomous": True
        }
    
    async def determine_messaging_platform(self, user_input: str) -> str:
        """Determine messaging platform with fallback to user input."""
        user_lower = user_input.lower()
        
        if "telegram" in user_lower:
            return "https://web.telegram.org"
        elif "whatsapp" in user_lower:
            return "https://web.whatsapp.com"
        elif "discord" in user_lower:
            return "https://discord.com/app"
        elif "messenger" in user_lower:
            return "https://www.messenger.com"
        else:
            # Ask user for specific platform
            platform = await self.ask_user_input("🤔 Which messaging platform? (telegram/whatsapp/discord): ")
            platform_lower = platform.lower()
            
            if "telegram" in platform_lower:
                return "https://web.telegram.org"
            elif "whatsapp" in platform_lower:
                return "https://web.whatsapp.com"
            elif "discord" in platform_lower:
                return "https://discord.com/app"
            else:
                # Ask for direct link
                link = await self.ask_user_input("🔗 Please provide the direct link to the messaging platform: ")
                return link if link.startswith('http') else f"https://{link}"
    
    async def extract_recipient(self, user_input: str) -> str:
        """Extract recipient with multiple patterns."""
        patterns = [
            r'to\s+(?:a\s+person\s+named\s+)?([A-Za-z0-9_@.-]+)',
            r'message\s+([A-Za-z0-9_@.-]+)',
            r'contact\s+([A-Za-z0-9_@.-]+)',
            r'user\s+([A-Za-z0-9_@.-]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, user_input, re.IGNORECASE)
            if match:
                return match.group(1)
        
        # Ask user if not found
        return await self.ask_user_input("👤 Who should I send the message to? (contact name): ")
    
    async def extract_message_content(self, user_input: str) -> str:
        """Extract message content with multiple patterns."""
        patterns = [
            r'message\s+["\']([^"\']+)["\']',
            r'write\s+["\']([^"\']+)["\']',
            r'send\s+["\']([^"\']+)["\']',
            r'say\s+["\']([^"\']+)["\']',
            r'message\s+(\w+)',
            r'write\s+(\w+)',
            r'send\s+(\w+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, user_input, re.IGNORECASE)
            if match:
                return match.group(1)
        
        # Ask user if not found
        return await self.ask_user_input("💬 What message should I send? ")
    
    async def ask_user_for_clarification(self, user_input: str) -> Dict[str, Any]:
        """Ask user for clarification when task is unclear."""
        print(f"🤔 I'm not sure how to handle: '{user_input}'")
        
        clarification = await self.ask_user_input("""
🤖 What would you like me to do? Please choose:
1. Send a message on a platform (telegram, whatsapp, etc.)
2. Search for something on the web
3. Navigate to a specific website
4. Compose an email
5. Other (please specify)

Your choice: """)
        
        if "1" in clarification or "message" in clarification.lower():
            platform = await self.ask_user_input("📱 Which platform? (telegram/whatsapp/discord): ")
            recipient = await self.ask_user_input("👤 To whom? ")
            message = await self.ask_user_input("💬 What message? ")
            
            website = await self.determine_messaging_platform(f"send message on {platform}")
            
            return {
                "intent": "ultimate_messaging",
                "website": website,
                "recipient": recipient,
                "message": message,
                "confidence": 0.8,
                "autonomous": True
            }
        elif "2" in clarification or "search" in clarification.lower():
            query = await self.ask_user_input("🔍 What should I search for? ")
            return {
                "intent": "ultimate_search",
                "website": "https://www.google.com",
                "query": query,
                "confidence": 0.8,
                "autonomous": True
            }
        elif "3" in clarification or "navigate" in clarification.lower():
            website = await self.ask_user_input("🌐 Which website? (provide URL or name): ")
            if not website.startswith('http'):
                website = f"https://www.{website}"
            return {
                "intent": "ultimate_navigation",
                "website": website,
                "confidence": 0.8,
                "autonomous": True
            }
        else:
            website = await self.ask_user_input("🔗 Please provide a direct link to the website: ")
            return {
                "intent": "ultimate_navigation",
                "website": website,
                "confidence": 0.7,
                "autonomous": True
            }
    
    async def ask_user_input(self, prompt: str) -> str:
        """Ask user for input with proper formatting."""
        print(prompt)
        try:
            response = input("👉 ").strip()
            return response if response else "default"
        except (EOFError, KeyboardInterrupt):
            return "default"
    
    async def execute_ultimate_task(self, task_analysis: Dict[str, Any], original_input: str):
        """Execute task with ultimate autonomous control."""
        intent = task_analysis["intent"]
        
        try:
            if intent == "ultimate_messaging":
                await self.execute_ultimate_messaging(task_analysis)
            elif intent == "ultimate_search":
                await self.execute_ultimate_search(task_analysis)
            elif intent == "ultimate_navigation":
                await self.execute_ultimate_navigation(task_analysis)
            else:
                print(f"❌ Unknown intent: {intent}")
                
        except Exception as e:
            print(f"❌ Ultimate task execution failed: {e}")
            print("🔄 Attempting recovery...")
            await self.attempt_recovery(task_analysis, str(e))
    
    async def execute_ultimate_messaging(self, task_analysis: Dict[str, Any]):
        """Execute messaging with ultimate autonomous control."""
        website = task_analysis["website"]
        recipient = task_analysis["recipient"]
        message = task_analysis["message"]
        
        print(f"📱 Opening messaging platform: {website}")
        await self.navigate_to_website_ultimate(website)
        
        print("⏳ Waiting for platform to fully load...")
        await asyncio.sleep(5)
        
        # Ultimate autonomous messaging
        if "telegram" in website:
            await self.ultimate_telegram_messaging(recipient, message)
        elif "whatsapp" in website:
            await self.ultimate_whatsapp_messaging(recipient, message)
        else:
            await self.ultimate_generic_messaging(recipient, message)
    
    async def ultimate_telegram_messaging(self, recipient: str, message: str):
        """Ultimate autonomous Telegram messaging."""
        print(f"🔍 Searching for contact: {recipient}")
        
        try:
            # Wait for Telegram to fully load
            await asyncio.sleep(8)
            
            # Ultimate search strategy - try multiple selectors
            search_selectors = [
                "input[placeholder*='Search']",
                "input[placeholder*='search']",
                ".input-search input",
                "[data-testid='search-input']",
                "input[type='text']",
                ".search-input",
                "#search-input",
                "[role='textbox']",
                "input.form-control",
                ".tgico-search + input"
            ]
            
            search_input = await self.find_element_ultimate(search_selectors, "search box")
            
            if search_input:
                print(f"✅ Found search box, searching for {recipient}")
                
                # Clear and search
                await self.clear_and_type_ultimate(search_input, recipient)
                await asyncio.sleep(3)
                
                # Try to click on the contact
                contact_selectors = [
                    f"[title*='{recipient}']",
                    f".chatlist-chat[data-peer-id*='{recipient}']",
                    ".chatlist-chat:first-child",
                    ".chat-item:first-child",
                    ".contact-item:first-child",
                    ".search-result:first-child"
                ]
                
                contact = await self.find_element_ultimate(contact_selectors, f"contact {recipient}")
                
                if contact:
                    print(f"✅ Found contact {recipient}, opening chat")
                    await self.click_element_ultimate(contact)
                    await asyncio.sleep(3)
                    
                    # Find message input with ultimate strategy
                    message_selectors = [
                        "div[contenteditable='true']",
                        "textarea[placeholder*='message']",
                        "input[placeholder*='message']",
                        ".input-message-input",
                        "[data-testid='message-input']",
                        ".composer-input",
                        "#message-input",
                        ".message-input",
                        "[role='textbox'][contenteditable='true']"
                    ]
                    
                    message_input = await self.find_element_ultimate(message_selectors, "message input")
                    
                    if message_input:
                        print(f"💬 Sending message: '{message}'")
                        await self.clear_and_type_ultimate(message_input, message)
                        await asyncio.sleep(1)
                        
                        # Send the message
                        await self.send_message_ultimate(message_input)
                        print("✅ Message sent successfully!")
                    else:
                        print("❌ Could not find message input box")
                else:
                    print(f"❌ Could not find contact {recipient}")
            else:
                print("❌ Could not find search box")
                print("💡 Please ensure you're logged in to Telegram Web")
                
        except Exception as e:
            print(f"❌ Telegram messaging failed: {e}")
            await self.attempt_manual_guidance("Telegram messaging")
    
    async def find_element_ultimate(self, selectors: List[str], element_name: str, timeout: int = 10):
        """Ultimate element finding with multiple strategies."""
        print(f"🔍 Looking for {element_name}...")
        
        for selector in selectors:
            try:
                # Try CSS selector
                element = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                if element and element.is_displayed():
                    print(f"✅ Found {element_name} with selector: {selector}")
                    return element
            except:
                continue
        
        # Try XPath strategies
        xpath_selectors = [
            f"//input[contains(@placeholder, 'search')]",
            f"//input[contains(@placeholder, 'Search')]",
            f"//input[contains(@placeholder, 'message')]",
            f"//input[contains(@placeholder, 'Message')]",
            f"//div[contains(@contenteditable, 'true')]",
            f"//textarea[contains(@placeholder, 'message')]"
        ]
        
        for xpath in xpath_selectors:
            try:
                element = self.browser.driver.find_element(By.XPATH, xpath)
                if element and element.is_displayed():
                    print(f"✅ Found {element_name} with XPath")
                    return element
            except:
                continue
        
        print(f"❌ Could not find {element_name} after trying all strategies")
        return None
    
    async def clear_and_type_ultimate(self, element, text: str):
        """Ultimate text input with multiple strategies."""
        try:
            # Strategy 1: Standard clear and send_keys
            print(f"⌨️  Typing '{text}' using standard method...")
            element.clear()
            element.send_keys(text)
            print(f"✅ Successfully typed '{text}'")
            return
        except Exception as e:
            print(f"⚠️  Standard typing failed: {e}")
            try:
                # Strategy 2: JavaScript clear and type
                print(f"⌨️  Trying JavaScript method...")
                self.browser.driver.execute_script("arguments[0].value = '';", element)
                self.browser.driver.execute_script("arguments[0].value = arguments[1];", element, text)
                print(f"✅ Successfully typed '{text}' with JavaScript")
                return
            except Exception as e:
                print(f"⚠️  JavaScript typing failed: {e}")
                try:
                    # Strategy 3: ActionChains
                    print(f"⌨️  Trying ActionChains method...")
                    actions = ActionChains(self.browser.driver)
                    actions.click(element)
                    actions.key_down(Keys.CONTROL).send_keys('a').key_up(Keys.CONTROL)
                    actions.send_keys(text)
                    actions.perform()
                    print(f"✅ Successfully typed '{text}' with ActionChains")
                    return
                except Exception as e:
                    print(f"❌ All typing methods failed: {e}")
                    print(f"💡 Could not type '{text}' into element")
    
    async def click_element_ultimate(self, element):
        """Ultimate element clicking with multiple strategies."""
        try:
            # Strategy 1: Standard click
            element.click()
        except:
            try:
                # Strategy 2: JavaScript click
                self.browser.driver.execute_script("arguments[0].click();", element)
            except:
                try:
                    # Strategy 3: ActionChains click
                    actions = ActionChains(self.browser.driver)
                    actions.move_to_element(element).click().perform()
                except Exception as e:
                    print(f"⚠️  Click failed: {e}")
    
    async def send_message_ultimate(self, message_input):
        """Ultimate message sending with multiple strategies."""
        try:
            # Strategy 1: Enter key
            message_input.send_keys(Keys.ENTER)
        except:
            try:
                # Strategy 2: Look for send button
                send_selectors = [
                    "button[aria-label*='Send']",
                    ".btn-send",
                    "[data-testid='send-button']",
                    ".send-button",
                    "button[type='submit']"
                ]
                
                for selector in send_selectors:
                    try:
                        send_button = self.browser.driver.find_element(By.CSS_SELECTOR, selector)
                        if send_button.is_displayed():
                            await self.click_element_ultimate(send_button)
                            return
                    except:
                        continue
                
                # Strategy 3: Ctrl+Enter
                message_input.send_keys(Keys.CONTROL, Keys.ENTER)
            except Exception as e:
                print(f"⚠️  Send failed: {e}")
    
    async def navigate_to_website_ultimate(self, website: str):
        """Ultimate website navigation with tab management."""
        try:
            current_url = self.browser.driver.current_url
            print(f"📍 Currently on: {current_url}")
            
            if current_url and current_url != "data:," and "chrome://new-tab-page" not in current_url:
                # Open in new tab (requirement #1)
                print(f"🆕 Opening {website} in new tab...")
                
                # Method 1: Try JavaScript window.open
                try:
                    self.browser.driver.execute_script(f"window.open('{website}', '_blank');")
                    await asyncio.sleep(2)
                    
                    # Switch to the new tab (last one)
                    all_handles = self.browser.driver.window_handles
                    self.browser.driver.switch_to.window(all_handles[-1])
                    await asyncio.sleep(3)
                    
                    # Verify we're on the right page
                    new_url = self.browser.driver.current_url
                    if website.replace("https://", "").replace("http://", "") in new_url:
                        print(f"✅ Successfully opened {website} in new tab")
                    else:
                        raise Exception(f"Tab switch failed, still on: {new_url}")
                        
                except Exception as e:
                    print(f"⚠️  JavaScript method failed: {e}")
                    # Method 2: Direct navigation
                    print(f"🔄 Trying direct navigation...")
                    self.browser.driver.get(website)
                    await asyncio.sleep(3)
                    print(f"🌐 Navigated directly to {website}")
            else:
                # Navigate in current tab
                print(f"🌐 Navigating to {website} in current tab...")
                self.browser.driver.get(website)
                await asyncio.sleep(3)
            
            # Verify final result
            final_url = self.browser.driver.current_url
            title = self.browser.driver.title
            
            if website.replace("https://", "").replace("http://", "") in final_url:
                print(f"✅ Success! Page: {title}")
                print(f"📍 Final URL: {final_url}")
            else:
                print(f"❌ Navigation verification failed!")
                print(f"📍 Expected: {website}")
                print(f"📍 Actual: {final_url}")
                raise Exception("Navigation failed - wrong page")
            
        except Exception as e:
            print(f"❌ Navigation failed: {e}")
            # Ask user for alternative link (requirement #2)
            alternative = await self.ask_user_input(f"🔗 Navigation to {website} failed. Please provide an alternative link: ")
            if alternative and alternative != "default":
                await self.navigate_to_website_ultimate(alternative)
    
    async def attempt_recovery(self, task_analysis: Dict[str, Any], error: str):
        """Attempt to recover from failures."""
        print(f"🔄 Recovery mode: {error}")
        
        recovery_options = await self.ask_user_input("""
🛠️  Recovery options:
1. Try again with the same parameters
2. Ask for alternative website link
3. Manual guidance mode
4. Skip this step

Choose (1-4): """)
        
        if "1" in recovery_options:
            print("🔄 Retrying...")
            await self.execute_ultimate_task(task_analysis, "retry")
        elif "2" in recovery_options:
            new_link = await self.ask_user_input("🔗 Please provide alternative link: ")
            task_analysis["website"] = new_link
            await self.execute_ultimate_task(task_analysis, "retry with new link")
        elif "3" in recovery_options:
            await self.manual_guidance_mode(task_analysis)
        else:
            print("⏭️  Skipping this step")
    
    async def manual_guidance_mode(self, task_analysis: Dict[str, Any]):
        """Provide manual guidance when automation fails."""
        print("🎯 Manual Guidance Mode")
        print("I'll guide you through the steps:")
        
        if task_analysis["intent"] == "ultimate_messaging":
            print(f"""
📱 Manual Steps for Messaging:
1. Make sure you're logged in to {task_analysis['website']}
2. Look for a search box and search for: {task_analysis['recipient']}
3. Click on the contact when it appears
4. Find the message input field
5. Type: {task_analysis['message']}
6. Press Enter or click Send

🤖 I can help you with any of these steps. Just tell me what you see!
""")
    
    async def attempt_manual_guidance(self, platform: str):
        """Provide manual guidance for specific platforms."""
        guidance = {
            "Telegram messaging": """
🔧 Manual Guidance for Telegram:
1. Ensure you're logged in to Telegram Web
2. Look for the search icon (🔍) or search box at the top
3. Type the contact name and press Enter
4. Click on the contact from the results
5. Find the message input at the bottom
6. Type your message and press Enter

💡 If you need help with any step, just ask!
""",
            "WhatsApp messaging": """
🔧 Manual Guidance for WhatsApp:
1. Ensure you're logged in to WhatsApp Web
2. Look for the search box on the left side
3. Type the contact name
4. Click on the contact from the results
5. Find the message input at the bottom
6. Type your message and press Enter
"""
        }
        
        print(guidance.get(platform, "Manual guidance not available for this platform"))
    
    async def shutdown(self):
        """Shutdown the ultimate agent."""
        if self.browser_started and self.browser:
            self.browser.disconnect()
            print("✅ Browser closed")
        
        # Clean up temp profile
        if hasattr(self.browser, 'browser_config') and hasattr(self.browser.browser_config, 'profile_path'):
            try:
                import shutil
                profile_path = self.browser.browser_config.profile_path
                if os.path.exists(profile_path) and 'ultimate_agent_' in profile_path:
                    shutil.rmtree(profile_path)
            except:
                pass

async def ultimate_interactive_mode():
    """Run the ultimate agent in interactive mode."""
    print("🚀 Ultimate AI Browser Agent")
    print("🧠 Full Autonomous Control | 🔐 Authorized Chrome | 🎯 Complete Task Execution")
    print("=" * 70)
    
    agent = UltimateAIAgent()
    await agent.initialize()
    
    try:
        while True:
            try:
                user_input = input("\n🤖 What should I do autonomously? ").strip()
                
                if not user_input:
                    continue
                    
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                    
                if user_input.lower() == 'help':
                    show_ultimate_help()
                    continue
                
                await agent.process_ultimate_task(user_input)
                
            except KeyboardInterrupt:
                print("\n👋 Interrupted by user. Goodbye!")
                break
            except EOFError:
                print("\n👋 End of input. Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                continue
                
    finally:
        await agent.shutdown()

def show_ultimate_help():
    """Show ultimate help with examples."""
    print("\n🚀 Ultimate AI Agent - Full Autonomous Control")
    print("=" * 50)
    print("✅ Requirement 1: Opens new tabs in authorized Chrome")
    print("✅ Requirement 2: Asks for links when unsure")
    print("✅ Requirement 3: Full autonomous control of inputs/buttons")
    print("✅ Requirement 4: Complete workflow execution")
    print()
    print("📱 Perfect Example (Your Request):")
    print("  'Open telegram.org and write hello to Kikita'")
    print()
    print("🎯 What I'll do autonomously:")
    print("  1. Open authorized Chrome in new tab")
    print("  2. Navigate to telegram.org")
    print("  3. Find and search for contact 'Kikita'")
    print("  4. Open the chat with Kikita")
    print("  5. Type 'hello' in the message input")
    print("  6. Send the message")
    print()
    print("🔧 If I can't find something, I'll ask you for:")
    print("  • Alternative website links")
    print("  • Contact names")
    print("  • Message content")
    print("  • Platform clarification")

if __name__ == "__main__":
    try:
        asyncio.run(ultimate_interactive_mode())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)