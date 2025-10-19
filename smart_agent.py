#!/usr/bin/env python3
"""Smart AI Browser Agent - Full Browser Control with AI Decision Making"""

import asyncio
import sys
import os
import tempfile
import json
import time
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

class SmartAIAgent:
    """Advanced AI agent with full browser control and decision-making capabilities."""
    
    def __init__(self):
        self.browser = None
        self.planner = None
        self.browser_started = False
        self.current_task_context = {}
        
    async def initialize(self):
        """Initialize the smart agent."""
        print("🧠 Initializing Smart AI Agent...")
        
        # Configure browser
        browser_config = BrowserConfig()
        temp_profile = tempfile.mkdtemp(prefix="smart_agent_")
        browser_config.profile_path = temp_profile
        browser_config.disable_automation_flags = True
        
        self.browser = BrowserController(browser_config)
        self.planner = TaskPlanner({}, MockModel())
        self.planner.initialize()
        
        print("✅ Smart AI Agent ready!")
    
    async def process_complex_task(self, user_input: str):
        """Process complex tasks with AI decision making."""
        print(f"\n🎯 Task: {user_input}")
        print("🧠 Analyzing task and planning actions...")
        
        # Start browser if needed
        if not self.browser_started:
            print("🔄 Starting browser...")
            self.browser.connect()
            self.browser_started = True
            print("✅ Browser ready!")
        
        # Parse the task to understand intent
        task_analysis = await self.analyze_task(user_input)
        print(f"📋 Task Analysis: {task_analysis['intent']}")
        
        # Execute the planned actions
        await self.execute_task_plan(task_analysis)
    
    async def analyze_task(self, user_input: str) -> Dict[str, Any]:
        """Analyze user input to understand intent and extract parameters."""
        user_lower = user_input.lower()
        
        # Complex task patterns
        if "send" in user_lower and "message" in user_lower:
            return await self.analyze_messaging_task(user_input)
        elif "write" in user_lower and "email" in user_lower:
            return await self.analyze_email_task(user_input)
        elif "search" in user_lower:
            return await self.analyze_search_task(user_input)
        elif "login" in user_lower or "sign in" in user_lower:
            return await self.analyze_login_task(user_input)
        else:
            return await self.analyze_navigation_task(user_input)
    
    async def analyze_messaging_task(self, user_input: str) -> Dict[str, Any]:
        """Analyze messaging tasks like sending messages on Telegram, WhatsApp, etc."""
        import re
        
        # Extract website/platform
        website = None
        user_lower = user_input.lower()
        if "telegram" in user_lower:
            website = "https://web.telegram.org"
        elif "whatsapp" in user_lower or "whats app" in user_lower:
            website = "https://web.whatsapp.com"
        elif "discord" in user_lower:
            website = "https://discord.com/app"
        elif "messenger" in user_lower or "facebook messenger" in user_lower:
            website = "https://www.messenger.com"
        
        # Extract recipient name
        recipient_match = re.search(r'to\s+(?:a\s+person\s+named\s+)?([A-Za-z0-9_]+)', user_input, re.IGNORECASE)
        recipient = recipient_match.group(1) if recipient_match else None
        
        # Extract message content
        message_match = re.search(r'message\s+(?:like\s+)?["\']([^"\']+)["\']', user_input, re.IGNORECASE)
        if not message_match:
            message_match = re.search(r'message\s+(?:like\s+)?(\w+)', user_input, re.IGNORECASE)
        message = message_match.group(1) if message_match else "Hello"
        
        return {
            "intent": "send_message",
            "website": website,
            "recipient": recipient,
            "message": message,
            "steps": [
                {"action": "navigate", "target": website},
                {"action": "wait_for_load", "target": "page"},
                {"action": "find_contact", "target": recipient},
                {"action": "send_message", "target": message}
            ]
        }
    
    async def analyze_email_task(self, user_input: str) -> Dict[str, Any]:
        """Analyze email tasks."""
        import re
        
        # Extract email service
        website = "https://mail.google.com"  # Default to Gmail
        if "outlook" in user_input.lower():
            website = "https://outlook.live.com"
        elif "yahoo" in user_input.lower():
            website = "https://mail.yahoo.com"
        
        # Extract recipient
        recipient_match = re.search(r'to\s+([A-Za-z0-9@._-]+)', user_input, re.IGNORECASE)
        recipient = recipient_match.group(1) if recipient_match else None
        
        # Extract subject
        subject_match = re.search(r'subject\s+["\']([^"\']+)["\']', user_input, re.IGNORECASE)
        subject = subject_match.group(1) if subject_match else "Hello"
        
        return {
            "intent": "send_email",
            "website": website,
            "recipient": recipient,
            "subject": subject,
            "steps": [
                {"action": "navigate", "target": website},
                {"action": "compose_email", "recipient": recipient, "subject": subject}
            ]
        }
    
    async def analyze_search_task(self, user_input: str) -> Dict[str, Any]:
        """Analyze search tasks."""
        import re
        
        # Extract search query
        search_match = re.search(r'search\s+(?:for\s+)?["\']([^"\']+)["\']', user_input, re.IGNORECASE)
        if not search_match:
            search_match = re.search(r'search\s+(?:for\s+)?(.+)', user_input, re.IGNORECASE)
        
        query = search_match.group(1) if search_match else user_input
        
        # Determine search engine
        website = "https://www.google.com"
        if "bing" in user_input.lower():
            website = "https://www.bing.com"
        elif "duckduckgo" in user_input.lower():
            website = "https://duckduckgo.com"
        
        return {
            "intent": "search",
            "website": website,
            "query": query.strip(),
            "steps": [
                {"action": "navigate", "target": website},
                {"action": "search", "target": query.strip()}
            ]
        }
    
    async def analyze_navigation_task(self, user_input: str) -> Dict[str, Any]:
        """Analyze simple navigation tasks."""
        # Use existing task planner for navigation
        steps = self.planner._parse_with_patterns(user_input)
        website = None
        
        if steps:
            for step in steps:
                if step.action_type == "navigate":
                    website = step.parameters.get('target')
                    break
        
        return {
            "intent": "navigate",
            "website": website,
            "steps": [{"action": "navigate", "target": website}]
        }
    
    async def analyze_login_task(self, user_input: str) -> Dict[str, Any]:
        """Analyze login tasks."""
        import re
        
        # Extract website
        website_match = re.search(r'(?:login\s+to|sign\s+in\s+to)\s+([A-Za-z0-9.-]+)', user_input, re.IGNORECASE)
        website = website_match.group(1) if website_match else None
        
        if website and not website.startswith('http'):
            website = f"https://www.{website}"
        
        return {
            "intent": "login",
            "website": website,
            "steps": [
                {"action": "navigate", "target": website},
                {"action": "find_login", "target": "login_form"}
            ]
        }
    
    async def execute_task_plan(self, task_analysis: Dict[str, Any]):
        """Execute the planned task steps."""
        intent = task_analysis["intent"]
        
        try:
            if intent == "send_message":
                await self.execute_messaging_task(task_analysis)
            elif intent == "send_email":
                await self.execute_email_task(task_analysis)
            elif intent == "search":
                await self.execute_search_task(task_analysis)
            elif intent == "navigate":
                await self.execute_navigation_task(task_analysis)
            elif intent == "login":
                await self.execute_login_task(task_analysis)
            else:
                print(f"❌ Unknown intent: {intent}")
                
        except Exception as e:
            print(f"❌ Task execution failed: {e}")
    
    async def execute_messaging_task(self, task_analysis: Dict[str, Any]):
        """Execute messaging tasks like Telegram, WhatsApp."""
        website = task_analysis["website"]
        recipient = task_analysis["recipient"]
        message = task_analysis["message"]
        
        print(f"📱 Opening {website}...")
        await self.navigate_to_website(website)
        
        print("⏳ Waiting for messaging platform to load...")
        await asyncio.sleep(3)
        
        if "telegram" in website:
            await self.handle_telegram_messaging(recipient, message)
        elif "whatsapp" in website:
            await self.handle_whatsapp_messaging(recipient, message)
        else:
            print("❌ Messaging platform not supported yet")
    
    async def handle_telegram_messaging(self, recipient: str, message: str):
        """Handle Telegram Web messaging."""
        try:
            print(f"🔍 Looking for contact: {recipient}")
            
            # Wait for Telegram to load and look for search box
            await asyncio.sleep(5)
            
            # Try to find search input
            search_selectors = [
                "input[placeholder*='Search']",
                "input[placeholder*='search']",
                ".input-search input",
                "[data-testid='search-input']",
                "input[type='text']"
            ]
            
            search_input = None
            for selector in search_selectors:
                try:
                    search_input = self.browser.driver.find_element(By.CSS_SELECTOR, selector)
                    if search_input.is_displayed():
                        break
                except:
                    continue
            
            if search_input:
                print(f"✅ Found search box, searching for {recipient}")
                search_input.clear()
                search_input.send_keys(recipient)
                await asyncio.sleep(2)
                search_input.send_keys(Keys.ENTER)
                await asyncio.sleep(2)
                
                # Look for message input
                message_selectors = [
                    "div[contenteditable='true']",
                    "textarea[placeholder*='message']",
                    "input[placeholder*='message']",
                    ".input-message-input",
                    "[data-testid='message-input']"
                ]
                
                message_input = None
                for selector in message_selectors:
                    try:
                        message_input = self.browser.driver.find_element(By.CSS_SELECTOR, selector)
                        if message_input.is_displayed():
                            break
                    except:
                        continue
                
                if message_input:
                    print(f"💬 Sending message: '{message}'")
                    message_input.clear()
                    message_input.send_keys(message)
                    await asyncio.sleep(1)
                    message_input.send_keys(Keys.ENTER)
                    print("✅ Message sent successfully!")
                else:
                    print("❌ Could not find message input box")
            else:
                print("❌ Could not find search box. You may need to log in first.")
                print("💡 Please log in to Telegram Web manually, then try again.")
                
        except Exception as e:
            print(f"❌ Telegram messaging failed: {e}")
            print("💡 Make sure you're logged in to Telegram Web")
    
    async def handle_whatsapp_messaging(self, recipient: str, message: str):
        """Handle WhatsApp Web messaging."""
        try:
            print(f"🔍 Looking for contact: {recipient}")
            await asyncio.sleep(5)
            
            # Look for search box
            search_selectors = [
                "div[contenteditable='true'][data-tab='3']",
                "input[placeholder*='Search']",
                ".input-chatlist-search input"
            ]
            
            search_input = None
            for selector in search_selectors:
                try:
                    search_input = self.browser.driver.find_element(By.CSS_SELECTOR, selector)
                    if search_input.is_displayed():
                        break
                except:
                    continue
            
            if search_input:
                print(f"✅ Found search box, searching for {recipient}")
                search_input.clear()
                search_input.send_keys(recipient)
                await asyncio.sleep(2)
                
                # Click on first result
                try:
                    first_result = self.browser.driver.find_element(By.CSS_SELECTOR, "[data-testid='cell-frame-container']")
                    first_result.click()
                    await asyncio.sleep(2)
                except:
                    pass
                
                # Look for message input
                message_selectors = [
                    "div[contenteditable='true'][data-tab='10']",
                    "div[contenteditable='true'][role='textbox']",
                    ".input-message input"
                ]
                
                message_input = None
                for selector in message_selectors:
                    try:
                        message_input = self.browser.driver.find_element(By.CSS_SELECTOR, selector)
                        if message_input.is_displayed():
                            break
                    except:
                        continue
                
                if message_input:
                    print(f"💬 Sending message: '{message}'")
                    message_input.clear()
                    message_input.send_keys(message)
                    await asyncio.sleep(1)
                    message_input.send_keys(Keys.ENTER)
                    print("✅ Message sent successfully!")
                else:
                    print("❌ Could not find message input box")
            else:
                print("❌ Could not find search box. You may need to log in first.")
                
        except Exception as e:
            print(f"❌ WhatsApp messaging failed: {e}")
    
    async def execute_search_task(self, task_analysis: Dict[str, Any]):
        """Execute search tasks."""
        website = task_analysis["website"]
        query = task_analysis["query"]
        
        print(f"🔍 Searching for: '{query}' on {website}")
        await self.navigate_to_website(website)
        
        await asyncio.sleep(2)
        
        # Find search box
        search_selectors = [
            "input[name='q']",
            "input[title='Search']",
            "textarea[name='q']",
            "input[type='search']",
            "input[placeholder*='Search']",
            "input[placeholder*='search']",
            "#search-box",
            ".search-input",
            "[role='combobox']"
        ]
        
        search_input = None
        for selector in search_selectors:
            try:
                search_input = self.browser.driver.find_element(By.CSS_SELECTOR, selector)
                if search_input.is_displayed():
                    break
            except:
                continue
        
        if search_input:
            print(f"✅ Found search box, searching for: {query}")
            search_input.clear()
            search_input.send_keys(query)
            search_input.send_keys(Keys.ENTER)
            await asyncio.sleep(2)
            print("✅ Search completed!")
        else:
            print("❌ Could not find search box")
    
    async def execute_navigation_task(self, task_analysis: Dict[str, Any]):
        """Execute simple navigation tasks."""
        website = task_analysis["website"]
        if website:
            await self.navigate_to_website(website)
        else:
            print("❌ No website specified")
    
    async def execute_email_task(self, task_analysis: Dict[str, Any]):
        """Execute email tasks."""
        website = task_analysis["website"]
        recipient = task_analysis.get("recipient")
        subject = task_analysis.get("subject")
        
        print(f"📧 Opening email service: {website}")
        await self.navigate_to_website(website)
        
        await asyncio.sleep(3)
        
        # Look for compose button
        compose_selectors = [
            "div[role='button'][aria-label*='Compose']",
            "button[aria-label*='Compose']",
            ".compose-button",
            "[data-testid='compose']"
        ]
        
        compose_button = None
        for selector in compose_selectors:
            try:
                compose_button = self.browser.driver.find_element(By.CSS_SELECTOR, selector)
                if compose_button.is_displayed():
                    break
            except:
                continue
        
        if compose_button:
            print("✅ Found compose button, opening new email")
            compose_button.click()
            await asyncio.sleep(2)
            print("💡 Email compose window opened. You can now compose your email manually.")
        else:
            print("❌ Could not find compose button. You may need to log in first.")
    
    async def execute_login_task(self, task_analysis: Dict[str, Any]):
        """Execute login tasks."""
        website = task_analysis["website"]
        
        print(f"🔐 Opening login page: {website}")
        await self.navigate_to_website(website)
        
        await asyncio.sleep(2)
        print("💡 Please log in manually. The agent will wait for you to complete the login process.")
    
    async def navigate_to_website(self, website: str):
        """Navigate to a website with smart tab management."""
        try:
            current_url = self.browser.get_current_url()
            if current_url and current_url != "data:,":
                # Open in new tab
                self.browser.driver.execute_script(f"window.open('{website}', '_blank');")
                self.browser.driver.switch_to.window(self.browser.driver.window_handles[-1])
                print(f"🆕 Opened {website} in new tab")
            else:
                # Navigate in current tab
                self.browser.navigate_to(website)
                print(f"🌐 Navigated to {website}")
            
            await asyncio.sleep(2)
            current_url = self.browser.get_current_url()
            title = self.browser.get_page_title()
            print(f"✅ Success! Current page: {title}")
            
        except Exception as e:
            print(f"❌ Navigation failed: {e}")
    
    async def shutdown(self):
        """Shutdown the agent."""
        if self.browser_started and self.browser:
            self.browser.disconnect()
            print("✅ Browser closed")
        
        # Clean up temp profile
        if hasattr(self.browser, 'browser_config') and hasattr(self.browser.browser_config, 'profile_path'):
            try:
                import shutil
                profile_path = self.browser.browser_config.profile_path
                if os.path.exists(profile_path) and 'smart_agent_' in profile_path:
                    shutil.rmtree(profile_path)
            except:
                pass

