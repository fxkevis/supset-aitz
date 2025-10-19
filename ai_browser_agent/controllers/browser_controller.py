"""Browser controller for web automation using Selenium WebDriver."""

import time
from typing import Dict, List, Optional, Any, Union
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.common.exceptions import (
    TimeoutException, 
    NoSuchElementException, 
    WebDriverException,
    ElementNotInteractableException
)
from webdriver_manager.chrome import ChromeDriverManager
from loguru import logger

from ..interfaces.base_interfaces import BaseController
from ..models.config import BrowserConfig
from ..models.page_content import PageContent, WebElement
from ..models.action import Action, ActionType


class BrowserController(BaseController):
    """Controls web browser automation using Selenium WebDriver."""
    
    def __init__(self, config: Optional[BrowserConfig] = None):
        """Initialize the browser controller.
        
        Args:
            config: Browser configuration settings
        """
        super().__init__(config.to_dict() if config else {})
        self.browser_config = config or BrowserConfig()
        self.driver: Optional[webdriver.Chrome] = None
        self.wait: Optional[WebDriverWait] = None
        self.action_chains: Optional[ActionChains] = None
        
    def connect(self) -> None:
        """Establish connection to the browser by initializing WebDriver."""
        if self.is_connected():
            logger.warning("Browser is already connected")
            return
            
        try:
            # Set up Chrome options
            chrome_options = ChromeOptions()
            
            # Configure headless mode
            if self.browser_config.headless:
                chrome_options.add_argument("--headless")
            
            # Set window size
            width, height = self.browser_config.window_size
            chrome_options.add_argument(f"--window-size={width},{height}")
            
            # Set user agent if specified
            if self.browser_config.user_agent:
                chrome_options.add_argument(f"--user-agent={self.browser_config.user_agent}")
            
            # Set profile path if specified
            if self.browser_config.profile_path:
                chrome_options.add_argument(f"--user-data-dir={self.browser_config.profile_path}")
                
                # Set specific profile directory if specified
                if hasattr(self.browser_config, 'profile_directory') and self.browser_config.profile_directory:
                    chrome_options.add_argument(f"--profile-directory={self.browser_config.profile_directory}")
            
            # Set download directory if specified
            if self.browser_config.download_directory:
                prefs = {"download.default_directory": self.browser_config.download_directory}
                chrome_options.add_experimental_option("prefs", prefs)
            
            # Disable images if configured
            if self.browser_config.disable_images:
                prefs = {"profile.managed_default_content_settings.images": 2}
                chrome_options.add_experimental_option("prefs", prefs)
            
            # Disable JavaScript if configured (not recommended for most use cases)
            if self.browser_config.disable_javascript:
                chrome_options.add_argument("--disable-javascript")
            
            # Additional Chrome options for stability
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            
            # Configure automation flags
            if hasattr(self.browser_config, 'disable_automation_flags') and self.browser_config.disable_automation_flags:
                # Remove automation indicators
                chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
                chrome_options.add_experimental_option('useAutomationExtension', False)
                chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            else:
                chrome_options.add_argument("--disable-extensions")
            
            # Configure remote debugging if specified
            if hasattr(self.browser_config, 'remote_debugging_port') and self.browser_config.remote_debugging_port:
                chrome_options.add_argument(f"--remote-debugging-port={self.browser_config.remote_debugging_port}")
                # Try to connect to existing Chrome instance first
                try:
                    from selenium.webdriver.chrome.options import Options
                    existing_options = Options()
                    existing_options.add_experimental_option("debuggerAddress", f"127.0.0.1:{self.browser_config.remote_debugging_port}")
                    self.driver = webdriver.Chrome(options=existing_options)
                    logger.info("Connected to existing Chrome instance")
                    return
                except Exception as e:
                    logger.info(f"Could not connect to existing Chrome, starting new instance: {e}")
            
            # Set up Chrome service with webdriver-manager
            service = ChromeService(ChromeDriverManager().install())
            
            # Initialize WebDriver
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Set timeouts
            self.driver.implicitly_wait(10)
            self.driver.set_page_load_timeout(self.browser_config.timeout)
            
            # Initialize WebDriverWait and ActionChains
            self.wait = WebDriverWait(self.driver, self.browser_config.timeout)
            self.action_chains = ActionChains(self.driver)
            
            self.is_initialized = True
            logger.info("Browser controller connected successfully")
            
        except Exception as e:
            logger.error(f"Failed to connect browser: {e}")
            raise WebDriverException(f"Failed to initialize browser: {e}")
    
    def disconnect(self) -> None:
        """Disconnect from the browser by closing WebDriver."""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Browser controller disconnected")
            except Exception as e:
                logger.error(f"Error during browser disconnect: {e}")
            finally:
                self.driver = None
                self.wait = None
                self.action_chains = None
                self.is_initialized = False
    
    def is_connected(self) -> bool:
        """Check if browser connection is active."""
        if not self.driver:
            return False
        
        try:
            # Try to get current URL to test if driver is still active
            _ = self.driver.current_url
            return True
        except Exception:
            return False
    
    def navigate_to(self, url: str) -> None:
        """Navigate to a specific URL.
        
        Args:
            url: The URL to navigate to
            
        Raises:
            WebDriverException: If navigation fails
        """
        if not self.is_connected():
            raise WebDriverException("Browser is not connected")
        
        try:
            logger.info(f"Navigating to: {url}")
            self.driver.get(url)
            
            # Wait for page to load
            self.wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
            
        except TimeoutException:
            logger.error(f"Timeout while navigating to {url}")
            raise
        except Exception as e:
            logger.error(f"Failed to navigate to {url}: {e}")
            raise WebDriverException(f"Navigation failed: {e}")
    
    def find_element(self, selector: str, by: By = By.CSS_SELECTOR, timeout: Optional[int] = None) -> Optional[Any]:
        """Find a single element on the page.
        
        Args:
            selector: The selector string
            by: The selection method (CSS_SELECTOR, XPATH, ID, etc.)
            timeout: Optional timeout override
            
        Returns:
            WebElement if found, None otherwise
        """
        if not self.is_connected():
            raise WebDriverException("Browser is not connected")
        
        try:
            wait_time = timeout or self.browser_config.timeout
            element = WebDriverWait(self.driver, wait_time).until(
                EC.presence_of_element_located((by, selector))
            )
            return element
        except TimeoutException:
            logger.warning(f"Element not found: {selector}")
            return None
        except Exception as e:
            logger.error(f"Error finding element {selector}: {e}")
            return None
    
    def find_elements(self, selector: str, by: By = By.CSS_SELECTOR) -> List[Any]:
        """Find multiple elements on the page.
        
        Args:
            selector: The selector string
            by: The selection method
            
        Returns:
            List of WebElements
        """
        if not self.is_connected():
            raise WebDriverException("Browser is not connected")
        
        try:
            elements = self.driver.find_elements(by, selector)
            return elements
        except Exception as e:
            logger.error(f"Error finding elements {selector}: {e}")
            return []
    
    def click_element(self, element_or_selector: Union[str, Any], by: By = By.CSS_SELECTOR) -> bool:
        """Click on an element.
        
        Args:
            element_or_selector: WebElement or selector string
            by: Selection method if selector is provided
            
        Returns:
            True if click was successful, False otherwise
        """
        if not self.is_connected():
            raise WebDriverException("Browser is not connected")
        
        try:
            # Get element if selector was provided
            if isinstance(element_or_selector, str):
                element = self.find_element(element_or_selector, by)
                if not element:
                    return False
            else:
                element = element_or_selector
            
            # Wait for element to be clickable
            clickable_element = self.wait.until(EC.element_to_be_clickable(element))
            
            # Scroll element into view
            self.driver.execute_script("arguments[0].scrollIntoView(true);", clickable_element)
            time.sleep(0.5)  # Brief pause for scroll to complete
            
            # Click the element
            clickable_element.click()
            logger.debug(f"Successfully clicked element")
            return True
            
        except (TimeoutException, ElementNotInteractableException) as e:
            logger.warning(f"Element not clickable: {e}")
            return False
        except Exception as e:
            logger.error(f"Error clicking element: {e}")
            return False
    
    def type_text(self, element_or_selector: Union[str, Any], text: str, 
                  clear_first: bool = True, by: By = By.CSS_SELECTOR) -> bool:
        """Type text into an input element.
        
        Args:
            element_or_selector: WebElement or selector string
            text: Text to type
            clear_first: Whether to clear existing text first
            by: Selection method if selector is provided
            
        Returns:
            True if typing was successful, False otherwise
        """
        if not self.is_connected():
            raise WebDriverException("Browser is not connected")
        
        try:
            # Get element if selector was provided
            if isinstance(element_or_selector, str):
                element = self.find_element(element_or_selector, by)
                if not element:
                    return False
            else:
                element = element_or_selector
            
            # Wait for element to be clickable
            input_element = self.wait.until(EC.element_to_be_clickable(element))
            
            # Clear existing text if requested
            if clear_first:
                input_element.clear()
            
            # Type the text
            input_element.send_keys(text)
            logger.debug(f"Successfully typed text into element")
            return True
            
        except (TimeoutException, ElementNotInteractableException) as e:
            logger.warning(f"Element not available for typing: {e}")
            return False
        except Exception as e:
            logger.error(f"Error typing text: {e}")
            return False
    
    def scroll_to_element(self, element_or_selector: Union[str, Any], by: By = By.CSS_SELECTOR) -> bool:
        """Scroll to bring an element into view.
        
        Args:
            element_or_selector: WebElement or selector string
            by: Selection method if selector is provided
            
        Returns:
            True if scrolling was successful, False otherwise
        """
        if not self.is_connected():
            raise WebDriverException("Browser is not connected")
        
        try:
            # Get element if selector was provided
            if isinstance(element_or_selector, str):
                element = self.find_element(element_or_selector, by)
                if not element:
                    return False
            else:
                element = element_or_selector
            
            # Scroll element into view
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(0.5)  # Brief pause for scroll to complete
            return True
            
        except Exception as e:
            logger.error(f"Error scrolling to element: {e}")
            return False
    
    def wait_for_element(self, selector: str, by: By = By.CSS_SELECTOR, 
                        timeout: Optional[int] = None) -> Optional[Any]:
        """Wait for an element to appear on the page.
        
        Args:
            selector: The selector string
            by: Selection method
            timeout: Optional timeout override
            
        Returns:
            WebElement if found within timeout, None otherwise
        """
        if not self.is_connected():
            raise WebDriverException("Browser is not connected")
        
        try:
            wait_time = timeout or self.browser_config.timeout
            element = WebDriverWait(self.driver, wait_time).until(
                EC.presence_of_element_located((by, selector))
            )
            return element
        except TimeoutException:
            logger.warning(f"Timeout waiting for element: {selector}")
            return None
    
    def get_current_url(self) -> str:
        """Get the current page URL.
        
        Returns:
            Current URL string
        """
        if not self.is_connected():
            raise WebDriverException("Browser is not connected")
        
        return self.driver.current_url
    
    def get_page_title(self) -> str:
        """Get the current page title.
        
        Returns:
            Page title string
        """
        if not self.is_connected():
            raise WebDriverException("Browser is not connected")
        
        return self.driver.title
    
    def get_page_source(self) -> str:
        """Get the current page HTML source.
        
        Returns:
            HTML source string
        """
        if not self.is_connected():
            raise WebDriverException("Browser is not connected")
        
        return self.driver.page_source
    
    async def get_page_content(self) -> 'PageContent':
        """Get comprehensive page content including elements and metadata.
        
        Returns:
            PageContent object with page data
        """
        from ..models.page_content import PageContent, WebElement
        
        if not self.is_connected():
            raise WebDriverException("Browser is not connected")
        
        start_time = time.time()
        
        # Get basic page information
        url = self.get_current_url()
        title = self.get_page_title()
        html_content = self.get_page_source()
        
        # Extract text content (simplified)
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            text_content = soup.get_text(separator=' ', strip=True)
        except ImportError:
            # Fallback if BeautifulSoup is not available
            text_content = html_content
        
        # Extract basic elements (simplified implementation)
        elements = []
        try:
            # Find common interactive elements
            interactive_selectors = [
                "a", "button", "input", "select", "textarea", 
                "[onclick]", "[href]", "[role='button']"
            ]
            
            for selector in interactive_selectors:
                try:
                    web_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for elem in web_elements[:20]:  # Limit to first 20 elements per type
                        try:
                            element_data = WebElement(
                                tag_name=elem.tag_name,
                                attributes={
                                    "id": elem.get_attribute("id") or "",
                                    "class": elem.get_attribute("class") or "",
                                    "href": elem.get_attribute("href") or "",
                                    "type": elem.get_attribute("type") or "",
                                },
                                text_content=elem.text[:200] if elem.text else "",  # Limit text length
                                is_visible=elem.is_displayed(),
                                is_enabled=elem.is_enabled(),
                                is_clickable=elem.is_enabled() and elem.is_displayed()
                            )
                            elements.append(element_data)
                        except Exception:
                            # Skip elements that can't be processed
                            continue
                except Exception:
                    # Skip selectors that fail
                    continue
        except Exception as e:
            logger.warning(f"Failed to extract page elements: {e}")
        
        load_time = time.time() - start_time
        
        return PageContent(
            url=url,
            title=title,
            text_content=text_content[:5000],  # Limit text content size
            html_content=html_content[:10000] if len(html_content) > 10000 else html_content,  # Limit HTML size
            elements=elements,
            metadata={
                "element_count": len(elements),
                "page_size": len(html_content),
                "extraction_method": "selenium"
            },
            load_time=load_time
        )
    
    def take_screenshot(self, filepath: Optional[str] = None) -> Optional[bytes]:
        """Take a screenshot of the current page.
        
        Args:
            filepath: Optional path to save screenshot file
            
        Returns:
            Screenshot bytes if no filepath provided, None otherwise
        """
        if not self.is_connected():
            raise WebDriverException("Browser is not connected")
        
        try:
            if filepath:
                self.driver.save_screenshot(filepath)
                logger.info(f"Screenshot saved to: {filepath}")
                return None
            else:
                return self.driver.get_screenshot_as_png()
        except Exception as e:
            logger.error(f"Error taking screenshot: {e}")
            return None
    
    def refresh_page(self) -> None:
        """Refresh the current page."""
        if not self.is_connected():
            raise WebDriverException("Browser is not connected")
        
        try:
            self.driver.refresh()
            # Wait for page to load
            self.wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
        except Exception as e:
            logger.error(f"Error refreshing page: {e}")
            raise WebDriverException(f"Page refresh failed: {e}")
    
    def go_back(self) -> None:
        """Navigate back in browser history."""
        if not self.is_connected():
            raise WebDriverException("Browser is not connected")
        
        try:
            self.driver.back()
        except Exception as e:
            logger.error(f"Error going back: {e}")
            raise WebDriverException(f"Navigation back failed: {e}")
    
    def go_forward(self) -> None:
        """Navigate forward in browser history."""
        if not self.is_connected():
            raise WebDriverException("Browser is not connected")
        
        try:
            self.driver.forward()
        except Exception as e:
            logger.error(f"Error going forward: {e}")
            raise WebDriverException(f"Navigation forward failed: {e}")
    
    def execute_script(self, script: str, *args) -> Any:
        """Execute JavaScript in the browser.
        
        Args:
            script: JavaScript code to execute
            *args: Arguments to pass to the script
            
        Returns:
            Script execution result
        """
        if not self.is_connected():
            raise WebDriverException("Browser is not connected")
        
        try:
            return self.driver.execute_script(script, *args)
        except Exception as e:
            logger.error(f"Error executing script: {e}")
            raise WebDriverException(f"Script execution failed: {e}")
    
    def get_window_size(self) -> Dict[str, int]:
        """Get current window size.
        
        Returns:
            Dictionary with 'width' and 'height' keys
        """
        if not self.is_connected():
            raise WebDriverException("Browser is not connected")
        
        size = self.driver.get_window_size()
        return {"width": size["width"], "height": size["height"]}
    
    def set_window_size(self, width: int, height: int) -> None:
        """Set window size.
        
        Args:
            width: Window width in pixels
            height: Window height in pixels
        """
        if not self.is_connected():
            raise WebDriverException("Browser is not connected")
        
        try:
            self.driver.set_window_size(width, height)
        except Exception as e:
            logger.error(f"Error setting window size: {e}")
            raise WebDriverException(f"Window resize failed: {e}")