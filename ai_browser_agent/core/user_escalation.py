"""User escalation system for unresolvable errors and complex decisions."""

import asyncio
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any, Optional, List, Callable, Union
from dataclasses import dataclass, field

from ai_browser_agent.interfaces.base_interfaces import BaseAgent
from ai_browser_agent.interfaces.user_interface import UserInterface, UserMessage, UserPrompt, MessageType
from ai_browser_agent.models.task import Task, TaskStatus
from ai_browser_agent.models.action import Action


logger = logging.getLogger(__name__)


class EscalationReason(Enum):
    """Reasons for escalating to user."""
    UNRESOLVABLE_ERROR = "unresolvable_error"
    SECURITY_CONCERN = "security_concern"
    AMBIGUOUS_INSTRUCTION = "ambiguous_instruction"
    MULTIPLE_OPTIONS = "multiple_options"
    AUTHENTICATION_REQUIRED = "authentication_required"
    DESTRUCTIVE_ACTION = "destructive_action"
    TASK_CLARIFICATION = "task_clarification"
    TECHNICAL_LIMITATION = "technical_limitation"
    UNEXPECTED_SCENARIO = "unexpected_scenario"
    USER_PREFERENCE_NEEDED = "user_preference_needed"


class EscalationPriority(Enum):
    """Priority levels for user escalation."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EscalationResponse(Enum):
    """Types of responses from user escalation."""
    CONTINUE = "continue"
    RETRY = "retry"
    SKIP = "skip"
    ABORT = "abort"
    MODIFY = "modify"
    MANUAL_TAKEOVER = "manual_takeover"
    PROVIDE_GUIDANCE = "provide_guidance"


@dataclass
class EscalationContext:
    """Context information for user escalation."""
    reason: EscalationReason
    priority: EscalationPriority
    task: Optional[Task]
    action: Optional[Action]
    error_message: Optional[str]
    current_state: Dict[str, Any]
    available_options: List[str]
    recommended_action: Optional[str]
    time_sensitive: bool = False
    requires_immediate_response: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class EscalationResult:
    """Result of user escalation."""
    response_type: EscalationResponse
    user_input: str
    selected_option: Optional[str]
    additional_guidance: Optional[str]
    should_continue: bool
    modified_action: Optional[Action]
    escalation_resolved: bool
    response_time: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class UserEscalationManager(BaseAgent):
    """Manages user escalation for complex decisions and unresolvable errors."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, 
                 user_interface: Optional[UserInterface] = None):
        super().__init__(config)
        self.user_interface = user_interface
        
        # Configuration
        self.escalation_timeout = config.get("escalation_timeout", 300) if config else 300  # 5 minutes
        self.auto_retry_attempts = config.get("auto_retry_attempts", 2) if config else 2
        self.priority_timeout_multiplier = config.get("priority_timeout_multiplier", {
            EscalationPriority.CRITICAL: 0.5,
            EscalationPriority.HIGH: 0.7,
            EscalationPriority.MEDIUM: 1.0,
            EscalationPriority.LOW: 2.0
        }) if config else {
            EscalationPriority.CRITICAL: 0.5,
            EscalationPriority.HIGH: 0.7,
            EscalationPriority.MEDIUM: 1.0,
            EscalationPriority.LOW: 2.0
        }
        
        # Tracking
        self.escalation_history: List[EscalationContext] = []
        self.pending_escalations: Dict[str, EscalationContext] = {}
        self.response_patterns: Dict[EscalationReason, Dict[str, int]] = {}
        
        # Callbacks
        self.escalation_callbacks: Dict[EscalationReason, Callable] = {}
        
        # Initialize escalation templates
        self._initialize_escalation_templates()
    
    def initialize(self) -> None:
        """Initialize the user escalation manager."""
        self.is_active = True
        logger.info("User escalation manager initialized")
    
    def shutdown(self) -> None:
        """Shutdown the user escalation manager."""
        self.is_active = False
        logger.info("User escalation manager shutdown")
    
    def _initialize_escalation_templates(self) -> None:
        """Initialize templates for different escalation scenarios."""
        self.escalation_templates = {
            EscalationReason.UNRESOLVABLE_ERROR: {
                "title": "Unresolvable Error Encountered",
                "message_template": "I encountered an error that I cannot resolve automatically:\n\n{error_message}\n\nHow would you like me to proceed?",
                "default_options": ["Retry", "Skip this step", "Abort task", "Try alternative approach"],
                "requires_immediate": False
            },
            
            EscalationReason.SECURITY_CONCERN: {
                "title": "Security Concern Detected",
                "message_template": "I detected a potential security concern:\n\n{concern_details}\n\nThis action may be risky. How should I proceed?",
                "default_options": ["Proceed with caution", "Skip this action", "Abort task", "Request manual review"],
                "requires_immediate": True
            },
            
            EscalationReason.AMBIGUOUS_INSTRUCTION: {
                "title": "Instruction Clarification Needed",
                "message_template": "The instruction is ambiguous and I need clarification:\n\n{instruction}\n\nPossible interpretations:\n{options}\n\nWhich interpretation is correct?",
                "default_options": [],  # Will be populated with specific interpretations
                "requires_immediate": False
            },
            
            EscalationReason.MULTIPLE_OPTIONS: {
                "title": "Multiple Valid Options Available",
                "message_template": "I found multiple valid options for this step:\n\n{options_description}\n\nWhich option would you prefer?",
                "default_options": [],  # Will be populated with specific options
                "requires_immediate": False
            },
            
            EscalationReason.AUTHENTICATION_REQUIRED: {
                "title": "Authentication Required",
                "message_template": "Authentication is required to continue:\n\n{auth_details}\n\nPlease provide authentication or guidance on how to proceed.",
                "default_options": ["Provide credentials", "Skip authentication", "Use alternative method", "Manual login"],
                "requires_immediate": True
            },
            
            EscalationReason.DESTRUCTIVE_ACTION: {
                "title": "Destructive Action Confirmation",
                "message_template": "I'm about to perform a potentially destructive action:\n\n{action_description}\n\nThis action cannot be undone. Do you want me to proceed?",
                "default_options": ["Proceed", "Cancel", "Modify action", "Manual review"],
                "requires_immediate": True
            },
            
            EscalationReason.TASK_CLARIFICATION: {
                "title": "Task Clarification Needed",
                "message_template": "I need clarification about the task:\n\n{clarification_needed}\n\nCurrent understanding: {current_understanding}\n\nPlease provide guidance.",
                "default_options": ["Confirm understanding", "Provide correction", "Modify task", "Start over"],
                "requires_immediate": False
            },
            
            EscalationReason.TECHNICAL_LIMITATION: {
                "title": "Technical Limitation Encountered",
                "message_template": "I encountered a technical limitation:\n\n{limitation_details}\n\nPossible workarounds:\n{workarounds}\n\nHow would you like to proceed?",
                "default_options": ["Try workaround", "Skip this step", "Manual intervention", "Abort task"],
                "requires_immediate": False
            },
            
            EscalationReason.UNEXPECTED_SCENARIO: {
                "title": "Unexpected Scenario",
                "message_template": "I encountered an unexpected scenario:\n\n{scenario_description}\n\nThis wasn't anticipated in the original plan. How should I handle this?",
                "default_options": ["Adapt and continue", "Seek guidance", "Revert to safe state", "Manual takeover"],
                "requires_immediate": False
            },
            
            EscalationReason.USER_PREFERENCE_NEEDED: {
                "title": "User Preference Required",
                "message_template": "I need your preference for this decision:\n\n{decision_context}\n\nAvailable options:\n{preference_options}",
                "default_options": [],  # Will be populated with preference options
                "requires_immediate": False
            }
        }
    
    async def escalate_to_user(self, context: EscalationContext) -> EscalationResult:
        """Escalate an issue to the user for resolution."""
        if not self.is_active:
            return EscalationResult(
                response_type=EscalationResponse.ABORT,
                user_input="Escalation manager not active",
                selected_option=None,
                additional_guidance=None,
                should_continue=False,
                modified_action=None,
                escalation_resolved=False,
                response_time=0.0
            )
        
        if not self.user_interface:
            logger.error("No user interface available for escalation")
            return await self._handle_no_interface_fallback(context)
        
        try:
            # Record escalation start time
            start_time = datetime.now()
            
            # Add to pending escalations
            escalation_id = f"escalation_{len(self.escalation_history)}"
            self.pending_escalations[escalation_id] = context
            
            # Log escalation
            logger.info(f"Escalating to user: {context.reason.value} (Priority: {context.priority.value})")
            
            # Prepare escalation message
            escalation_message = self._prepare_escalation_message(context)
            
            # Display escalation to user
            await self._display_escalation(context, escalation_message)
            
            # Get user response
            user_response = await self._get_user_response(context, escalation_message)
            
            # Process response
            result = await self._process_user_response(context, user_response, start_time)
            
            # Clean up
            if escalation_id in self.pending_escalations:
                del self.pending_escalations[escalation_id]
            
            # Add to history
            self.escalation_history.append(context)
            
            # Update response patterns
            self._update_response_patterns(context.reason, result.response_type)
            
            logger.info(f"Escalation resolved: {result.response_type.value}")
            return result
            
        except Exception as e:
            logger.error(f"Error in user escalation: {e}")
            return EscalationResult(
                response_type=EscalationResponse.ABORT,
                user_input=f"Escalation error: {str(e)}",
                selected_option=None,
                additional_guidance=None,
                should_continue=False,
                modified_action=None,
                escalation_resolved=False,
                response_time=(datetime.now() - start_time).total_seconds() if 'start_time' in locals() else 0.0
            )
    
    def _prepare_escalation_message(self, context: EscalationContext) -> Dict[str, Any]:
        """Prepare the escalation message for display."""
        template = self.escalation_templates.get(context.reason)
        if not template:
            template = {
                "title": f"User Input Required: {context.reason.value}",
                "message_template": "I need your input to proceed:\n\n{details}",
                "default_options": ["Continue", "Skip", "Abort"],
                "requires_immediate": False
            }
        
        # Format message
        message_vars = {
            "error_message": context.error_message or "Unknown error",
            "concern_details": context.metadata.get("concern_details", "Security concern detected"),
            "instruction": context.metadata.get("instruction", "Current instruction"),
            "options": "\n".join(f"- {opt}" for opt in context.available_options),
            "options_description": context.metadata.get("options_description", "Multiple options available"),
            "auth_details": context.metadata.get("auth_details", "Authentication required"),
            "action_description": context.action.description if context.action else "Unknown action",
            "clarification_needed": context.metadata.get("clarification_needed", "Task clarification needed"),
            "current_understanding": context.metadata.get("current_understanding", "Current task understanding"),
            "limitation_details": context.metadata.get("limitation_details", "Technical limitation encountered"),
            "workarounds": "\n".join(f"- {w}" for w in context.metadata.get("workarounds", [])),
            "scenario_description": context.metadata.get("scenario_description", "Unexpected scenario"),
            "decision_context": context.metadata.get("decision_context", "Decision context"),
            "preference_options": "\n".join(f"- {opt}" for opt in context.available_options),
            "details": context.metadata.get("details", "Additional details needed")
        }
        
        formatted_message = template["message_template"].format(**message_vars)
        
        # Determine options
        options = context.available_options if context.available_options else template["default_options"]
        
        return {
            "title": template["title"],
            "message": formatted_message,
            "options": options,
            "priority": context.priority,
            "requires_immediate": template["requires_immediate"] or context.requires_immediate_response,
            "recommended_action": context.recommended_action,
            "time_sensitive": context.time_sensitive
        }
    
    async def _display_escalation(self, context: EscalationContext, message: Dict[str, Any]) -> None:
        """Display escalation message to user."""
        # Determine message type based on priority
        message_type_map = {
            EscalationPriority.CRITICAL: MessageType.ERROR,
            EscalationPriority.HIGH: MessageType.WARNING,
            EscalationPriority.MEDIUM: MessageType.PROMPT,
            EscalationPriority.LOW: MessageType.INFO
        }
        
        message_type = message_type_map.get(context.priority, MessageType.PROMPT)
        
        # Display title and message
        self.user_interface.display_message(UserMessage(
            content=f"🚨 {message['title']}\n\n{message['message']}",
            message_type=message_type,
            metadata={
                "escalation_reason": context.reason.value,
                "priority": context.priority.value,
                "time_sensitive": message["time_sensitive"],
                "requires_immediate": message["requires_immediate"]
            }
        ))
        
        # Display recommended action if available
        if message["recommended_action"]:
            self.user_interface.display_message(UserMessage(
                content=f"💡 Recommended: {message['recommended_action']}",
                message_type=MessageType.INFO
            ))
    
    async def _get_user_response(self, context: EscalationContext, message: Dict[str, Any]) -> str:
        """Get response from user with timeout handling."""
        # Calculate timeout based on priority
        timeout = self.escalation_timeout * self.priority_timeout_multiplier[context.priority]
        
        # Create user prompt
        prompt = UserPrompt(
            question=f"How would you like me to proceed?",
            options=message["options"],
            default_value=message.get("recommended_action"),
            is_required=True,
            input_type="choice" if message["options"] else "text",
            timeout=timeout
        )
        
        try:
            # Get user input with timeout
            if message["requires_immediate"]:
                # For immediate responses, use shorter timeout
                prompt.timeout = min(timeout, 60)  # Max 1 minute for immediate responses
            
            response = self.user_interface.get_user_input(prompt)
            
            if not response and message["options"]:
                # If no response and options available, use first option as default
                response = message["options"][0]
            
            return response or "continue"
            
        except asyncio.TimeoutError:
            logger.warning(f"User escalation timed out after {timeout}s")
            
            # Handle timeout based on priority
            if context.priority == EscalationPriority.CRITICAL:
                return "abort"  # Abort critical operations on timeout
            elif context.priority == EscalationPriority.HIGH:
                return "skip"   # Skip high priority operations
            else:
                return "continue"  # Continue with medium/low priority
        
        except Exception as e:
            logger.error(f"Error getting user response: {e}")
            return "abort"
    
    async def _process_user_response(self, context: EscalationContext, 
                                   user_response: str, start_time: datetime) -> EscalationResult:
        """Process the user's response and create result."""
        response_time = (datetime.now() - start_time).total_seconds()
        
        # Normalize response
        response_lower = user_response.lower().strip()
        
        # Determine response type
        response_type = EscalationResponse.CONTINUE  # Default
        
        if any(keyword in response_lower for keyword in ["abort", "cancel", "stop"]):
            response_type = EscalationResponse.ABORT
        elif any(keyword in response_lower for keyword in ["retry", "try again"]):
            response_type = EscalationResponse.RETRY
        elif any(keyword in response_lower for keyword in ["skip", "ignore", "bypass"]):
            response_type = EscalationResponse.SKIP
        elif any(keyword in response_lower for keyword in ["modify", "change", "edit"]):
            response_type = EscalationResponse.MODIFY
        elif any(keyword in response_lower for keyword in ["manual", "takeover", "control"]):
            response_type = EscalationResponse.MANUAL_TAKEOVER
        elif any(keyword in response_lower for keyword in ["guidance", "help", "explain"]):
            response_type = EscalationResponse.PROVIDE_GUIDANCE
        
        # Determine if escalation is resolved
        escalation_resolved = response_type in [
            EscalationResponse.CONTINUE,
            EscalationResponse.RETRY,
            EscalationResponse.SKIP,
            EscalationResponse.ABORT
        ]
        
        # Determine if should continue
        should_continue = response_type not in [
            EscalationResponse.ABORT,
            EscalationResponse.MANUAL_TAKEOVER
        ]
        
        # Extract selected option
        selected_option = None
        if context.available_options:
            for option in context.available_options:
                if option.lower() in response_lower:
                    selected_option = option
                    break
        
        # Extract additional guidance
        additional_guidance = None
        if len(user_response) > 20:  # Assume longer responses contain guidance
            additional_guidance = user_response
        
        # Create modified action if needed
        modified_action = None
        if response_type == EscalationResponse.MODIFY and context.action:
            # This would need more sophisticated parsing in a real implementation
            modified_action = context.action  # Placeholder
        
        return EscalationResult(
            response_type=response_type,
            user_input=user_response,
            selected_option=selected_option,
            additional_guidance=additional_guidance,
            should_continue=should_continue,
            modified_action=modified_action,
            escalation_resolved=escalation_resolved,
            response_time=response_time,
            metadata={
                "escalation_reason": context.reason.value,
                "priority": context.priority.value,
                "timeout_used": response_time >= (self.escalation_timeout * 0.9)
            }
        )
    
    async def _handle_no_interface_fallback(self, context: EscalationContext) -> EscalationResult:
        """Handle escalation when no user interface is available."""
        logger.warning("No user interface available, using fallback strategy")
        
        # Use conservative fallback based on escalation reason
        fallback_responses = {
            EscalationReason.SECURITY_CONCERN: EscalationResponse.ABORT,
            EscalationReason.DESTRUCTIVE_ACTION: EscalationResponse.ABORT,
            EscalationReason.AUTHENTICATION_REQUIRED: EscalationResponse.SKIP,
            EscalationReason.UNRESOLVABLE_ERROR: EscalationResponse.SKIP,
            EscalationReason.TECHNICAL_LIMITATION: EscalationResponse.SKIP,
        }
        
        response_type = fallback_responses.get(context.reason, EscalationResponse.CONTINUE)
        
        return EscalationResult(
            response_type=response_type,
            user_input="Automatic fallback (no user interface)",
            selected_option=None,
            additional_guidance="No user interface available for escalation",
            should_continue=response_type != EscalationResponse.ABORT,
            modified_action=None,
            escalation_resolved=True,
            response_time=0.0,
            metadata={"fallback_used": True}
        )
    
    def _update_response_patterns(self, reason: EscalationReason, response: EscalationResponse) -> None:
        """Update response patterns for learning user preferences."""
        if reason not in self.response_patterns:
            self.response_patterns[reason] = {}
        
        response_key = response.value
        self.response_patterns[reason][response_key] = self.response_patterns[reason].get(response_key, 0) + 1
    
    def get_preferred_response(self, reason: EscalationReason) -> Optional[EscalationResponse]:
        """Get the user's preferred response for a given escalation reason."""
        if reason not in self.response_patterns:
            return None
        
        patterns = self.response_patterns[reason]
        if not patterns:
            return None
        
        # Return most common response
        most_common = max(patterns.items(), key=lambda x: x[1])
        return EscalationResponse(most_common[0])
    
    def set_escalation_callback(self, reason: EscalationReason, callback: Callable) -> None:
        """Set a callback for specific escalation reasons."""
        self.escalation_callbacks[reason] = callback
    
    def get_escalation_statistics(self) -> Dict[str, Any]:
        """Get escalation statistics."""
        if not self.escalation_history:
            return {"total_escalations": 0}
        
        total_escalations = len(self.escalation_history)
        
        # Reason distribution
        reason_counts = {}
        priority_counts = {}
        avg_response_times = {}
        
        for context in self.escalation_history:
            reason = context.reason.value
            priority = context.priority.value
            
            reason_counts[reason] = reason_counts.get(reason, 0) + 1
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
        
        # Calculate average response times by reason
        for reason in reason_counts:
            reason_enum = EscalationReason(reason)
            if reason_enum in self.response_patterns:
                # This is a simplified calculation
                avg_response_times[reason] = 30.0  # Placeholder
        
        return {
            "total_escalations": total_escalations,
            "reason_distribution": reason_counts,
            "priority_distribution": priority_counts,
            "response_patterns": {
                reason.value: patterns for reason, patterns in self.response_patterns.items()
            },
            "average_response_times": avg_response_times,
            "pending_escalations": len(self.pending_escalations)
        }
    
    async def create_escalation_context(self, reason: EscalationReason, 
                                      priority: EscalationPriority = EscalationPriority.MEDIUM,
                                      **kwargs) -> EscalationContext:
        """Helper method to create escalation context."""
        return EscalationContext(
            reason=reason,
            priority=priority,
            task=kwargs.get("task"),
            action=kwargs.get("action"),
            error_message=kwargs.get("error_message"),
            current_state=kwargs.get("current_state", {}),
            available_options=kwargs.get("available_options", []),
            recommended_action=kwargs.get("recommended_action"),
            time_sensitive=kwargs.get("time_sensitive", False),
            requires_immediate_response=kwargs.get("requires_immediate_response", False),
            metadata=kwargs.get("metadata", {})
        )