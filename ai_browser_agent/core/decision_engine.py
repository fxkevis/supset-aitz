"""Decision engine for autonomous AI decision-making."""

import json
import logging
import uuid
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from ..interfaces.ai_model_interface import ModelInterface, ModelRequest, ModelResponse
from ..interfaces.model_factory import ModelFactory
from ..models.action import Action, ActionType
from ..models.task import Task, TaskStep, ExecutionPlan
from ..models.page_content import PageContent, WebElement
from ..models.config import AIModelConfig, SecurityConfig


logger = logging.getLogger(__name__)


class DecisionEngine:
    """Engine for making autonomous decisions based on web page content and task context."""
    
    def __init__(self, model_factory: ModelFactory, security_config: SecurityConfig):
        self.model_factory = model_factory
        self.security_config = security_config
        self.current_model: Optional[ModelInterface] = None
        self.decision_history: List[Dict[str, Any]] = []
        
        # Decision-making prompts and templates
        self.system_prompt = self._build_system_prompt()
        
    def _build_system_prompt(self) -> str:
        """Build the system prompt for AI decision-making."""
        return """You are an AI browser automation agent. Your role is to analyze web page content and make decisions about what actions to take to complete user tasks.

Key principles:
1. Always prioritize user safety and avoid destructive actions without confirmation
2. Be precise in element selection - use specific selectors when possible
3. Provide confidence scores for your decisions (0.0 to 1.0)
4. Consider the current task context when making decisions
5. If uncertain, request user input rather than guessing

When analyzing a page, consider:
- The current task objective
- Available interactive elements (buttons, links, forms)
- Page content and structure
- Previous actions taken
- Potential risks or destructive actions

Respond with structured JSON containing your decision and reasoning."""
    
    async def analyze_page_and_decide(self, page_content: PageContent, task: Task, 
                                    context: Dict[str, Any]) -> List[Action]:
        """Analyze page content and decide on the next actions to take."""
        try:
            # Get the current AI model
            if not self.current_model:
                self.current_model = await self.model_factory.get_best_available_model()
                if not self.current_model:
                    raise Exception("No AI model available for decision-making")
            
            # Build the analysis prompt
            analysis_prompt = self._build_analysis_prompt(page_content, task, context)
            
            # Create model request
            request = ModelRequest(
                prompt=analysis_prompt,
                system_message=self.system_prompt,
                max_tokens=2000,
                temperature=0.3  # Lower temperature for more consistent decisions
            )
            
            # Get AI response
            response = await self.current_model.generate_response(request)
            
            # Parse the response into actions
            actions = self._parse_ai_response(response, page_content, task)
            
            # Apply security validation
            validated_actions = self._validate_actions_security(actions, page_content.url)
            
            # Log the decision
            self._log_decision(page_content, task, context, validated_actions, response)
            
            return validated_actions
            
        except Exception as e:
            logger.error(f"Error in decision-making: {e}")
            # Return a safe fallback action
            return [self._create_fallback_action(str(e))]
    
    def _build_analysis_prompt(self, page_content: PageContent, task: Task, 
                             context: Dict[str, Any]) -> str:
        """Build the prompt for AI analysis of the current situation."""
        # Extract relevant page information
        page_summary = self._extract_page_summary(page_content)
        
        # Build context information
        context_info = self._build_context_info(task, context)
        
        prompt = f"""
CURRENT TASK: {task.description}
TASK STATUS: {task.status.value}

PAGE ANALYSIS:
{page_summary}

CONTEXT:
{context_info}

INSTRUCTIONS:
Analyze the current page and determine the next action(s) to take to progress toward completing the task.

Consider:
1. What elements are available for interaction?
2. What action would best advance the task?
3. Are there any risks or destructive actions to avoid?
4. What is your confidence level in this decision?

Respond with a JSON array of actions in this format:
[
  {{
    "action_type": "click|type|navigate|scroll|wait|extract|submit|select",
    "target": "CSS selector or URL",
    "parameters": {{"key": "value"}},
    "description": "Clear description of what this action does",
    "confidence": 0.85,
    "is_destructive": false,
    "reasoning": "Why this action was chosen"
  }}
]

If you're uncertain or need more information, include an action with type "request_input" and describe what information you need.
"""
        
        return prompt
    
    def _extract_page_summary(self, page_content: PageContent) -> str:
        """Extract a concise summary of the page for AI analysis."""
        summary_parts = []
        
        # Basic page info
        summary_parts.append(f"URL: {page_content.url}")
        summary_parts.append(f"Title: {page_content.title}")
        
        # Element counts
        element_counts = page_content.get_element_count_by_tag()
        summary_parts.append(f"Elements: {dict(list(element_counts.items())[:10])}")  # Top 10 element types
        
        # Interactive elements
        clickable_elements = page_content.find_clickable_elements()
        if clickable_elements:
            summary_parts.append(f"Clickable elements: {len(clickable_elements)}")
            # Include details of first few clickable elements
            for i, elem in enumerate(clickable_elements[:5]):
                elem_desc = f"  {elem.tag_name}"
                if elem.text_content:
                    elem_desc += f" '{elem.text_content[:50]}'"
                if elem.css_selector:
                    elem_desc += f" ({elem.css_selector})"
                summary_parts.append(elem_desc)
        
        # Form elements
        form_elements = page_content.find_form_elements()
        if form_elements:
            summary_parts.append(f"Form elements: {len(form_elements)}")
            for i, elem in enumerate(form_elements[:3]):
                elem_desc = f"  {elem.tag_name}"
                if elem.get_attribute("type"):
                    elem_desc += f" type='{elem.get_attribute('type')}'"
                if elem.get_attribute("name"):
                    elem_desc += f" name='{elem.get_attribute('name')}'"
                summary_parts.append(elem_desc)
        
        # Links
        links = page_content.get_links()
        if links:
            summary_parts.append(f"Links: {len(links)}")
            for i, link in enumerate(links[:3]):
                link_desc = f"  '{link.text_content[:30]}' -> {link.href}"
                summary_parts.append(link_desc)
        
        # Page text preview
        if page_content.text_content:
            text_preview = page_content.text_content[:300].replace('\n', ' ')
            summary_parts.append(f"Text preview: {text_preview}...")
        
        return "\n".join(summary_parts)
    
    def _build_context_info(self, task: Task, context: Dict[str, Any]) -> str:
        """Build context information for the AI."""
        context_parts = []
        
        # Task progress
        if task.execution_plan:
            progress = task.get_progress_percentage()
            context_parts.append(f"Task progress: {progress:.1f}%")
            
            current_step = task.execution_plan.current_step
            if current_step:
                context_parts.append(f"Current step: {current_step.description}")
        
        # Previous actions
        if "previous_actions" in context:
            prev_actions = context["previous_actions"][-3:]  # Last 3 actions
            context_parts.append("Recent actions:")
            for action in prev_actions:
                context_parts.append(f"  - {action.get('type', 'unknown')}: {action.get('description', 'N/A')}")
        
        # User preferences or constraints
        if "user_preferences" in context:
            context_parts.append(f"User preferences: {context['user_preferences']}")
        
        # Current session info
        if "session_info" in context:
            session = context["session_info"]
            if "logged_in" in session:
                context_parts.append(f"Logged in: {session['logged_in']}")
            if "current_domain" in session:
                context_parts.append(f"Domain: {session['current_domain']}")
        
        return "\n".join(context_parts) if context_parts else "No additional context available"
    
    def _parse_ai_response(self, response: ModelResponse, page_content: PageContent, 
                          task: Task) -> List[Action]:
        """Parse AI response into Action objects."""
        actions = []
        
        try:
            # Try to parse JSON response
            response_data = json.loads(response.content.strip())
            
            # Handle both single action and array of actions
            if isinstance(response_data, dict):
                response_data = [response_data]
            
            for action_data in response_data:
                action = self._create_action_from_data(action_data, response.confidence)
                if action and action.validate():
                    actions.append(action)
                else:
                    logger.warning(f"Invalid action data: {action_data}")
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            # Try to extract action from natural language response
            action = self._extract_action_from_text(response.content, response.confidence)
            if action:
                actions.append(action)
        
        # If no valid actions were parsed, create a fallback
        if not actions:
            actions.append(self._create_fallback_action("Could not parse AI response"))
        
        return actions
    
    def _create_action_from_data(self, action_data: Dict[str, Any], base_confidence: float) -> Optional[Action]:
        """Create an Action object from parsed data."""
        try:
            action_type_str = action_data.get("action_type", "").lower()
            
            # Map action type string to enum
            action_type_map = {
                "click": ActionType.CLICK,
                "type": ActionType.TYPE,
                "navigate": ActionType.NAVIGATE,
                "scroll": ActionType.SCROLL,
                "wait": ActionType.WAIT,
                "extract": ActionType.EXTRACT,
                "submit": ActionType.SUBMIT,
                "select": ActionType.SELECT,
                "hover": ActionType.HOVER,
                "screenshot": ActionType.SCREENSHOT,
                "refresh": ActionType.REFRESH,
                "back": ActionType.BACK,
                "forward": ActionType.FORWARD
            }
            
            if action_type_str not in action_type_map:
                logger.warning(f"Unknown action type: {action_type_str}")
                return None
            
            action_type = action_type_map[action_type_str]
            
            # Calculate final confidence
            ai_confidence = action_data.get("confidence", base_confidence)
            final_confidence = min(ai_confidence, base_confidence)
            
            # Determine if action is destructive
            is_destructive = action_data.get("is_destructive", False)
            if not is_destructive:
                # Additional checks for destructive actions
                description = action_data.get("description", "").lower()
                target = action_data.get("target", "").lower()
                is_destructive = self.security_config.is_destructive_action(description) or \
                               any(word in target for word in ["delete", "remove", "cancel"])
            
            action = Action(
                id=str(uuid.uuid4()),
                type=action_type,
                target=action_data.get("target", ""),
                parameters=action_data.get("parameters", {}),
                is_destructive=is_destructive,
                confidence=final_confidence,
                description=action_data.get("description", "")
            )
            
            return action
            
        except Exception as e:
            logger.error(f"Error creating action from data: {e}")
            return None
    
    def _extract_action_from_text(self, text: str, confidence: float) -> Optional[Action]:
        """Extract action from natural language text as fallback."""
        # This is a simplified fallback - in practice, you might use NLP
        text_lower = text.lower()
        
        if "click" in text_lower:
            return Action(
                id=str(uuid.uuid4()),
                type=ActionType.CLICK,
                target="",  # Would need to extract from text
                confidence=confidence * 0.5,  # Lower confidence for text extraction
                description=f"Extracted from text: {text[:100]}"
            )
        elif "type" in text_lower or "enter" in text_lower:
            return Action(
                id=str(uuid.uuid4()),
                type=ActionType.TYPE,
                target="",
                confidence=confidence * 0.5,
                description=f"Extracted from text: {text[:100]}"
            )
        
        return None
    
    def _validate_actions_security(self, actions: List[Action], current_url: str) -> List[Action]:
        """Apply security validation to actions."""
        validated_actions = []
        
        for action in actions:
            # Check if action requires confirmation
            requires_confirmation = self.security_config.requires_confirmation(
                action.type.value,
                current_url,
                action.description
            )
            
            if requires_confirmation:
                action.is_destructive = True
            
            # Additional security checks
            if self.security_config.is_sensitive_domain(current_url):
                # Reduce confidence for actions on sensitive domains
                action.confidence *= 0.8
            
            validated_actions.append(action)
        
        return validated_actions
    
    def _create_fallback_action(self, error_message: str) -> Action:
        """Create a safe fallback action when decision-making fails."""
        return Action(
            id=str(uuid.uuid4()),
            type=ActionType.WAIT,
            target="body",
            parameters={"duration": 1},
            confidence=0.1,
            description=f"Fallback action due to error: {error_message}",
            is_destructive=False
        )
    
    def _log_decision(self, page_content: PageContent, task: Task, context: Dict[str, Any],
                     actions: List[Action], ai_response: ModelResponse) -> None:
        """Log the decision-making process for audit and debugging."""
        decision_log = {
            "timestamp": datetime.now().isoformat(),
            "page_url": page_content.url,
            "task_id": task.id,
            "task_description": task.description,
            "ai_model": ai_response.model_name,
            "ai_confidence": ai_response.confidence,
            "tokens_used": ai_response.tokens_used,
            "actions_decided": [
                {
                    "type": action.type.value,
                    "target": action.target,
                    "confidence": action.confidence,
                    "is_destructive": action.is_destructive,
                    "description": action.description
                }
                for action in actions
            ],
            "context_keys": list(context.keys())
        }
        
        self.decision_history.append(decision_log)
        
        # Keep only last 100 decisions to prevent memory issues
        if len(self.decision_history) > 100:
            self.decision_history = self.decision_history[-100:]
        
        logger.info(f"Decision made for task {task.id}: {len(actions)} actions")
    
    async def evaluate_action_success(self, action: Action, result_page: PageContent,
                                    expected_outcome: str) -> Tuple[bool, float, str]:
        """Evaluate whether an action was successful based on the resulting page."""
        try:
            if not self.current_model:
                self.current_model = await self.model_factory.get_best_available_model()
            
            evaluation_prompt = f"""
Evaluate whether this action was successful:

ACTION TAKEN:
Type: {action.type.value}
Target: {action.target}
Description: {action.description}
Expected outcome: {expected_outcome}

RESULTING PAGE:
URL: {result_page.url}
Title: {result_page.title}
Content preview: {result_page.text_content[:500]}

Was the action successful? Respond with JSON:
{{
  "success": true/false,
  "confidence": 0.0-1.0,
  "reasoning": "explanation of why it succeeded or failed"
}}
"""
            
            request = ModelRequest(
                prompt=evaluation_prompt,
                max_tokens=500,
                temperature=0.2
            )
            
            response = await self.current_model.generate_response(request)
            
            try:
                eval_data = json.loads(response.content.strip())
                return (
                    eval_data.get("success", False),
                    eval_data.get("confidence", 0.5),
                    eval_data.get("reasoning", "No reasoning provided")
                )
            except json.JSONDecodeError:
                # Fallback evaluation
                return self._simple_success_evaluation(action, result_page)
                
        except Exception as e:
            logger.error(f"Error evaluating action success: {e}")
            return False, 0.0, f"Evaluation error: {str(e)}"
    
    def _simple_success_evaluation(self, action: Action, result_page: PageContent) -> Tuple[bool, float, str]:
        """Simple heuristic-based success evaluation as fallback."""
        if action.type == ActionType.NAVIGATE:
            # Check if URL changed appropriately
            target_url = action.target
            success = target_url in result_page.url
            return success, 0.7 if success else 0.3, f"URL navigation check"
        
        elif action.type == ActionType.CLICK:
            # Basic check - assume success if page changed or has expected elements
            success = len(result_page.elements) > 0
            return success, 0.6, "Basic page content check"
        
        # Default: assume moderate success
        return True, 0.5, "Default success assumption"
    
    def get_decision_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent decision history."""
        return self.decision_history[-limit:]
    
    def clear_decision_history(self) -> None:
        """Clear the decision history."""
        self.decision_history.clear()
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        if self.model_factory:
            await self.model_factory.cleanup()
        self.current_model = None