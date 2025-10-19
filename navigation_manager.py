#!/usr/bin/env python3
"""Navigation Manager - Reliable Website Navigation"""

import asyncio
import time
from typing import Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


class NavigationManager:
    """Manages reliable website navigation."""
    
    def __init__(self, debug_port: int = 9222):
        self.debug_port = debug_port
        self.driver: Optional[webdriver.Chrome] = None
        self.wait: Optional[WebDriverWait] = None
        
    def connect_to_chrome(self) -> bool:
        """Connect to existing Chrome with remote debugging."""
        try:
            print("🔗 Connecting to Chrome...")
            
            options = Options()
            options.add_experimental_option("debuggerAddress", f"127.0.0.1:{self.debug_port}")
            
            self.driver = webdriver.Chrome(options=options)
            self.wait = WebDriverWait(self.driver, 10)
            
            # Test the connection
            current_url = self.driver.current_url
            title = self.driver.title
            
            print(f"✅ Connected to Chrome!")
            print(f"📍 Current tab: {current_url}")
            print(f"📄 Title: {title}")
            
            return True
            
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def navigate_to_website(self, url: str, open_new_tab: bool = True) -> bool:
        """Navigate to website with reliable tab management."""
        if not self.driver:
            print("❌ Not connected to Chrome")
            return False
        
        try:
            print(f"🌐 Navigating to {url}...")
            
            current_url = self.driver.current_url
            print(f"📍 Currently on: {current_url}")
            
            if open_new_tab and current_url and current_url not in ["data:,", "chrome://new-tab-page/"]:
                # Open in new tab
                print("🆕 Opening in new tab...")
                
                # Method 1: Use Ctrl+T to open new tab, then navigate
                try:
                    from selenium.webdriver.common.keys import Keys
                    from selenium.webdriver.common.action_chains import ActionChains
                    
                    # Open new tab with Ctrl+T
                    ActionChains(self.driver).key_down(Keys.COMMAND).send_keys('t').key_up(Keys.COMMAND).perform()
                    time.sleep(1)
                    
                    # Navigate to URL
                    self.driver.get(url)
                    
                except Exception as e:
                    print(f"⚠️  New tab method failed: {e}")
                    # Fallback: direct navigation
                    print("🔄 Using direct navigation...")
                    self.driver.get(url)
            else:
                # Navigate in current tab
                print("🌐 Navigating in current tab...")
                self.driver.get(url)
            
            # Wait for page to load
            print("⏳ Waiting for page to load...")
            return self._wait_for_page_load(url)
            
        except Exception as e:
            print(f"❌ Navigation failed: {e}")
            return False
    
    def _wait_for_page_load(self, expected_url: str, timeout: int = 15) -> bool:
        """Wait for page to load and verify URL."""
        domain = expected_url.replace("https://", "").replace("http://", "").split('/')[0]
        
        for i in range(timeout):
            try:
                current_url = self.driver.current_url
                title = self.driver.title
                
                # Check if we're on the right domain
                if domain in current_url:
                    print(f"✅ Successfully loaded: {title}")
                    print(f"📍 URL: {current_url}")
                    return True
                
                # Check if page is still loading
                ready_state = self.driver.execute_script("return document.readyState")
                if ready_state != "complete":
                    print(f"⏳ Page loading... ({i+1}/{timeout})")
                    time.sleep(1)
                    continue
                
                # Page is complete but wrong URL - might be redirect
                if i < 5:  # Give it a few more seconds for redirects
                    print(f"⏳ Waiting for redirect... ({i+1}/{timeout})")
                    time.sleep(1)
                    continue
                else:
                    print(f"⚠️  Unexpected URL: {current_url}")
                    # Still return True if the page loaded, even if URL is different
                    return True
                    
            except Exception as e:
                print(f"⚠️  Error checking page load: {e}")
                time.sleep(1)
        
        print(f"❌ Page load timeout after {timeout} seconds")
        return False
    
    def get_current_info(self) -> dict:
        """Get current page information."""
        if not self.driver:
            return {"error": "Not connected"}
        
        try:
            return {
                "url": self.driver.current_url,
                "title": self.driver.title,
                "ready_state": self.driver.execute_script("return document.readyState"),
                "tabs_count": len(self.driver.window_handles)
            }
        except Exception as e:
            return {"error": str(e)}
    
    def find_element_reliable(self, selectors: list, element_name: str, timeout: int = 10):
        """Find element using multiple selectors with reliability."""
        if not self.driver:
            print("❌ Not connected to Chrome")
            return None
        
        print(f"🔍 Looking for {element_name}...")
        
        for selector in selectors:
            try:
                # Check if it's XPath or CSS selector
                if selector.startswith("//"):
                    elements = self.driver.find_elements(By.XPATH, selector)
                else:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        print(f"✅ Found {element_name} with selector: {selector}")
                        return element
                        
            except Exception as e:
                print(f"⚠️  Selector {selector} failed: {e}")
                continue
        
        print(f"❌ Could not find {element_name}")
        return None
    
    def type_text_reliable(self, element, text: str) -> bool:
        """Type text into element with multiple strategies."""
        if not element:
            return False
        
        print(f"⌨️  Typing '{text}'...")
        
        strategies = [
            # Strategy 1: Standard clear and send_keys
            lambda: (element.clear(), element.send_keys(text)),
            
            # Strategy 2: Click first, then clear and type
            lambda: (element.click(), time.sleep(0.5), element.clear(), element.send_keys(text)),
            
            # Strategy 3: JavaScript
            lambda: self.driver.execute_script("arguments[0].value = arguments[1];", element, text),
            
            # Strategy 4: ActionChains
            lambda: self._action_chains_type(element, text)
        ]
        
        for i, strategy in enumerate(strategies, 1):
            try:
                strategy()
                print(f"✅ Successfully typed '{text}' (method {i})")
                return True
            except Exception as e:
                print(f"⚠️  Typing method {i} failed: {e}")
                continue
        
        print(f"❌ All typing methods failed for '{text}'")
        return False
    
    def _action_chains_type(self, element, text: str):
        """Type using ActionChains."""
        from selenium.webdriver.common.action_chains import ActionChains
        from selenium.webdriver.common.keys import Keys
        
        actions = ActionChains(self.driver)
        actions.click(element)
        actions.key_down(Keys.COMMAND).send_keys('a').key_up(Keys.COMMAND)  # Select all
        actions.send_keys(text)
        actions.perform()
    
    def click_element_reliable(self, element) -> bool:
        """Click element with multiple strategies."""
        if not element:
            return False
        
        print("🖱️  Clicking element...")
        
        strategies = [
            # Strategy 1: Standard click
            lambda: element.click(),
            
            # Strategy 2: JavaScript click
            lambda: self.driver.execute_script("arguments[0].click();", element),
            
            # Strategy 3: ActionChains click
            lambda: ActionChains(self.driver).click(element).perform(),
            
            # Strategy 4: Scroll into view then click
            lambda: (
                self.driver.execute_script("arguments[0].scrollIntoView(true);", element),
                time.sleep(0.5),
                element.click()
            )
        ]
        
        for i, strategy in enumerate(strategies, 1):
            try:
                strategy()
                print(f"✅ Successfully clicked element (method {i})")
                return True
            except Exception as e:
                print(f"⚠️  Click method {i} failed: {e}")
                continue
        
        print("❌ All click methods failed")
        return False
    
    def close(self):
        """Close the connection (but keep Chrome running)."""
        if self.driver:
            try:
                # Don't quit the driver - just disconnect
                # self.driver.quit()  # This would close Chrome
                print("🔌 Disconnected from Chrome (keeping Chrome open)")
            except:
                pass


def main():
    """Test Navigation Manager."""
    print("🧪 Testing Navigation Manager...")
    print("=" * 50)
    
    nav = NavigationManager()
    
    if nav.connect_to_chrome():
        print("\n🌐 Testing navigation to Google...")
        if nav.navigate_to_website("https://www.google.com"):
            info = nav.get_current_info()
            print(f"📊 Page info: {info}")
            
            # Test element finding
            search_box = nav.find_element_reliable(
                ["input[name='q']", "input[type='search']", "#search"],
                "search box"
            )
            
            if search_box:
                nav.type_text_reliable(search_box, "test search")
        
        nav.close()
    else:
        print("❌ Could not connect to Chrome")


if __name__ == "__main__":
    main()