async def interactive_mode():
    """Run the smart agent in interactive mode."""
    print("🧠 Smart AI Browser Agent - Advanced Mode")
    print("I can navigate websites, send messages, write emails, search, and more!")
    print("Type 'help' for examples or 'quit' to exit")
    print("=" * 60)
    
    agent = SmartAIAgent()
    await agent.initialize()
    
    try:
        while True:
            try:
                user_input = input("\n🤖 What would you like me to do? ").strip()
                
                if not user_input:
                    continue
                    
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                    
                if user_input.lower() == 'help':
                    show_help()
                    continue
                
                await agent.process_complex_task(user_input)
                
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

def show_help():
    """Show help with examples."""
    print("\n🧠 Smart AI Agent - Examples")
    print("=" * 40)
    print("📱 Messaging:")
    print("  • Send a message 'Hello' to Kikita on Telegram")
    print("  • Send 'How are you?' to John on WhatsApp")
    print()
    print("📧 Email:")
    print("  • Write an email to john@example.com with subject 'Meeting'")
    print("  • Compose email on Gmail")
    print()
    print("🔍 Search:")
    print("  • Search for 'Python tutorials' on Google")
    print("  • Search 'AI news' on Bing")
    print()
    print("🌐 Navigation:")
    print("  • Open GitHub")
    print("  • Go to YouTube")
    print("  • Visit stackoverflow.com")
    print()
    print("🔐 Login:")
    print("  • Login to Gmail")
    print("  • Sign in to Facebook")

if __name__ == "__main__":
    try:
        asyncio.run(interactive_mode())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)