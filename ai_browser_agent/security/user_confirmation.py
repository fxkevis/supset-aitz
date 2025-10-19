"""User confirmation system for destructive actions."""

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Callable, Any
from pathlib import Path

from ..models.action import Action
from .action_validator import SecurityAssessment, SecurityRisk, ActionCategory


class ConfirmationResult(Enum):
    """Result of user confirmation request."""
    APPROVED = "approved"
    DENIED = "denied"
    TIMEOUT = "timeout"
    ERROR = "error"


class ConfirmationMode(Enum):
    """Mode for confirmation requests."""
    INTERACTIVE = "interactive"  # Prompt user for each action
    BATCH = "batch"  # Collect multiple actions and confirm together
    AUTO_APPROVE = "auto_approve"  # Auto-approve based on rules
    AUTO_DENY = "auto_deny"  # Auto-deny all destructive actions


@dataclass
class ConfirmationRequest:
    """Request for user confirmation of an action."""
    id: str
    action: Action
    assessment: SecurityAssessment
    timestamp: datetime = field(default_factory=datetime.now)
    timeout_seconds: int = 300  # 5 minutes default
    result: Optional[ConfirmationResult] = None
    user_response: Optional[str] = None
    response_timestamp: Optional[datetime] = None
    
    def is_expired(self) -> bool:
        """Check if the confirmation request has expired."""
        if self.timeout_seconds <= 0:
            return False
        
        elapsed = (datetime.now() - self.timestamp).total_seconds()
        return elapsed > self.timeout_seconds
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "action": self.action.to_dict(),
            "assessment": {
                "risk_level": self.assessment.risk_level.value,
                "categories": [cat.value for cat in self.assessment.categories],
                "reasons": self.assessment.reasons,
                "requires_confirmation": self.assessment.requires_confirmation,
                "blocked": self.assessment.blocked,
            },
            "timestamp": self.timestamp.isoformat(),
            "timeout_seconds": self.timeout_seconds,
            "result": self.result.value if self.result else None,
            "user_response": self.user_response,
            "response_timestamp": self.response_timestamp.isoformat() if self.response_timestamp else None,
        }


@dataclass
class SecuritySettings:
    """Configuration for security and confirmation behavior."""
    confirmation_mode: ConfirmationMode = ConfirmationMode.INTERACTIVE
    auto_approve_categories: List[ActionCategory] = field(default_factory=list)
    auto_deny_categories: List[ActionCategory] = field(default_factory=list)
    require_confirmation_for_risk_levels: List[SecurityRisk] = field(default_factory=lambda: [SecurityRisk.HIGH, SecurityRisk.CRITICAL])
    default_timeout_seconds: int = 300
    max_batch_size: int = 10
    enable_audit_logging: bool = True
    
    def should_auto_approve(self, assessment: SecurityAssessment) -> bool:
        """Check if action should be auto-approved based on settings."""
        if self.confirmation_mode == ConfirmationMode.AUTO_APPROVE:
            return True
        
        # Check if any category is in auto-approve list
        return any(cat in self.auto_approve_categories for cat in assessment.categories)
    
    def should_auto_deny(self, assessment: SecurityAssessment) -> bool:
        """Check if action should be auto-denied based on settings."""
        if self.confirmation_mode == ConfirmationMode.AUTO_DENY:
            return True
        
        # Check if any category is in auto-deny list
        return any(cat in self.auto_deny_categories for cat in assessment.categories)
    
    def requires_confirmation(self, assessment: SecurityAssessment) -> bool:
        """Check if action requires confirmation based on settings."""
        if self.confirmation_mode in [ConfirmationMode.AUTO_APPROVE, ConfirmationMode.AUTO_DENY]:
            return False
        
        return (assessment.risk_level in self.require_confirmation_for_risk_levels or 
                assessment.requires_confirmation)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "confirmation_mode": self.confirmation_mode.value,
            "auto_approve_categories": [cat.value for cat in self.auto_approve_categories],
            "auto_deny_categories": [cat.value for cat in self.auto_deny_categories],
            "require_confirmation_for_risk_levels": [risk.value for risk in self.require_confirmation_for_risk_levels],
            "default_timeout_seconds": self.default_timeout_seconds,
            "max_batch_size": self.max_batch_size,
            "enable_audit_logging": self.enable_audit_logging,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SecuritySettings':
        """Create SecuritySettings from dictionary."""
        return cls(
            confirmation_mode=ConfirmationMode(data.get("confirmation_mode", "interactive")),
            auto_approve_categories=[ActionCategory(cat) for cat in data.get("auto_approve_categories", [])],
            auto_deny_categories=[ActionCategory(cat) for cat in data.get("auto_deny_categories", [])],
            require_confirmation_for_risk_levels=[SecurityRisk(risk) for risk in data.get("require_confirmation_for_risk_levels", ["high", "critical"])],
            default_timeout_seconds=data.get("default_timeout_seconds", 300),
            max_batch_size=data.get("max_batch_size", 10),
            enable_audit_logging=data.get("enable_audit_logging", True),
        )


