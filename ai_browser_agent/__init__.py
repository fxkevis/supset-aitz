"""
AI Browser Agent - An autonomous web browser automation system.

This package provides AI-powered browser automation capabilities for complex
multi-step tasks including email management, online ordering, and web navigation.
"""

__version__ = "0.1.0"
__author__ = "AI Browser Agent Team"

from .core.ai_agent import AIAgent
from .models.task import Task, TaskStatus
from .models.action import Action, ActionType

__all__ = [
    "AIAgent",
    "Task",
    "TaskStatus", 
    "Action",
    "ActionType",
]