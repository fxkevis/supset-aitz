"""Comprehensive error handling and recovery system."""

import asyncio
import logging
import time
import traceback
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any, Optional, List, Callable, Union, Tuple
from dataclasses import dataclass, field

from ai_browser_agent.interfaces.base_interfaces import BaseAgent
from ai_browser_agent.models.action import Action, ActionType
from ai_browser_agent.models.task import Task, TaskStatus
from ai_browser_agent.core.graceful_degradation import GracefulDegradationManager, DegradationContext, DegradationLevel
from ai_browser_agent.core.user_escalation import UserEscalationManager, EscalationContext, EscalationReason, EscalationPriority
from ai_browser_agent.core.alternative_strategies import AlternativeStrategyManager, FailureScenario


logger = logging.getLogger(__name__)


class ErrorType(Enum):
    """Types of errors that can occur in the system."""
    BROWSER_ERROR = "browser_error"
    AI_MODEL_ERROR = "ai_model_error"
    NETWORK_ERROR = "network_error"
    TASK_ERROR = "task_error"
    SECURITY_ERROR = "security_error"
    TIMEOUT_ERROR = "timeout_error"
    ELEMENT_NOT_FOUND = "element_not_found"
    AUTHENTICATION_ERROR = "authentication_error"
    VALIDATION_ERROR = "validation_error"
    SYSTEM_ERROR = "system_error"


class RecoveryStrategy(Enum):
    """Available recovery strategies."""
    RETRY = "retry"
    RETRY_WITH_BACKOFF = "retry_with_backoff"
    FALLBACK_ACTION = "fallback_action"
    ALTERNATIVE_SELECTOR = "alternative_selector"
    USER_ESCALATION = "user_escalation"
    GRACEFUL_DEGRADATION = "graceful_degradation"
    SKIP_STEP = "skip_step"
    RESTART_COMPONENT = "restart_component"
    ABORT_TASK = "abort_task"


@dataclass
class ErrorContext:
    """Context information for error handling."""
    error: Exception
    error_type: ErrorType
    component: str
    action: Optional[Action] = None
    task: Optional[Task] = None
    page_url: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    retry_count: int = 0
    previous_errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RecoveryResult:
    """Result of a recovery attempt."""
    success: bool
    strategy_used: RecoveryStrategy
    message: str
    new_action: Optional[Action] = None
    should_continue: bool = True
    escalate_to_user: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