class UserConfirmation:
    """Handles user confirmation for potentially destructive actions."""
    
    def __init__(self, settings: Optional[SecuritySettings] = None, 
                 input_handler: Optional[Callable[[str], str]] = None):
        """
        Initialize the user confirmation system.
        
        Args:
            settings: Security settings configuration
            input_handler: Function to handle user input (defaults to built-in input)
        """
        self.settings = settings or SecuritySettings()
        self.input_handler = input_handler or input
        self.pending_requests: Dict[str, ConfirmationRequest] = {}
        self.batch_requests: List[ConfirmationRequest] = []
        
    def request_confirmation(self, action: Action, assessment: SecurityAssessment, 
                           timeout_seconds: Optional[int] = None) -> ConfirmationResult:
        """
        Request user confirmation for an action.
        
        Args:
            action: The action requiring confirmation
            assessment: Security assessment of the action
            timeout_seconds: Timeout for confirmation (uses default if None)
            
        Returns:
            ConfirmationResult indicating user's decision
        """
        # Check if action should be auto-approved or auto-denied
        if self.settings.should_auto_approve(assessment):
            return ConfirmationResult.APPROVED
        
        if self.settings.should_auto_deny(assessment):
            return ConfirmationResult.DENIED
        
        # Check if confirmation is actually required
        if not self.settings.requires_confirmation(assessment):
            return ConfirmationResult.APPROVED
        
        # Create confirmation request
        request = ConfirmationRequest(
            id=f"conf_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{action.id}",
            action=action,
            assessment=assessment,
            timeout_seconds=timeout_seconds or self.settings.default_timeout_seconds
        )
        
        # Handle based on confirmation mode
        if self.settings.confirmation_mode == ConfirmationMode.BATCH:
            return self._handle_batch_confirmation(request)
        else:
            return self._handle_interactive_confirmation(request)
    
    def _handle_interactive_confirmation(self, request: ConfirmationRequest) -> ConfirmationResult:
        """Handle interactive confirmation for a single action."""
        self.pending_requests[request.id] = request
        
        try:
            # Display confirmation prompt
            prompt = self._create_confirmation_prompt(request)
            
            # Get user input
            response = self.input_handler(prompt).strip().lower()
            
            # Process response
            result = self._process_user_response(response)
            
            # Update request
            request.result = result
            request.user_response = response
            request.response_timestamp = datetime.now()
            
            return result
            
        except KeyboardInterrupt:
            request.result = ConfirmationResult.DENIED
            request.user_response = "interrupted"
            request.response_timestamp = datetime.now()
            return ConfirmationResult.DENIED
            
        except Exception as e:
            request.result = ConfirmationResult.ERROR
            request.user_response = f"error: {str(e)}"
            request.response_timestamp = datetime.now()
            return ConfirmationResult.ERROR
            
        finally:
            # Clean up
            if request.id in self.pending_requests:
                del self.pending_requests[request.id]
    
    def _handle_batch_confirmation(self, request: ConfirmationRequest) -> ConfirmationResult:
        """Handle batch confirmation by collecting requests."""
        self.batch_requests.append(request)
        
        # If batch is full, process all requests
        if len(self.batch_requests) >= self.settings.max_batch_size:
            return self._process_batch_requests()
        
        # For now, return approved (batch processing would be handled separately)
        # In a real implementation, this would queue the request
        return ConfirmationResult.APPROVED
    
    def _process_batch_requests(self) -> ConfirmationResult:
        """Process all pending batch requests."""
        if not self.batch_requests:
            return ConfirmationResult.APPROVED
        
        try:
            # Create batch prompt
            prompt = self._create_batch_prompt(self.batch_requests)
            
            # Get user input
            response = self.input_handler(prompt).strip().lower()
            
            # Process response for all requests
            result = self._process_user_response(response)
            
            # Update all requests
            timestamp = datetime.now()
            for request in self.batch_requests:
                request.result = result
                request.user_response = response
                request.response_timestamp = timestamp
            
            return result
            
        except Exception as e:
            # Mark all as error
            timestamp = datetime.now()
            for request in self.batch_requests:
                request.result = ConfirmationResult.ERROR
                request.user_response = f"batch_error: {str(e)}"
                request.response_timestamp = timestamp
            
            return ConfirmationResult.ERROR
            
        finally:
            # Clear batch
            self.batch_requests.clear()
    
    def _create_confirmation_prompt(self, request: ConfirmationRequest) -> str:
        """Create a user-friendly confirmation prompt."""
        action = request.action
        assessment = request.assessment
        
        prompt = "\n" + "="*60 + "\n"
        prompt += "🚨 SECURITY CONFIRMATION REQUIRED 🚨\n"
        prompt += "="*60 + "\n\n"
        
        # Action details
        prompt += f"Action: {action.type.value.upper()}\n"
        prompt += f"Target: {action.target}\n"
        if action.description:
            prompt += f"Description: {action.description}\n"
        
        # Risk assessment
        prompt += f"\nRisk Level: {assessment.risk_level.value.upper()}\n"
        
        if assessment.categories:
            categories = ", ".join([cat.value.title() for cat in assessment.categories])
            prompt += f"Categories: {categories}\n"
        
        if assessment.reasons:
            prompt += "\nSecurity Concerns:\n"
            for reason in assessment.reasons:
                prompt += f"  • {reason}\n"
        
        # Parameters (if any sensitive data, mask it)
        if action.parameters:
            prompt += "\nParameters:\n"
            for key, value in action.parameters.items():
                if key.lower() in ['password', 'token', 'key']:
                    prompt += f"  {key}: [HIDDEN]\n"
                else:
                    prompt += f"  {key}: {str(value)[:100]}{'...' if len(str(value)) > 100 else ''}\n"
        
        prompt += "\n" + "-"*60 + "\n"
        prompt += "Do you want to proceed with this action?\n"
        prompt += "Type 'yes' to approve, 'no' to deny, or 'details' for more info: "
        
        return prompt
    
    def _create_batch_prompt(self, requests: List[ConfirmationRequest]) -> str:
        """Create a prompt for batch confirmation."""
        prompt = "\n" + "="*60 + "\n"
        prompt += f"🚨 BATCH CONFIRMATION REQUIRED ({len(requests)} actions) 🚨\n"
        prompt += "="*60 + "\n\n"
        
        for i, request in enumerate(requests, 1):
            action = request.action
            assessment = request.assessment
            
            prompt += f"{i}. {action.type.value.upper()} - {action.target}\n"
            prompt += f"   Risk: {assessment.risk_level.value.upper()}"
            
            if assessment.categories:
                categories = ", ".join([cat.value for cat in assessment.categories])
                prompt += f" | Categories: {categories}"
            
            prompt += "\n"
            
            if action.description:
                prompt += f"   Description: {action.description}\n"
            
            prompt += "\n"
        
        prompt += "-"*60 + "\n"
        prompt += "Do you want to approve ALL these actions?\n"
        prompt += "Type 'yes' to approve all, 'no' to deny all: "
        
        return prompt
    
    def _process_user_response(self, response: str) -> ConfirmationResult:
        """Process user response and return appropriate result."""
        response = response.lower().strip()
        
        # Positive responses
        if response in ['yes', 'y', 'approve', 'ok', 'proceed', '1', 'true']:
            return ConfirmationResult.APPROVED
        
        # Negative responses
        if response in ['no', 'n', 'deny', 'cancel', 'abort', '0', 'false']:
            return ConfirmationResult.DENIED
        
        # Handle details request (for interactive mode)
        if response in ['details', 'detail', 'info', 'more']:
            # In a real implementation, this would show more details
            # For now, treat as denied to be safe
            return ConfirmationResult.DENIED
        
        # Unknown response - default to denied for safety
        return ConfirmationResult.DENIED
    
    def update_settings(self, settings: SecuritySettings) -> None:
        """Update security settings."""
        self.settings = settings
    
    def get_pending_requests(self) -> List[ConfirmationRequest]:
        """Get all pending confirmation requests."""
        return list(self.pending_requests.values())
    
    def cancel_request(self, request_id: str) -> bool:
        """Cancel a pending confirmation request."""
        if request_id in self.pending_requests:
            request = self.pending_requests[request_id]
            request.result = ConfirmationResult.DENIED
            request.user_response = "cancelled"
            request.response_timestamp = datetime.now()
            del self.pending_requests[request_id]
            return True
        return False
    
    def cleanup_expired_requests(self) -> List[str]:
        """Clean up expired confirmation requests and return their IDs."""
        expired_ids = []
        current_time = datetime.now()
        
        for request_id, request in list(self.pending_requests.items()):
            if request.is_expired():
                request.result = ConfirmationResult.TIMEOUT
                request.response_timestamp = current_time
                expired_ids.append(request_id)
                del self.pending_requests[request_id]
        
        return expired_ids
    
    def save_settings(self, filepath: Path) -> None:
        """Save security settings to file."""
        try:
            with open(filepath, 'w') as f:
                json.dump(self.settings.to_dict(), f, indent=2)
        except Exception as e:
            raise RuntimeError(f"Failed to save security settings: {e}")
    
    def load_settings(self, filepath: Path) -> None:
        """Load security settings from file."""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                self.settings = SecuritySettings.from_dict(data)
        except FileNotFoundError:
            # Use default settings if file doesn't exist
            pass
        except Exception as e:
            raise RuntimeError(f"Failed to load security settings: {e}")