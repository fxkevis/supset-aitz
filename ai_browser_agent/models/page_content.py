"""Page content and web element data models."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional


@dataclass
class WebElement:
    """Represents a web element on a page."""
    tag_name: str
    attributes: Dict[str, str] = field(default_factory=dict)
    text_content: str = ""
    inner_html: str = ""
    css_selector: str = ""
    xpath: str = ""
    is_visible: bool = True
    is_enabled: bool = True
    is_clickable: bool = False
    bounding_box: Optional[Dict[str, float]] = None
    
    @property
    def id(self) -> Optional[str]:
        """Get the element ID if available."""
        return self.attributes.get("id")
    
    @property
    def class_name(self) -> Optional[str]:
        """Get the element class name if available."""
        return self.attributes.get("class")
    
    @property
    def href(self) -> Optional[str]:
        """Get the href attribute for links."""
        return self.attributes.get("href")
    
    def has_text(self, text: str) -> bool:
        """Check if element contains specific text."""
        return text.lower() in self.text_content.lower()
    
    def matches_selector(self, selector: str) -> bool:
        """Check if element matches a CSS selector (simplified)."""
        # This is a simplified implementation
        # In practice, this would use proper CSS selector matching
        return selector in self.css_selector
    
    def validate(self) -> bool:
        """Validate the web element data."""
        if not self.tag_name:
            return False
        
        # Validate bounding box if present
        if self.bounding_box:
            required_keys = ["x", "y", "width", "height"]
            if not all(key in self.bounding_box for key in required_keys):
                return False
        
        return True
    
    def get_attribute(self, name: str, default: Optional[str] = None) -> Optional[str]:
        """Get an attribute value with optional default."""
        return self.attributes.get(name, default)
    
    def has_attribute(self, name: str) -> bool:
        """Check if element has a specific attribute."""
        return name in self.attributes


@dataclass
class PageContent:
    """Represents the content of a web page."""
    url: str
    title: str = ""
    text_content: str = ""
    html_content: str = ""
    elements: List[WebElement] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    screenshot_path: Optional[str] = None
    load_time: Optional[float] = None
    extracted_at: datetime = field(default_factory=datetime.now)
    
    def find_elements_by_tag(self, tag_name: str) -> List[WebElement]:
        """Find all elements with a specific tag name."""
        return [elem for elem in self.elements if elem.tag_name.lower() == tag_name.lower()]
    
    def find_elements_by_text(self, text: str) -> List[WebElement]:
        """Find all elements containing specific text."""
        return [elem for elem in self.elements if elem.has_text(text)]
    
    def find_clickable_elements(self) -> List[WebElement]:
        """Find all clickable elements on the page."""
        return [elem for elem in self.elements if elem.is_clickable]
    
    def find_form_elements(self) -> List[WebElement]:
        """Find all form-related elements."""
        form_tags = ["input", "textarea", "select", "button", "form"]
        return [elem for elem in self.elements if elem.tag_name.lower() in form_tags]
    
    def get_links(self) -> List[WebElement]:
        """Get all link elements."""
        return [elem for elem in self.elements if elem.tag_name.lower() == "a" and elem.href]
    
    def get_summary(self, max_length: int = 500) -> str:
        """Get a summary of the page content."""
        summary = f"Page: {self.title}\nURL: {self.url}\n"
        
        if self.text_content:
            content_preview = self.text_content[:max_length]
            if len(self.text_content) > max_length:
                content_preview += "..."
            summary += f"Content: {content_preview}"
        
        summary += f"\nElements: {len(self.elements)} total"
        summary += f"\nClickable: {len(self.find_clickable_elements())}"
        summary += f"\nLinks: {len(self.get_links())}"
        summary += f"\nForms: {len(self.find_form_elements())}"
        
        return summary
    
    def validate(self) -> bool:
        """Validate the page content data."""
        if not self.url:
            return False
        
        # Validate all elements
        for element in self.elements:
            if not element.validate():
                return False
        
        return True
    
    def get_element_count_by_tag(self) -> Dict[str, int]:
        """Get count of elements by tag name."""
        counts = {}
        for element in self.elements:
            tag = element.tag_name.lower()
            counts[tag] = counts.get(tag, 0) + 1
        return counts