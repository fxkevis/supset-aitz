"""Task planning component for creating and managing execution plans."""

import re
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime

from ai_browser_agent.interfaces.base_interfaces import BaseAgent
from ai_browser_agent.interfaces.ai_model_interface import ModelInterface, ModelRequest
from ai_browser_agent.models.task import Task, TaskStep, ExecutionPlan, TaskStatus
from ai_browser_agent.models.action import ActionType


class TaskPlanner(BaseAgent):
    """Plans and manages task execution using AI-powered natural language processing."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, model_interface: Optional[ModelInterface] = None):
        super().__init__(config)
        self.model_interface = model_interface
        self.task_patterns = self._initialize_task_patterns()
        self.fallback_strategies = self._initialize_fallback_strategies()
    
    def initialize(self) -> None:
        """Initialize the task planner."""
        self.is_active = True
    
    def shutdown(self) -> None:
        """Shutdown the task planner."""
        self.is_active = False
    
    async def create_plan(self, task_description: str, context: Optional[Dict[str, Any]] = None) -> ExecutionPlan:
        """Create an execution plan for a task using AI-powered analysis."""
        task_id = str(uuid.uuid4())
        
        # First try pattern-based parsing for common tasks
        steps = self._parse_with_patterns(task_description)
        
        # If pattern-based parsing doesn't yield good results, use AI
        if not steps or len(steps) < 2:
            if self.model_interface:
                steps = await self._parse_with_ai(task_description, context)
            else:
                # Fallback to basic parsing if no AI model available
                steps = self._basic_task_parsing(task_description)
        
        # Generate fallback strategies
        fallback_strategies = self._generate_fallback_strategies(task_description, steps)
        
        execution_plan = ExecutionPlan(
            task_id=task_id,
            steps=steps,
            context=context or {},
            fallback_strategies=fallback_strategies
        )
        
        return execution_plan
    
    async def update_plan(self, execution_plan: ExecutionPlan, current_state: Dict[str, Any]) -> ExecutionPlan:
        """Update execution plan based on current progress and state."""
        if not execution_plan.current_step:
            return execution_plan
        
        # Check if current step failed and needs replanning
        current_step = execution_plan.current_step
        if current_step.error_message:
            # Generate alternative steps for failed action
            alternative_steps = await self._generate_alternative_steps(
                current_step, current_state, execution_plan.context
            )
            
            if alternative_steps:
                # Insert alternative steps after current failed step
                insert_index = execution_plan.current_step_index + 1
                for i, alt_step in enumerate(alternative_steps):
                    execution_plan.steps.insert(insert_index + i, alt_step)
        
        # Update context with current state
        execution_plan.context.update(current_state)
        
        return execution_plan
    
    def _initialize_task_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize common task patterns for quick recognition."""
        return {
            "email_management": {
                "patterns": [
                    r"(?i).*check.*email.*",
                    r"(?i).*delete.*spam.*",
                    r"(?i).*organize.*inbox.*",
                    r"(?i).*read.*email.*"
                ],
                "steps": [
                    {"action": "navigate", "target": "email_service", "description": "Navigate to email service"},
                    {"action": "wait", "target": "page_load", "description": "Wait for page to load"},
                    {"action": "extract", "target": "email_list", "description": "Extract email list"},
                    {"action": "click", "target": "email_item", "description": "Select emails to process"}
                ]
            },
            "online_ordering": {
                "patterns": [
                    r"(?i).*order.*food.*",
                    r"(?i).*buy.*online.*",
                    r"(?i).*purchase.*",
                    r"(?i).*add.*cart.*"
                ],
                "steps": [
                    {"action": "navigate", "target": "shopping_site", "description": "Navigate to shopping website"},
                    {"action": "type", "target": "search_box", "description": "Search for items"},
                    {"action": "click", "target": "product", "description": "Select product"},
                    {"action": "click", "target": "add_to_cart", "description": "Add to cart"},
                    {"action": "navigate", "target": "checkout", "description": "Proceed to checkout"}
                ]
            },
            "web_navigation": {
                "patterns": [
                    r"(?i).*go.*to.*",
                    r"(?i).*visit.*",
                    r"(?i).*navigate.*",
                    r"(?i).*open.*website.*",
                    r"(?i).*open.*",
                    r"(?i).*load.*",
                    r"(?i).*browse.*"
                ],
                "steps": [
                    {"action": "navigate", "target": "url", "description": "Navigate to specified URL"},
                    {"action": "wait", "target": "page_load", "description": "Wait for page to load"},
                    {"action": "extract", "target": "page_content", "description": "Extract page content"}
                ]
            }
        }
    
    def _initialize_fallback_strategies(self) -> Dict[str, List[str]]:
        """Initialize fallback strategies for common failure scenarios."""
        return {
            "element_not_found": [
                "Try alternative selectors (ID, class, xpath)",
                "Wait longer for element to appear",
                "Scroll to make element visible",
                "Refresh page and retry"
            ],
            "page_load_timeout": [
                "Increase wait time",
                "Check network connection",
                "Try alternative URL or route",
                "Refresh and retry"
            ],
            "authentication_required": [
                "Check for login prompts",
                "Use stored credentials if available",
                "Request user authentication",
                "Try alternative access method"
            ],
            "form_submission_failed": [
                "Validate form fields",
                "Check for required fields",
                "Try alternative submission method",
                "Clear and refill form"
            ]
        }
    
    def _parse_with_patterns(self, task_description: str) -> List[TaskStep]:
        """Parse task using predefined patterns."""
        steps = []
        
        for task_type, pattern_data in self.task_patterns.items():
            for pattern in pattern_data["patterns"]:
                if re.match(pattern, task_description):
                    # Convert pattern steps to TaskStep objects
                    for i, step_data in enumerate(pattern_data["steps"]):
                        # Extract actual URL or target from task description
                        target = self._extract_target_from_description(task_description, step_data["target"], task_type)
                        
                        step = TaskStep(
                            id=f"step_{i+1}",
                            description=step_data["description"],
                            action_type=step_data["action"],
                            parameters={"target": target}
                        )
                        steps.append(step)
                    break
            
            if steps:  # Found matching pattern
                break
        
        return steps
    
    def _extract_target_from_description(self, task_description: str, generic_target: str, task_type: str) -> str:
        """Extract specific target from task description."""
        if task_type == "web_navigation" and generic_target == "url":
            # Look for URLs in the description
            url_pattern = r'https?://[^\s]+'
            urls = re.findall(url_pattern, task_description)
            if urls:
                return urls[0]
            
            # Look for domain names like "google.com"
            domain_pattern = r'[a-zA-Z0-9-]+\.[a-zA-Z]{2,}'
            domains = re.findall(domain_pattern, task_description)
            if domains:
                domain = domains[0]
                # Add https:// if not present
                if not domain.startswith(('http://', 'https://')):
                    return f"https://www.{domain}"
                return domain
            
            # Look for common site names
            task_lower = task_description.lower()
            if "google" in task_lower:
                return "https://www.google.com"
            elif "youtube" in task_lower:
                return "https://www.youtube.com"
            elif "facebook" in task_lower:
                return "https://www.facebook.com"
            elif "gmail" in task_lower:
                return "https://mail.google.com"
            elif "github" in task_lower:
                return "https://www.github.com"
            elif "stackoverflow" in task_lower or "stack overflow" in task_lower:
                return "https://stackoverflow.com"
            elif "reddit" in task_lower:
                return "https://www.reddit.com"
            elif "wikipedia" in task_lower:
                return "https://www.wikipedia.org"
            elif "twitter" in task_lower:
                return "https://www.twitter.com"
            elif "linkedin" in task_lower:
                return "https://www.linkedin.com"
        
        return generic_target
    
    async def _parse_with_ai(self, task_description: str, context: Optional[Dict[str, Any]] = None) -> List[TaskStep]:
        """Parse task using AI model for complex natural language understanding."""
        if not self.model_interface:
            return []
        
        system_message = """You are a task planning AI that converts natural language descriptions into step-by-step browser automation plans.

Available actions: navigate, click, type, scroll, wait, extract, submit, select, hover, screenshot, refresh, back, forward

For each step, provide:
1. A clear description
2. The action type
3. Target selector or URL
4. Any parameters needed

Format your response as a JSON array of steps:
[
  {
    "description": "Navigate to Gmail",
    "action_type": "navigate", 
    "target": "https://gmail.com",
    "parameters": {}
  },
  {
    "description": "Wait for page to load",
    "action_type": "wait",
    "target": "body",
    "parameters": {"duration": 3}
  }
]"""
        
        context_str = ""
        if context:
            context_str = f"\nContext: {context}"
        
        prompt = f"Create a step-by-step browser automation plan for: {task_description}{context_str}"
        
        request = ModelRequest(
            prompt=prompt,
            system_message=system_message,
            max_tokens=1000,
            temperature=0.3
        )
        
        try:
            response = await self.model_interface.generate_response(request)
            steps = self._parse_ai_response(response.content)
            return steps
        except Exception as e:
            # Fallback to basic parsing if AI fails
            return self._basic_task_parsing(task_description)
    
    def _parse_ai_response(self, ai_response: str) -> List[TaskStep]:
        """Parse AI response into TaskStep objects."""
        steps = []
        
        try:
            import json
            # Try to extract JSON from response
            json_start = ai_response.find('[')
            json_end = ai_response.rfind(']') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = ai_response[json_start:json_end]
                step_data_list = json.loads(json_str)
                
                for i, step_data in enumerate(step_data_list):
                    step = TaskStep(
                        id=f"ai_step_{i+1}",
                        description=step_data.get("description", ""),
                        action_type=step_data.get("action_type", "wait"),
                        parameters=step_data.get("parameters", {})
                    )
                    # Add target to parameters if provided
                    if "target" in step_data:
                        step.parameters["target"] = step_data["target"]
                    
                    steps.append(step)
        
        except (json.JSONDecodeError, KeyError, IndexError):
            # If JSON parsing fails, try to extract steps from text
            steps = self._extract_steps_from_text(ai_response)
        
        return steps
    
    def _extract_steps_from_text(self, text: str) -> List[TaskStep]:
        """Extract steps from plain text AI response."""
        steps = []
        lines = text.split('\n')
        
        step_counter = 1
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # Look for numbered steps or action keywords
            if (re.match(r'^\d+\.', line) or 
                any(action in line.lower() for action in ['navigate', 'click', 'type', 'wait', 'extract'])):
                
                # Extract action type
                action_type = "wait"  # default
                for action in ActionType:
                    if action.value in line.lower():
                        action_type = action.value
                        break
                
                step = TaskStep(
                    id=f"text_step_{step_counter}",
                    description=line,
                    action_type=action_type,
                    parameters={}
                )
                steps.append(step)
                step_counter += 1
        
        return steps
    
    def _basic_task_parsing(self, task_description: str) -> List[TaskStep]:
        """Basic fallback parsing when AI is not available."""
        steps = []
        
        # Create basic steps based on common task structure
        steps.append(TaskStep(
            id="basic_step_1",
            description=f"Start task: {task_description}",
            action_type="wait",
            parameters={"duration": 1}
        ))
        
        # Look for URLs in the description
        url_pattern = r'https?://[^\s]+'
        urls = re.findall(url_pattern, task_description)
        
        if urls:
            steps.append(TaskStep(
                id="basic_step_2", 
                description=f"Navigate to {urls[0]}",
                action_type="navigate",
                parameters={"target": urls[0]}
            ))
        
        # Add a generic interaction step
        steps.append(TaskStep(
            id="basic_step_3",
            description="Interact with page elements",
            action_type="extract",
            parameters={"target": "body"}
        ))
        
        return steps
    
    def _generate_fallback_strategies(self, task_description: str, steps: List[TaskStep]) -> List[str]:
        """Generate fallback strategies based on task type and steps."""
        strategies = []
        
        # Add general fallback strategies
        strategies.extend([
            "Retry failed step with longer wait time",
            "Try alternative element selectors",
            "Request user assistance for manual intervention"
        ])
        
        # Add task-specific strategies
        if "email" in task_description.lower():
            strategies.extend(self.fallback_strategies.get("authentication_required", []))
        
        if "order" in task_description.lower() or "buy" in task_description.lower():
            strategies.extend(self.fallback_strategies.get("form_submission_failed", []))
        
        # Add step-specific strategies
        for step in steps:
            if step.action_type == "navigate":
                strategies.extend(self.fallback_strategies.get("page_load_timeout", []))
            elif step.action_type in ["click", "type"]:
                strategies.extend(self.fallback_strategies.get("element_not_found", []))
        
        # Remove duplicates while preserving order
        unique_strategies = []
        for strategy in strategies:
            if strategy not in unique_strategies:
                unique_strategies.append(strategy)
        
        return unique_strategies
    
    async def _generate_alternative_steps(self, failed_step: TaskStep, current_state: Dict[str, Any], 
                                        context: Dict[str, Any]) -> List[TaskStep]:
        """Generate alternative steps when a step fails."""
        alternatives = []
        
        # Generate alternatives based on failure type and action
        if failed_step.action_type == "click":
            # Try alternative selectors
            alternatives.append(TaskStep(
                id=f"alt_{failed_step.id}_1",
                description=f"Retry click with alternative selector",
                action_type="click",
                parameters={**failed_step.parameters, "retry": True}
            ))
            
            # Try scrolling to element first
            alternatives.append(TaskStep(
                id=f"alt_{failed_step.id}_2", 
                description="Scroll to make element visible",
                action_type="scroll",
                parameters={"target": failed_step.parameters.get("target", "body")}
            ))
        
        elif failed_step.action_type == "navigate":
            # Try refreshing and navigating again
            alternatives.append(TaskStep(
                id=f"alt_{failed_step.id}_1",
                description="Refresh page before navigation",
                action_type="refresh",
                parameters={}
            ))
            
            alternatives.append(TaskStep(
                id=f"alt_{failed_step.id}_2",
                description=f"Retry navigation to {failed_step.parameters.get('target', '')}",
                action_type="navigate", 
                parameters=failed_step.parameters
            ))
        
        elif failed_step.action_type == "type":
            # Clear field and retry typing
            alternatives.append(TaskStep(
                id=f"alt_{failed_step.id}_1",
                description="Clear field before typing",
                action_type="click",
                parameters={"target": failed_step.parameters.get("target", ""), "clear": True}
            ))
            
            alternatives.append(TaskStep(
                id=f"alt_{failed_step.id}_2",
                description=f"Retry typing: {failed_step.description}",
                action_type="type",
                parameters=failed_step.parameters
            ))
        
        return alternatives