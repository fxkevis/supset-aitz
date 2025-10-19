"""Task handler registry for managing specialized task handlers."""

import logging
from typing import Dict, List, Optional, Any, Type
from ai_browser_agent.interfaces.base_interfaces import BaseTaskHandler
from ai_browser_agent.models.task import Task
from ai_browser_agent.handlers.email_task_handler import EmailTaskHandler
from ai_browser_agent.handlers.ordering_task_handler import OrderingTaskHandler


logger = logging.getLogger(__name__)


class TaskHandlerRegistry:
    """Registry for managing and routing tasks to specialized handlers."""
    
    def __init__(self):
        self._handlers: Dict[str, BaseTaskHandler] = {}
        self._handler_classes: Dict[str, Type[BaseTaskHandler]] = {
            "email": EmailTaskHandler,
            "ordering": OrderingTaskHandler
        }
    
    def register_handler(self, handler_type: str, handler: BaseTaskHandler) -> None:
        """Register a task handler."""
        self._handlers[handler_type] = handler
        logger.info(f"Registered task handler: {handler_type}")
    
    def unregister_handler(self, handler_type: str) -> None:
        """Unregister a task handler."""
        if handler_type in self._handlers:
            del self._handlers[handler_type]
            logger.info(f"Unregistered task handler: {handler_type}")
    
    def get_handler(self, handler_type: str) -> Optional[BaseTaskHandler]:
        """Get a specific handler by type."""
        return self._handlers.get(handler_type)
    
    def get_all_handlers(self) -> Dict[str, BaseTaskHandler]:
        """Get all registered handlers."""
        return self._handlers.copy()
    
    async def find_suitable_handler(self, task: Task) -> Optional[BaseTaskHandler]:
        """Find a suitable handler for the given task."""
        for handler_type, handler in self._handlers.items():
            try:
                if await handler.can_handle_task(task):
                    logger.info(f"Found suitable handler for task: {handler_type}")
                    return handler
            except Exception as e:
                logger.error(f"Error checking handler {handler_type}: {e}")
                continue
        
        logger.warning(f"No suitable handler found for task: {task.description}")
        return None
    
    async def execute_task_with_handler(self, task: Task, handler: Optional[BaseTaskHandler] = None) -> Dict[str, Any]:
        """Execute a task using a specific handler or find the best one."""
        if handler is None:
            handler = await self.find_suitable_handler(task)
        
        if handler is None:
            return {
                "error": "No suitable handler found for task",
                "task_description": task.description
            }
        
        try:
            logger.info(f"Executing task with handler: {handler.handler_id}")
            result = await handler.execute_task(task)
            result["handler_used"] = handler.handler_id
            return result
        except Exception as e:
            logger.error(f"Task execution failed with handler {handler.handler_id}: {e}")
            return {
                "error": f"Task execution failed: {str(e)}",
                "handler_used": handler.handler_id,
                "task_description": task.description
            }
    
    def get_handler_capabilities(self) -> Dict[str, Dict[str, Any]]:
        """Get capabilities of all registered handlers."""
        capabilities = {}
        
        for handler_type, handler in self._handlers.items():
            capabilities[handler_type] = handler.get_handler_info()
        
        return capabilities
    
    def get_registry_status(self) -> Dict[str, Any]:
        """Get status of the handler registry."""
        return {
            "registered_handlers": list(self._handlers.keys()),
            "handler_count": len(self._handlers),
            "available_handler_classes": list(self._handler_classes.keys())
        }
    
    def create_handler(self, handler_type: str, browser_controller, context_manager, config: Optional[Dict[str, Any]] = None) -> Optional[BaseTaskHandler]:
        """Create a new handler instance."""
        if handler_type not in self._handler_classes:
            logger.error(f"Unknown handler type: {handler_type}")
            return None
        
        try:
            handler_class = self._handler_classes[handler_type]
            handler = handler_class(browser_controller, context_manager, config)
            logger.info(f"Created handler instance: {handler_type}")
            return handler
        except Exception as e:
            logger.error(f"Failed to create handler {handler_type}: {e}")
            return None
    
    def initialize_default_handlers(self, browser_controller, context_manager, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize and register default handlers."""
        default_handlers = ["email", "ordering"]
        
        for handler_type in default_handlers:
            try:
                handler = self.create_handler(handler_type, browser_controller, context_manager, config)
                if handler:
                    self.register_handler(handler_type, handler)
            except Exception as e:
                logger.error(f"Failed to initialize default handler {handler_type}: {e}")
        
        logger.info(f"Initialized {len(self._handlers)} default handlers")