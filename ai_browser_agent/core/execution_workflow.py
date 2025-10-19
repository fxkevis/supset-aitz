"""Task execution workflow management."""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List, Callable, Tuple
from enum import Enum

from ai_browser_agent.models.task import Task, TaskStatus, TaskStep, ExecutionPlan
from ai_browser_agent.models.action import Action, ActionType
from ai_browser_agent.models.page_content import PageContent
from ai_browser_agent.interfaces.user_interface import UserInterface, UserMessage, MessageType


logger = logging.getLogger(__name__)


class WorkflowStage(Enum):
    """Stages of task execution workflow."""
    PLANNING = "planning"
    VALIDATION = "validation"
    EXECUTION = "execution"
    MONITORING = "monitoring"
    COMPLETION = "completion"
    ERROR_HANDLING = "error_handling"


class WorkflowResult:
    """Result of workflow execution."""
    
    def __init__(self, success: bool, message: str, data: Optional[Dict[str, Any]] = None):
        self.success = success
        self.message = message
        self.data = data or {}
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "success": self.success,
            "message": self.message,
            "data": self.data,
            "timestamp": self.timestamp.isoformat()
        }


class TaskExecutionWorkflow:
    """Manages the complete task execution pipeline from planning to completion."""
    
    def __init__(self, ai_agent, config: Optional[Dict[str, Any]] = None):
        self.ai_agent = ai_agent
        self.config = config or {}
        
        # Workflow configuration
        self.max_retry_attempts = config.get("max_retry_attempts", 3)
        self.stage_timeout = config.get("stage_timeout", 300)  # 5 minutes per stage
        self.progress_update_interval = config.get("progress_update_interval", 5)  # seconds
        
        # Workflow state
        self.current_stage = WorkflowStage.PLANNING
        self.workflow_id = str(uuid.uuid4())
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        
        # Progress tracking
        self.progress_callbacks: List[Callable[[str, Dict[str, Any]], None]] = []
        self.stage_results: Dict[WorkflowStage, WorkflowResult] = {}
        
        # Error handling
        self.error_count = 0
        self.last_error: Optional[Exception] = None
    
    async def execute_complete_workflow(self, task: Task) -> WorkflowResult:
        """Execute the complete task workflow from planning to completion."""
        self.start_time = datetime.now()
        self.workflow_id = f"workflow_{task.id}_{int(self.start_time.timestamp())}"
        
        logger.info(f"Starting complete workflow for task {task.id}")
        
        try:
            # Stage 1: Planning and Validation
            planning_result = await self._execute_planning_stage(task)
            if not planning_result.success:
                return planning_result
            
            # Stage 2: Task Execution
            execution_result = await self._execute_execution_stage(task)
            if not execution_result.success:
                return execution_result
            
            # Stage 3: Completion and Reporting
            completion_result = await self._execute_completion_stage(task)
            
            self.end_time = datetime.now()
            execution_time = (self.end_time - self.start_time).total_seconds()
            
            logger.info(f"Workflow completed for task {task.id} in {execution_time:.2f}s")
            
            return WorkflowResult(
                success=True,
                message=f"Task workflow completed successfully in {execution_time:.2f}s",
                data={
                    "workflow_id": self.workflow_id,
                    "execution_time": execution_time,
                    "stages_completed": list(self.stage_results.keys()),
                    "final_status": task.status.value
                }
            )
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            self.last_error = e
            
            # Execute error handling stage
            error_result = await self._execute_error_handling_stage(task, e)
            
            self.end_time = datetime.now()
            
            return WorkflowResult(
                success=False,
                message=f"Workflow failed: {str(e)}",
                data={
                    "workflow_id": self.workflow_id,
                    "error": str(e),
                    "error_stage": self.current_stage.value,
                    "error_handling_result": error_result.to_dict()
                }
            )
    
    async def _execute_planning_stage(self, task: Task) -> WorkflowResult:
        """Execute the planning and validation stage."""
        self.current_stage = WorkflowStage.PLANNING
        
        try:
            self._update_progress("Starting task planning", 10)
            
            # Validate task input
            if not task.validate():
                return WorkflowResult(False, "Task validation failed")
            
            # Create or validate execution plan
            if not task.execution_plan:
                if self.ai_agent.task_planner:
                    task.execution_plan = await self.ai_agent.task_planner.create_plan(
                        task.description, task.context
                    )
                else:
                    return WorkflowResult(False, "No task planner available and no execution plan provided")
            
            # Validate execution plan
            if not task.execution_plan.validate():
                return WorkflowResult(False, "Execution plan validation failed")
            
            self._update_progress("Task planning completed", 20)
            
            # Set up initial context
            if self.ai_agent.task_manager:
                self.ai_agent.task_manager.context_manager.set_task_context(task.id, {
                    "workflow_id": self.workflow_id,
                    "planning_completed_at": datetime.now().isoformat(),
                    "total_steps": len(task.execution_plan.steps)
                })
            
            result = WorkflowResult(
                success=True,
                message="Planning stage completed successfully",
                data={
                    "execution_plan_steps": len(task.execution_plan.steps),
                    "fallback_strategies": len(task.execution_plan.fallback_strategies)
                }
            )
            
            self.stage_results[WorkflowStage.PLANNING] = result
            return result
            
        except Exception as e:
            logger.error(f"Planning stage failed: {e}")
            return WorkflowResult(False, f"Planning stage failed: {str(e)}")
    
    async def _execute_execution_stage(self, task: Task) -> WorkflowResult:
        """Execute the main task execution stage."""
        self.current_stage = WorkflowStage.EXECUTION
        
        try:
            self._update_progress("Starting task execution", 30)
            
            # Update task status
            task.update_status(TaskStatus.IN_PROGRESS)
            
            # Execute the autonomous execution loop
            execution_result = await self._run_monitored_execution(task)
            
            if execution_result.success:
                self._update_progress("Task execution completed", 80)
            else:
                self._update_progress("Task execution failed", 80)
            
            result = WorkflowResult(
                success=execution_result.success,
                message=execution_result.message,
                data=execution_result.data
            )
            
            self.stage_results[WorkflowStage.EXECUTION] = result
            return result
            
        except Exception as e:
            logger.error(f"Execution stage failed: {e}")
            return WorkflowResult(False, f"Execution stage failed: {str(e)}")
    
    async def _run_monitored_execution(self, task: Task) -> WorkflowResult:
        """Run the execution with monitoring and progress tracking."""
        action_count = 0
        max_actions = self.ai_agent.max_actions_per_task
        
        # Start monitoring task
        monitoring_task = asyncio.create_task(self._monitor_execution_progress(task))
        
        try:
            while (task.status == TaskStatus.IN_PROGRESS and 
                   action_count < max_actions and 
                   self.ai_agent.is_active):
                
                # Get current page content
                page_content = await self.ai_agent.browser_controller.get_page_content()
                
                # Optimize content for AI processing
                optimized_content = self.ai_agent.context_manager.process_page_content(
                    page_content, task.description
                )
                
                # Get task context
                task_context = self.ai_agent.task_manager.context_manager.get_combined_context(task.id)
                
                # Make decision about next actions
                actions = await self.ai_agent.decision_engine.analyze_page_and_decide(
                    page_content, task, task_context
                )
                
                if not actions:
                    # Request user input for guidance
                    user_response = await self._handle_uncertain_situation(task, page_content)
                    if user_response == "stop":
                        task.update_status(TaskStatus.CANCELLED)
                        break
                    continue
                
                # Execute actions with progress tracking
                for action in actions:
                    if not self.ai_agent.is_active or task.status != TaskStatus.IN_PROGRESS:
                        break
                    
                    success = await self._execute_action_with_tracking(action, task, action_count, max_actions)
                    action_count += 1
                    
                    if not success and action.confidence < self.ai_agent.decision_confidence_threshold:
                        # Handle low confidence failure
                        retry_decision = await self._handle_action_failure(action, task)
                        if retry_decision == "stop":
                            task.update_status(TaskStatus.FAILED)
                            break
                
                # Check task completion
                if await self._check_and_handle_completion(task, page_content):
                    break
                
                # Brief pause between cycles
                await asyncio.sleep(1)
            
            # Cancel monitoring
            monitoring_task.cancel()
            
            # Determine final result
            if task.status == TaskStatus.COMPLETED:
                return WorkflowResult(
                    success=True,
                    message="Task completed successfully",
                    data={
                        "actions_executed": action_count,
                        "final_status": task.status.value
                    }
                )
            elif action_count >= max_actions:
                task.set_error(f"Task exceeded maximum actions limit ({max_actions})")
                return WorkflowResult(
                    success=False,
                    message=f"Task exceeded maximum actions limit ({max_actions})",
                    data={"actions_executed": action_count}
                )
            else:
                return WorkflowResult(
                    success=False,
                    message=f"Task execution stopped with status: {task.status.value}",
                    data={
                        "actions_executed": action_count,
                        "final_status": task.status.value
                    }
                )
                
        except Exception as e:
            monitoring_task.cancel()
            raise
    
    async def _execute_action_with_tracking(self, action: Action, task: Task, 
                                          action_index: int, total_max: int) -> bool:
        """Execute an action with progress tracking."""
        # Update progress
        progress = 30 + (action_index / total_max) * 50  # 30-80% range for execution
        self._update_progress(f"Executing: {action.description}", progress)
        
        # Execute the action
        success = await self.ai_agent._execute_action(action, task)
        
        # Update context with detailed tracking
        if self.ai_agent.task_manager:
            self.ai_agent.task_manager.context_manager.update_task_context(task.id, {
                f"action_{action_index}": {
                    "type": action.type.value,
                    "description": action.description,
                    "success": success,
                    "timestamp": datetime.now().isoformat(),
                    "confidence": action.confidence
                }
            })
        
        return success
    
    async def _monitor_execution_progress(self, task: Task) -> None:
        """Monitor execution progress and provide regular updates."""
        while task.status == TaskStatus.IN_PROGRESS:
            try:
                # Get current progress
                progress_percentage = task.get_progress_percentage()
                
                # Update progress with current status
                self._update_progress(
                    f"Task in progress - {progress_percentage:.1f}% complete",
                    30 + (progress_percentage / 100) * 50
                )
                
                # Wait for next update
                await asyncio.sleep(self.progress_update_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in progress monitoring: {e}")
                await asyncio.sleep(self.progress_update_interval)
    
    async def _handle_uncertain_situation(self, task: Task, page_content: PageContent) -> str:
        """Handle situations where the AI is uncertain about next steps."""
        prompt = (
            f"I'm not sure what to do next for the task: {task.description}. "
            f"Current page: {page_content.url}. "
            f"Page title: {page_content.title}. "
            f"What should I do?"
        )
        
        if self.ai_agent.user_interface:
            return await self.ai_agent._request_user_input(prompt)
        else:
            logger.warning("No user interface available for uncertain situation")
            return "continue"
    
    async def _handle_action_failure(self, action: Action, task: Task) -> str:
        """Handle action failures with user input."""
        prompt = (
            f"Action failed: {action.description} "
            f"(confidence: {action.confidence:.2f}). "
            f"Error: {action.error_message or 'Unknown error'}. "
            f"How should I proceed with the task: {task.description}?"
        )
        
        if self.ai_agent.user_interface:
            return await self.ai_agent._request_user_input(prompt)
        else:
            logger.warning("No user interface available for action failure handling")
            return "continue"
    
    async def _check_and_handle_completion(self, task: Task, page_content: PageContent) -> bool:
        """Check if task is complete and handle completion."""
        is_complete = await self.ai_agent._check_task_completion(task, page_content)
        
        if is_complete:
            task.update_status(TaskStatus.COMPLETED)
            task.set_result({
                "completed_at": datetime.now().isoformat(),
                "final_url": page_content.url,
                "workflow_id": self.workflow_id
            })
            
            self._update_progress("Task completed successfully", 80)
            return True
        
        return False
    
    async def _execute_completion_stage(self, task: Task) -> WorkflowResult:
        """Execute the completion and reporting stage."""
        self.current_stage = WorkflowStage.COMPLETION
        
        try:
            self._update_progress("Generating completion report", 90)
            
            # Generate execution report
            actions_executed = []
            if self.ai_agent.task_manager:
                task_context = self.ai_agent.task_manager.context_manager.get_task_context(task.id)
                
                # Extract executed actions from context
                for key, value in task_context.items():
                    if key.startswith("action_") and isinstance(value, dict):
                        actions_executed.append(value)
            
            # Create completion report
            completion_report = {
                "task_id": task.id,
                "task_description": task.description,
                "final_status": task.status.value,
                "actions_executed": len(actions_executed),
                "workflow_id": self.workflow_id,
                "completion_time": datetime.now().isoformat(),
                "execution_summary": actions_executed[-5:] if actions_executed else []  # Last 5 actions
            }
            
            # Update task result
            if task.result:
                task.result.update(completion_report)
            else:
                task.set_result(completion_report)
            
            self._update_progress("Workflow completed", 100)
            
            # Display completion message
            if self.ai_agent.user_interface:
                status_message = "completed successfully" if task.status == TaskStatus.COMPLETED else f"ended with status: {task.status.value}"
                self.ai_agent.user_interface.display_message(UserMessage(
                    content=f"Task {status_message}: {task.description}",
                    message_type=MessageType.SUCCESS if task.status == TaskStatus.COMPLETED else MessageType.INFO
                ))
            
            result = WorkflowResult(
                success=True,
                message="Completion stage finished",
                data=completion_report
            )
            
            self.stage_results[WorkflowStage.COMPLETION] = result
            return result
            
        except Exception as e:
            logger.error(f"Completion stage failed: {e}")
            return WorkflowResult(False, f"Completion stage failed: {str(e)}")
    
    async def _execute_error_handling_stage(self, task: Task, error: Exception) -> WorkflowResult:
        """Execute error handling and recovery procedures."""
        self.current_stage = WorkflowStage.ERROR_HANDLING
        self.error_count += 1
        
        try:
            logger.info(f"Executing error handling for: {str(error)}")
            
            # Update task with error
            task.set_error(str(error))
            
            # Attempt recovery if within retry limits
            if self.error_count <= self.max_retry_attempts:
                recovery_prompt = (
                    f"An error occurred during task execution: {str(error)}. "
                    f"This is attempt {self.error_count} of {self.max_retry_attempts}. "
                    f"Should I retry the task: {task.description}?"
                )
                
                if self.ai_agent.user_interface:
                    user_response = await self.ai_agent._request_user_input(recovery_prompt)
                    
                    if user_response.lower() in ["yes", "retry", "continue"]:
                        # Reset task for retry
                        task.update_status(TaskStatus.PENDING)
                        task.error_message = None
                        
                        return WorkflowResult(
                            success=True,
                            message="Error handled - task reset for retry",
                            data={"retry_attempt": self.error_count}
                        )
            
            # Create error report
            error_report = {
                "error_message": str(error),
                "error_type": type(error).__name__,
                "error_stage": self.current_stage.value,
                "error_count": self.error_count,
                "workflow_id": self.workflow_id,
                "task_id": task.id
            }
            
            # Display error message
            if self.ai_agent.user_interface:
                self.ai_agent.user_interface.display_message(UserMessage(
                    content=f"Task failed with error: {str(error)}",
                    message_type=MessageType.ERROR
                ))
            
            result = WorkflowResult(
                success=False,
                message="Error handling completed - task failed",
                data=error_report
            )
            
            self.stage_results[WorkflowStage.ERROR_HANDLING] = result
            return result
            
        except Exception as e:
            logger.error(f"Error handling stage failed: {e}")
            return WorkflowResult(False, f"Error handling failed: {str(e)}")
    
    def _update_progress(self, message: str, percentage: float) -> None:
        """Update workflow progress."""
        progress_data = {
            "workflow_id": self.workflow_id,
            "stage": self.current_stage.value,
            "message": message,
            "progress_percentage": percentage,
            "timestamp": datetime.now().isoformat()
        }
        
        # Notify progress callbacks
        for callback in self.progress_callbacks:
            try:
                callback(self.workflow_id, progress_data)
            except Exception as e:
                logger.error(f"Progress callback error: {e}")
        
        logger.info(f"Workflow progress: {percentage:.1f}% - {message}")
    
    def add_progress_callback(self, callback: Callable[[str, Dict[str, Any]], None]) -> None:
        """Add a progress callback."""
        self.progress_callbacks.append(callback)
    
    def get_workflow_summary(self) -> Dict[str, Any]:
        """Get a summary of the workflow execution."""
        execution_time = None
        if self.start_time:
            end_time = self.end_time or datetime.now()
            execution_time = (end_time - self.start_time).total_seconds()
        
        return {
            "workflow_id": self.workflow_id,
            "current_stage": self.current_stage.value,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "execution_time": execution_time,
            "stages_completed": list(self.stage_results.keys()),
            "error_count": self.error_count,
            "last_error": str(self.last_error) if self.last_error else None
        }