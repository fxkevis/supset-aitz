"""Status reporter for real-time updates and progress tracking."""

import threading
import time
from datetime import datetime
from typing import Dict, Any, Optional, List, Callable
from enum import Enum
from dataclasses import dataclass

from ai_browser_agent.interfaces.user_interface import UserInterface, UserMessage, MessageType
from ai_browser_agent.models.task import Task, TaskStatus, TaskStep


class StatusLevel(Enum):
    """Levels of status messages."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"


@dataclass
class StatusUpdate:
    """Status update message."""
    level: StatusLevel
    message: str
    timestamp: datetime
    context: Optional[Dict[str, Any]] = None
    task_id: Optional[str] = None
    step_id: Optional[str] = None


class StatusReporter:
    """Real-time status reporter with progress indicators and notifications."""
    
    def __init__(self, user_interface: UserInterface):
        self.user_interface = user_interface
        self._status_history: List[StatusUpdate] = []
        self._subscribers: List[Callable[[StatusUpdate], None]] = []
        self._lock = threading.Lock()
        self._current_task: Optional[Task] = None
        self._progress_thread: Optional[threading.Thread] = None
        self._stop_progress = threading.Event()
        
    def report_status(self, level: StatusLevel, message: str, 
                     context: Optional[Dict[str, Any]] = None,
                     task_id: Optional[str] = None,
                     step_id: Optional[str] = None) -> None:
        """Report a status update."""
        status_update = StatusUpdate(
            level=level,
            message=message,
            timestamp=datetime.now(),
            context=context,
            task_id=task_id,
            step_id=step_id
        )
        
        with self._lock:
            self._status_history.append(status_update)
            
        # Convert to user message and display
        msg_type = self._level_to_message_type(level)
        user_msg = UserMessage(
            content=message,
            message_type=msg_type,
            timestamp=status_update.timestamp.strftime("%H:%M:%S"),
            metadata=context
        )
        
        self.user_interface.display_message(user_msg)
        
        # Notify subscribers
        for subscriber in self._subscribers:
            try:
                subscriber(status_update)
            except Exception as e:
                # Don't let subscriber errors break status reporting
                pass
    
    def _level_to_message_type(self, level: StatusLevel) -> MessageType:
        """Convert status level to message type."""
        mapping = {
            StatusLevel.DEBUG: MessageType.INFO,
            StatusLevel.INFO: MessageType.INFO,
            StatusLevel.WARNING: MessageType.WARNING,
            StatusLevel.ERROR: MessageType.ERROR,
            StatusLevel.SUCCESS: MessageType.SUCCESS
        }
        return mapping.get(level, MessageType.INFO)
    
    def report_task_started(self, task: Task) -> None:
        """Report that a task has started."""
        self._current_task = task
        self.report_status(
            StatusLevel.INFO,
            f"Task started: {task.description}",
            context={"task_id": task.id, "status": task.status.value},
            task_id=task.id
        )
        
        # Start progress monitoring if task has execution plan
        if task.execution_plan:
            self._start_progress_monitoring()
    
    def report_task_completed(self, task: Task) -> None:
        """Report that a task has completed."""
        self._stop_progress_monitoring()
        
        level = StatusLevel.SUCCESS if task.status == TaskStatus.COMPLETED else StatusLevel.ERROR
        message = f"Task {task.status.value}: {task.description}"
        
        self.report_status(
            level,
            message,
            context={
                "task_id": task.id,
                "status": task.status.value,
                "progress": task.get_progress_percentage()
            },
            task_id=task.id
        )
        
        # Display detailed report if available
        if hasattr(self.user_interface, 'display_task_report'):
            self.user_interface.display_task_report(task)
    
    def report_step_started(self, step: TaskStep, task_id: str) -> None:
        """Report that a task step has started."""
        self.report_status(
            StatusLevel.INFO,
            f"Starting step: {step.description}",
            context={
                "step_id": step.id,
                "action_type": step.action_type,
                "parameters": step.parameters
            },
            task_id=task_id,
            step_id=step.id
        )
        
        # Update UI with execution step status
        status_data = {
            "type": "execution_step",
            "step_name": step.description,
            "step_status": "running",
            "details": f"Action: {step.action_type}"
        }
        self.user_interface.display_status(status_data)
    
    def report_step_completed(self, step: TaskStep, task_id: str, 
                            execution_time: Optional[float] = None) -> None:
        """Report that a task step has completed."""
        details = f"Completed in {execution_time:.2f}s" if execution_time else "Completed"
        
        self.report_status(
            StatusLevel.SUCCESS,
            f"Step completed: {step.description}",
            context={
                "step_id": step.id,
                "execution_time": execution_time,
                "action_type": step.action_type
            },
            task_id=task_id,
            step_id=step.id
        )
        
        # Update UI with execution step status
        status_data = {
            "type": "execution_step",
            "step_name": step.description,
            "step_status": "completed",
            "details": details
        }
        self.user_interface.display_status(status_data)
    
    def report_step_failed(self, step: TaskStep, task_id: str, error_message: str) -> None:
        """Report that a task step has failed."""
        self.report_status(
            StatusLevel.ERROR,
            f"Step failed: {step.description} - {error_message}",
            context={
                "step_id": step.id,
                "error_message": error_message,
                "action_type": step.action_type
            },
            task_id=task_id,
            step_id=step.id
        )
        
        # Update UI with execution step status
        status_data = {
            "type": "execution_step",
            "step_name": step.description,
            "step_status": "failed",
            "details": f"Error: {error_message}"
        }
        self.user_interface.display_status(status_data)
    
    def report_progress(self, task_id: str, progress_percentage: float, 
                       current_step: Optional[str] = None) -> None:
        """Report task progress with percentage and current step."""
        message = f"Progress: {progress_percentage:.1f}%"
        if current_step:
            message += f" - {current_step}"
        
        self.report_status(
            StatusLevel.INFO,
            message,
            context={
                "progress": progress_percentage,
                "current_step": current_step
            },
            task_id=task_id
        )
        
        # Update UI with progress bar
        status_data = {
            "type": "task_progress",
            "task_id": task_id,
            "progress": progress_percentage,
            "current_step": current_step or ""
        }
        self.user_interface.display_status(status_data)
    
    def report_user_input_required(self, prompt: str, task_id: str, 
                                  context: Optional[Dict[str, Any]] = None) -> None:
        """Report that user input is required."""
        self.report_status(
            StatusLevel.WARNING,
            f"User input required: {prompt}",
            context=context,
            task_id=task_id
        )
        
        # Create notification for user attention
        notification_msg = UserMessage(
            content=f"🔔 Action Required: {prompt}",
            message_type=MessageType.PROMPT
        )
        self.user_interface.display_message(notification_msg)
    
    def report_security_prompt(self, action_description: str, is_destructive: bool,
                              task_id: str) -> None:
        """Report a security confirmation prompt."""
        level = StatusLevel.WARNING if is_destructive else StatusLevel.INFO
        message = f"Security confirmation required for: {action_description}"
        
        self.report_status(
            level,
            message,
            context={
                "action_description": action_description,
                "is_destructive": is_destructive
            },
            task_id=task_id
        )
    
    def report_error(self, error_message: str, task_id: Optional[str] = None,
                    step_id: Optional[str] = None, 
                    context: Optional[Dict[str, Any]] = None) -> None:
        """Report an error."""
        self.report_status(
            StatusLevel.ERROR,
            f"Error: {error_message}",
            context=context,
            task_id=task_id,
            step_id=step_id
        )
    
    def report_warning(self, warning_message: str, task_id: Optional[str] = None,
                      context: Optional[Dict[str, Any]] = None) -> None:
        """Report a warning."""
        self.report_status(
            StatusLevel.WARNING,
            f"Warning: {warning_message}",
            context=context,
            task_id=task_id
        )
    
    def report_info(self, info_message: str, task_id: Optional[str] = None,
                   context: Optional[Dict[str, Any]] = None) -> None:
        """Report informational message."""
        self.report_status(
            StatusLevel.INFO,
            info_message,
            context=context,
            task_id=task_id
        )
    
    def report_success(self, success_message: str, task_id: Optional[str] = None,
                      context: Optional[Dict[str, Any]] = None) -> None:
        """Report a success message."""
        self.report_status(
            StatusLevel.SUCCESS,
            success_message,
            context=context,
            task_id=task_id
        )
    
    def _start_progress_monitoring(self) -> None:
        """Start background thread for progress monitoring."""
        if self._progress_thread and self._progress_thread.is_alive():
            return
        
        self._stop_progress.clear()
        self._progress_thread = threading.Thread(
            target=self._progress_monitor_loop,
            daemon=True
        )
        self._progress_thread.start()
    
    def _stop_progress_monitoring(self) -> None:
        """Stop background progress monitoring."""
        self._stop_progress.set()
        if self._progress_thread:
            self._progress_thread.join(timeout=1.0)
    
    def _progress_monitor_loop(self) -> None:
        """Background loop for monitoring and reporting progress."""
        while not self._stop_progress.is_set():
            if self._current_task and self._current_task.execution_plan:
                progress = self._current_task.get_progress_percentage()
                current_step = None
                
                if self._current_task.execution_plan.current_step:
                    current_step = self._current_task.execution_plan.current_step.description
                
                # Only report progress if it has changed significantly
                last_progress = getattr(self, '_last_reported_progress', -1)
                if abs(progress - last_progress) >= 5.0:  # Report every 5% change
                    self.report_progress(
                        self._current_task.id,
                        progress,
                        current_step
                    )
                    self._last_reported_progress = progress
            
            # Wait before next check
            self._stop_progress.wait(2.0)  # Check every 2 seconds
    
    def subscribe_to_updates(self, callback: Callable[[StatusUpdate], None]) -> None:
        """Subscribe to status updates."""
        with self._lock:
            self._subscribers.append(callback)
    
    def unsubscribe_from_updates(self, callback: Callable[[StatusUpdate], None]) -> None:
        """Unsubscribe from status updates."""
        with self._lock:
            if callback in self._subscribers:
                self._subscribers.remove(callback)
    
    def get_status_history(self, task_id: Optional[str] = None,
                          level: Optional[StatusLevel] = None,
                          limit: Optional[int] = None) -> List[StatusUpdate]:
        """Get status history with optional filtering."""
        with self._lock:
            history = self._status_history.copy()
        
        # Apply filters
        if task_id:
            history = [s for s in history if s.task_id == task_id]
        
        if level:
            history = [s for s in history if s.level == level]
        
        # Apply limit
        if limit:
            history = history[-limit:]
        
        return history
    
    def clear_history(self) -> None:
        """Clear status history."""
        with self._lock:
            self._status_history.clear()
    
    def get_current_task_status(self) -> Optional[Dict[str, Any]]:
        """Get current task status summary."""
        if not self._current_task:
            return None
        
        return {
            "task_id": self._current_task.id,
            "description": self._current_task.description,
            "status": self._current_task.status.value,
            "progress": self._current_task.get_progress_percentage(),
            "created_at": self._current_task.created_at.isoformat(),
            "updated_at": self._current_task.updated_at.isoformat()
        }