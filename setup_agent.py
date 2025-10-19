#!/usr/bin/env python3
"""Setup Agent - One-Command AI Browser Agent"""

import sys
import asyncio
import time
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from chrome_manager import ChromeManager
from navigation_manager import NavigationManager


class SetupAgent:
    """Unified AI Browser Agent with reliable Chrome connection and navigation."""
    
    def __init__(self):
        self.chrome_manager = ChromeManager()
        self.navigation_manager = NavigationManager()
        self.connected = False
    
    def setup_and_connect(self) -> bool:
        """Setup Chrome and establish connection."""
        print("🚀 AI Browser Agent Setup")
        print("=" * 50)
        
        # Step 1: Ensure Chrome is ready
        if not self.chrome_manager.ensure_chrome_ready():
            print("❌ Chrome setup failed")
            return False
        
        # Step 2: Connect navigation manager
        if not self.navigation_manager.connect_to_chrome():
            print("❌ Navigation connection failed")
            return False
        
        self.connected = True
        print("✅ AI Browser Agent ready!")
        return True
    
    def execute_task(self, task: str) -> bool:
        """Execute a browser automation task."""
        if not self.connected:
            print("❌ Not connected. Run setup_and_connect() first.")
            return False
        
        print(f"\n🎯 Task: {task}")
        print("-" * 50)
        
        # Parse task and determine action
        task_lower = task.lower()
        
        if "telegram" in task_lower and ("write" in task_lower or "send" in task_lower or "message" in task_lower):
            return self._execute_telegram_task(task)
        elif "google" in task_lower and "search" in task_lower:
            return self._execute_google_search_task(task)
        elif "open" in task_lower or "go to" in task_lower or "visit" in task_lower:
            return self._execute_navigation_task(task)
        else:
            print("❌ Task type not recognized")
            print("💡 Supported tasks:")
            print("   - 'Open telegram.org and write hello to @username'")
            print("   - 'Go to google.com and search for something'")
            print("   - 'Open website.com'")
            return False
    
    def _execute_telegram_task(self, task: str) -> bool:
        """Execute Telegram messaging task."""
        print("📱 Executing Telegram task...")
        
        # Extract recipient and message
        recipient = self._extract_recipient(task)
        message = self._extract_message(task)
        
        if not recipient:
            print("❌ Could not extract recipient from task")
            return False
        
        if not message:
            print("❌ Could not extract message from task")
            return False
        
        print(f"👤 Recipient: {recipient}")
        print(f"💬 Message: {message}")
        
        # Step 1: Navigate to Telegram
        print("\n📱 Step 1: Opening Telegram Web...")
        if not self.navigation_manager.navigate_to_website("https://web.telegram.org"):
            print("❌ Failed to open Telegram Web")
            return False
        
        # Wait for Telegram to load
        time.sleep(5)
        
        # Step 2: Find and use search box
        print("\n🔍 Step 2: Searching for contact...")
        search_selectors = [
            "input[type='search']",
            "input[placeholder*='Search']",
            "input[placeholder*='search']",
            "input[type='text']"
        ]
        
        search_box = self.navigation_manager.find_element_reliable(
            search_selectors, "search box", timeout=10
        )
        
        if not search_box:
            print("❌ Could not find search box")
            print("💡 Make sure you're logged in to Telegram Web")
            return False
        
        # Type recipient name
        if not self.navigation_manager.type_text_reliable(search_box, recipient):
            print("❌ Could not type recipient name")
            return False
        
        # Wait for search results
        time.sleep(3)
        
        # Step 3: Click on contact
        print("\n👤 Step 3: Opening chat with contact...")
        contact_selectors = [
            f"//*[contains(text(), '{recipient}')]",
            f"//*[contains(text(), '{recipient.replace('@', '')}')]",
            ".ListItem",
            ".chat-item:first-child",
            ".contact-item:first-child"
        ]
        
        contact = self.navigation_manager.find_element_reliable(
            contact_selectors, f"contact {recipient}", timeout=10
        )
        
        if not contact:
            print(f"❌ Could not find contact {recipient}")
            return False
        
        if not self.navigation_manager.click_element_reliable(contact):
            print("❌ Could not click on contact")
            return False
        
        # Wait for chat to open
        time.sleep(3)
        
        # Step 4: Find message input and send message
        print("\n💬 Step 4: Sending message...")
        
        # Wait a bit more for chat to fully load
        time.sleep(5)
        
        message_selectors = [
            "[role='textbox'][contenteditable='true']",
            "div[contenteditable='true']",
            "[role='textbox']",
            "[placeholder*='Message']",
            "[placeholder*='message']",
            ".composer-input-wrapper",
            ".composer-input",
            "textarea",
            ".input-message-input",
            "[data-testid='message-input']"
        ]
        
        message_input = self.navigation_manager.find_element_reliable(
            message_selectors, "message input", timeout=10
        )
        
        if not message_input:
            print("❌ Could not find message input")
            return False
        
        if not self.navigation_manager.type_text_reliable(message_input, message):
            print("❌ Could not type message")
            return False
        
        # Send message (press Enter)
        try:
            from selenium.webdriver.common.keys import Keys
            message_input.send_keys(Keys.ENTER)
            print("✅ Message sent successfully!")
            return True
        except Exception as e:
            print(f"❌ Could not send message: {e}")
            return False
    
    def _execute_google_search_task(self, task: str) -> bool:
        """Execute Google search task."""
        print("🔍 Executing Google search task...")
        
        # Extract search query
        query = self._extract_search_query(task)
        if not query:
            print("❌ Could not extract search query")
            return False
        
        print(f"🔍 Search query: {query}")
        
        # Navigate to Google
        print("\n🌐 Step 1: Opening Google...")
        if not self.navigation_manager.navigate_to_website("https://www.google.com"):
            print("❌ Failed to open Google")
            return False
        
        # Find search box
        print("\n🔍 Step 2: Finding search box...")
        search_box = self.navigation_manager.find_element_reliable(
            [
                "input[name='q']", 
                "input[title='Search']",
                "textarea[name='q']",
                "input[type='search']", 
                "#search",
                ".gLFyf",  # Google's search input class
                "[role='combobox']",
                "input[aria-label*='Search']"
            ],
            "search box"
        )
        
        if not search_box:
            print("❌ Could not find search box")
            return False
        
        # Type search query
        if not self.navigation_manager.type_text_reliable(search_box, query):
            print("❌ Could not type search query")
            return False
        
        # Submit search
        try:
            from selenium.webdriver.common.keys import Keys
            search_box.send_keys(Keys.ENTER)
            print("✅ Search executed successfully!")
            
            # Wait for results
            time.sleep(3)
            info = self.navigation_manager.get_current_info()
            print(f"📊 Results page: {info.get('title', 'Unknown')}")
            return True
            
        except Exception as e:
            print(f"❌ Could not execute search: {e}")
            return False
    
    def _execute_navigation_task(self, task: str) -> bool:
        """Execute simple navigation task."""
        print("🌐 Executing navigation task...")
        
        # Extract URL
        url = self._extract_url(task)
        if not url:
            print("❌ Could not extract URL from task")
            return False
        
        print(f"🌐 URL: {url}")
        
        if not self.navigation_manager.navigate_to_website(url):
            print("❌ Navigation failed")
            return False
        
        info = self.navigation_manager.get_current_info()
        print(f"✅ Successfully opened: {info.get('title', 'Unknown')}")
        return True
    
    def _extract_recipient(self, task: str) -> str:
        """Extract recipient from task."""
        task_lower = task.lower()
        
        # Look for @username pattern
        import re
        at_match = re.search(r'@(\w+)', task)
        if at_match:
            return f"@{at_match.group(1)}"
        
        # Look for "to [name]" pattern
        to_match = re.search(r'to\s+([^\s]+)', task_lower)
        if to_match:
            return to_match.group(1)
        
        return ""
    
    def _extract_message(self, task: str) -> str:
        """Extract message from task."""
        # Look for common message patterns
        patterns = [
            r'write\s+([^"\']+?)(?:\s+to|\s*$)',
            r'send\s+([^"\']+?)(?:\s+to|\s*$)',
            r'message\s+([^"\']+?)(?:\s+to|\s*$)',
            r'"([^"]+)"',
            r"'([^']+)'"
        ]
        
        for pattern in patterns:
            import re
            match = re.search(pattern, task, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # Default message
        return "hello"
    
    def _extract_search_query(self, task: str) -> str:
        """Extract search query from task."""
        # Look for "search for [query]" pattern
        import re
        patterns = [
            r'search\s+for\s+([^"\']+?)(?:\s*$)',
            r'search\s+([^"\']+?)(?:\s*$)',
            r'"([^"]+)"',
            r"'([^']+)'"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, task, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return ""
    
    def _extract_url(self, task: str) -> str:
        """Extract URL from task."""
        import re
        
        # Look for explicit URLs
        url_match = re.search(r'https?://[^\s]+', task)
        if url_match:
            return url_match.group(0)
        
        # Handle common services without domain extensions
        common_services = {
            'gmail': 'https://gmail.com',
            'youtube': 'https://youtube.com',
            'facebook': 'https://facebook.com',
            'twitter': 'https://twitter.com',
            'instagram': 'https://instagram.com',
            'linkedin': 'https://linkedin.com',
            'github': 'https://github.com',
            'stackoverflow': 'https://stackoverflow.com',
            'reddit': 'https://reddit.com',
            'amazon': 'https://amazon.com',
            'netflix': 'https://netflix.com',
            'spotify': 'https://spotify.com'
        }
        
        task_lower = task.lower()
        for service, url in common_services.items():
            if service in task_lower:
                return url
        
        # Look for domain names (expanded to include more TLDs)
        domain_match = re.search(r'(?:open|go to|visit)\s+([^\s]+\.(?:com|org|net|ru|io|co|uk|de|fr|jp|cn|br|in|au|ca|mx|es|it|nl|se|no|dk|fi|pl|cz|sk|hu|ro|bg|hr|si|ee|lv|lt|gr|pt|ie|be|at|ch|lu|mt|cy))', task, re.IGNORECASE)
        if domain_match:
            domain = domain_match.group(1)
            if not domain.startswith('http'):
                return f"https://{domain}"
            return domain
        
        # Look for simple domain patterns without "open/go to/visit"
        simple_domain_match = re.search(r'([^\s]+\.(?:com|org|net|ru|io|co|uk|de|fr|jp|cn|br|in|au|ca|mx|es|it|nl|se|no|dk|fi|pl|cz|sk|hu|ro|bg|hr|si|ee|lv|lt|gr|pt|ie|be|at|ch|lu|mt|cy))', task, re.IGNORECASE)
        if simple_domain_match:
            domain = simple_domain_match.group(1)
            if not domain.startswith('http'):
                return f"https://{domain}"
            return domain
        
        return ""
    
    def cleanup(self):
        """Cleanup resources."""
        if self.navigation_manager:
            self.navigation_manager.close()
        print("🧹 Cleanup complete")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("🤖 AI Browser Agent")
        print("=" * 50)
        print("Usage: python setup_agent.py \"<task>\"")
        print()
        print("Examples:")
        print("  python setup_agent.py \"Open telegram.org and write hello to @stroiteeleva\"")
        print("  python setup_agent.py \"Go to google.com and search for AI browser automation\"")
        print("  python setup_agent.py \"Open github.com\"")
        return
    
    task = " ".join(sys.argv[1:])
    
    agent = SetupAgent()
    
    try:
        # Setup and connect
        if agent.setup_and_connect():
            # Execute task
            success = agent.execute_task(task)
            
            if success:
                print("\n🎉 Task completed successfully!")
            else:
                print("\n❌ Task failed")
        else:
            print("\n❌ Setup failed")
    
    except KeyboardInterrupt:
        print("\n\n⏹️  Task interrupted by user")
    
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
    
    finally:
        agent.cleanup()
        print("\n👋 AI Browser Agent finished")


if __name__ == "__main__":
    main()