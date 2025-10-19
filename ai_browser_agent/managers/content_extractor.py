"""Content extractor for extracting task-relevant content from web pages."""

import re
from typing import Dict, List, Optional, Any, Set
from bs4 import BeautifulSoup, Tag, NavigableString
from loguru import logger

from ..models.page_content import PageContent, WebElement
from ..models.task import Task


class ContentExtractor:
    """Extracts task-relevant content from web pages using intelligent filtering."""
    
    def __init__(self):
        """Initialize the content extractor."""
        self.task_keywords: Set[str] = set()
        self.content_filters = {
            'email': self._email_content_filter,
            'shopping': self._shopping_content_filter,
            'form': self._form_content_filter,
            'navigation': self._navigation_content_filter,
            'general': self._general_content_filter
        }
    
    def extract_relevant_content(self, page_content: PageContent, 
                               task_context: str,
                               task_type: Optional[str] = None) -> Dict[str, Any]:
        """Extract content relevant to the given task context.
        
        Args:
            page_content: PageContent object containing full page data
            task_context: Description of the current task
            task_type: Optional task type hint (email, shopping, etc.)
            
        Returns:
            Dictionary with extracted relevant content
        """
        try:
            # Parse task context to extract keywords
            self.task_keywords = self._extract_task_keywords(task_context)
            
            # Determine task type if not provided
            if not task_type:
                task_type = self._infer_task_type(task_context, page_content)
            
            # Apply appropriate content filter
            filter_func = self.content_filters.get(task_type, self._general_content_filter)
            relevant_content = filter_func(page_content, task_context)
            
            # Add metadata
            relevant_content['extraction_metadata'] = {
                'task_type': task_type,
                'task_keywords': list(self.task_keywords),
                'original_elements_count': len(page_content.elements),
                'filtered_elements_count': len(relevant_content.get('elements', [])),
                'content_length': len(relevant_content.get('text_content', '')),
                'page_url': page_content.url
            }
            
            logger.info(f"Extracted relevant content for task type '{task_type}': "
                       f"{len(relevant_content.get('elements', []))} elements, "
                       f"{len(relevant_content.get('text_content', ''))} chars")
            
            return relevant_content
            
        except Exception as e:
            logger.error(f"Error extracting relevant content: {e}")
            return {
                'text_content': page_content.text_content[:1000],  # Fallback
                'elements': page_content.elements[:20],  # Fallback
                'extraction_metadata': {'error': str(e)}
            }
    
    def extract_actionable_elements(self, page_content: PageContent,
                                  task_context: str) -> List[WebElement]:
        """Extract elements that are actionable for the given task.
        
        Args:
            page_content: PageContent object
            task_context: Task description
            
        Returns:
            List of actionable WebElement objects
        """
        actionable_elements = []
        task_keywords = self._extract_task_keywords(task_context)
        
        try:
            for element in page_content.elements:
                if self._is_element_actionable(element, task_keywords):
                    actionable_elements.append(element)
            
            # Sort by relevance score
            actionable_elements.sort(
                key=lambda e: self._calculate_element_relevance(e, task_keywords),
                reverse=True
            )
            
            return actionable_elements
            
        except Exception as e:
            logger.error(f"Error extracting actionable elements: {e}")
            return []
    
    def extract_text_by_relevance(self, page_content: PageContent,
                                task_context: str,
                                max_length: int = 2000) -> str:
        """Extract text content prioritized by relevance to task.
        
        Args:
            page_content: PageContent object
            task_context: Task description
            max_length: Maximum length of extracted text
            
        Returns:
            Relevant text content
        """
        try:
            # Parse HTML to get structured text
            soup = BeautifulSoup(page_content.html_content, 'html.parser')
            
            # Remove irrelevant sections
            for tag in soup(['script', 'style', 'nav', 'footer', 'aside']):
                tag.decompose()
            
            # Extract text from relevant sections
            relevant_sections = []
            task_keywords = self._extract_task_keywords(task_context)
            
            # Prioritize sections with task-relevant content
            for tag in soup.find_all(['main', 'article', 'section', 'div', 'p', 'h1', 'h2', 'h3']):
                text = tag.get_text(strip=True)
                if text and self._text_contains_keywords(text, task_keywords):
                    relevance_score = self._calculate_text_relevance(text, task_keywords)
                    relevant_sections.append((text, relevance_score))
            
            # Sort by relevance and combine
            relevant_sections.sort(key=lambda x: x[1], reverse=True)
            
            combined_text = ""
            for text, _ in relevant_sections:
                if len(combined_text) + len(text) <= max_length:
                    combined_text += text + "\n"
                else:
                    # Add partial text if it fits
                    remaining_space = max_length - len(combined_text)
                    if remaining_space > 100:  # Only add if meaningful space left
                        combined_text += text[:remaining_space] + "..."
                    break
            
            return combined_text.strip()
            
        except Exception as e:
            logger.error(f"Error extracting relevant text: {e}")
            # Fallback to truncated original text
            return page_content.text_content[:max_length]
    
    def _extract_task_keywords(self, task_context: str) -> Set[str]:
        """Extract keywords from task context.
        
        Args:
            task_context: Task description
            
        Returns:
            Set of relevant keywords
        """
        # Convert to lowercase and split
        words = re.findall(r'\b\w+\b', task_context.lower())
        
        # Filter out common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during',
            'before', 'after', 'above', 'below', 'between', 'among', 'this', 'that',
            'these', 'those', 'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves',
            'you', 'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 'himself',
            'she', 'her', 'hers', 'herself', 'it', 'its', 'itself', 'they', 'them', 'their',
            'theirs', 'themselves', 'what', 'which', 'who', 'whom', 'whose', 'this', 'that',
            'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'will', 'would',
            'could', 'should', 'may', 'might', 'must', 'can', 'shall'
        }
        
        keywords = {word for word in words if len(word) > 2 and word not in stop_words}
        
        # Add domain-specific keywords based on task type
        if any(word in task_context.lower() for word in ['email', 'mail', 'inbox']):
            keywords.update(['email', 'mail', 'inbox', 'message', 'send', 'reply', 'delete'])
        
        if any(word in task_context.lower() for word in ['buy', 'order', 'purchase', 'shop']):
            keywords.update(['buy', 'order', 'purchase', 'cart', 'checkout', 'price', 'product'])
        
        if any(word in task_context.lower() for word in ['login', 'sign', 'account']):
            keywords.update(['login', 'signin', 'account', 'password', 'username'])
        
        return keywords
    
    def _infer_task_type(self, task_context: str, page_content: PageContent) -> str:
        """Infer the task type from context and page content.
        
        Args:
            task_context: Task description
            page_content: Current page content
            
        Returns:
            Inferred task type
        """
        task_lower = task_context.lower()
        page_type = page_content.metadata.get('page_type', 'general')
        
        # Check task context keywords
        if any(word in task_lower for word in ['email', 'mail', 'inbox', 'spam']):
            return 'email'
        
        if any(word in task_lower for word in ['buy', 'order', 'purchase', 'shop', 'cart']):
            return 'shopping'
        
        if any(word in task_lower for word in ['fill', 'form', 'submit', 'register']):
            return 'form'
        
        if any(word in task_lower for word in ['navigate', 'go to', 'find', 'search']):
            return 'navigation'
        
        # Use page type as fallback
        if page_type in ['ecommerce', 'login', 'form']:
            return page_type
        
        return 'general'
    
    def _email_content_filter(self, page_content: PageContent, 
                            task_context: str) -> Dict[str, Any]:
        """Filter content for email-related tasks."""
        relevant_elements = []
        
        # Look for email-specific elements
        email_selectors = [
            'input[type="email"]', 'input[name*="email"]', 'input[id*="email"]',
            'button[type="submit"]', 'a[href*="mailto"]',
            '.email', '.message', '.inbox', '.compose'
        ]
        
        for element in page_content.elements:
            if (element.tag_name.lower() in ['input', 'button', 'a', 'div', 'span'] and
                self._element_matches_email_context(element, task_context)):
                relevant_elements.append(element)
        
        # Extract email-relevant text
        relevant_text = self._extract_email_text(page_content.html_content, task_context)
        
        return {
            'text_content': relevant_text,
            'elements': relevant_elements,
            'task_type': 'email'
        }
    
    def _shopping_content_filter(self, page_content: PageContent,
                               task_context: str) -> Dict[str, Any]:
        """Filter content for shopping-related tasks."""
        relevant_elements = []
        
        # Look for shopping-specific elements
        for element in page_content.elements:
            if self._element_matches_shopping_context(element, task_context):
                relevant_elements.append(element)
        
        # Extract shopping-relevant text
        relevant_text = self._extract_shopping_text(page_content.html_content, task_context)
        
        return {
            'text_content': relevant_text,
            'elements': relevant_elements,
            'task_type': 'shopping'
        }
    
    def _form_content_filter(self, page_content: PageContent,
                           task_context: str) -> Dict[str, Any]:
        """Filter content for form-related tasks."""
        relevant_elements = []
        
        # Prioritize form elements
        for element in page_content.elements:
            if (element.tag_name.lower() in ['input', 'textarea', 'select', 'button', 'form'] or
                element.is_clickable):
                relevant_elements.append(element)
        
        # Extract form-relevant text (labels, instructions)
        relevant_text = self._extract_form_text(page_content.html_content)
        
        return {
            'text_content': relevant_text,
            'elements': relevant_elements,
            'task_type': 'form'
        }
    
    def _navigation_content_filter(self, page_content: PageContent,
                                 task_context: str) -> Dict[str, Any]:
        """Filter content for navigation-related tasks."""
        relevant_elements = []
        
        # Focus on navigation elements
        for element in page_content.elements:
            if (element.tag_name.lower() in ['a', 'button'] or
                element.is_clickable or
                'nav' in element.css_selector.lower()):
                relevant_elements.append(element)
        
        # Extract navigation-relevant text
        relevant_text = self._extract_navigation_text(page_content.html_content, task_context)
        
        return {
            'text_content': relevant_text,
            'elements': relevant_elements,
            'task_type': 'navigation'
        }
    
    def _general_content_filter(self, page_content: PageContent,
                              task_context: str) -> Dict[str, Any]:
        """General content filter for unspecified tasks."""
        # Include all interactive elements and relevant text
        relevant_elements = [
            element for element in page_content.elements
            if element.is_clickable or element.tag_name.lower() in ['input', 'button', 'a', 'select']
        ]
        
        # Extract text based on task keywords
        relevant_text = self.extract_text_by_relevance(page_content, task_context, 1500)
        
        return {
            'text_content': relevant_text,
            'elements': relevant_elements,
            'task_type': 'general'
        }
    
    def _is_element_actionable(self, element: WebElement, task_keywords: Set[str]) -> bool:
        """Check if an element is actionable for the given task."""
        # Must be visible and enabled
        if not element.is_visible or not element.is_enabled:
            return False
        
        # Interactive elements are generally actionable
        if element.is_clickable or element.tag_name.lower() in ['input', 'button', 'select', 'textarea']:
            return True
        
        # Check if element text/attributes contain task keywords
        element_text = (element.text_content + ' ' + 
                       ' '.join(element.attributes.values())).lower()
        
        return any(keyword in element_text for keyword in task_keywords)
    
    def _calculate_element_relevance(self, element: WebElement, task_keywords: Set[str]) -> float:
        """Calculate relevance score for an element."""
        score = 0.0
        
        # Base score for interactive elements
        if element.is_clickable:
            score += 1.0
        if element.tag_name.lower() in ['button', 'input', 'a']:
            score += 0.5
        
        # Keyword matching in text and attributes
        element_text = (element.text_content + ' ' + 
                       ' '.join(element.attributes.values())).lower()
        
        keyword_matches = sum(1 for keyword in task_keywords if keyword in element_text)
        score += keyword_matches * 0.3
        
        # Bonus for specific attributes
        if element.attributes.get('type') in ['submit', 'button']:
            score += 0.2
        if element.attributes.get('role') == 'button':
            score += 0.2
        
        return score
    
    def _text_contains_keywords(self, text: str, keywords: Set[str]) -> bool:
        """Check if text contains any of the keywords."""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in keywords)
    
    def _calculate_text_relevance(self, text: str, keywords: Set[str]) -> float:
        """Calculate relevance score for text content."""
        text_lower = text.lower()
        score = 0.0
        
        for keyword in keywords:
            count = text_lower.count(keyword)
            score += count * (len(keyword) / 10.0)  # Longer keywords get higher weight
        
        # Normalize by text length
        if len(text) > 0:
            score = score / (len(text) / 100.0)
        
        return score
    
    def _element_matches_email_context(self, element: WebElement, task_context: str) -> bool:
        """Check if element is relevant for email tasks."""
        email_indicators = [
            'email', 'mail', 'inbox', 'compose', 'send', 'reply', 'delete',
            'message', 'subject', 'recipient', 'attachment'
        ]
        
        element_text = (element.text_content + ' ' + 
                       ' '.join(element.attributes.values())).lower()
        
        return any(indicator in element_text for indicator in email_indicators)
    
    def _element_matches_shopping_context(self, element: WebElement, task_context: str) -> bool:
        """Check if element is relevant for shopping tasks."""
        shopping_indicators = [
            'buy', 'purchase', 'cart', 'checkout', 'order', 'price', 'product',
            'add to cart', 'quantity', 'size', 'color', 'shipping', 'payment'
        ]
        
        element_text = (element.text_content + ' ' + 
                       ' '.join(element.attributes.values())).lower()
        
        return any(indicator in element_text for indicator in shopping_indicators)
    
    def _extract_email_text(self, html_content: str, task_context: str) -> str:
        """Extract email-relevant text from HTML."""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove irrelevant sections
        for tag in soup(['script', 'style', 'nav', 'footer']):
            tag.decompose()
        
        # Look for email-specific sections
        email_sections = soup.find_all(['div', 'section', 'main'], 
                                     class_=re.compile(r'(email|mail|inbox|message)', re.I))
        
        if email_sections:
            return ' '.join(section.get_text(strip=True) for section in email_sections)
        
        # Fallback to general text extraction
        return soup.get_text(strip=True)[:1000]
    
    def _extract_shopping_text(self, html_content: str, task_context: str) -> str:
        """Extract shopping-relevant text from HTML."""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove irrelevant sections
        for tag in soup(['script', 'style', 'nav', 'footer']):
            tag.decompose()
        
        # Look for shopping-specific sections
        shopping_sections = soup.find_all(['div', 'section', 'main'], 
                                        class_=re.compile(r'(product|cart|shop|order)', re.I))
        
        if shopping_sections:
            return ' '.join(section.get_text(strip=True) for section in shopping_sections)
        
        return soup.get_text(strip=True)[:1000]
    
    def _extract_form_text(self, html_content: str) -> str:
        """Extract form-relevant text from HTML."""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Focus on labels, form instructions, and error messages
        relevant_tags = soup.find_all(['label', 'legend', 'fieldset', 'form'])
        form_text = ' '.join(tag.get_text(strip=True) for tag in relevant_tags)
        
        # Also include text near form elements
        input_elements = soup.find_all(['input', 'textarea', 'select'])
        for input_elem in input_elements:
            # Get surrounding text
            parent = input_elem.parent
            if parent:
                form_text += ' ' + parent.get_text(strip=True)
        
        return form_text[:1000]
    
    def _extract_navigation_text(self, html_content: str, task_context: str) -> str:
        """Extract navigation-relevant text from HTML."""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Focus on navigation elements and links
        nav_elements = soup.find_all(['nav', 'menu', 'a'])
        nav_text = ' '.join(elem.get_text(strip=True) for elem in nav_elements)
        
        # Include headings and main content areas
        content_elements = soup.find_all(['h1', 'h2', 'h3', 'main', 'article'])
        content_text = ' '.join(elem.get_text(strip=True) for elem in content_elements)
        
        return (nav_text + ' ' + content_text)[:1000]