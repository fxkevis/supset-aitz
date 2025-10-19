"""Action-related data models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional


class ActionType(Enum):
    """Types of actions that can be performed."""
    NAVIGATE = "navigate"
    CLICK = "click"
    TYPE = "type"
    SCROLL = "scroll"
    WAIT = "wait"
    EXTRACT = "extract"
    SUBMIT = "submit"
    SELECT = "select"
    HOVER = "hover"
    SCREENSHOT = "screenshot"
    REFRESH = "refresh"
    BACK = "back"
    FORWARD = "forward"


@dataclass
class Action:
    """Represents an action to be performed by the browser."""
    id: str
    type: ActionType
    target: str  # CSS selector, URL, or other target identifier
    parameters: Dict[str, Any] = field(default_factory=dict)
    is_destructive: bool = False
    confidence: float = 1.0
    description: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    executed_at: Optional[datetime] = None
    execution_time: Optional[float] = None
    success: bool = False
    error_message: Optional[str] = None
    result: Optional[Any] = None
    
    def mark_executed(self, success: bool, result: Optional[Any] = None, error: Optional[str] = None) -> None:
        """Mark the action as executed with results."""
        self.executed_at = datetime.now()
        self.success = success
        self.result = result
        self.error_message = error
    
    def set_execution_time(self, execution_time: float) -> None:
        """Set the execution time for the action."""
        self.execution_time = execution_time
    
    def is_safe_action(self) -> bool:
        """Check if this is a safe (non-destructive) action."""
        return not self.is_destructive
    
    def requires_confirmation(self) -> bool:
        """Check if this action requires user confirmation."""
        return self.is_destructive or self.type in [
            ActionType.SUBMIT,  # Form submissions might be destructive
        ]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert action to dictionary representation."""
        return {
            "id": self.id,
            "type": self.type.value,
            "target": self.target,
            "parameters": self.parameters,
            "is_destructive": self.is_destructive,
            "confidence": self.confidence,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "executed_at": self.executed_at.isoformat() if self.executed_at else None,
            "execution_time": self.execution_time,
            "success": self.success,
            "error_message": self.error_message,
            "result": self.result,
        }
    
    def validate(self) -> bool:
        """Validate the action data."""
        if not self.id or not self.target:
            return False
        
        if not isinstance(self.type, ActionType):
            return False
        
        if not 0.0 <= self.confidence <= 1.0:
            return False
        
        # Validate required parameters for specific action types
        if self.type == ActionType.TYPE and "text" not in self.parameters:
            return False
        
        if self.type == ActionType.WAIT and "duration" not in self.parameters:
            return False
        
        return True
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Action':
        """Create Action from dictionary representation."""
        action = cls(
            id=data["id"],
            type=ActionType(data["type"]),
            target=data["target"],
            parameters=data.get("parameters", {}),
            is_destructive=data.get("is_destructive", False),
            confidence=data.get("confidence", 1.0),
            description=data.get("description", ""),
        )
        
        # Set optional fields if present
        if "created_at" in data:
            action.created_at = datetime.fromisoformat(data["created_at"])
        if "executed_at" in data and data["executed_at"]:
            action.executed_at = datetime.fromisoformat(data["executed_at"])
        if "execution_time" in data:
            action.execution_time = data["execution_time"]
        if "success" in data:
            action.success = data["success"]
        if "error_message" in data:
            action.error_message = data["error_message"]
        if "result" in data:
            action.result = data["result"]
        
        return action