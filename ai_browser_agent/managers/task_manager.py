"""Task management and orchestration component."""

import asyncio
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from queue import Queue, Empty
from threading import Lock

from ai_browser_agent.interfaces.base_interfaces import BaseManager
from ai_browser_agent.models.task import Task, TaskStatus, ExecutionPlan, TaskStep
from ai_browser_agent.core.task_planner import TaskPlanner


class TaskQueue:
    """Thread-safe task queue for managing task execution order."""
    
    def __init__(self, max_size: Optional[int] = None):
        self._queue = Queue(maxsize=max_size or 0)
        self._lock = Lock()
        self._task_map = {}  # task_id -> Task mapping for quick lookup
    
    def add_task(self, task: Task) -> None:
        """Add a task to the queue."""
        with self._lock:
            self._queue.put(task)
            self._task_map[task.id] = task
    
    def get_next_task(self, timeout: Optional[float] = None) -> Optional[Task]:
        """Get the next task from the queue."""
        try:
            task = self._queue.get(timeout=timeout)
            return task
        except Empty:
            return None
    
    def get_task_by_id(self, task_id: str) -> Optional[Task]:
        """Get a task by its ID."""
        with self._lock:
            return self._task_map.get(task_id)
    
    def remove_task(self, task_id: str) -> Optional[Task]:
        """Remove a task from tracking."""
        with self._lock:
            return self._task_map.pop(task_id, None)
    
    def get_all_tasks(self) -> List[Task]:
        """Get all tasks currently in the system."""
        with self._lock:
            return list(self._task_map.values())
    
    def size(self) -> int:
        """Get the current queue size."""
        return self._queue.qsize()
    
    def is_empty(self) -> bool:
        """Check if the queue is empty."""
        return self._queue.empty()


class TaskProgressTracker:
    """Tracks progress and status of task execution."""
    
    def __init__(self):
        self._progress_callbacks: List[Callable[[str, Dict[str, Any]], None]] = []
        self._status_history: Dict[str, List[Dict[str, Any]]] = {}
        self._lock = Lock()
    
    def add_progress_callback(self, callback: Callable[[str, Dict[str, Any]], None]) -> None:
        """Add a callback for progress updates."""
        self._progress_callbacks.append(callback)
    
    def update_progress(self, task_id: str, progress_data: Dict[str, Any]) -> None:
        """Update progress for a task."""
        with self._lock:
            # Add timestamp to progress data
            progress_data["timestamp"] = datetime.now()
            
            # Store in history
            if task_id not in self._status_history:
                self._status_history[task_id] = []
            self._status_history[task_id].append(progress_data)
            
            # Notify callbacks
            for callback in self._progress_callbacks:
                try:
                    callback(task_id, progress_data)
                except Exception as e:
                    # Don't let callback errors break progress tracking
                    print(f"Progress callback error: {e}")
    
    def get_progress_history(self, task_id: str) -> List[Dict[str, Any]]:
        """Get progress history for a task."""
        with self._lock:
            return self._status_history.get(task_id, []).copy()
    
    def clear_history(self, task_id: str) -> None:
        """Clear progress history for a task."""
        with self._lock:
            self._status_history.pop(task_id, None)


class TaskContextManager:
    """Manages context and state across multiple task steps."""
    
    def __init__(self):
        self._contexts: Dict[str, Dict[str, Any]] = {}
        self._shared_context: Dict[str, Any] = {}
        self._lock = Lock()
    
    def set_task_context(self, task_id: str, context: Dict[str, Any]) -> None:
        """Set context for a specific task."""
        with self._lock:
            self._contexts[task_id] = context.copy()
    
    def get_task_context(self, task_id: str) -> Dict[str, Any]:
        """Get context for a specific task."""
        with self._lock:
            return self._contexts.get(task_id, {}).copy()
    
    def update_task_context(self, task_id: str, updates: Dict[str, Any]) -> None:
        """Update context for a specific task."""
        with self._lock:
            if task_id not in self._contexts:
                self._contexts[task_id] = {}
            self._contexts[task_id].update(updates)
    
    def set_shared_context(self, key: str, value: Any) -> None:
        """Set shared context available to all tasks."""
        with self._lock:
            self._shared_context[key] = value
    
    def get_shared_context(self) -> Dict[str, Any]:
        """Get shared context."""
        with self._lock:
            return self._shared_context.copy()
    
    def clear_task_context(self, task_id: str) -> None:
        """Clear context for a specific task."""
        with self._lock:
            self._contexts.pop(task_id, None)
    
    def get_combined_context(self, task_id: str) -> Dict[str, Any]:
        """Get combined task and shared context."""
        with self._lock:
            combined = self._shared_context.copy()
            combined.update(self._contexts.get(task_id, {}))
            return combined


