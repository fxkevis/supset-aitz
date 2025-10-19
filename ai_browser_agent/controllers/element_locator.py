"""Element locator for robust web element finding with multiple strategies."""

import time
from typing import Dict, List, Optional, Any, Union, Tuple
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, 
    NoSuchElementException, 
    StaleElementReferenceException
)
from loguru import logger

from ..models.page_content import WebElement


class ElementSelector:
    """Represents different ways to select an element."""
    
    def __init__(self, 
                 css_selector: Optional[str] = None,
                 xpath: Optional[str] = None,
                 id_attr: Optional[str] = None,
                 class_name: Optional[str] = None,
                 tag_name: Optional[str] = None,
                 name_attr: Optional[str] = None,
                 link_text: Optional[str] = None,
                 partial_link_text: Optional[str] = None,
                 text_content: Optional[str] = None,
                 attributes: Optional[Dict[str, str]] = None):
        """Initialize element selector with multiple selection strategies.
        
        Args:
            css_selector: CSS selector string
            xpath: XPath selector string
            id_attr: Element ID attribute
            class_name: Element class name
            tag_name: HTML tag name
            name_attr: Element name attribute
            link_text: Exact link text
            partial_link_text: Partial link text
            text_content: Element text content
            attributes: Dictionary of attribute name-value pairs
        """
        self.css_selector = css_selector
        self.xpath = xpath
        self.id_attr = id_attr
        self.class_name = class_name
        self.tag_name = tag_name
        self.name_attr = name_attr
        self.link_text = link_text
        self.partial_link_text = partial_link_text
        self.text_content = text_content
        self.attributes = attributes or {}
    
    def get_selenium_selectors(self) -> List[Tuple[By, str]]:
        """Get list of Selenium selector tuples in priority order.
        
        Returns:
            List of (By, selector_string) tuples
        """
        selectors = []
        
        # ID has highest priority (most specific)
        if self.id_attr:
            selectors.append((By.ID, self.id_attr))
        
        # CSS selector
        if self.css_selector:
            selectors.append((By.CSS_SELECTOR, self.css_selector))
        
        # XPath
        if self.xpath:
            selectors.append((By.XPATH, self.xpath))
        
        # Name attribute
        if self.name_attr:
            selectors.append((By.NAME, self.name_attr))
        
        # Class name
        if self.class_name:
            selectors.append((By.CLASS_NAME, self.class_name))
        
        # Link text (exact)
        if self.link_text:
            selectors.append((By.LINK_TEXT, self.link_text))
        
        # Partial link text
        if self.partial_link_text:
            selectors.append((By.PARTIAL_LINK_TEXT, self.partial_link_text))
        
        # Tag name (least specific)
        if self.tag_name:
            selectors.append((By.TAG_NAME, self.tag_name))
        
        return selectors
    
    def generate_css_from_attributes(self) -> Optional[str]:
        """Generate CSS selector from attributes.
        
        Returns:
            CSS selector string or None
        """
        if not self.attributes:
            return None
        
        css_parts = []
        for attr_name, attr_value in self.attributes.items():
            if attr_name == "class":
                # Handle class attributes specially
                classes = attr_value.split()
                css_parts.extend([f".{cls}" for cls in classes])
            elif attr_name == "id":
                css_parts.append(f"#{attr_value}")
            else:
                css_parts.append(f"[{attr_name}='{attr_value}']")
        
        return "".join(css_parts) if css_parts else None
    
    def generate_xpath_from_text(self) -> Optional[str]:
        """Generate XPath selector from text content.
        
        Returns:
            XPath selector string or None
        """
        if not self.text_content:
            return None
        
        # Try exact text match first
        xpath = f"//*[text()='{self.text_content}']"
        return xpath


