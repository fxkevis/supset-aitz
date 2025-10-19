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
        elif "gmail" in task_lower and any(word in task_lower for word in ["move", "delete", "spam", "archive", "select"]):
            return self._execute_gmail_task(task)
        elif "google" in task_lower and "search" in task_lower:
            return self._execute_google_search_task(task)
        elif "open" in task_lower or "go to" in task_lower or "visit" in task_lower:
            return self._execute_navigation_task(task)
        else:
            print("❌ Task type not recognized")
            print("💡 Supported tasks:")
            print("   - 'Open telegram.org and write hello to @username'")
            print("   - 'Find and move spam emails to spam in Gmail'")
            print("   - 'Delete suspicious emails in Gmail'")
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
        
        # Type recipient name using JavaScript (most reliable for Telegram)
        print(f"⌨️  Typing '{recipient}' using JavaScript method...")
        try:
            # Use JavaScript to set the value and trigger input event
            self.navigation_manager.driver.execute_script("arguments[0].value = arguments[1];", search_box, recipient)
            self.navigation_manager.driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", search_box)
            print(f"✅ Successfully typed '{recipient}'")
        except Exception as e:
            print(f"❌ Could not type recipient name: {e}")
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
        print("⏳ Waiting for chat to load...")
        time.sleep(8)  # Increased wait time
        
        # Step 4: Find message input and send message
        print("\n💬 Step 4: Sending message...")
        
        # Check current page to make sure we're in a chat
        current_info = self.navigation_manager.get_current_info()
        print(f"📍 Current page: {current_info.get('title', 'Unknown')}")
        
        # Wait a bit more for chat to fully load
        time.sleep(3)
        
        message_selectors = [
            "[role='textbox'][contenteditable='true']",
            "div[contenteditable='true']",
            "[role='textbox']",
            "[placeholder*='Message']",
            "[placeholder*='message']",
            ".composer-input-wrapper div[contenteditable='true']",
            ".composer-input",
            ".input-message-input",
            "textarea",
            "[data-testid='message-input']",
            ".message-input-wrapper [contenteditable='true']",
            ".chat-input [contenteditable='true']",
            "#message-input-text"
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
    
    def _execute_gmail_task(self, task: str) -> bool:
        """Execute Gmail email management task."""
        print("📧 Executing Gmail task...")
        
        # Extract action and count
        action = self._extract_gmail_action(task)
        count = self._extract_email_count(task)
        
        if not action:
            print("❌ Could not extract Gmail action from task")
            return False
        
        print(f"📧 Action: {action}")
        print(f"🔢 Analyzing up to {count} emails for spam indicators")
        print("🧠 Using intelligent spam detection (not random selection)")
        
        # Step 1: Navigate to Gmail if not already there
        print("\n📧 Step 1: Opening Gmail...")
        if not self.navigation_manager.navigate_to_website("https://gmail.com"):
            print("❌ Failed to open Gmail")
            return False
        
        # Wait for Gmail to load
        time.sleep(5)
        
        # Step 2: Select emails
        print(f"\n☑️  Step 2: Selecting {count} emails...")
        selected_count = self._select_emails(count)
        
        if selected_count == 0:
            print("❌ Could not select any emails")
            return False
        
        print(f"✅ Selected {selected_count} emails")
        
        # Step 3: Perform action
        print(f"\n🎯 Step 3: Performing action '{action}'...")
        if self._perform_gmail_action(action):
            print(f"✅ Successfully {action}ed {selected_count} emails!")
            return True
        else:
            print(f"❌ Failed to {action} emails")
            return False
    
    def _select_emails(self, count: int) -> int:
        """Select emails intelligently based on spam analysis."""
        print(f"🔍 Analyzing emails to identify potential spam...")
        
        # Find email rows for analysis
        email_row_selectors = [
            "tr.zA",  # Gmail email rows
            "tr[role='row']",
            "tbody tr"
        ]
        
        email_rows = []
        for selector in email_row_selectors:
            try:
                rows = self.navigation_manager.driver.find_elements("css selector", selector)
                if rows:
                    email_rows = [row for row in rows if row.is_displayed()]
                    print(f"📧 Found {len(email_rows)} email rows with selector: {selector}")
                    break
            except Exception as e:
                print(f"⚠️  Selector {selector} failed: {e}")
                continue
        
        if not email_rows:
            print("❌ No email rows found")
            return 0
        
        # Analyze emails and select spam candidates
        selected_count = 0
        spam_candidates = []
        
        print(f"🧠 Analyzing {min(len(email_rows), count * 3)} emails for spam indicators...")
        
        for i, row in enumerate(email_rows[:count * 3]):  # Check more emails than needed
            try:
                spam_score = self._analyze_email_for_spam(row, i + 1)
                if spam_score >= 0.3:  # Threshold for spam detection
                    spam_candidates.append((row, spam_score))
                    print(f"🎯 Email {i+1}: Spam score {spam_score:.2f} - SPAM CANDIDATE")
                else:
                    print(f"✅ Email {i+1}: Spam score {spam_score:.2f} - Legitimate")
                    
            except Exception as e:
                print(f"⚠️  Could not analyze email {i+1}: {e}")
                continue
        
        # Sort by spam score (highest first) and select top candidates
        spam_candidates.sort(key=lambda x: x[1], reverse=True)
        selected_emails = spam_candidates[:count]
        
        print(f"\n☑️  Selecting {len(selected_emails)} emails identified as spam...")
        
        # Select the identified spam emails
        for row, spam_score in selected_emails:
            try:
                # Find checkbox within this row
                checkbox = row.find_element("css selector", "div[role='checkbox']")
                if checkbox and checkbox.is_displayed():
                    if self.navigation_manager.click_element_reliable(checkbox):
                        selected_count += 1
                        print(f"✅ Selected spam email {selected_count} (score: {spam_score:.2f})")
                        time.sleep(0.5)
            except Exception as e:
                print(f"⚠️  Could not select spam email: {e}")
                continue
        
        if selected_count == 0:
            print("🎉 No spam emails detected! Your inbox looks clean.")
        
        return selected_count
    
    def _analyze_email_for_spam(self, email_row, email_num: int) -> float:
        """Analyze an email row for spam indicators. Returns spam score 0.0-1.0."""
        spam_score = 0.0
        
        try:
            # Extract email information
            sender_element = email_row.find_element("css selector", "span[email], .go span, .yW span")
            sender = sender_element.get_attribute("email") or sender_element.text or ""
        except:
            sender = ""
        
        try:
            subject_element = email_row.find_element("css selector", ".bog, .y6 span, [data-thread-id] span")
            subject = subject_element.text or ""
        except:
            subject = ""
        
        try:
            # Check if email is unread (might indicate spam)
            unread = "zE" in email_row.get_attribute("class")
        except:
            unread = False
        
        # Spam indicators analysis
        spam_indicators = {
            # Sender-based indicators
            "suspicious_domains": [
                "noreply", "no-reply", "donotreply", "marketing", "promo", 
                "offer", "deal", "sale", "discount", "free", "win", "prize"
            ],
            "suspicious_tlds": [".tk", ".ml", ".ga", ".cf", ".click", ".download"],
            
            # Subject-based indicators  
            "spam_keywords": [
                "free", "win", "prize", "congratulations", "urgent", "act now",
                "limited time", "exclusive", "guarantee", "no obligation",
                "click here", "buy now", "order now", "call now", "apply now",
                "cash", "money", "earn", "income", "profit", "investment",
                "loan", "credit", "debt", "mortgage", "insurance",
                "viagra", "cialis", "pharmacy", "pills", "medication",
                "weight loss", "diet", "supplement", "enhancement",
                "casino", "gambling", "lottery", "jackpot", "betting"
            ],
            
            # Russian spam keywords
            "russian_spam": [
                "бесплатно", "выиграть", "приз", "срочно", "акция", "скидка",
                "кредит", "займ", "деньги", "заработок", "доход", "прибыль",
                "казино", "ставки", "лотерея", "выигрыш", "бонус"
            ]
        }
        
        # Check sender for spam indicators
        sender_lower = sender.lower()
        for domain in spam_indicators["suspicious_domains"]:
            if domain in sender_lower:
                spam_score += 0.3
                break
        
        for tld in spam_indicators["suspicious_tlds"]:
            if sender_lower.endswith(tld):
                spam_score += 0.4
                break
        
        # Check subject for spam keywords
        subject_lower = subject.lower()
        spam_keyword_count = 0
        
        for keyword in spam_indicators["spam_keywords"]:
            if keyword in subject_lower:
                spam_keyword_count += 1
        
        for keyword in spam_indicators["russian_spam"]:
            if keyword in subject_lower:
                spam_keyword_count += 1
        
        # Add score based on spam keywords
        if spam_keyword_count > 0:
            spam_score += min(spam_keyword_count * 0.2, 0.6)
        
        # Additional indicators
        if len(subject) > 100:  # Very long subjects often spam
            spam_score += 0.1
        
        if subject.count("!") > 2:  # Multiple exclamation marks
            spam_score += 0.1
        
        if subject.isupper() and len(subject) > 10:  # ALL CAPS subjects
            spam_score += 0.2
        
        # Check for excessive special characters
        special_chars = sum(1 for c in subject if c in "!@#$%^&*()+=[]{}|;:,.<>?")
        if special_chars > len(subject) * 0.2:  # More than 20% special chars
            spam_score += 0.2
        
        # Cap the score at 1.0
        spam_score = min(spam_score, 1.0)
        
        return spam_score
    
    def _perform_gmail_action(self, action: str) -> bool:
        """Perform the specified action on selected emails."""
        print(f"🎯 Performing action: {action}")
        
        # Gmail action button selectors (supporting multiple languages)
        action_selectors = {
            "spam": [
                "div[aria-label='В спам!']",  # Russian
                "div[data-tooltip='В спам!']",  # Russian
                "div[aria-label='Report spam']",  # English
                "div[data-tooltip='Report spam']",  # English
                "div[aria-label*='spam']",
                "div[data-tooltip*='spam']",
                ".G-Ni div[role='button'][aria-label*='спам']"
            ],
            "delete": [
                "div[aria-label='Удалить']",  # Russian
                "div[data-tooltip='Удалить']",  # Russian
                "div[aria-label='Delete']",  # English
                "div[data-tooltip='Delete']",  # English
                "div[aria-label*='Delete']", 
                "div[data-tooltip*='Delete']",
                ".G-Ni div[role='button'][aria-label*='Удалить']"
            ],
            "archive": [
                "div[aria-label='Архивировать']",  # Russian
                "div[data-tooltip='Архивировать']",  # Russian
                "div[aria-label='Archive']",  # English
                "div[data-tooltip='Archive']",  # English
                "div[aria-label*='Archive']",
                "div[data-tooltip*='Archive']", 
                ".G-Ni div[role='button'][aria-label*='Архивировать']"
            ]
        }
        
        selectors = action_selectors.get(action, [])
        if not selectors:
            print(f"❌ Unknown action: {action}")
            return False
        
        # Try to find and click the action button
        for selector in selectors:
            try:
                buttons = self.navigation_manager.driver.find_elements("css selector", selector)
                print(f"🔍 Found {len(buttons)} {action} buttons with selector: {selector}")
                
                for button in buttons:
                    if button.is_displayed() and button.is_enabled():
                        print(f"🖱️  Clicking {action} button...")
                        if self.navigation_manager.click_element_reliable(button):
                            print(f"✅ Successfully clicked {action} button")
                            time.sleep(2)  # Wait for action to complete
                            return True
                        
            except Exception as e:
                print(f"⚠️  Selector {selector} failed: {e}")
                continue
        
        print(f"❌ Could not find {action} button")
        return False
    
    def _extract_gmail_action(self, task: str) -> str:
        """Extract Gmail action from task."""
        task_lower = task.lower()
        
        if "spam" in task_lower:
            return "spam"
        elif "delete" in task_lower:
            return "delete"
        elif "archive" in task_lower:
            return "archive"
        
        return ""
    
    def _extract_email_count(self, task: str) -> int:
        """Extract number of emails from task."""
        import re
        
        # Look for numbers in the task
        numbers = re.findall(r'\d+', task)
        if numbers:
            return int(numbers[0])
        
        # Default to 10 if no number specified
        return 10
    
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