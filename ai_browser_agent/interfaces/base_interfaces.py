"""Base interfaces and abstract classes for all major components."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime


class BaseAgent(ABC):
    """Base class for all agent components."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.created_at = datetime.now()
        self.is_active = False
    
    @abstractmethod
    def initialize(self) -> None:
        """Initialize the agent component."""
        pass
    
    @abstractmethod
    def shutdown(self) -> None:
        """Shutdown the agent component gracefully."""
        pass
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of the agent component."""
        return {
            "is_active": self.is_active,
            "created_at": self.created_at,
            "config": self.config
        }


class BaseController(ABC):
    """Base class for all controller components."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.is_initialized = False
    
    @abstractmethod
    def connect(self) -> None:
        """Establish connection to the controlled resource."""
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from the controlled resource."""
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if connection is active."""
        pass


class BaseManager(ABC):
    """Base class for all manager components."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.managed_resources = []
    
    @abstractmethod
    def start(self) -> None:
        """Start managing resources."""
        pass
    
    @abstractmethod
    def stop(self) -> None:
        """Stop managing resources."""
        pass
    
    def add_resource(self, resource: Any) -> None:
        """Add a resource to be managed."""
        self.managed_resources.append(resource)
    
    def remove_resource(self, resource: Any) -> None:
        """Remove a resource from management."""
        if resource in self.managed_resources:
            self.managed_resources.remove(resource)


class BaseInterface(ABC):
    """Base class for all interface components."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.is_ready = False
    
    @abstractmethod
    def setup(self) -> None:
        """Set up the interface."""
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """Clean up the interface resources."""
        pass


class BaseValidator(ABC):
    """Base class for all validation components."""
    
    def __init__(self, rules: Optional[List[Dict[str, Any]]] = None):
        self.rules = rules or []
    
    @abstractmethod
    def validate(self, data: Any) -> bool:
        """Validate the provided data."""
        pass
    
    @abstractmethod
    def get_validation_errors(self, data: Any) -> List[str]:
        """Get list of validation errors for the data."""
        pass
    
    def add_rule(self, rule: Dict[str, Any]) -> None:
        """Add a validation rule."""
        self.rules.append(rule)


class BaseTaskHandler(ABC):
    """Base class for specialized task handlers."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.handler_id = self.__class__.__name__
        self.created_at = datetime.now()
    
    @abstractmethod
    async def can_handle_task(self, task: Any) -> bool:
        """Check if this handler can process the given task."""
        pass
    
    @abstractmethod
    async def execute_task(self, task: Any) -> Dict[str, Any]:
        """Execute the task and return results."""
        pass
    
    def get_handler_info(self) -> Dict[str, Any]:
        """Get information about this handler."""
        return {
            "handler_id": self.handler_id,
            "handler_type": self.__class__.__name__,
            "created_at": self.created_at,
            "config": self.config
        }