"""Page analyzer for extracting and analyzing web page content."""

import re
import time
from typing import Dict, List, Optional, Any, Set
from urllib.parse import urljoin, urlparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import StaleElementReferenceException, WebDriverException
from bs4 import BeautifulSoup
from loguru import logger

from ..models.page_content import PageContent, WebElement


class PageAnalyzer:
    """Analyzes web pages to extract structured content and metadata."""
    
    def __init__(self, driver: webdriver.Chrome):
        """Initialize the page analyzer.
        
        Args:
            driver: Selenium WebDriver instance
        """
        self.driver = driver
        self.current_url = ""
        self.page_title = ""
    
    def analyze_page(self, extract_all_elements: bool = False,
                    include_hidden: bool = False,
                    max_elements: int = 1000) -> PageContent:
        """Analyze the current page and extract structured content.
        
        Args:
            extract_all_elements: Whether to extract all elements or just important ones
            include_hidden: Whether to include hidden elements
            max_elements: Maximum number of elements to extract
            
        Returns:
            PageContent object with extracted data
        """
        try:
            # Get basic page information
            self.current_url = self.driver.current_url
            self.page_title = self.driver.title
            
            # Get page source and create BeautifulSoup object
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Extract text content
            text_content = self._extract_text_content(soup)
            
            # Extract elements
            elements = self._extract_elements(
                extract_all=extract_all_elements,
                include_hidden=include_hidden,
                max_elements=max_elements
            )
            
            # Extract metadata
            metadata = self._extract_metadata(soup)
            
            # Create PageContent object
            page_content = PageContent(
                url=self.current_url,
                title=self.page_title,
                text_content=text_content,
                html_content=page_source,
                elements=elements,
                metadata=metadata
            )
            
            logger.info(f"Analyzed page: {self.page_title} ({len(elements)} elements)")
            return page_content
            
        except Exception as e:
            logger.error(f"Error analyzing page: {e}")
            # Return minimal page content on error
            return PageContent(
                url=self.current_url or "unknown",
                title=self.page_title or "Error",
                text_content="",
                elements=[],
                metadata={"error": str(e)}
            )
    
    def extract_forms(self) -> List[Dict[str, Any]]:
        """Extract all forms and their input fields.
        
        Returns:
            List of form dictionaries with field information
        """
        forms = []
        
        try:
            form_elements = self.driver.find_elements(By.TAG_NAME, "form")
            
            for i, form in enumerate(form_elements):
                try:
                    form_data = {
                        "index": i,
                        "action": form.get_attribute("action") or "",
                        "method": form.get_attribute("method") or "GET",
                        "id": form.get_attribute("id") or "",
                        "class": form.get_attribute("class") or "",
                        "fields": []
                    }
                    
                    # Find all input fields in the form
                    input_selectors = [
                        "input", "textarea", "select", "button"
                    ]
                    
                    for selector in input_selectors:
                        fields = form.find_elements(By.TAG_NAME, selector)
                        for field in fields:
                            field_data = self._extract_field_data(field)
                            if field_data:
                                form_data["fields"].append(field_data)
                    
                    forms.append(form_data)
                    
                except StaleElementReferenceException:
                    continue
                except Exception as e:
                    logger.debug(f"Error extracting form {i}: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Error extracting forms: {e}")
        
        return forms
    
    def extract_links(self, internal_only: bool = False) -> List[Dict[str, str]]:
        """Extract all links from the page.
        
        Args:
            internal_only: Whether to include only internal links
            
        Returns:
            List of link dictionaries
        """
        links = []
        
        try:
            link_elements = self.driver.find_elements(By.TAG_NAME, "a")
            current_domain = urlparse(self.current_url).netloc
            
            for link in link_elements:
                try:
                    href = link.get_attribute("href")
                    text = link.text.strip()
                    title = link.get_attribute("title") or ""
                    
                    if not href:
                        continue
                    
                    # Convert relative URLs to absolute
                    absolute_url = urljoin(self.current_url, href)
                    
                    # Filter internal links if requested
                    if internal_only:
                        link_domain = urlparse(absolute_url).netloc
                        if link_domain != current_domain:
                            continue
                    
                    links.append({
                        "url": absolute_url,
                        "text": text,
                        "title": title,
                        "is_external": urlparse(absolute_url).netloc != current_domain
                    })
                    
                except StaleElementReferenceException:
                    continue
                except Exception as e:
                    logger.debug(f"Error extracting link: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Error extracting links: {e}")
        
        return links
    
    def extract_images(self) -> List[Dict[str, str]]:
        """Extract all images from the page.
        
        Returns:
            List of image dictionaries
        """
        images = []
        
        try:
            img_elements = self.driver.find_elements(By.TAG_NAME, "img")
            
            for img in img_elements:
                try:
                    src = img.get_attribute("src")
                    alt = img.get_attribute("alt") or ""
                    title = img.get_attribute("title") or ""
                    
                    if src:
                        # Convert relative URLs to absolute
                        absolute_src = urljoin(self.current_url, src)
                        
                        images.append({
                            "src": absolute_src,
                            "alt": alt,
                            "title": title,
                            "width": img.get_attribute("width") or "",
                            "height": img.get_attribute("height") or ""
                        })
                        
                except StaleElementReferenceException:
                    continue
                except Exception as e:
                    logger.debug(f"Error extracting image: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Error extracting images: {e}")
        
        return images
    
    def detect_page_type(self) -> str:
        """Detect the type of page based on content and structure.
        
        Returns:
            String indicating page type (e.g., 'login', 'search', 'product', 'article')
        """
        try:
            page_source = self.driver.page_source.lower()
            
            # Check for login page indicators
            login_indicators = [
                'type="password"', 'login', 'sign in', 'username', 'email'
            ]
            if any(indicator in page_source for indicator in login_indicators):
                return "login"
            
            # Check for search page indicators
            search_indicators = [
                'type="search"', 'search results', 'query', 'search for'
            ]
            if any(indicator in page_source for indicator in search_indicators):
                return "search"
            
            # Check for e-commerce indicators
            ecommerce_indicators = [
                'add to cart', 'buy now', 'price', '$', 'checkout', 'product'
            ]
            if any(indicator in page_source for indicator in ecommerce_indicators):
                return "ecommerce"
            
            # Check for article/blog indicators
            article_indicators = [
                '<article', 'published', 'author', 'blog', 'post'
            ]
            if any(indicator in page_source for indicator in article_indicators):
                return "article"
            
            # Check for form page indicators
            form_elements = self.driver.find_elements(By.TAG_NAME, "form")
            if len(form_elements) > 0:
                return "form"
            
            return "general"
            
        except Exception as e:
            logger.error(f"Error detecting page type: {e}")
            return "unknown"
    
    def find_main_content_area(self) -> Optional[Any]:
        """Find the main content area of the page.
        
        Returns:
            WebElement representing the main content area, or None
        """
        try:
            # Try semantic HTML5 elements first
            main_selectors = [
                "main",
                "[role='main']",
                "#main",
                "#content",
                ".main",
                ".content",
                "article",
                ".post-content",
                ".entry-content"
            ]
            
            for selector in main_selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if element.is_displayed():
                        return element
                except:
                    continue
            
            # Fallback: find the largest content div
            content_divs = self.driver.find_elements(By.TAG_NAME, "div")
            largest_div = None
            largest_size = 0
            
            for div in content_divs:
                try:
                    if div.is_displayed():
                        size = div.size
                        area = size['width'] * size['height']
                        if area > largest_size:
                            largest_size = area
                            largest_div = div
                except:
                    continue
            
            return largest_div
            
        except Exception as e:
            logger.error(f"Error finding main content area: {e}")
            return None
    
    def _extract_text_content(self, soup: BeautifulSoup) -> str:
        """Extract clean text content from the page.
        
        Args:
            soup: BeautifulSoup object of the page
            
        Returns:
            Clean text content
        """
        try:
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # Get text content
            text = soup.get_text()
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            return text
            
        except Exception as e:
            logger.error(f"Error extracting text content: {e}")
            return ""
    
    def _extract_elements(self, extract_all: bool = False, 
                         include_hidden: bool = False,
                         max_elements: int = 1000) -> List[WebElement]:
        """Extract web elements from the page.
        
        Args:
            extract_all: Whether to extract all elements
            include_hidden: Whether to include hidden elements
            max_elements: Maximum number of elements to extract
            
        Returns:
            List of WebElement objects
        """
        elements = []
        
        try:
            if extract_all:
                # Extract all elements
                all_elements = self.driver.find_elements(By.XPATH, "//*")
            else:
                # Extract only interactive and important elements
                important_selectors = [
                    "a", "button", "input", "textarea", "select", 
                    "h1", "h2", "h3", "h4", "h5", "h6",
                    "form", "img", "[onclick]", "[role='button']"
                ]
                all_elements = []
                for selector in important_selectors:
                    try:
                        found_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        all_elements.extend(found_elements)
                    except:
                        continue
            
            # Process elements
            processed_count = 0
            for element in all_elements:
                if processed_count >= max_elements:
                    break
                
                try:
                    # Skip hidden elements if not requested
                    if not include_hidden and not element.is_displayed():
                        continue
                    
                    web_element = self._create_web_element(element)
                    if web_element:
                        elements.append(web_element)
                        processed_count += 1
                        
                except StaleElementReferenceException:
                    continue
                except Exception as e:
                    logger.debug(f"Error processing element: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Error extracting elements: {e}")
        
        return elements
    
    def _create_web_element(self, element: Any) -> Optional[WebElement]:
        """Create a WebElement object from a Selenium element.
        
        Args:
            element: Selenium WebElement
            
        Returns:
            WebElement object or None if creation fails
        """
        try:
            # Get basic properties
            tag_name = element.tag_name
            text_content = element.text
            
            # Get attributes
            attributes = {}
            common_attrs = [
                "id", "class", "name", "type", "value", "href", "src", 
                "alt", "title", "placeholder", "role", "onclick"
            ]
            
            for attr in common_attrs:
                attr_value = element.get_attribute(attr)
                if attr_value:
                    attributes[attr] = attr_value
            
            # Get element state
            is_visible = element.is_displayed()
            is_enabled = element.is_enabled()
            
            # Determine if clickable
            is_clickable = (
                tag_name.lower() in ["a", "button"] or
                attributes.get("type") in ["button", "submit"] or
                "onclick" in attributes or
                attributes.get("role") == "button"
            )
            
            # Get bounding box
            try:
                location = element.location
                size = element.size
                bounding_box = {
                    "x": location["x"],
                    "y": location["y"],
                    "width": size["width"],
                    "height": size["height"]
                }
            except:
                bounding_box = None
            
            # Generate selectors
            css_selector = self._generate_css_selector(element, attributes)
            xpath = self._generate_xpath(element)
            
            return WebElement(
                tag_name=tag_name,
                attributes=attributes,
                text_content=text_content,
                css_selector=css_selector,
                xpath=xpath,
                is_visible=is_visible,
                is_enabled=is_enabled,
                is_clickable=is_clickable,
                bounding_box=bounding_box
            )
            
        except Exception as e:
            logger.debug(f"Error creating WebElement: {e}")
            return None
    
    def _generate_css_selector(self, element: Any, attributes: Dict[str, str]) -> str:
        """Generate a CSS selector for the element.
        
        Args:
            element: Selenium WebElement
            attributes: Element attributes
            
        Returns:
            CSS selector string
        """
        try:
            # Use ID if available (most specific)
            if attributes.get("id"):
                return f"#{attributes['id']}"
            
            # Use class if available
            if attributes.get("class"):
                classes = attributes["class"].split()
                if classes:
                    return f".{classes[0]}"
            
            # Use tag name with attributes
            tag_name = element.tag_name
            selector = tag_name
            
            # Add type attribute for inputs
            if attributes.get("type"):
                selector += f"[type='{attributes['type']}']"
            
            # Add name attribute
            if attributes.get("name"):
                selector += f"[name='{attributes['name']}']"
            
            return selector
            
        except Exception:
            return element.tag_name
    
    def _generate_xpath(self, element: Any) -> str:
        """Generate an XPath for the element.
        
        Args:
            element: Selenium WebElement
            
        Returns:
            XPath string
        """
        try:
            # This is a simplified XPath generation
            # In practice, you might want a more sophisticated approach
            return f"//{element.tag_name}"
        except Exception:
            return "//*"
    
    def _extract_metadata(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract page metadata.
        
        Args:
            soup: BeautifulSoup object of the page
            
        Returns:
            Dictionary with metadata
        """
        metadata = {}
        
        try:
            # Extract meta tags
            meta_tags = soup.find_all("meta")
            for meta in meta_tags:
                name = meta.get("name") or meta.get("property")
                content = meta.get("content")
                if name and content:
                    metadata[name] = content
            
            # Extract page language
            html_tag = soup.find("html")
            if html_tag:
                lang = html_tag.get("lang")
                if lang:
                    metadata["language"] = lang
            
            # Count elements
            metadata["element_counts"] = {
                "links": len(soup.find_all("a")),
                "images": len(soup.find_all("img")),
                "forms": len(soup.find_all("form")),
                "buttons": len(soup.find_all("button")),
                "inputs": len(soup.find_all("input"))
            }
            
            # Page type detection
            metadata["page_type"] = self.detect_page_type()
            
        except Exception as e:
            logger.error(f"Error extracting metadata: {e}")
            metadata["error"] = str(e)
        
        return metadata
    
    def _extract_field_data(self, field: Any) -> Optional[Dict[str, Any]]:
        """Extract data from a form field element.
        
        Args:
            field: Selenium WebElement representing a form field
            
        Returns:
            Dictionary with field data or None
        """
        try:
            field_data = {
                "tag": field.tag_name,
                "type": field.get_attribute("type") or "",
                "name": field.get_attribute("name") or "",
                "id": field.get_attribute("id") or "",
                "placeholder": field.get_attribute("placeholder") or "",
                "value": field.get_attribute("value") or "",
                "required": field.get_attribute("required") is not None,
                "disabled": not field.is_enabled(),
                "visible": field.is_displayed()
            }
            
            # Add options for select elements
            if field.tag_name.lower() == "select":
                options = []
                option_elements = field.find_elements(By.TAG_NAME, "option")
                for option in option_elements:
                    options.append({
                        "value": option.get_attribute("value") or "",
                        "text": option.text
                    })
                field_data["options"] = options
            
            return field_data
            
        except Exception as e:
            logger.debug(f"Error extracting field data: {e}")
            return None