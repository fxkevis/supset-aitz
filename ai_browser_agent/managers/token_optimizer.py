"""Token optimizer for managing AI model token constraints."""

import re
import math
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from loguru import logger

from ..models.page_content import PageContent, WebElement


@dataclass
class TokenBudget:
    """Represents token allocation for different content types."""
    total_tokens: int
    text_content: int
    elements: int
    metadata: int
    context: int
    
    def validate(self) -> bool:
        """Validate that budget allocation doesn't exceed total."""
        allocated = self.text_content + self.elements + self.metadata + self.context
        return allocated <= self.total_tokens


class TokenOptimizer:
    """Optimizes content to fit within AI model token constraints."""
    
    def __init__(self, max_tokens: int = 4000):
        """Initialize the token optimizer.
        
        Args:
            max_tokens: Maximum number of tokens allowed
        """
        self.max_tokens = max_tokens
        self.chars_per_token = 4  # Rough estimate: 1 token ≈ 4 characters
        self.element_base_tokens = 20  # Base tokens per element description
        
        # Priority weights for different content types
        self.content_priorities = {
            'interactive_elements': 1.0,
            'form_elements': 0.9,
            'navigation_elements': 0.8,
            'text_content': 0.7,
            'metadata': 0.5,
            'static_elements': 0.3
        }
    
    def optimize_content(self, extracted_content: Dict[str, Any],
                        task_context: str,
                        preserve_elements: bool = True) -> Dict[str, Any]:
        """Optimize extracted content to fit within token limits.
        
        Args:
            extracted_content: Content extracted by ContentExtractor
            task_context: Current task description
            preserve_elements: Whether to prioritize element preservation
            
        Returns:
            Optimized content dictionary
        """
        try:
            # Calculate current token usage
            current_tokens = self._estimate_tokens(extracted_content)
            
            if current_tokens <= self.max_tokens:
                logger.info(f"Content already within token limit: {current_tokens}/{self.max_tokens}")
                return extracted_content
            
            logger.info(f"Optimizing content: {current_tokens} -> {self.max_tokens} tokens")
            
            # Create token budget
            budget = self._create_token_budget(task_context, preserve_elements)
            
            # Optimize each content type
            optimized_content = {
                'text_content': self._optimize_text_content(
                    extracted_content.get('text_content', ''),
                    budget.text_content,
                    task_context
                ),
                'elements': self._optimize_elements(
                    extracted_content.get('elements', []),
                    budget.elements,
                    task_context
                ),
                'metadata': self._optimize_metadata(
                    extracted_content.get('extraction_metadata', {}),
                    budget.metadata
                ),
                'task_type': extracted_content.get('task_type', 'general'),
                'optimization_applied': True,
                'token_budget': {
                    'allocated': budget.total_tokens,
                    'text_tokens': budget.text_content,
                    'element_tokens': budget.elements,
                    'metadata_tokens': budget.metadata
                }
            }
            
            # Verify final token count
            final_tokens = self._estimate_tokens(optimized_content)
            logger.info(f"Content optimized: {final_tokens}/{self.max_tokens} tokens used")
            
            return optimized_content
            
        except Exception as e:
            logger.error(f"Error optimizing content: {e}")
            # Return minimal fallback content
            return {
                'text_content': extracted_content.get('text_content', '')[:500],
                'elements': extracted_content.get('elements', [])[:10],
                'metadata': {'error': str(e)},
                'task_type': extracted_content.get('task_type', 'general'),
                'optimization_applied': True
            }
    
    def optimize_for_context_window(self, content_parts: List[Dict[str, Any]],
                                  context_description: str) -> List[Dict[str, Any]]:
        """Optimize multiple content parts to fit in context window.
        
        Args:
            content_parts: List of content dictionaries to optimize
            context_description: Description of the context/conversation
            
        Returns:
            List of optimized content parts
        """
        try:
            # Calculate total current tokens
            total_tokens = sum(self._estimate_tokens(part) for part in content_parts)
            
            if total_tokens <= self.max_tokens:
                return content_parts
            
            # Calculate reduction ratio
            reduction_ratio = self.max_tokens / total_tokens
            
            optimized_parts = []
            for part in content_parts:
                part_tokens = self._estimate_tokens(part)
                target_tokens = int(part_tokens * reduction_ratio)
                
                # Create mini-budget for this part
                mini_budget = TokenBudget(
                    total_tokens=target_tokens,
                    text_content=int(target_tokens * 0.4),
                    elements=int(target_tokens * 0.4),
                    metadata=int(target_tokens * 0.1),
                    context=int(target_tokens * 0.1)
                )
                
                optimized_part = {
                    'text_content': self._optimize_text_content(
                        part.get('text_content', ''),
                        mini_budget.text_content,
                        context_description
                    ),
                    'elements': self._optimize_elements(
                        part.get('elements', []),
                        mini_budget.elements,
                        context_description
                    ),
                    'metadata': self._optimize_metadata(
                        part.get('metadata', {}),
                        mini_budget.metadata
                    )
                }
                
                optimized_parts.append(optimized_part)
            
            return optimized_parts
            
        except Exception as e:
            logger.error(f"Error optimizing context window: {e}")
            return content_parts[:1]  # Return only first part as fallback
    
    def prioritize_elements(self, elements: List[WebElement],
                          task_context: str,
                          max_elements: int = 50) -> List[WebElement]:
        """Prioritize elements based on task relevance and importance.
        
        Args:
            elements: List of WebElement objects
            task_context: Current task description
            max_elements: Maximum number of elements to return
            
        Returns:
            Prioritized list of elements
        """
        try:
            # Calculate priority scores for each element
            scored_elements = []
            task_keywords = self._extract_keywords(task_context)
            
            for element in elements:
                score = self._calculate_element_priority(element, task_keywords, task_context)
                scored_elements.append((element, score))
            
            # Sort by score (descending) and take top elements
            scored_elements.sort(key=lambda x: x[1], reverse=True)
            prioritized = [elem for elem, score in scored_elements[:max_elements]]
            
            logger.info(f"Prioritized {len(prioritized)} elements from {len(elements)} total")
            return prioritized
            
        except Exception as e:
            logger.error(f"Error prioritizing elements: {e}")
            return elements[:max_elements]
    
    def create_content_summary(self, content: str, max_tokens: int,
                             preserve_keywords: List[str] = None) -> str:
        """Create a summary of content that fits within token limit.
        
        Args:
            content: Original content text
            max_tokens: Maximum tokens for summary
            preserve_keywords: Keywords that must be preserved in summary
            
        Returns:
            Summarized content
        """
        try:
            max_chars = max_tokens * self.chars_per_token
            
            if len(content) <= max_chars:
                return content
            
            # Split content into sentences
            sentences = re.split(r'[.!?]+', content)
            sentences = [s.strip() for s in sentences if s.strip()]
            
            if not sentences:
                return content[:max_chars]
            
            # Score sentences by importance
            scored_sentences = []
            preserve_keywords = preserve_keywords or []
            
            for sentence in sentences:
                score = self._calculate_sentence_importance(sentence, preserve_keywords)
                scored_sentences.append((sentence, score))
            
            # Sort by importance and build summary
            scored_sentences.sort(key=lambda x: x[1], reverse=True)
            
            summary = ""
            for sentence, score in scored_sentences:
                if len(summary) + len(sentence) + 2 <= max_chars:  # +2 for ". "
                    summary += sentence + ". "
                else:
                    break
            
            # If summary is too short, add more content
            if len(summary) < max_chars * 0.5:
                remaining_chars = max_chars - len(summary)
                additional_content = content[len(summary):len(summary) + remaining_chars]
                summary += additional_content
            
            return summary.strip()
            
        except Exception as e:
            logger.error(f"Error creating content summary: {e}")
            return content[:max_tokens * self.chars_per_token]
    
    def _estimate_tokens(self, content: Dict[str, Any]) -> int:
        """Estimate token count for content dictionary.
        
        Args:
            content: Content dictionary
            
        Returns:
            Estimated token count
        """
        total_tokens = 0
        
        # Text content tokens
        text_content = content.get('text_content', '')
        if isinstance(text_content, str):
            total_tokens += len(text_content) // self.chars_per_token
        
        # Element tokens
        elements = content.get('elements', [])
        if isinstance(elements, list):
            for element in elements:
                total_tokens += self._estimate_element_tokens(element)
        
        # Metadata tokens
        metadata = content.get('metadata', {})
        if isinstance(metadata, dict):
            metadata_str = str(metadata)
            total_tokens += len(metadata_str) // self.chars_per_token
        
        return total_tokens
    
    def _estimate_element_tokens(self, element: WebElement) -> int:
        """Estimate tokens for a single element.
        
        Args:
            element: WebElement object
            
        Returns:
            Estimated token count
        """
        # Base tokens for element structure
        tokens = self.element_base_tokens
        
        # Add tokens for text content
        if element.text_content:
            tokens += len(element.text_content) // self.chars_per_token
        
        # Add tokens for attributes
        for key, value in element.attributes.items():
            tokens += len(f"{key}={value}") // self.chars_per_token
        
        return tokens
    
    def _create_token_budget(self, task_context: str, preserve_elements: bool) -> TokenBudget:
        """Create token budget allocation.
        
        Args:
            task_context: Current task description
            preserve_elements: Whether to prioritize elements
            
        Returns:
            TokenBudget object
        """
        if preserve_elements:
            # Prioritize elements for interactive tasks
            return TokenBudget(
                total_tokens=self.max_tokens,
                text_content=int(self.max_tokens * 0.3),
                elements=int(self.max_tokens * 0.5),
                metadata=int(self.max_tokens * 0.1),
                context=int(self.max_tokens * 0.1)
            )
        else:
            # Prioritize text content for reading tasks
            return TokenBudget(
                total_tokens=self.max_tokens,
                text_content=int(self.max_tokens * 0.6),
                elements=int(self.max_tokens * 0.25),
                metadata=int(self.max_tokens * 0.1),
                context=int(self.max_tokens * 0.05)
            )
    
    def _optimize_text_content(self, text_content: str, token_budget: int,
                             task_context: str) -> str:
        """Optimize text content to fit within token budget.
        
        Args:
            text_content: Original text content
            token_budget: Available tokens for text
            task_context: Current task description
            
        Returns:
            Optimized text content
        """
        if not text_content:
            return ""
        
        max_chars = token_budget * self.chars_per_token
        
        if len(text_content) <= max_chars:
            return text_content
        
        # Extract keywords from task context
        task_keywords = self._extract_keywords(task_context)
        
        # Create summary preserving task-relevant content
        return self.create_content_summary(text_content, token_budget, task_keywords)
    
    def _optimize_elements(self, elements: List[WebElement], token_budget: int,
                         task_context: str) -> List[WebElement]:
        """Optimize elements list to fit within token budget.
        
        Args:
            elements: List of WebElement objects
            token_budget: Available tokens for elements
            task_context: Current task description
            
        Returns:
            Optimized list of elements
        """
        if not elements:
            return []
        
        # Calculate how many elements we can fit
        avg_tokens_per_element = token_budget // len(elements) if elements else 0
        
        if avg_tokens_per_element < 10:  # Minimum viable element description
            # Need to reduce number of elements
            max_elements = max(1, token_budget // 15)  # 15 tokens per element minimum
            return self.prioritize_elements(elements, task_context, max_elements)
        
        # All elements can fit, but may need to simplify them
        optimized_elements = []
        remaining_tokens = token_budget
        
        # Prioritize elements first
        prioritized_elements = self.prioritize_elements(elements, task_context, len(elements))
        
        for element in prioritized_elements:
            element_tokens = self._estimate_element_tokens(element)
            
            if element_tokens <= remaining_tokens:
                optimized_elements.append(element)
                remaining_tokens -= element_tokens
            elif remaining_tokens > 10:  # Can fit a simplified version
                simplified_element = self._simplify_element(element, remaining_tokens)
                optimized_elements.append(simplified_element)
                break
            else:
                break
        
        return optimized_elements
    
    def _optimize_metadata(self, metadata: Dict[str, Any], token_budget: int) -> Dict[str, Any]:
        """Optimize metadata to fit within token budget.
        
        Args:
            metadata: Original metadata dictionary
            token_budget: Available tokens for metadata
            
        Returns:
            Optimized metadata dictionary
        """
        if not metadata:
            return {}
        
        # Keep only essential metadata fields
        essential_fields = [
            'task_type', 'page_url', 'filtered_elements_count',
            'content_length', 'error'
        ]
        
        optimized_metadata = {}
        for field in essential_fields:
            if field in metadata:
                optimized_metadata[field] = metadata[field]
        
        # Check if we're within budget
        metadata_str = str(optimized_metadata)
        if len(metadata_str) // self.chars_per_token <= token_budget:
            return optimized_metadata
        
        # Further reduce if needed
        minimal_metadata = {
            'task_type': metadata.get('task_type', 'general'),
            'elements_count': metadata.get('filtered_elements_count', 0)
        }
        
        return minimal_metadata
    
    def _calculate_element_priority(self, element: WebElement, task_keywords: List[str],
                                  task_context: str) -> float:
        """Calculate priority score for an element.
        
        Args:
            element: WebElement object
            task_keywords: Keywords from task context
            task_context: Full task description
            
        Returns:
            Priority score (higher = more important)
        """
        score = 0.0
        
        # Base score by element type
        if element.is_clickable:
            score += 10.0
        if element.tag_name.lower() in ['button', 'input', 'a']:
            score += 8.0
        elif element.tag_name.lower() in ['select', 'textarea']:
            score += 6.0
        elif element.tag_name.lower() in ['div', 'span']:
            score += 2.0
        
        # Visibility and interaction state
        if element.is_visible:
            score += 5.0
        if element.is_enabled:
            score += 3.0
        
        # Keyword matching
        element_text = (element.text_content + ' ' + 
                       ' '.join(element.attributes.values())).lower()
        
        keyword_matches = sum(1 for keyword in task_keywords if keyword in element_text)
        score += keyword_matches * 4.0
        
        # Special attribute bonuses
        if element.attributes.get('type') in ['submit', 'button']:
            score += 3.0
        if element.attributes.get('role') == 'button':
            score += 2.0
        if element.attributes.get('id'):
            score += 1.0
        
        # Text content quality
        if element.text_content and len(element.text_content.strip()) > 0:
            score += 2.0
        
        return score
    
    def _calculate_sentence_importance(self, sentence: str, 
                                     preserve_keywords: List[str]) -> float:
        """Calculate importance score for a sentence.
        
        Args:
            sentence: Sentence text
            preserve_keywords: Keywords to preserve
            
        Returns:
            Importance score
        """
        score = 0.0
        sentence_lower = sentence.lower()
        
        # Keyword matching
        for keyword in preserve_keywords:
            if keyword.lower() in sentence_lower:
                score += 2.0
        
        # Sentence length (prefer medium-length sentences)
        length = len(sentence.split())
        if 5 <= length <= 20:
            score += 1.0
        elif length > 20:
            score -= 0.5
        
        # Question sentences are often important
        if sentence.strip().endswith('?'):
            score += 1.0
        
        # Sentences with numbers or specific details
        if re.search(r'\d+', sentence):
            score += 0.5
        
        return score
    
    def _simplify_element(self, element: WebElement, max_tokens: int) -> WebElement:
        """Create a simplified version of an element.
        
        Args:
            element: Original WebElement
            max_tokens: Maximum tokens allowed
            
        Returns:
            Simplified WebElement
        """
        # Keep essential attributes only
        essential_attrs = {}
        for attr in ['id', 'class', 'type', 'name', 'href']:
            if attr in element.attributes:
                essential_attrs[attr] = element.attributes[attr]
        
        # Truncate text content if needed
        max_text_chars = (max_tokens - 10) * self.chars_per_token  # Reserve 10 tokens for structure
        text_content = element.text_content
        if len(text_content) > max_text_chars:
            text_content = text_content[:max_text_chars] + "..."
        
        return WebElement(
            tag_name=element.tag_name,
            attributes=essential_attrs,
            text_content=text_content,
            css_selector=element.css_selector,
            xpath="",  # Remove xpath to save space
            is_visible=element.is_visible,
            is_enabled=element.is_enabled,
            is_clickable=element.is_clickable,
            bounding_box=None  # Remove bounding box to save space
        )
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text.
        
        Args:
            text: Input text
            
        Returns:
            List of keywords
        """
        # Simple keyword extraction
        words = re.findall(r'\b\w+\b', text.lower())
        
        # Filter out common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during',
            'before', 'after', 'above', 'below', 'between', 'among', 'this', 'that',
            'these', 'those', 'i', 'me', 'my', 'we', 'our', 'you', 'your', 'he',
            'him', 'his', 'she', 'her', 'it', 'its', 'they', 'them', 'their'
        }
        
        keywords = [word for word in words if len(word) > 2 and word not in stop_words]
        return keywords[:10]  # Return top 10 keywords