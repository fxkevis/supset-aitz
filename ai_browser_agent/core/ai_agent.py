"""Main AI Agent class - central orchestration component."""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List, Callable, Tuple

from ai_browser_agent.interfaces.base_interfaces import BaseAgent
from ai_browser_agent.interfaces.user_interface import UserInterface, UserMessage, UserPrompt, MessageType
from ai_browser_agent.interfaces.model_factory import ModelFactory
from ai_browser_agent.controllers.browser_controller import BrowserController
from ai_browser_agent.controllers.session_manager import SessionManager
from ai_browser_agent.core.decision_engine import DecisionEngine
from ai_browser_agent.core.task_planner import TaskPlanner
from ai_browser_agent.managers.task_manager import TaskManager
from ai_browser_agent.managers.context_manager import ContextManager
from ai_browser_agent.security.security_layer import SecurityLayer
from ai_browser_agent.models.task import Task, TaskStatus
from ai_browser_agent.models.action import Action, ActionType
from ai_browser_agent.models.page_content import PageContent
from ai_browser_agent.models.config import AIModelConfig, SecurityConfig, BrowserConfig
from ai_browser_agent.core.execution_workflow import TaskExecutionWorkflow


logger = logging.getLogger(__name__)


class AIAgent(BaseAgent):
    """Main AI Agent orchestrator that combines all components for autonomous task execution."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, user_interface: Optional[UserInterface] = None):
        super().__init__(config)
        self.user_interface = user_interface
        
        # Core components
        self.model_factory: Optional[ModelFactory] = None
        self.browser_controller: Optional[BrowserController] = None
        self.session_manager: Optional[SessionManager] = None
        self.decision_engine: Optional[DecisionEngine] = None
        self.task_planner: Optional[TaskPlanner] = None
        self.task_manager: Optional[TaskManager] = None
        self.context_manager: Optional[ContextManager] = None
        self.security_layer: Optional[SecurityLayer] = None
        self.execution_workflow: Optional[TaskExecutionWorkflow] = None
        
        # Execution state
        self._execution_loop_running = False
        self._current_task: Optional[Task] = None
        self._user_input_callbacks: List[Callable[[str], str]] = []
        
        # Configuration
        self.ai_config = AIModelConfig(**(config.get("ai_model", {}) if config else {}))
        self.security_config = SecurityConfig(**(config.get("security", {}) if config else {}))
        self.browser_config = BrowserConfig(**(config.get("browser", {}) if config else {}))
        
        # Autonomous execution settings
        self.max_actions_per_task = config.get("max_actions_per_task", 50) if config else 50
        self.action_timeout = config.get("action_timeout", 30) if config else 30
        self.decision_confidence_threshold = config.get("decision_confidence_threshold", 0.7) if config else 0.7
    
    async def initialize(self) -> None:
        """Initialize the AI agent and all its components."""
        try:
            logger.info("Initializing AI Agent...")
            
            # Initialize model factory
            self.model_factory = ModelFactory(self.ai_config)
            
            # Initialize browser controller
            self.browser_controller = BrowserController(self.browser_config)
            self.browser_controller.connect()
            
            # Initialize session manager
            self.session_manager = SessionManager(self.browser_config.to_dict())
            self.session_manager.start()
            
            # Initialize context manager
            logger.info(f"Config type: {type(self.config)}, Config: {self.config}")
            context_config = self.config.get("context", {})
            max_tokens = self.ai_config.max_tokens
            self.context_manager = ContextManager(max_tokens)
            
            # Initialize security layer
            from ai_browser_agent.security.user_confirmation import SecuritySettings, ConfirmationMode
            from ai_browser_agent.security.audit_logger import AuditConfig
            from pathlib import Path
            
            # Convert SecurityConfig to SecuritySettings
            security_settings = SecuritySettings(
                confirmation_mode=ConfirmationMode.INTERACTIVE,
                enable_audit_logging=self.security_config.audit_log_enabled
            )
            
            # Convert SecurityConfig to AuditConfig
            audit_config = AuditConfig(
                enabled=self.security_config.audit_log_enabled,
                log_file_path=Path(self.security_config.audit_log_file) if self.security_config.audit_log_file else None
            )
            
            # Create input handler from user interface
            def input_handler(prompt: str) -> str:
                if self.user_interface:
                    return self.user_interface.get_user_input(prompt)
                return ""
            
            self.security_layer = SecurityLayer(
                security_settings=security_settings,
                audit_config=audit_config,
                input_handler=input_handler
            )
            
            # Initialize decision engine
            self.decision_engine = DecisionEngine(self.model_factory, self.security_config)
            
            # Initialize task planner
            best_model = await self.model_factory.get_best_available_model()
            self.task_planner = TaskPlanner(self.config.get("task_planner", {}), best_model)
            self.task_planner.initialize()
            
            # Initialize task manager
            self.task_manager = TaskManager(self.config.get("task_manager", {}), self.task_planner)
            self.task_manager.start()
            
            # Set up progress callbacks
            self.task_manager.add_progress_callback(self._on_task_progress)
            
            # Initialize execution workflow
            self.execution_workflow = TaskExecutionWorkflow(self, self.config.get("workflow", {}))
            self.execution_workflow.add_progress_callback(self._on_workflow_progress)
            
            # Initialize user interface if provided
            if self.user_interface:
                self.user_interface.start_interface()
            
            self.is_active = True
            logger.info("AI Agent initialized successfully")
            
            # Display initialization message
            if self.user_interface:
                self.user_interface.display_message(UserMessage(
                    content="AI Browser Agent initialized and ready for tasks",
                    message_type=MessageType.SUCCESS
                ))
            
        except Exception as e:
            logger.error(f"Failed to initialize AI Agent: {e}")
            await self.shutdown()
            raise
    
    async def shutdown(self) -> None:
        """Shutdown the AI agent gracefully."""
        logger.info("Shutting down AI Agent...")
        
        self.is_active = False
        self._execution_loop_running = False
        
        # Stop task manager
        if self.task_manager:
            self.task_manager.stop()
        
        # Shutdown components in reverse order
        if self.security_layer:
            self.security_layer.shutdown()
        
        if self.context_manager:
            self.context_manager.reset_context()
        
        if self.session_manager:
            self.session_manager.stop()
        
        if self.browser_controller:
            self.browser_controller.disconnect()
        
        if self.decision_engine:
            await self.decision_engine.cleanup()
        
        if self.task_planner:
            self.task_planner.shutdown()
        
        if self.model_factory:
            await self.model_factory.cleanup()
        
        # Stop user interface
        if self.user_interface:
            self.user_interface.stop_interface()
        
        logger.info("AI Agent shutdown complete")
    
    async def execute_task(self, task_description: str, context: Optional[Dict[str, Any]] = None) -> Task:
        """Execute a task with autonomous decision-making and user interaction when needed."""
        if not self.is_active:
            raise RuntimeError("AI Agent is not initialized")
        
        logger.info(f"Starting task execution: {task_description}")
        
        # Submit task to task manager
        task = await self.task_manager.submit_task(task_description, context)
        
        # Display task start message
        if self.user_interface:
            self.user_interface.display_message(UserMessage(
                content=f"Starting task: {task_description}",
                message_type=MessageType.INFO
            ))
        
        # Execute the task using the workflow manager
        if self.execution_workflow:
            workflow_result = await self.execution_workflow.execute_complete_workflow(task)
            
            # Display workflow result
            if self.user_interface:
                message_type = MessageType.SUCCESS if workflow_result.success else MessageType.ERROR
                self.user_interface.display_message(UserMessage(
                    content=workflow_result.message,
                    message_type=message_type,
                    metadata=workflow_result.data
                ))
        else:
            # Fallback to direct execution
            await self._execute_task_workflow(task)
        
        return task
    
    async def _execute_task_workflow(self, task: Task) -> None:
        """Execute the complete task workflow from planning to completion."""
        try:
            # Set current task
            self._current_task = task
            
            # Start autonomous execution loop
            await self._autonomous_execution_loop(task)
            
        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            task.set_error(str(e))
            
            if self.user_interface:
                self.user_interface.display_message(UserMessage(
                    content=f"Task failed: {str(e)}",
                    message_type=MessageType.ERROR
                ))
        finally:
            self._current_task = None
    
    async def _autonomous_execution_loop(self, task: Task) -> None:
        """Main autonomous execution loop with decision-making."""
        action_count = 0
        
        while (task.status == TaskStatus.IN_PROGRESS and 
               action_count < self.max_actions_per_task and 
               self.is_active):
            
            try:
                # Get current page content
                page_content = await self.browser_controller.get_page_content()
                
                # Optimize content for AI processing
                optimized_content = self.context_manager.process_page_content(
                    page_content, task.description
                )
                
                # Get task context
                task_context = self.task_manager.context_manager.get_combined_context(task.id)
                
                # Make decision about next actions
                actions = await self.decision_engine.analyze_page_and_decide(
                    page_content, task, task_context
                )
                
                if not actions:
                    # No actions decided - request user input
                    user_response = await self._request_user_input(
                        f"I'm not sure what to do next for the task: {task.description}. "
                        f"Current page: {page_content.url}. What should I do?"
                    )
                    
                    # Update task context with user input
                    self.task_manager.context_manager.update_task_context(
                        task.id, {"user_guidance": user_response}
                    )
                    continue
                
                # Execute actions
                for action in actions:
                    if not self.is_active or task.status != TaskStatus.IN_PROGRESS:
                        break
                    
                    success = await self._execute_action(action, task)
                    action_count += 1
                    
                    if not success and action.confidence < self.decision_confidence_threshold:
                        # Low confidence action failed - request user input
                        user_response = await self._request_user_input(
                            f"Action failed: {action.description}. "
                            f"How should I proceed with the task: {task.description}?"
                        )
                        
                        # Update context and continue
                        self.task_manager.context_manager.update_task_context(
                            task.id, {"user_guidance_after_failure": user_response}
                        )
                        break
                
                # Check if task is complete
                if await self._check_task_completion(task, page_content):
                    task.update_status(TaskStatus.COMPLETED)
                    task.set_result({
                        "actions_executed": action_count,
                        "final_url": page_content.url,
                        "completion_time": datetime.now()
                    })
                    
                    if self.user_interface:
                        self.user_interface.display_message(UserMessage(
                            content=f"Task completed successfully: {task.description}",
                            message_type=MessageType.SUCCESS
                        ))
                    break
                
                # Small delay between decision cycles
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error in execution loop: {e}")
                
                # Request user input on errors
                user_response = await self._request_user_input(
                    f"An error occurred: {str(e)}. How should I handle this for task: {task.description}?"
                )
                
                # Update context with error handling guidance
                self.task_manager.context_manager.update_task_context(
                    task.id, {"error_handling_guidance": user_response}
                )
        
        # Check final status
        if action_count >= self.max_actions_per_task:
            task.set_error(f"Task exceeded maximum actions limit ({self.max_actions_per_task})")
        elif task.status == TaskStatus.IN_PROGRESS:
            # Task didn't complete naturally - mark as requiring input
            task.update_status(TaskStatus.REQUIRES_INPUT)
    
    async def _execute_action(self, action: Action, task: Task) -> bool:
        """Execute a single action with security validation."""
        try:
            logger.info(f"Executing action: {action.type.value} - {action.description}")
            
            # Security validation
            if action.is_destructive:
                confirmation_result = await self.security_layer.validate_and_confirm_action(action)
                if not confirmation_result.approved:
                    logger.info(f"Action blocked by security layer: {confirmation_result.reason}")
                    return False
            
            # Execute action based on type
            start_time = datetime.now()
            success = False
            
            if action.type == ActionType.NAVIGATE:
                try:
                    self.browser_controller.navigate_to(action.target)
                    success = True
                except Exception as e:
                    logger.error(f"Navigation failed: {e}")
                    success = False
            
            elif action.type == ActionType.CLICK:
                element = self.browser_controller.find_element(action.target)
                if element:
                    success = self.browser_controller.click_element(element)
            
            elif action.type == ActionType.TYPE:
                element = self.browser_controller.find_element(action.target)
                text = action.parameters.get("text", "")
                if element and text:
                    success = self.browser_controller.type_text(element, text)
            
            elif action.type == ActionType.SCROLL:
                success = self.browser_controller.scroll_to_element(action.target)
            
            elif action.type == ActionType.WAIT:
                duration = action.parameters.get("duration", 1)
                await asyncio.sleep(duration)
                success = True
            
            elif action.type == ActionType.EXTRACT:
                page_content = await self.browser_controller.get_page_content()
                action.result = page_content
                success = True
            
            elif action.type == ActionType.SCREENSHOT:
                screenshot_path = self.browser_controller.take_screenshot()
                action.result = screenshot_path
                success = True
            
            else:
                logger.warning(f"Unsupported action type: {action.type}")
                success = False
            
            # Record execution results
            execution_time = (datetime.now() - start_time).total_seconds()
            action.mark_executed(success, action.result, None if success else "Action execution failed")
            action.set_execution_time(execution_time)
            
            # Update task context with action results
            self.task_manager.context_manager.update_task_context(task.id, {
                f"action_{action.id}_result": {
                    "success": success,
                    "execution_time": execution_time,
                    "result": action.result
                }
            })
            
            return success
            
        except Exception as e:
            logger.error(f"Action execution error: {e}")
            action.mark_executed(False, None, str(e))
            return False
    
    async def _check_task_completion(self, task: Task, current_page: PageContent) -> bool:
        """Check if the task has been completed based on current state."""
        # This is a simplified completion check
        # In practice, this would use AI to evaluate task completion
        
        if not task.execution_plan:
            return False
        
        # Check if all planned steps are completed
        if task.execution_plan.is_complete():
            return True
        
        # Use AI to evaluate completion if available
        if self.decision_engine:
            try:
                # Get expected outcome from task description
                expected_outcome = f"Task completed: {task.description}"
                
                # Create a dummy action to evaluate
                dummy_action = Action(
                    id="completion_check",
                    type=ActionType.EXTRACT,
                    target="body",
                    description=task.description
                )
                
                success, confidence, reasoning = await self.decision_engine.evaluate_action_success(
                    dummy_action, current_page, expected_outcome
                )
                
                logger.info(f"Task completion evaluation: success={success}, confidence={confidence}, reasoning={reasoning}")
                return success and confidence > 0.8
                
            except Exception as e:
                logger.error(f"Error evaluating task completion: {e}")
        
        return False
    
    async def _request_user_input(self, prompt: str) -> str:
        """Request input from the user when the agent is uncertain."""
        if not self.user_interface:
            logger.warning("No user interface available for input request")
            return "continue"  # Default response
        
        try:
            # Display the prompt
            self.user_interface.display_message(UserMessage(
                content=prompt,
                message_type=MessageType.PROMPT
            ))
            
            # Get user input
            user_prompt = UserPrompt(
                question=prompt,
                options=["continue", "stop", "retry", "skip"],
                default_value="continue",
                is_required=True,
                input_type="choice"
            )
            
            response = self.user_interface.get_user_input(user_prompt)
            
            logger.info(f"User input received: {response}")
            return response
            
        except Exception as e:
            logger.error(f"Error requesting user input: {e}")
            return "continue"  # Default fallback
    
    def _on_task_progress(self, task_id: str, progress_data: Dict[str, Any]) -> None:
        """Handle task progress updates."""
        if self.user_interface:
            status_message = progress_data.get("message", "Task in progress")
            progress_percentage = progress_data.get("progress_percentage", 0)
            
            self.user_interface.display_status({
                "task_id": task_id,
                "message": status_message,
                "progress": progress_percentage,
                "timestamp": progress_data.get("timestamp")
            })
    
    def _on_workflow_progress(self, workflow_id: str, progress_data: Dict[str, Any]) -> None:
        """Handle workflow progress updates."""
        if self.user_interface:
            stage = progress_data.get("stage", "unknown")
            message = progress_data.get("message", "Workflow in progress")
            progress_percentage = progress_data.get("progress_percentage", 0)
            
            self.user_interface.display_status({
                "workflow_id": workflow_id,
                "stage": stage,
                "message": message,
                "progress": progress_percentage,
                "timestamp": progress_data.get("timestamp")
            })
    
    def analyze_page(self, page_content: PageContent) -> List[Action]:
        """Analyze page content and return suggested actions (synchronous version)."""
        if not self.decision_engine:
            return []
        
        # This is a simplified synchronous version for external use
        # In practice, you might want to run this in an event loop
        try:
            # Create a dummy task for analysis
            dummy_task = Task(
                id="analysis_task",
                description="Analyze page content"
            )
            
            # Use asyncio to run the async method
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're already in an async context, we can't use run_until_complete
                logger.warning("Cannot run synchronous analysis in async context")
                return []
            else:
                return loop.run_until_complete(
                    self.decision_engine.analyze_page_and_decide(page_content, dummy_task, {})
                )
        except Exception as e:
            logger.error(f"Error analyzing page: {e}")
            return []
    
    def request_user_input(self, prompt: str) -> str:
        """Request user input (synchronous version)."""
        if not self.user_interface:
            return "continue"
        
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                logger.warning("Cannot request user input synchronously in async context")
                return "continue"
            else:
                return loop.run_until_complete(self._request_user_input(prompt))
        except Exception as e:
            logger.error(f"Error requesting user input: {e}")
            return "continue"
    
    def generate_report(self, actions: List[Action]) -> str:
        """Generate a report of executed actions."""
        if not actions:
            return "No actions were executed."
        
        report_lines = ["Task Execution Report", "=" * 25, ""]
        
        successful_actions = [a for a in actions if a.success]
        failed_actions = [a for a in actions if not a.success]
        
        report_lines.append(f"Total Actions: {len(actions)}")
        report_lines.append(f"Successful: {len(successful_actions)}")
        report_lines.append(f"Failed: {len(failed_actions)}")
        report_lines.append("")
        
        if successful_actions:
            report_lines.append("Successful Actions:")
            for action in successful_actions:
                execution_time = f" ({action.execution_time:.2f}s)" if action.execution_time else ""
                report_lines.append(f"  ✓ {action.description}{execution_time}")
            report_lines.append("")
        
        if failed_actions:
            report_lines.append("Failed Actions:")
            for action in failed_actions:
                error_msg = f" - {action.error_message}" if action.error_message else ""
                report_lines.append(f"  ✗ {action.description}{error_msg}")
            report_lines.append("")
        
        return "\n".join(report_lines)
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive status of the AI agent."""
        status = super().get_status()
        
        status.update({
            "components": {
                "model_factory": self.model_factory is not None,
                "browser_controller": self.browser_controller is not None,
                "decision_engine": self.decision_engine is not None,
                "task_manager": self.task_manager is not None,
                "security_layer": self.security_layer is not None
            },
            "current_task": self._current_task.id if self._current_task else None,
            "execution_loop_running": self._execution_loop_running,
            "configuration": {
                "max_actions_per_task": self.max_actions_per_task,
                "action_timeout": self.action_timeout,
                "decision_confidence_threshold": self.decision_confidence_threshold
            }
        })
        
        # Add task manager status if available
        if self.task_manager:
            status["task_queue"] = self.task_manager.get_queue_status()
        
        return status
    
    async def execute_task_with_workflow(self, task_description: str, 
                                       context: Optional[Dict[str, Any]] = None,
                                       workflow_config: Optional[Dict[str, Any]] = None) -> Tuple[Task, Dict[str, Any]]:
        """Execute a task using the complete workflow system with detailed reporting."""
        if not self.is_active:
            raise RuntimeError("AI Agent is not initialized")
        
        # Create custom workflow if config provided
        workflow = self.execution_workflow
        if workflow_config:
            workflow = TaskExecutionWorkflow(self, workflow_config)
            workflow.add_progress_callback(self._on_workflow_progress)
        
        # Submit task
        task = await self.task_manager.submit_task(task_description, context)
        
        # Execute with workflow
        workflow_result = await workflow.execute_complete_workflow(task)
        
        # Get workflow summary
        workflow_summary = workflow.get_workflow_summary()
        
        return task, {
            "workflow_result": workflow_result.to_dict(),
            "workflow_summary": workflow_summary
        }
    
    def get_execution_report(self, task: Task) -> Dict[str, Any]:
        """Generate a comprehensive execution report for a task."""
        if not task:
            return {"error": "No task provided"}
        
        # Get task context
        task_context = {}
        if self.task_manager:
            task_context = self.task_manager.context_manager.get_task_context(task.id)
        
        # Extract executed actions
        actions_executed = []
        for key, value in task_context.items():
            if key.startswith("action_") and isinstance(value, dict):
                actions_executed.append(value)
        
        # Calculate execution statistics
        successful_actions = [a for a in actions_executed if a.get("success", False)]
        failed_actions = [a for a in actions_executed if not a.get("success", False)]
        
        execution_time = None
        if task.completed_at and task.created_at:
            execution_time = (task.completed_at - task.created_at).total_seconds()
        
        return {
            "task_summary": {
                "id": task.id,
                "description": task.description,
                "status": task.status.value,
                "created_at": task.created_at.isoformat(),
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                "execution_time": execution_time
            },
            "execution_statistics": {
                "total_actions": len(actions_executed),
                "successful_actions": len(successful_actions),
                "failed_actions": len(failed_actions),
                "success_rate": len(successful_actions) / len(actions_executed) if actions_executed else 0
            },
            "actions_executed": actions_executed,
            "task_result": task.result,
            "error_message": task.error_message,
            "context_data": task_context
        }
    
    async def pause_current_task(self) -> bool:
        """Pause the currently executing task."""
        if self._current_task and self.task_manager:
            return self.task_manager.pause_task(self._current_task.id)
        return False
    
    async def resume_current_task(self, user_input: Optional[Dict[str, Any]] = None) -> bool:
        """Resume the currently paused task."""
        if self._current_task and self.task_manager:
            return self.task_manager.resume_task(self._current_task.id, user_input)
        return False
    
    async def cancel_current_task(self) -> bool:
        """Cancel the currently executing task."""
        if self._current_task and self.task_manager:
            return self.task_manager.cancel_task(self._current_task.id)
        return False
    
    def get_current_task_status(self) -> Optional[Dict[str, Any]]:
        """Get status of the currently executing task."""
        if self._current_task and self.task_manager:
            return self.task_manager.get_task_status(self._current_task.id)
        return None