class ErrorHandler(BaseAgent):
    """Comprehensive error handling and recovery system."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, 
                 user_interface: Optional[Any] = None):
        super().__init__(config)
        
        # Configuration
        self.max_retries = config.get("max_retries", 3) if config else 3
        self.base_retry_delay = config.get("base_retry_delay", 1.0) if config else 1.0
        self.max_retry_delay = config.get("max_retry_delay", 30.0) if config else 30.0
        self.backoff_multiplier = config.get("backoff_multiplier", 2.0) if config else 2.0
        
        # Error tracking
        self.error_history: List[ErrorContext] = []
        self.component_error_counts: Dict[str, int] = {}
        self.recovery_success_rates: Dict[RecoveryStrategy, float] = {}
        
        # Recovery callbacks
        self.user_escalation_callback: Optional[Callable[[ErrorContext], str]] = None
        self.component_restart_callbacks: Dict[str, Callable[[], bool]] = {}
        
        # Sub-managers
        self.degradation_manager = GracefulDegradationManager(config.get("degradation", {}) if config else {})
        self.escalation_manager = UserEscalationManager(config.get("escalation", {}) if config else {}, user_interface)
        self.strategy_manager = AlternativeStrategyManager(config.get("strategies", {}) if config else {})
        
        # Error patterns and strategies
        self._initialize_error_patterns()
    
    def initialize(self) -> None:
        """Initialize the error handler."""
        self.degradation_manager.initialize()
        self.escalation_manager.initialize()
        self.strategy_manager.initialize()
        self.is_active = True
        logger.info("Error handler initialized")
    
    def shutdown(self) -> None:
        """Shutdown the error handler."""
        self.is_active = False
        self.degradation_manager.shutdown()
        self.escalation_manager.shutdown()
        self.strategy_manager.shutdown()
        logger.info("Error handler shutdown")
    
    def _initialize_error_patterns(self) -> None:
        """Initialize error patterns and their corresponding recovery strategies."""
        self.error_patterns = {
            # Browser errors
            "TimeoutException": {
                "error_type": ErrorType.TIMEOUT_ERROR,
                "strategies": [RecoveryStrategy.RETRY, RecoveryStrategy.RETRY_WITH_BACKOFF]
            },
            "NoSuchElementException": {
                "error_type": ErrorType.ELEMENT_NOT_FOUND,
                "strategies": [RecoveryStrategy.ALTERNATIVE_SELECTOR, RecoveryStrategy.RETRY, RecoveryStrategy.SKIP_STEP]
            },
            "ElementNotInteractableException": {
                "error_type": ErrorType.BROWSER_ERROR,
                "strategies": [RecoveryStrategy.RETRY, RecoveryStrategy.ALTERNATIVE_SELECTOR]
            },
            "WebDriverException": {
                "error_type": ErrorType.BROWSER_ERROR,
                "strategies": [RecoveryStrategy.RESTART_COMPONENT, RecoveryStrategy.RETRY]
            },
            
            # Network errors
            "ConnectionError": {
                "error_type": ErrorType.NETWORK_ERROR,
                "strategies": [RecoveryStrategy.RETRY_WITH_BACKOFF, RecoveryStrategy.USER_ESCALATION]
            },
            "HTTPError": {
                "error_type": ErrorType.NETWORK_ERROR,
                "strategies": [RecoveryStrategy.RETRY, RecoveryStrategy.FALLBACK_ACTION]
            },
            
            # AI Model errors
            "APIError": {
                "error_type": ErrorType.AI_MODEL_ERROR,
                "strategies": [RecoveryStrategy.RETRY_WITH_BACKOFF, RecoveryStrategy.FALLBACK_ACTION]
            },
            "TokenLimitError": {
                "error_type": ErrorType.AI_MODEL_ERROR,
                "strategies": [RecoveryStrategy.GRACEFUL_DEGRADATION, RecoveryStrategy.FALLBACK_ACTION]
            },
            
            # Authentication errors
            "AuthenticationError": {
                "error_type": ErrorType.AUTHENTICATION_ERROR,
                "strategies": [RecoveryStrategy.USER_ESCALATION, RecoveryStrategy.ABORT_TASK]
            },
            
            # Validation errors
            "ValidationError": {
                "error_type": ErrorType.VALIDATION_ERROR,
                "strategies": [RecoveryStrategy.FALLBACK_ACTION, RecoveryStrategy.USER_ESCALATION]
            }
        }
    
    async def handle_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> RecoveryResult:
        """Handle an error and return recovery strategy."""
        if not self.is_active:
            return RecoveryResult(
                success=False,
                strategy_used=RecoveryStrategy.ABORT_TASK,
                message="Error handler is not active"
            )
        
        # Create error context
        error_context = self._create_error_context(error, context)
        
        # Log error
        logger.error(f"Handling error: {error_context.error_type.value} - {str(error)}")
        
        # Add to error history
        self.error_history.append(error_context)
        self._update_component_error_count(error_context.component)
        
        # Determine recovery strategy
        recovery_strategies = self._determine_recovery_strategies(error_context)
        
        # Attempt recovery
        for strategy in recovery_strategies:
            try:
                result = await self._execute_recovery_strategy(strategy, error_context)
                
                # Update success rates
                self._update_recovery_success_rate(strategy, result.success)
                
                if result.success:
                    logger.info(f"Recovery successful using strategy: {strategy.value}")
                    return result
                else:
                    logger.warning(f"Recovery strategy failed: {strategy.value} - {result.message}")
                    
            except Exception as recovery_error:
                logger.error(f"Recovery strategy {strategy.value} raised exception: {recovery_error}")
                continue
        
        # All recovery strategies failed
        logger.error("All recovery strategies failed")
        return RecoveryResult(
            success=False,
            strategy_used=RecoveryStrategy.USER_ESCALATION,
            message="All recovery strategies failed",
            escalate_to_user=True
        )
    
    def _create_error_context(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> ErrorContext:
        """Create error context from exception and additional context."""
        context = context or {}
        
        # Determine error type
        error_type = self._classify_error(error)
        
        # Extract component name
        component = context.get("component", "unknown")
        
        # Create error context
        error_context = ErrorContext(
            error=error,
            error_type=error_type,
            component=component,
            action=context.get("action"),
            task=context.get("task"),
            page_url=context.get("page_url"),
            retry_count=context.get("retry_count", 0),
            metadata=context.get("metadata", {})
        )
        
        # Add previous errors for this component
        error_context.previous_errors = [
            str(ec.error) for ec in self.error_history[-5:]
            if ec.component == component
        ]
        
        return error_context
    
    def _classify_error(self, error: Exception) -> ErrorType:
        """Classify error type based on exception."""
        error_name = error.__class__.__name__
        
        # Check known patterns
        for pattern, config in self.error_patterns.items():
            if pattern in error_name or pattern in str(error):
                return config["error_type"]
        
        # Check by exception type
        if "timeout" in str(error).lower():
            return ErrorType.TIMEOUT_ERROR
        elif "network" in str(error).lower() or "connection" in str(error).lower():
            return ErrorType.NETWORK_ERROR
        elif "element" in str(error).lower():
            return ErrorType.ELEMENT_NOT_FOUND
        elif "auth" in str(error).lower():
            return ErrorType.AUTHENTICATION_ERROR
        elif "validation" in str(error).lower():
            return ErrorType.VALIDATION_ERROR
        
        return ErrorType.SYSTEM_ERROR
    
    def _determine_recovery_strategies(self, error_context: ErrorContext) -> List[RecoveryStrategy]:
        """Determine appropriate recovery strategies for the error."""
        strategies = []
        
        # Get strategies from error patterns
        error_name = error_context.error.__class__.__name__
        for pattern, config in self.error_patterns.items():
            if pattern in error_name or pattern in str(error_context.error):
                strategies.extend(config["strategies"])
                break
        
        # Add context-specific strategies
        if error_context.retry_count == 0:
            # First attempt - try simple retry
            if RecoveryStrategy.RETRY not in strategies:
                strategies.insert(0, RecoveryStrategy.RETRY)
        elif error_context.retry_count < self.max_retries:
            # Multiple failures - use backoff
            if RecoveryStrategy.RETRY_WITH_BACKOFF not in strategies:
                strategies.insert(0, RecoveryStrategy.RETRY_WITH_BACKOFF)
        
        # Component-specific strategies
        if self.component_error_counts.get(error_context.component, 0) > 5:
            # Component having many errors - consider restart
            if RecoveryStrategy.RESTART_COMPONENT not in strategies:
                strategies.append(RecoveryStrategy.RESTART_COMPONENT)
        
        # Task-specific strategies
        if error_context.task and error_context.task.status == TaskStatus.REQUIRES_INPUT:
            strategies.append(RecoveryStrategy.USER_ESCALATION)
        
        # Default fallback
        if not strategies:
            strategies = [RecoveryStrategy.RETRY, RecoveryStrategy.USER_ESCALATION]
        
        # Sort by success rate (if we have data)
        strategies.sort(key=lambda s: self.recovery_success_rates.get(s, 0.5), reverse=True)
        
        return strategies[:3]  # Limit to top 3 strategies
    
    async def _execute_recovery_strategy(self, strategy: RecoveryStrategy, 
                                       error_context: ErrorContext) -> RecoveryResult:
        """Execute a specific recovery strategy."""
        try:
            if strategy == RecoveryStrategy.RETRY:
                return await self._retry_action(error_context)
            
            elif strategy == RecoveryStrategy.RETRY_WITH_BACKOFF:
                return await self._retry_with_backoff(error_context)
            
            elif strategy == RecoveryStrategy.FALLBACK_ACTION:
                return await self._create_fallback_action(error_context)
            
            elif strategy == RecoveryStrategy.ALTERNATIVE_SELECTOR:
                return await self._try_alternative_selector(error_context)
            
            elif strategy == RecoveryStrategy.USER_ESCALATION:
                return await self._escalate_to_user(error_context)
            
            elif strategy == RecoveryStrategy.GRACEFUL_DEGRADATION:
                return await self._graceful_degradation(error_context)
            
            elif strategy == RecoveryStrategy.SKIP_STEP:
                return await self._skip_step(error_context)
            
            elif strategy == RecoveryStrategy.RESTART_COMPONENT:
                return await self._restart_component(error_context)
            
            elif strategy == RecoveryStrategy.ABORT_TASK:
                return await self._abort_task(error_context)
            
            else:
                return RecoveryResult(
                    success=False,
                    strategy_used=strategy,
                    message=f"Unknown recovery strategy: {strategy.value}"
                )
                
        except Exception as e:
            logger.error(f"Error executing recovery strategy {strategy.value}: {e}")
            return RecoveryResult(
                success=False,
                strategy_used=strategy,
                message=f"Recovery strategy execution failed: {str(e)}"
            )
    
    async def _retry_action(self, error_context: ErrorContext) -> RecoveryResult:
        """Simple retry of the failed action."""
        if error_context.retry_count >= self.max_retries:
            return RecoveryResult(
                success=False,
                strategy_used=RecoveryStrategy.RETRY,
                message=f"Maximum retries ({self.max_retries}) exceeded"
            )
        
        # Small delay before retry
        await asyncio.sleep(0.5)
        
        return RecoveryResult(
            success=True,
            strategy_used=RecoveryStrategy.RETRY,
            message="Retrying action",
            new_action=error_context.action,
            metadata={"retry_count": error_context.retry_count + 1}
        )
    
    async def _retry_with_backoff(self, error_context: ErrorContext) -> RecoveryResult:
        """Retry with exponential backoff."""
        if error_context.retry_count >= self.max_retries:
            return RecoveryResult(
                success=False,
                strategy_used=RecoveryStrategy.RETRY_WITH_BACKOFF,
                message=f"Maximum retries ({self.max_retries}) exceeded"
            )
        
        # Calculate backoff delay
        delay = min(
            self.base_retry_delay * (self.backoff_multiplier ** error_context.retry_count),
            self.max_retry_delay
        )
        
        logger.info(f"Retrying with backoff delay: {delay:.2f}s")
        await asyncio.sleep(delay)
        
        return RecoveryResult(
            success=True,
            strategy_used=RecoveryStrategy.RETRY_WITH_BACKOFF,
            message=f"Retrying with {delay:.2f}s backoff",
            new_action=error_context.action,
            metadata={"retry_count": error_context.retry_count + 1, "backoff_delay": delay}
        )
    
    async def _create_fallback_action(self, error_context: ErrorContext) -> RecoveryResult:
        """Create a fallback action based on the failed action."""
        if not error_context.action:
            return RecoveryResult(
                success=False,
                strategy_used=RecoveryStrategy.FALLBACK_ACTION,
                message="No action to create fallback for"
            )
        
        action = error_context.action
        fallback_action = None
        
        # Create fallback based on action type
        if action.type == ActionType.CLICK:
            # Try double-click or enter key as fallback
            fallback_action = Action(
                id=f"{action.id}_fallback",
                type=ActionType.TYPE,
                target=action.target,
                parameters={"text": "\n"},  # Enter key
                description=f"Fallback: Press Enter on {action.target}"
            )
        
        elif action.type == ActionType.TYPE:
            # Try clicking first then typing
            fallback_action = Action(
                id=f"{action.id}_fallback",
                type=ActionType.CLICK,
                target=action.target,
                description=f"Fallback: Click before typing on {action.target}"
            )
        
        elif action.type == ActionType.NAVIGATE:
            # Try refreshing current page
            fallback_action = Action(
                id=f"{action.id}_fallback",
                type=ActionType.REFRESH,
                target="",
                description="Fallback: Refresh page before navigation"
            )
        
        if fallback_action:
            return RecoveryResult(
                success=True,
                strategy_used=RecoveryStrategy.FALLBACK_ACTION,
                message=f"Created fallback action: {fallback_action.description}",
                new_action=fallback_action
            )
        
        return RecoveryResult(
            success=False,
            strategy_used=RecoveryStrategy.FALLBACK_ACTION,
            message=f"No fallback available for action type: {action.type.value}"
        )
    
    async def _try_alternative_selector(self, error_context: ErrorContext) -> RecoveryResult:
        """Try alternative selectors for element not found errors."""
        if not error_context.action or error_context.error_type != ErrorType.ELEMENT_NOT_FOUND:
            return RecoveryResult(
                success=False,
                strategy_used=RecoveryStrategy.ALTERNATIVE_SELECTOR,
                message="Not applicable for this error type"
            )
        
        action = error_context.action
        original_selector = action.target
        
        # Generate alternative selectors
        alternative_selectors = self._generate_alternative_selectors(original_selector)
        
        if alternative_selectors:
            # Use the first alternative
            new_selector = alternative_selectors[0]
            
            # Create new action with alternative selector
            new_action = Action(
                id=f"{action.id}_alt_selector",
                type=action.type,
                target=new_selector,
                parameters=action.parameters.copy(),
                description=f"Alternative selector: {new_selector}",
                confidence=action.confidence * 0.8  # Slightly lower confidence
            )
            
            return RecoveryResult(
                success=True,
                strategy_used=RecoveryStrategy.ALTERNATIVE_SELECTOR,
                message=f"Trying alternative selector: {new_selector}",
                new_action=new_action,
                metadata={"original_selector": original_selector, "alternatives": alternative_selectors}
            )
        
        return RecoveryResult(
            success=False,
            strategy_used=RecoveryStrategy.ALTERNATIVE_SELECTOR,
            message="No alternative selectors available"
        )
    
    def _generate_alternative_selectors(self, original_selector: str) -> List[str]:
        """Generate alternative CSS selectors."""
        alternatives = []
        
        # If it's an ID selector, try class-based alternatives
        if original_selector.startswith("#"):
            element_id = original_selector[1:]
            alternatives.extend([
                f'[id="{element_id}"]',
                f'*[id*="{element_id}"]',
                f'input[id="{element_id}"]',
                f'button[id="{element_id}"]'
            ])
        
        # If it's a class selector, try variations
        elif original_selector.startswith("."):
            class_name = original_selector[1:]
            alternatives.extend([
                f'[class*="{class_name}"]',
                f'*[class~="{class_name}"]',
                f'div.{class_name}',
                f'span.{class_name}'
            ])
        
        # If it's an attribute selector, try variations
        elif "[" in original_selector:
            alternatives.extend([
                original_selector.replace("=", "*="),
                original_selector.replace("[", "*["),
                f"*{original_selector}"
            ])
        
        # Generic alternatives
        alternatives.extend([
            f"{original_selector}, {original_selector}:enabled",
            f"{original_selector}, {original_selector}:visible",
            f"*:contains('{original_selector}')" if not original_selector.startswith(("#", ".", "[")) else None
        ])
        
        # Remove None values and duplicates
        alternatives = list(filter(None, alternatives))
        return list(dict.fromkeys(alternatives))  # Remove duplicates while preserving order
    
    async def _escalate_to_user(self, error_context: ErrorContext) -> RecoveryResult:
        """Escalate error to user for manual intervention."""
        if not self.user_escalation_callback:
            return RecoveryResult(
                success=False,
                strategy_used=RecoveryStrategy.USER_ESCALATION,
                message="No user escalation callback available",
                escalate_to_user=True
            )
        
        try:
            # Prepare user prompt
            error_message = str(error_context.error)
            context_info = f"Component: {error_context.component}"
            if error_context.action:
                context_info += f", Action: {error_context.action.description}"
            if error_context.page_url:
                context_info += f", Page: {error_context.page_url}"
            
            user_response = self.user_escalation_callback(error_context)
            
            return RecoveryResult(
                success=True,
                strategy_used=RecoveryStrategy.USER_ESCALATION,
                message=f"User guidance received: {user_response}",
                escalate_to_user=True,
                metadata={"user_response": user_response}
            )
            
        except Exception as e:
            logger.error(f"User escalation failed: {e}")
            return RecoveryResult(
                success=False,
                strategy_used=RecoveryStrategy.USER_ESCALATION,
                message=f"User escalation failed: {str(e)}",
                escalate_to_user=True
            )
    
    async def _graceful_degradation(self, error_context: ErrorContext) -> RecoveryResult:
        """Implement graceful degradation by simplifying the action."""
        if not error_context.action:
            return RecoveryResult(
                success=False,
                strategy_used=RecoveryStrategy.GRACEFUL_DEGRADATION,
                message="No action to degrade"
            )
        
        action = error_context.action
        
        # Create simplified version of the action
        if action.type == ActionType.TYPE and len(action.parameters.get("text", "")) > 100:
            # Truncate long text
            simplified_text = action.parameters["text"][:50] + "..."
            simplified_action = Action(
                id=f"{action.id}_degraded",
                type=action.type,
                target=action.target,
                parameters={"text": simplified_text},
                description=f"Degraded: Shortened text input"
            )
            
            return RecoveryResult(
                success=True,
                strategy_used=RecoveryStrategy.GRACEFUL_DEGRADATION,
                message="Simplified action by shortening text",
                new_action=simplified_action
            )
        
        elif action.type == ActionType.EXTRACT:
            # Simplify extraction to basic text only
            simplified_action = Action(
                id=f"{action.id}_degraded",
                type=ActionType.EXTRACT,
                target="body",
                parameters={"extract_type": "text_only"},
                description="Degraded: Basic text extraction only"
            )
            
            return RecoveryResult(
                success=True,
                strategy_used=RecoveryStrategy.GRACEFUL_DEGRADATION,
                message="Simplified extraction to text only",
                new_action=simplified_action
            )
        
        return RecoveryResult(
            success=False,
            strategy_used=RecoveryStrategy.GRACEFUL_DEGRADATION,
            message=f"No degradation available for action type: {action.type.value}"
        )
    
    async def _skip_step(self, error_context: ErrorContext) -> RecoveryResult:
        """Skip the current step and continue with the next one."""
        return RecoveryResult(
            success=True,
            strategy_used=RecoveryStrategy.SKIP_STEP,
            message="Skipping failed step",
            should_continue=True,
            metadata={"skipped_action": error_context.action.id if error_context.action else None}
        )
    
    async def _restart_component(self, error_context: ErrorContext) -> RecoveryResult:
        """Restart the component that caused the error."""
        component = error_context.component
        
        if component in self.component_restart_callbacks:
            try:
                restart_callback = self.component_restart_callbacks[component]
                success = restart_callback()
                
                if success:
                    # Reset error count for this component
                    self.component_error_counts[component] = 0
                    
                    return RecoveryResult(
                        success=True,
                        strategy_used=RecoveryStrategy.RESTART_COMPONENT,
                        message=f"Component {component} restarted successfully"
                    )
                else:
                    return RecoveryResult(
                        success=False,
                        strategy_used=RecoveryStrategy.RESTART_COMPONENT,
                        message=f"Failed to restart component {component}"
                    )
                    
            except Exception as e:
                logger.error(f"Error restarting component {component}: {e}")
                return RecoveryResult(
                    success=False,
                    strategy_used=RecoveryStrategy.RESTART_COMPONENT,
                    message=f"Component restart failed: {str(e)}"
                )
        
        return RecoveryResult(
            success=False,
            strategy_used=RecoveryStrategy.RESTART_COMPONENT,
            message=f"No restart callback available for component: {component}"
        )
    
    async def _abort_task(self, error_context: ErrorContext) -> RecoveryResult:
        """Abort the current task due to unrecoverable error."""
        return RecoveryResult(
            success=False,
            strategy_used=RecoveryStrategy.ABORT_TASK,
            message="Task aborted due to unrecoverable error",
            should_continue=False,
            escalate_to_user=True
        )
    
    def _update_component_error_count(self, component: str) -> None:
        """Update error count for a component."""
        self.component_error_counts[component] = self.component_error_counts.get(component, 0) + 1
    
    def _update_recovery_success_rate(self, strategy: RecoveryStrategy, success: bool) -> None:
        """Update success rate for a recovery strategy."""
        if strategy not in self.recovery_success_rates:
            self.recovery_success_rates[strategy] = 0.5  # Start with neutral rate
        
        # Simple moving average
        current_rate = self.recovery_success_rates[strategy]
        new_rate = current_rate * 0.9 + (1.0 if success else 0.0) * 0.1
        self.recovery_success_rates[strategy] = new_rate
    
    def set_user_escalation_callback(self, callback: Callable[[ErrorContext], str]) -> None:
        """Set callback for user escalation."""
        self.user_escalation_callback = callback
    
    def set_component_restart_callback(self, component: str, callback: Callable[[], bool]) -> None:
        """Set restart callback for a component."""
        self.component_restart_callbacks[component] = callback
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error handling statistics."""
        total_errors = len(self.error_history)
        
        if total_errors == 0:
            return {"total_errors": 0}
        
        # Error type distribution
        error_type_counts = {}
        for error_context in self.error_history:
            error_type = error_context.error_type.value
            error_type_counts[error_type] = error_type_counts.get(error_type, 0) + 1
        
        # Component error distribution
        component_errors = self.component_error_counts.copy()
        
        # Recent error rate (last hour)
        recent_errors = [
            ec for ec in self.error_history
            if ec.timestamp > datetime.now() - timedelta(hours=1)
        ]
        
        return {
            "total_errors": total_errors,
            "recent_errors_last_hour": len(recent_errors),
            "error_type_distribution": error_type_counts,
            "component_error_counts": component_errors,
            "recovery_success_rates": {
                strategy.value: rate for strategy, rate in self.recovery_success_rates.items()
            },
            "most_problematic_component": max(component_errors.items(), key=lambda x: x[1])[0] if component_errors else None
        }
    
    def clear_error_history(self) -> None:
        """Clear error history (useful for testing or reset)."""
        self.error_history.clear()
        self.component_error_counts.clear()
        logger.info("Error history cleared")
    
    def get_recent_errors(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent errors for debugging."""
        recent_errors = self.error_history[-limit:]
        
        return [
            {
                "timestamp": ec.timestamp.isoformat(),
                "error_type": ec.error_type.value,
                "component": ec.component,
                "error_message": str(ec.error),
                "action_id": ec.action.id if ec.action else None,
                "task_id": ec.task.id if ec.task else None,
                "retry_count": ec.retry_count
            }
            for ec in recent_errors
        ]
    
    async def handle_unresolvable_error(self, error_context: ErrorContext) -> RecoveryResult:
        """Handle errors that cannot be resolved through normal recovery strategies."""
        logger.warning(f"Handling unresolvable error: {error_context.error_type.value}")
        
        # Check if graceful degradation is appropriate
        if error_context.task:
            degradation_context = DegradationContext(
                task=error_context.task,
                failed_actions=[error_context.action] if error_context.action else [],
                current_progress=0.5,  # Estimate based on context
                error_count=error_context.retry_count + 1,
                time_elapsed=300.0,  # Estimate
                available_alternatives=[]
            )
            
            degradation_needed, degradation_level = await self.degradation_manager.assess_degradation_need(degradation_context)
            
            if degradation_needed:
                logger.info(f"Attempting graceful degradation at level: {degradation_level.value}")
                degradation_result = await self.degradation_manager.execute_partial_completion(
                    degradation_context, degradation_level
                )
                
                if degradation_result.success:
                    return RecoveryResult(
                        success=True,
                        strategy_used=RecoveryStrategy.GRACEFUL_DEGRADATION,
                        message=f"Graceful degradation successful: {degradation_result.message}",
                        should_continue=True,
                        metadata={
                            "degradation_result": degradation_result,
                            "completion_percentage": degradation_result.completion_percentage
                        }
                    )
        
        # If degradation not appropriate or failed, escalate to user
        escalation_context = EscalationContext(
            reason=EscalationReason.UNRESOLVABLE_ERROR,
            priority=EscalationPriority.HIGH,
            task=error_context.task,
            action=error_context.action,
            error_message=str(error_context.error),
            current_state={"component": error_context.component, "retry_count": error_context.retry_count},
            available_options=["Retry", "Skip", "Abort", "Manual intervention"],
            recommended_action="Manual intervention"
        )
        
        escalation_result = await self.escalation_manager.escalate_to_user(escalation_context)
        
        return RecoveryResult(
            success=escalation_result.escalation_resolved,
            strategy_used=RecoveryStrategy.USER_ESCALATION,
            message=f"User escalation: {escalation_result.user_input}",
            should_continue=escalation_result.should_continue,
            escalate_to_user=True,
            metadata={"escalation_result": escalation_result}
        )
    
    async def try_alternative_strategies(self, error_context: ErrorContext) -> RecoveryResult:
        """Try alternative strategies for common failure scenarios."""
        if not error_context.action:
            return RecoveryResult(
                success=False,
                strategy_used=RecoveryStrategy.FALLBACK_ACTION,
                message="No action available for alternative strategies"
            )
        
        # Map error types to failure scenarios
        scenario_mapping = {
            ErrorType.ELEMENT_NOT_FOUND: FailureScenario.ELEMENT_NOT_FOUND,
            ErrorType.BROWSER_ERROR: FailureScenario.ELEMENT_NOT_CLICKABLE,
            ErrorType.TIMEOUT_ERROR: FailureScenario.PAGE_LOAD_TIMEOUT,
            ErrorType.NETWORK_ERROR: FailureScenario.NETWORK_ERROR,
            ErrorType.AUTHENTICATION_ERROR: FailureScenario.AUTHENTICATION_FAILED
        }
        
        failure_scenario = scenario_mapping.get(error_context.error_type)
        if not failure_scenario:
            return RecoveryResult(
                success=False,
                strategy_used=RecoveryStrategy.FALLBACK_ACTION,
                message=f"No alternative strategies for error type: {error_context.error_type.value}"
            )
        
        # Get alternative strategies
        context_dict = {
            "page_url": error_context.page_url,
            "component": error_context.component,
            "retry_count": error_context.retry_count
        }
        
        strategies = await self.strategy_manager.get_alternative_strategies(
            failure_scenario, error_context.action, context_dict
        )
        
        if not strategies:
            return RecoveryResult(
                success=False,
                strategy_used=RecoveryStrategy.FALLBACK_ACTION,
                message="No alternative strategies available"
            )
        
        # Try the best strategy
        best_strategy = strategies[0]
        logger.info(f"Trying alternative strategy: {best_strategy.name}")
        
        # For now, return success with the strategy (actual execution would be done by the caller)
        return RecoveryResult(
            success=True,
            strategy_used=RecoveryStrategy.ALTERNATIVE_SELECTOR,
            message=f"Alternative strategy available: {best_strategy.description}",
            new_action=best_strategy.actions[0] if best_strategy.actions else None,
            metadata={
                "strategy": best_strategy,
                "available_strategies": [s.name for s in strategies]
            }
        )
    
    async def assess_partial_completion(self, task: Task, failed_actions: List[Action], 
                                      current_progress: float) -> Dict[str, Any]:
        """Assess whether partial completion is viable for a task."""
        degradation_context = DegradationContext(
            task=task,
            failed_actions=failed_actions,
            current_progress=current_progress,
            error_count=len(failed_actions),
            time_elapsed=300.0,  # Estimate or calculate from task
            available_alternatives=[]
        )
        
        degradation_needed, degradation_level = await self.degradation_manager.assess_degradation_need(degradation_context)
        
        if degradation_needed:
            partial_result = await self.degradation_manager.execute_partial_completion(
                degradation_context, degradation_level
            )
            
            return {
                "viable": True,
                "degradation_level": degradation_level.value,
                "completion_percentage": partial_result.completion_percentage,
                "completed_steps": partial_result.completed_steps,
                "skipped_steps": partial_result.skipped_steps,
                "recommendations": partial_result.recommendations,
                "message": partial_result.message
            }
        
        return {
            "viable": False,
            "reason": "Degradation not needed or not viable",
            "current_progress": current_progress
        }
    
    def create_comprehensive_error_report(self, error_context: ErrorContext, 
                                        recovery_result: RecoveryResult) -> str:
        """Create a comprehensive error report including all recovery attempts."""
        report_lines = [
            "Comprehensive Error Report",
            "=" * 30,
            "",
            f"Error Type: {error_context.error_type.value}",
            f"Component: {error_context.component}",
            f"Error Message: {str(error_context.error)}",
            f"Timestamp: {error_context.timestamp.isoformat()}",
            f"Retry Count: {error_context.retry_count}",
            ""
        ]
        
        if error_context.action:
            report_lines.extend([
                "Failed Action:",
                f"  ID: {error_context.action.id}",
                f"  Type: {error_context.action.type.value}",
                f"  Target: {error_context.action.target}",
                f"  Description: {error_context.action.description}",
                ""
            ])
        
        if error_context.task:
            report_lines.extend([
                "Task Context:",
                f"  ID: {error_context.task.id}",
                f"  Description: {error_context.task.description}",
                f"  Status: {error_context.task.status.value}",
                ""
            ])
        
        report_lines.extend([
            "Recovery Attempt:",
            f"  Strategy Used: {recovery_result.strategy_used.value}",
            f"  Success: {recovery_result.success}",
            f"  Message: {recovery_result.message}",
            f"  Should Continue: {recovery_result.should_continue}",
            ""
        ])
        
        if recovery_result.escalate_to_user:
            report_lines.append("⚠️  User intervention required")
        
        if recovery_result.metadata:
            report_lines.extend([
                "Additional Information:",
                f"  {recovery_result.metadata}",
                ""
            ])
        
        # Add statistics
        stats = self.get_error_statistics()
        if stats.get("total_errors", 0) > 0:
            report_lines.extend([
                "Error Statistics:",
                f"  Total Errors: {stats['total_errors']}",
                f"  Recent Errors (1h): {stats['recent_errors_last_hour']}",
                f"  Most Problematic Component: {stats.get('most_problematic_component', 'N/A')}",
                ""
            ])
        
        return "\n".join(report_lines)