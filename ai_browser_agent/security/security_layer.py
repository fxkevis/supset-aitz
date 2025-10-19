"""Main security layer that integrates all security components."""

from pathlib import Path
from typing import Optional, Callable

from ..models.action import Action
from .action_validator import ActionValidator, SecurityAssessment
from .user_confirmation import UserConfirmation, SecuritySettings, ConfirmationResult
from .audit_logger import AuditLogger, AuditConfig


class SecurityLayer:
    """
    Main security layer that coordinates action validation, user confirmation,
    and audit logging for the AI browser agent.
    """
    
    def __init__(self, 
                 security_settings: Optional[SecuritySettings] = None,
                 audit_config: Optional[AuditConfig] = None,
                 input_handler: Optional[Callable[[str], str]] = None,
                 session_id: Optional[str] = None):
        """
        Initialize the security layer.
        
        Args:
            security_settings: Configuration for security behavior
            audit_config: Configuration for audit logging
            input_handler: Function to handle user input
            session_id: Current session identifier
        """
        self.validator = ActionValidator()
        self.confirmation = UserConfirmation(security_settings, input_handler)
        self.audit_logger = AuditLogger(audit_config, session_id)
        
    def validate_action(self, action: Action) -> SecurityAssessment:
        """
        Validate an action and assess its security risk.
        
        Args:
            action: The action to validate
            
        Returns:
            SecurityAssessment with risk level and recommendations
        """
        assessment = self.validator.validate_action(action)
        
        # Log the validation
        self.audit_logger.log_action_validation(action, assessment)
        
        return assessment
    
    def request_confirmation(self, action: Action, assessment: SecurityAssessment,
                           timeout_seconds: Optional[int] = None) -> ConfirmationResult:
        """
        Request user confirmation for an action if needed.
        
        Args:
            action: The action requiring confirmation
            assessment: Security assessment of the action
            timeout_seconds: Timeout for confirmation
            
        Returns:
            ConfirmationResult indicating user's decision
        """
        # Create confirmation request
        result = self.confirmation.request_confirmation(action, assessment, timeout_seconds)
        
        # Log the confirmation process
        # Note: The confirmation system logs its own events, but we can add additional logging here
        
        return result
    
    def authorize_action(self, action: Action, timeout_seconds: Optional[int] = None) -> tuple[bool, SecurityAssessment, Optional[ConfirmationResult]]:
        """
        Complete authorization flow: validate action and get confirmation if needed.
        
        Args:
            action: The action to authorize
            timeout_seconds: Timeout for confirmation if needed
            
        Returns:
            Tuple of (authorized, assessment, confirmation_result)
        """
        # Step 1: Validate the action
        assessment = self.validate_action(action)
        
        # Step 2: Check if action is blocked
        if assessment.blocked:
            self.audit_logger.log_action_blocked(action, assessment, "Action blocked by security policy")
            return False, assessment, None
        
        # Step 3: Get confirmation if required
        confirmation_result = None
        if assessment.requires_confirmation:
            confirmation_result = self.request_confirmation(action, assessment, timeout_seconds)
            
            # Check confirmation result
            if confirmation_result != ConfirmationResult.APPROVED:
                reason = f"User confirmation {confirmation_result.value}"
                self.audit_logger.log_action_blocked(action, assessment, reason)
                return False, assessment, confirmation_result
        
        # Action is authorized
        return True, assessment, confirmation_result
    
    def log_action_execution(self, action: Action, success: bool, error: Optional[str] = None) -> None:
        """
        Log the execution of an action.
        
        Args:
            action: The executed action
            success: Whether execution was successful
            error: Error message if execution failed
        """
        self.audit_logger.log_action_execution(action, success, error)
    
    def log_security_violation(self, description: str, details: Optional[dict] = None) -> None:
        """
        Log a security violation.
        
        Args:
            description: Description of the violation
            details: Additional details about the violation
        """
        self.audit_logger.log_security_violation(description, details)
    
    def update_security_settings(self, settings: SecuritySettings) -> None:
        """
        Update security settings.
        
        Args:
            settings: New security settings
        """
        old_settings = self.confirmation.settings
        self.confirmation.update_settings(settings)
        
        # Log the settings change
        self.audit_logger.log_settings_change(
            "security_settings", 
            old_settings.to_dict(), 
            settings.to_dict()
        )
    
    def save_settings(self, filepath: Path) -> None:
        """
        Save security settings to file.
        
        Args:
            filepath: Path to save settings file
        """
        self.confirmation.save_settings(filepath)
    
    def load_settings(self, filepath: Path) -> None:
        """
        Load security settings from file.
        
        Args:
            filepath: Path to settings file
        """
        self.confirmation.load_settings(filepath)
    
    def cleanup(self) -> None:
        """Clean up resources and finalize audit logging."""
        # Clean up expired confirmation requests
        expired = self.confirmation.cleanup_expired_requests()
        if expired:
            self.audit_logger.log_error(f"Cleaned up {len(expired)} expired confirmation requests")
        
        # Clean up old audit logs
        self.audit_logger.cleanup_old_logs()
    
    def shutdown(self) -> None:
        """Shutdown the security layer and clean up resources."""
        self.cleanup()
    
    def get_risk_explanation(self, assessment: SecurityAssessment) -> str:
        """
        Get a human-readable explanation of the risk assessment.
        
        Args:
            assessment: Security assessment to explain
            
        Returns:
            Human-readable risk explanation
        """
        return self.validator.get_risk_explanation(assessment)
    
    def set_user_id(self, user_id: str) -> None:
        """
        Set the current user ID for audit logging.
        
        Args:
            user_id: User identifier
        """
        self.audit_logger.set_user_id(user_id)