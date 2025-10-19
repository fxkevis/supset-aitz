"""Specialized task handlers for different types of automation tasks."""

from .email_task_handler import EmailTaskHandler
from .ordering_task_handler import OrderingTaskHandler
from .task_handler_registry import TaskHandlerRegistry

__all__ = [
    "EmailTaskHandler",
    "OrderingTaskHandler",
    "TaskHandlerRegistry"
]