class ElementLocator:
    """Robust element locator with multiple finding strategies."""
    
    def __init__(self, driver: webdriver.Chrome, default_timeout: int = 10):
        """Initialize the element locator.
        
        Args:
            driver: Selenium WebDriver instance
            default_timeout: Default timeout for element finding
        """
        self.driver = driver
        self.default_timeout = default_timeout
        self.wait = WebDriverWait(driver, default_timeout)
    
    def find_element(self, selector: ElementSelector, 
                    timeout: Optional[int] = None,
                    wait_for_visible: bool = True,
                    wait_for_clickable: bool = False) -> Optional[Any]:
        """Find a single element using multiple strategies.
        
        Args:
            selector: ElementSelector with multiple selection strategies
            timeout: Optional timeout override
            wait_for_visible: Whether to wait for element to be visible
            wait_for_clickable: Whether to wait for element to be clickable
            
        Returns:
            WebElement if found, None otherwise
        """
        wait_time = timeout or self.default_timeout
        wait = WebDriverWait(self.driver, wait_time)
        
        # Get all possible selectors in priority order
        selenium_selectors = selector.get_selenium_selectors()
        
        # Try CSS from attributes if no direct selectors
        if not selenium_selectors:
            css_from_attrs = selector.generate_css_from_attributes()
            if css_from_attrs:
                selenium_selectors.append((By.CSS_SELECTOR, css_from_attrs))
        
        # Try XPath from text if available
        xpath_from_text = selector.generate_xpath_from_text()
        if xpath_from_text:
            selenium_selectors.append((By.XPATH, xpath_from_text))
        
        # Try each selector strategy
        for by, selector_string in selenium_selectors:
            try:
                logger.debug(f"Trying selector: {by} = {selector_string}")
                
                if wait_for_clickable:
                    element = wait.until(EC.element_to_be_clickable((by, selector_string)))
                elif wait_for_visible:
                    element = wait.until(EC.visibility_of_element_located((by, selector_string)))
                else:
                    element = wait.until(EC.presence_of_element_located((by, selector_string)))
                
                logger.debug(f"Found element using: {by} = {selector_string}")
                return element
                
            except TimeoutException:
                logger.debug(f"Timeout with selector: {by} = {selector_string}")
                continue
            except Exception as e:
                logger.debug(f"Error with selector {by} = {selector_string}: {e}")
                continue
        
        # If text content is specified, try fuzzy text matching
        if selector.text_content:
            element = self._find_by_fuzzy_text(selector.text_content, wait_time)
            if element:
                return element
        
        logger.warning(f"Element not found with any strategy")
        return None
    
    def find_elements(self, selector: ElementSelector, 
                     timeout: Optional[int] = None) -> List[Any]:
        """Find multiple elements using multiple strategies.
        
        Args:
            selector: ElementSelector with multiple selection strategies
            timeout: Optional timeout override
            
        Returns:
            List of WebElements
        """
        wait_time = timeout or self.default_timeout
        
        # Get all possible selectors
        selenium_selectors = selector.get_selenium_selectors()
        
        # Try CSS from attributes if no direct selectors
        if not selenium_selectors:
            css_from_attrs = selector.generate_css_from_attributes()
            if css_from_attrs:
                selenium_selectors.append((By.CSS_SELECTOR, css_from_attrs))
        
        # Try each selector strategy
        for by, selector_string in selenium_selectors:
            try:
                logger.debug(f"Trying multi-selector: {by} = {selector_string}")
                
                # Wait for at least one element to be present
                WebDriverWait(self.driver, wait_time).until(
                    EC.presence_of_element_located((by, selector_string))
                )
                
                elements = self.driver.find_elements(by, selector_string)
                if elements:
                    logger.debug(f"Found {len(elements)} elements using: {by} = {selector_string}")
                    return elements
                
            except TimeoutException:
                logger.debug(f"Timeout with multi-selector: {by} = {selector_string}")
                continue
            except Exception as e:
                logger.debug(f"Error with multi-selector {by} = {selector_string}: {e}")
                continue
        
        logger.warning(f"No elements found with any strategy")
        return []
    
    def find_clickable_elements(self, timeout: Optional[int] = None) -> List[Any]:
        """Find all clickable elements on the page.
        
        Args:
            timeout: Optional timeout override
            
        Returns:
            List of clickable WebElements
        """
        clickable_selectors = [
            "button",
            "input[type='button']",
            "input[type='submit']",
            "a[href]",
            "[onclick]",
            "[role='button']",
            ".btn",
            ".button"
        ]
        
        clickable_elements = []
        for css_selector in clickable_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, css_selector)
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        clickable_elements.append(element)
            except Exception as e:
                logger.debug(f"Error finding clickable elements with {css_selector}: {e}")
        
        return clickable_elements
    
    def find_form_elements(self, timeout: Optional[int] = None) -> List[Any]:
        """Find all form input elements on the page.
        
        Args:
            timeout: Optional timeout override
            
        Returns:
            List of form WebElements
        """
        form_selectors = [
            "input",
            "textarea", 
            "select",
            "[contenteditable='true']"
        ]
        
        form_elements = []
        for css_selector in form_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, css_selector)
                for element in elements:
                    if element.is_displayed():
                        form_elements.append(element)
            except Exception as e:
                logger.debug(f"Error finding form elements with {css_selector}: {e}")
        
        return form_elements
    
    def find_by_smart_text(self, text: str, element_types: Optional[List[str]] = None,
                          timeout: Optional[int] = None) -> Optional[Any]:
        """Find element by text content with smart matching.
        
        Args:
            text: Text to search for
            element_types: Optional list of element types to search in
            timeout: Optional timeout override
            
        Returns:
            WebElement if found, None otherwise
        """
        element_types = element_types or ["button", "a", "span", "div", "p", "h1", "h2", "h3", "h4", "h5", "h6"]
        
        # Try exact text match first
        for tag in element_types:
            xpath = f"//{tag}[text()='{text}']"
            try:
                element = WebDriverWait(self.driver, 2).until(
                    EC.presence_of_element_located((By.XPATH, xpath))
                )
                if element.is_displayed():
                    return element
            except TimeoutException:
                continue
        
        # Try partial text match
        for tag in element_types:
            xpath = f"//{tag}[contains(text(), '{text}')]"
            try:
                element = WebDriverWait(self.driver, 2).until(
                    EC.presence_of_element_located((By.XPATH, xpath))
                )
                if element.is_displayed():
                    return element
            except TimeoutException:
                continue
        
        # Try case-insensitive match
        text_lower = text.lower()
        for tag in element_types:
            xpath = f"//{tag}[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{text_lower}')]"
            try:
                element = WebDriverWait(self.driver, 2).until(
                    EC.presence_of_element_located((By.XPATH, xpath))
                )
                if element.is_displayed():
                    return element
            except TimeoutException:
                continue
        
        return None
    
    def wait_for_element_to_disappear(self, selector: ElementSelector, 
                                    timeout: Optional[int] = None) -> bool:
        """Wait for an element to disappear from the page.
        
        Args:
            selector: ElementSelector to wait for disappearance
            timeout: Optional timeout override
            
        Returns:
            True if element disappeared, False if timeout
        """
        wait_time = timeout or self.default_timeout
        selenium_selectors = selector.get_selenium_selectors()
        
        if not selenium_selectors:
            return False
        
        # Use the first available selector
        by, selector_string = selenium_selectors[0]
        
        try:
            WebDriverWait(self.driver, wait_time).until_not(
                EC.presence_of_element_located((by, selector_string))
            )
            return True
        except TimeoutException:
            return False
    
    def _find_by_fuzzy_text(self, text: str, timeout: int) -> Optional[Any]:
        """Find element by fuzzy text matching.
        
        Args:
            text: Text to search for
            timeout: Timeout in seconds
            
        Returns:
            WebElement if found, None otherwise
        """
        try:
            # Get all elements with text content
            all_elements = self.driver.find_elements(By.XPATH, "//*[text()]")
            
            text_lower = text.lower().strip()
            
            for element in all_elements:
                try:
                    element_text = element.text.lower().strip()
                    
                    # Exact match
                    if element_text == text_lower:
                        return element
                    
                    # Contains match
                    if text_lower in element_text:
                        return element
                    
                    # Word boundary match
                    words = text_lower.split()
                    if all(word in element_text for word in words):
                        return element
                        
                except StaleElementReferenceException:
                    continue
                except Exception:
                    continue
            
        except Exception as e:
            logger.debug(f"Error in fuzzy text search: {e}")
        
        return None
    
    def create_selector_from_element(self, element: Any) -> ElementSelector:
        """Create an ElementSelector from an existing WebElement.
        
        Args:
            element: Selenium WebElement
            
        Returns:
            ElementSelector that can be used to find the element again
        """
        try:
            # Get element attributes
            tag_name = element.tag_name
            element_id = element.get_attribute("id")
            class_name = element.get_attribute("class")
            name_attr = element.get_attribute("name")
            text_content = element.text
            
            # Build attributes dictionary
            attributes = {}
            for attr in ["type", "value", "placeholder", "title", "alt"]:
                attr_value = element.get_attribute(attr)
                if attr_value:
                    attributes[attr] = attr_value
            
            # Create selector with multiple strategies
            return ElementSelector(
                id_attr=element_id,
                class_name=class_name.split()[0] if class_name else None,  # Use first class
                tag_name=tag_name,
                name_attr=name_attr,
                text_content=text_content if text_content and len(text_content) < 50 else None,
                attributes=attributes
            )
            
        except Exception as e:
            logger.error(f"Error creating selector from element: {e}")
            return ElementSelector(tag_name="*")  # Fallback selector