class TaskManager(BaseManager):
    """Manages task queue, execution, and orchestration."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, task_planner: Optional[TaskPlanner] = None):
        super().__init__(config)
        self.task_planner = task_planner
        self.task_queue = TaskQueue(max_size=config.get("max_queue_size") if config else None)
        self.progress_tracker = TaskProgressTracker()
        self.context_manager = TaskContextManager()
        
        # Execution state
        self._is_running = False
        self._current_task: Optional[Task] = None
        self._execution_lock = Lock()
        
        # Configuration
        self.max_concurrent_tasks = config.get("max_concurrent_tasks", 1) if config else 1
        self.task_timeout = config.get("task_timeout", 300) if config else 300  # 5 minutes default
    
    def start(self) -> None:
        """Start the task manager."""
        self._is_running = True
    
    def stop(self) -> None:
        """Stop the task manager."""
        self._is_running = False
        
        # Cancel current task if running
        if self._current_task:
            self._current_task.update_status(TaskStatus.CANCELLED)
            self._current_task = None
    
    async def submit_task(self, task_description: str, context: Optional[Dict[str, Any]] = None) -> Task:
        """Submit a new task for execution."""
        # Create task object
        task = Task(
            id=str(uuid.uuid4()),
            description=task_description,
            context=context or {}
        )
        
        # Create execution plan if task planner is available
        if self.task_planner:
            try:
                execution_plan = await self.task_planner.create_plan(task_description, context)
                task.execution_plan = execution_plan
            except Exception as e:
                task.set_error(f"Failed to create execution plan: {str(e)}")
                return task
        
        # Set task context
        self.context_manager.set_task_context(task.id, task.context)
        
        # Add to queue
        self.task_queue.add_task(task)
        
        # Update progress
        self.progress_tracker.update_progress(task.id, {
            "status": "queued",
            "message": "Task added to queue",
            "progress_percentage": 0.0
        })
        
        return task
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of a task."""
        task = self.task_queue.get_task_by_id(task_id)
        if not task:
            return None
        
        progress_history = self.progress_tracker.get_progress_history(task_id)
        latest_progress = progress_history[-1] if progress_history else {}
        
        return {
            "task_id": task.id,
            "description": task.description,
            "status": task.status.value,
            "created_at": task.created_at,
            "updated_at": task.updated_at,
            "completed_at": task.completed_at,
            "progress_percentage": task.get_progress_percentage(),
            "latest_progress": latest_progress,
            "error_message": task.error_message,
            "result": task.result
        }
    
    def get_all_task_statuses(self) -> List[Dict[str, Any]]:
        """Get status of all tasks."""
        tasks = self.task_queue.get_all_tasks()
        return [self.get_task_status(task.id) for task in tasks if task]
    
    async def execute_next_task(self) -> Optional[Task]:
        """Execute the next task in the queue."""
        if not self._is_running:
            return None
        
        # Get next task
        task = self.task_queue.get_next_task(timeout=1.0)
        if not task:
            return None
        
        # Set as current task
        with self._execution_lock:
            self._current_task = task
        
        try:
            await self._execute_task(task)
        except Exception as e:
            task.set_error(f"Task execution failed: {str(e)}")
            self.progress_tracker.update_progress(task.id, {
                "status": "failed",
                "message": f"Execution error: {str(e)}",
                "progress_percentage": 0.0
            })
        finally:
            # Clear current task
            with self._execution_lock:
                self._current_task = None
            
            # Remove from tracking
            self.task_queue.remove_task(task.id)
        
        return task
    
    async def _execute_task(self, task: Task) -> None:
        """Execute a single task."""
        task.update_status(TaskStatus.IN_PROGRESS)
        
        self.progress_tracker.update_progress(task.id, {
            "status": "started",
            "message": "Task execution started",
            "progress_percentage": 0.0
        })
        
        if not task.execution_plan:
            task.set_error("No execution plan available")
            return
        
        execution_plan = task.execution_plan
        total_steps = len(execution_plan.steps)
        
        # Execute each step
        for step_index, step in enumerate(execution_plan.steps):
            if not self._is_running:
                task.update_status(TaskStatus.CANCELLED)
                return
            
            # Update current step
            execution_plan.current_step_index = step_index
            
            # Update progress
            progress_percentage = (step_index / total_steps) * 100
            self.progress_tracker.update_progress(task.id, {
                "status": "executing_step",
                "message": f"Executing step: {step.description}",
                "progress_percentage": progress_percentage,
                "current_step": step_index + 1,
                "total_steps": total_steps,
                "step_description": step.description
            })
            
            # Execute step (this would be handled by the AI Agent Core in practice)
            success = await self._execute_step(task, step)
            
            if success:
                step.mark_completed()
            else:
                step.mark_failed("Step execution failed")
                
                # Try to update plan with alternatives
                if self.task_planner:
                    try:
                        current_state = self.context_manager.get_combined_context(task.id)
                        updated_plan = await self.task_planner.update_plan(execution_plan, current_state)
                        task.execution_plan = updated_plan
                        
                        # Continue with updated plan
                        continue
                    except Exception as e:
                        task.set_error(f"Failed to update execution plan: {str(e)}")
                        return
                else:
                    # No planner available, fail the task
                    task.set_error(f"Step failed: {step.description}")
                    return
        
        # Task completed successfully
        task.update_status(TaskStatus.COMPLETED)
        task.set_result({
            "completed_steps": len([s for s in execution_plan.steps if s.is_completed]),
            "total_steps": len(execution_plan.steps),
            "execution_time": (datetime.now() - task.created_at).total_seconds()
        })
        
        self.progress_tracker.update_progress(task.id, {
            "status": "completed",
            "message": "Task completed successfully",
            "progress_percentage": 100.0
        })
    
    async def _execute_step(self, task: Task, step: TaskStep) -> bool:
        """Execute a single task step. This is a placeholder - actual execution would be handled by AI Agent."""
        # This is a placeholder implementation
        # In the real system, this would delegate to the AI Agent Core
        # which would use the Browser Controller to perform the actual actions
        
        # Simulate step execution
        await asyncio.sleep(0.1)  # Simulate some work
        
        # Update context with step results (placeholder)
        self.context_manager.update_task_context(task.id, {
            f"step_{step.id}_result": "success",
            f"step_{step.id}_timestamp": datetime.now()
        })
        
        # For now, assume all steps succeed (placeholder)
        return True
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a task."""
        task = self.task_queue.get_task_by_id(task_id)
        if not task:
            return False
        
        # If it's the current task, mark for cancellation
        with self._execution_lock:
            if self._current_task and self._current_task.id == task_id:
                self._current_task.update_status(TaskStatus.CANCELLED)
        
        task.update_status(TaskStatus.CANCELLED)
        
        self.progress_tracker.update_progress(task_id, {
            "status": "cancelled",
            "message": "Task cancelled by user",
            "progress_percentage": task.get_progress_percentage()
        })
        
        return True
    
    def pause_task(self, task_id: str) -> bool:
        """Pause a task (mark as requiring input)."""
        task = self.task_queue.get_task_by_id(task_id)
        if not task:
            return False
        
        task.update_status(TaskStatus.REQUIRES_INPUT)
        
        self.progress_tracker.update_progress(task_id, {
            "status": "paused",
            "message": "Task paused - requires user input",
            "progress_percentage": task.get_progress_percentage()
        })
        
        return True
    
    def resume_task(self, task_id: str, user_input: Optional[Dict[str, Any]] = None) -> bool:
        """Resume a paused task."""
        task = self.task_queue.get_task_by_id(task_id)
        if not task or task.status != TaskStatus.REQUIRES_INPUT:
            return False
        
        # Add user input to context if provided
        if user_input:
            self.context_manager.update_task_context(task_id, {"user_input": user_input})
        
        task.update_status(TaskStatus.IN_PROGRESS)
        
        self.progress_tracker.update_progress(task_id, {
            "status": "resumed",
            "message": "Task resumed",
            "progress_percentage": task.get_progress_percentage()
        })
        
        return True
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status."""
        return {
            "is_running": self._is_running,
            "queue_size": self.task_queue.size(),
            "current_task_id": self._current_task.id if self._current_task else None,
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "task_timeout": self.task_timeout
        }
    
    def add_progress_callback(self, callback: Callable[[str, Dict[str, Any]], None]) -> None:
        """Add a callback for task progress updates."""
        self.progress_tracker.add_progress_callback(callback)
    
    def cleanup_completed_tasks(self, max_age_hours: int = 24) -> int:
        """Clean up old completed tasks from memory."""
        cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
        cleaned_count = 0
        
        tasks = self.task_queue.get_all_tasks()
        for task in tasks:
            if (task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED] and
                task.completed_at and task.completed_at.timestamp() < cutoff_time):
                
                self.task_queue.remove_task(task.id)
                self.context_manager.clear_task_context(task.id)
                self.progress_tracker.clear_history(task.id)
                cleaned_count += 1
        
        return cleaned_count