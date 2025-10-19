"""Context manager for handling AI model token limitations and content optimization."""

from typing import Dict, List, Optional, Any
from loguru import logger

from ..models.page_content import PageContent, WebElement
from ..models.task import Task
from .content_extractor import ContentExtractor
from .token_optimizer import TokenOptimizer


class ContextManager:
    """Manages context and content optimization for AI model interactions."""
    
    def __init__(self, max_tokens: int = 4000):
        """Initialize the context manager.
        
        Args:
            max_tokens: Maximum tokens allowed for AI model input
        """
        self.max_tokens = max_tokens
        self.content_extractor = ContentExtractor()
        self.token_optimizer = TokenOptimizer(max_tokens)
        
        # Context history for maintaining conversation state
        self.context_history: List[Dict[str, Any]] = []
        self.current_task_context = ""
    
    def process_page_content(self, page_content: PageContent,
                           task_context: str,
                           task_type: Optional[str] = None,
                           preserve_elements: bool = True) -> Dict[str, Any]:
        """Process page content for AI model consumption.
        
        Args:
            page_content: PageContent object from browser
            task_context: Current task description
            task_type: Optional task type hint
            preserve_elements: Whether to prioritize element preservation
            
        Returns:
            Optimized content dictionary ready for AI model
        """
        try:
            logger.info(f"Processing page content for task: {task_context[:100]}...")
            
            # Extract relevant content
            relevant_content = self.content_extractor.extract_relevant_content(
                page_content, task_context, task_type
            )
            
            # Optimize for token constraints
            optimized_content = self.token_optimizer.optimize_content(
                relevant_content, task_context, preserve_elements
            )
            
            # Add context metadata
            optimized_content['context_metadata'] = {
                'page_url': page_content.url,
                'page_title': page_content.title,
                'task_context': task_context,
                'processing_timestamp': page_content.extracted_at.isoformat(),
                'token_limit': self.max_tokens
            }
            
            # Update context history
            self._update_context_history(optimized_content, task_context)
            
            logger.info(f"Page content processed successfully. "
                       f"Elements: {len(optimized_content.get('elements', []))}, "
                       f"Text length: {len(optimized_content.get('text_content', ''))}")
            
            return optimized_content
            
        except Exception as e:
            logger.error(f"Error processing page content: {e}")
            return self._create_fallback_content(page_content, task_context)
    
    def extract_relevant_content(self, page_content: PageContent, 
                               task_context: str) -> str:
        """Extract task-relevant content from web page.
        
        Args:
            page_content: PageContent object
            task_context: Task description
            
        Returns:
            Relevant content string optimized for AI processing
        """
        try:
            # Use content extractor to get relevant text
            relevant_text = self.content_extractor.extract_text_by_relevance(
                page_content, task_context, max_length=2000
            )
            
            # Further optimize if needed
            if len(relevant_text) > self.max_tokens * self.token_optimizer.chars_per_token:
                relevant_text = self.token_optimizer.create_content_summary(
                    relevant_text, 
                    self.max_tokens // 2,  # Reserve half tokens for other content
                    self.token_optimizer._extract_keywords(task_context)
                )
            
            return relevant_text
            
        except Exception as e:
            logger.error(f"Error extracting relevant content: {e}")
            return page_content.text_content[:1000]  # Fallback
    
    def prioritize_elements(self, elements: List[WebElement],
                          task_context: str,
                          max_elements: int = 50) -> List[WebElement]:
        """Prioritize page elements based on task relevance.
        
        Args:
            elements: List of WebElement objects
            task_context: Current task description
            max_elements: Maximum number of elements to return
            
        Returns:
            Prioritized list of elements
        """
        return self.token_optimizer.prioritize_elements(
            elements, task_context, max_elements
        )
    
    def optimize_for_tokens(self, content: str, max_tokens: int) -> str:
        """Optimize content string to fit within token limit.
        
        Args:
            content: Original content string
            max_tokens: Maximum tokens allowed
            
        Returns:
            Optimized content string
        """
        return self.token_optimizer.create_content_summary(content, max_tokens)
    
    def get_actionable_elements(self, page_content: PageContent,
                              task_context: str) -> List[WebElement]:
        """Get elements that are actionable for the current task.
        
        Args:
            page_content: PageContent object
            task_context: Task description
            
        Returns:
            List of actionable elements
        """
        return self.content_extractor.extract_actionable_elements(
            page_content, task_context
        )
    
    def maintain_context_across_pages(self, new_content: Dict[str, Any],
                                    task_context: str) -> Dict[str, Any]:
        """Maintain context information across multiple page interactions.
        
        Args:
            new_content: New page content to process
            task_context: Current task description
            
        Returns:
            Content with maintained context
        """
        try:
            # Combine with relevant history
            if self.context_history:
                # Get the most recent relevant context
                recent_context = self._get_relevant_history(task_context, max_items=2)
                
                # Merge contexts while staying within token limits
                combined_content = self._merge_contexts(
                    new_content, recent_context, task_context
                )
                
                return combined_content
            
            return new_content
            
        except Exception as e:
            logger.error(f"Error maintaining context: {e}")
            return new_content
    
    def create_task_summary(self, task: Task, 
                          page_contents: List[PageContent]) -> str:
        """Create a summary of task progress across multiple pages.
        
        Args:
            task: Task object
            page_contents: List of PageContent objects from task execution
            
        Returns:
            Task summary string
        """
        try:
            summary_parts = [
                f"Task: {task.description}",
                f"Status: {task.status.value}",
                f"Pages visited: {len(page_contents)}"
            ]
            
            # Add key information from each page
            for i, page_content in enumerate(page_contents[-3:]):  # Last 3 pages
                page_summary = f"Page {i+1}: {page_content.title} ({page_content.url})"
                
                # Extract key actions or findings
                key_elements = self.prioritize_elements(
                    page_content.elements, task.description, 5
                )
                
                if key_elements:
                    element_summary = ", ".join([
                        f"{elem.tag_name}({elem.text_content[:20]}...)" 
                        for elem in key_elements[:3]
                    ])
                    page_summary += f" - Key elements: {element_summary}"
                
                summary_parts.append(page_summary)
            
            # Optimize summary length
            full_summary = "\n".join(summary_parts)
            return self.optimize_for_tokens(full_summary, 500)  # 500 token limit for summary
            
        except Exception as e:
            logger.error(f"Error creating task summary: {e}")
            return f"Task: {task.description} (Status: {task.status.value})"
    
    def reset_context(self):
        """Reset the context history."""
        self.context_history.clear()
        self.current_task_context = ""
        logger.info("Context history reset")
    
    def get_context_stats(self) -> Dict[str, Any]:
        """Get statistics about current context usage.
        
        Returns:
            Dictionary with context statistics
        """
        total_history_items = len(self.context_history)
        
        if self.context_history:
            latest_content = self.context_history[-1]
            latest_tokens = self.token_optimizer._estimate_tokens(latest_content)
        else:
            latest_tokens = 0
        
        return {
            'max_tokens': self.max_tokens,
            'history_items': total_history_items,
            'latest_content_tokens': latest_tokens,
            'current_task': self.current_task_context[:100] if self.current_task_context else None
        }
    
    def _update_context_history(self, content: Dict[str, Any], task_context: str):
        """Update the context history with new content.
        
        Args:
            content: Processed content dictionary
            task_context: Current task context
        """
        # Add timestamp and task context
        history_item = {
            **content,
            'task_context': task_context,
            'timestamp': content.get('context_metadata', {}).get('processing_timestamp')
        }
        
        self.context_history.append(history_item)
        self.current_task_context = task_context
        
        # Keep only recent history to prevent memory bloat
        max_history_items = 10
        if len(self.context_history) > max_history_items:
            self.context_history = self.context_history[-max_history_items:]
    
    def _get_relevant_history(self, task_context: str, max_items: int = 3) -> List[Dict[str, Any]]:
        """Get relevant items from context history.
        
        Args:
            task_context: Current task context
            max_items: Maximum number of history items to return
            
        Returns:
            List of relevant history items
        """
        if not self.context_history:
            return []
        
        # Score history items by relevance to current task
        scored_items = []
        task_keywords = set(self.token_optimizer._extract_keywords(task_context))
        
        for item in self.context_history:
            item_task = item.get('task_context', '')
            item_keywords = set(self.token_optimizer._extract_keywords(item_task))
            
            # Calculate keyword overlap
            overlap = len(task_keywords.intersection(item_keywords))
            relevance_score = overlap / max(len(task_keywords), 1)
            
            scored_items.append((item, relevance_score))
        
        # Sort by relevance and recency (recent items get slight boost)
        scored_items.sort(key=lambda x: x[1] + (0.1 if x == scored_items[-1] else 0), reverse=True)
        
        return [item for item, score in scored_items[:max_items]]
    
    def _merge_contexts(self, new_content: Dict[str, Any],
                       history_items: List[Dict[str, Any]],
                       task_context: str) -> Dict[str, Any]:
        """Merge new content with relevant history items.
        
        Args:
            new_content: New content to process
            history_items: Relevant history items
            task_context: Current task context
            
        Returns:
            Merged content dictionary
        """
        try:
            # Start with new content
            merged_content = new_content.copy()
            
            # Add context from history
            if history_items:
                context_text_parts = [new_content.get('text_content', '')]
                
                for item in history_items:
                    item_text = item.get('text_content', '')
                    if item_text:
                        # Add a brief summary of the historical context
                        context_summary = f"Previous page context: {item_text[:200]}..."
                        context_text_parts.append(context_summary)
                
                # Combine and optimize
                combined_text = "\n\n".join(context_text_parts)
                optimized_text = self.token_optimizer.create_content_summary(
                    combined_text,
                    self.max_tokens // 2,  # Reserve half tokens for elements
                    self.token_optimizer._extract_keywords(task_context)
                )
                
                merged_content['text_content'] = optimized_text
                merged_content['has_context_history'] = True
                merged_content['context_items_used'] = len(history_items)
            
            return merged_content
            
        except Exception as e:
            logger.error(f"Error merging contexts: {e}")
            return new_content
    
    def _create_fallback_content(self, page_content: PageContent, 
                               task_context: str) -> Dict[str, Any]:
        """Create minimal fallback content when processing fails.
        
        Args:
            page_content: Original page content
            task_context: Task context
            
        Returns:
            Minimal content dictionary
        """
        return {
            'text_content': page_content.text_content[:500],
            'elements': page_content.elements[:10],
            'metadata': {
                'page_url': page_content.url,
                'page_title': page_content.title,
                'fallback_used': True
            },
            'task_type': 'general',
            'context_metadata': {
                'page_url': page_content.url,
                'task_context': task_context,
                'token_limit': self.max_tokens,
                'error': 'Fallback content used due to processing error'
            }
        }