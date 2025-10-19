"""Task-related data models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Any, Optional


class TaskStatus(Enum):
    """Status of a task execution."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    REQUIRES_INPUT = "requires_input"
    CANCELLED = "cancelled"


@dataclass
class TaskStep:
    """Individual step within a task execution plan."""
    id: str
    description: str
    action_type: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    is_completed: bool = False
    error_message: Optional[str] = None
    execution_time: Optional[float] = None
    
    def validate(self) -> bool:
        """Validate the task step."""
        if not self.id or not self.description or not self.action_type:
            return False
        
        return True
    
    def mark_completed(self, execution_time: Optional[float] = None) -> None:
        """Mark the step as completed."""
        self.is_completed = True
        if execution_time is not None:
            self.execution_time = execution_time
    
    def mark_failed(self, error_message: str) -> None:
        """Mark the step as failed with an error message."""
        self.is_completed = False
        self.error_message = error_message


@dataclass
class ExecutionPlan:
    """Plan for executing a multi-step task."""
    task_id: str
    steps: List[TaskStep] = field(default_factory=list)
    current_step_index: int = 0
    context: Dict[str, Any] = field(default_factory=dict)
    fallback_strategies: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    
    @property
    def current_step(self) -> Optional[TaskStep]:
        """Get the current step being executed."""
        if 0 <= self.current_step_index < len(self.steps):
            return self.steps[self.current_step_index]
        return None
    
    def advance_step(self) -> bool:
        """Advance to the next step. Returns True if successful."""
        if self.current_step_index < len(self.steps) - 1:
            self.current_step_index += 1
            return True
        return False
    
    def is_complete(self) -> bool:
        """Check if all steps are completed."""
        return all(step.is_completed for step in self.steps)
    
    def validate(self) -> bool:
        """Validate the execution plan."""
        if not self.task_id or not self.steps:
            return False
        
        # Validate each step
        for step in self.steps:
            if not step.validate():
                return False
        
        # Validate current step index
        if self.current_step_index < 0 or self.current_step_index >= len(self.steps):
            return False
        
        return True
    
    def get_remaining_steps(self) -> List[TaskStep]:
        """Get list of remaining steps to execute."""
        return [step for step in self.steps if not step.is_completed]


@dataclass
class Task:
    """Main task data model."""
    id: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    execution_plan: Optional[ExecutionPlan] = None
    context: Dict[str, Any] = field(default_factory=dict)
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    
    def update_status(self, new_status: TaskStatus) -> None:
        """Update the task status and timestamp."""
        self.status = new_status
        self.updated_at = datetime.now()
        
        if new_status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            self.completed_at = datetime.now()
    
    def add_context(self, key: str, value: Any) -> None:
        """Add context information to the task."""
        self.context[key] = value
        self.updated_at = datetime.now()
    
    def set_result(self, result: Dict[str, Any]) -> None:
        """Set the task result."""
        self.result = result
        self.updated_at = datetime.now()
    
    def set_error(self, error_message: str) -> None:
        """Set an error message for the task."""
        self.error_message = error_message
        self.status = TaskStatus.FAILED
        self.updated_at = datetime.now()
        self.completed_at = datetime.now()
    
    def validate(self) -> bool:
        """Validate the task data."""
        if not self.id or not self.description:
            return False
        
        if self.status not in TaskStatus:
            return False
        
        # Validate execution plan if present
        if self.execution_plan and not self.execution_plan.validate():
            return False
        
        return True
    
    def get_progress_percentage(self) -> float:
        """Get task completion percentage."""
        if not self.execution_plan or not self.execution_plan.steps:
            return 0.0
        
        completed_steps = sum(1 for step in self.execution_plan.steps if step.is_completed)
        return (completed_steps / len(self.execution_plan.steps)) * 100.0