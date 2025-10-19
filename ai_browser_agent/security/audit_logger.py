"""Audit logging system for security events and user confirmations."""

import json
import logging
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import threading
from contextlib import contextmanager

from ..models.action import Action
from .action_validator import SecurityAssessment, SecurityRisk, ActionCategory
from .user_confirmation import ConfirmationRequest, ConfirmationResult


class AuditEventType(Enum):
    """Types of audit events."""
    ACTION_VALIDATED = "action_validated"
    CONFIRMATION_REQUESTED = "confirmation_requested"
    CONFIRMATION_RECEIVED = "confirmation_received"
    ACTION_EXECUTED = "action_executed"
    ACTION_BLOCKED = "action_blocked"
    SECURITY_VIOLATION = "security_violation"
    SETTINGS_CHANGED = "settings_changed"
    SESSION_STARTED = "session_started"
    SESSION_ENDED = "session_ended"
    ERROR_OCCURRED = "error_occurred"


class AuditLevel(Enum):
    """Audit logging levels."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """Represents a security audit event."""
    id: str
    event_type: AuditEventType
    level: AuditLevel
    timestamp: datetime = field(default_factory=datetime.now)
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    action_id: Optional[str] = None
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    risk_level: Optional[SecurityRisk] = None
    categories: List[ActionCategory] = field(default_factory=list)
    confirmation_result: Optional[ConfirmationResult] = None
    execution_success: Optional[bool] = None
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert audit event to dictionary for serialization."""
        data = asdict(self)
        
        # Convert enums to strings
        data['event_type'] = self.event_type.value
        data['level'] = self.level.value
        data['timestamp'] = self.timestamp.isoformat()
        
        if self.risk_level:
            data['risk_level'] = self.risk_level.value
        
        if self.categories:
            data['categories'] = [cat.value for cat in self.categories]
        
        if self.confirmation_result:
            data['confirmation_result'] = self.confirmation_result.value
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AuditEvent':
        """Create AuditEvent from dictionary."""
        # Convert string values back to enums
        event = cls(
            id=data['id'],
            event_type=AuditEventType(data['event_type']),
            level=AuditLevel(data['level']),
            timestamp=datetime.fromisoformat(data['timestamp']),
            session_id=data.get('session_id'),
            user_id=data.get('user_id'),
            action_id=data.get('action_id'),
            message=data.get('message', ''),
            details=data.get('details', {}),
            execution_success=data.get('execution_success'),
            error_message=data.get('error_message'),
        )
        
        if 'risk_level' in data and data['risk_level']:
            event.risk_level = SecurityRisk(data['risk_level'])
        
        if 'categories' in data and data['categories']:
            event.categories = [ActionCategory(cat) for cat in data['categories']]
        
        if 'confirmation_result' in data and data['confirmation_result']:
            event.confirmation_result = ConfirmationResult(data['confirmation_result'])
        
        return event


@dataclass
class AuditConfig:
    """Configuration for audit logging."""
    enabled: bool = True
    log_file_path: Optional[Path] = None
    max_file_size_mb: int = 100
    max_files: int = 10
    log_level: AuditLevel = AuditLevel.INFO
    include_action_details: bool = True
    include_page_content: bool = False  # Can be large, disabled by default
    retention_days: int = 90
    compress_old_logs: bool = True
    real_time_alerts: bool = False
    alert_risk_levels: List[SecurityRisk] = field(default_factory=lambda: [SecurityRisk.HIGH, SecurityRisk.CRITICAL])
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['log_file_path'] = str(self.log_file_path) if self.log_file_path else None
        data['log_level'] = self.log_level.value
        data['alert_risk_levels'] = [risk.value for risk in self.alert_risk_levels]
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AuditConfig':
        """Create AuditConfig from dictionary."""
        config = cls(
            enabled=data.get('enabled', True),
            max_file_size_mb=data.get('max_file_size_mb', 100),
            max_files=data.get('max_files', 10),
            include_action_details=data.get('include_action_details', True),
            include_page_content=data.get('include_page_content', False),
            retention_days=data.get('retention_days', 90),
            compress_old_logs=data.get('compress_old_logs', True),
            real_time_alerts=data.get('real_time_alerts', False),
        )
        
        if 'log_file_path' in data and data['log_file_path']:
            config.log_file_path = Path(data['log_file_path'])
        
        if 'log_level' in data:
            config.log_level = AuditLevel(data['log_level'])
        
        if 'alert_risk_levels' in data:
            config.alert_risk_levels = [SecurityRisk(risk) for risk in data['alert_risk_levels']]
        
        return config


class AuditLogger:
    """Comprehensive audit logging system for security events."""
    
    def __init__(self, config: Optional[AuditConfig] = None, session_id: Optional[str] = None):
        """
        Initialize the audit logger.
        
        Args:
            config: Audit configuration
            session_id: Current session identifier
        """
        self.config = config or AuditConfig()
        self.session_id = session_id or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.user_id: Optional[str] = None
        
        # Thread safety
        self._lock = threading.Lock()
        
        # Setup logging
        self._setup_logging()
        
        # Event counter for unique IDs
        self._event_counter = 0
        
        # Log session start
        if self.config.enabled:
            self.log_session_start()
    
    def _setup_logging(self) -> None:
        """Setup the underlying logging system."""
        if not self.config.enabled or not self.config.log_file_path:
            return
        
        # Create log directory if it doesn't exist
        self.config.log_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Setup rotating file handler
        self.logger = logging.getLogger(f"audit_{self.session_id}")
        self.logger.setLevel(logging.DEBUG)
        
        # Remove existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Create file handler
        handler = logging.FileHandler(self.config.log_file_path)
        handler.setLevel(self._audit_level_to_logging_level(self.config.log_level))
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        
        self.logger.addHandler(handler)
    
    def _audit_level_to_logging_level(self, audit_level: AuditLevel) -> int:
        """Convert audit level to logging level."""
        mapping = {
            AuditLevel.DEBUG: logging.DEBUG,
            AuditLevel.INFO: logging.INFO,
            AuditLevel.WARNING: logging.WARNING,
            AuditLevel.ERROR: logging.ERROR,
            AuditLevel.CRITICAL: logging.CRITICAL,
        }
        return mapping.get(audit_level, logging.INFO)
    
    def _generate_event_id(self) -> str:
        """Generate unique event ID."""
        with self._lock:
            self._event_counter += 1
            return f"audit_{self.session_id}_{self._event_counter:06d}"
    
    def set_user_id(self, user_id: str) -> None:
        """Set the current user ID for audit events."""
        self.user_id = user_id
    
    def log_event(self, event: AuditEvent) -> None:
        """Log an audit event."""
        if not self.config.enabled:
            return
        
        # Set session and user info
        event.session_id = self.session_id
        if self.user_id:
            event.user_id = self.user_id
        
        # Log to file if configured
        if hasattr(self, 'logger'):
            log_level = self._audit_level_to_logging_level(event.level)
            self.logger.log(log_level, json.dumps(event.to_dict(), indent=2))
        
        # Handle real-time alerts
        if (self.config.real_time_alerts and 
            event.risk_level and 
            event.risk_level in self.config.alert_risk_levels):
            self._send_alert(event)
    
    def log_action_validation(self, action: Action, assessment: SecurityAssessment) -> None:
        """Log action validation event."""
        event = AuditEvent(
            id=self._generate_event_id(),
            event_type=AuditEventType.ACTION_VALIDATED,
            level=self._risk_to_audit_level(assessment.risk_level),
            action_id=action.id,
            message=f"Action validated: {action.type.value} on {action.target}",
            details={
                "action_type": action.type.value,
                "target": action.target,
                "description": action.description,
                "parameters": action.parameters if self.config.include_action_details else {},
            },
            risk_level=assessment.risk_level,
            categories=assessment.categories,
        )
        
        if assessment.blocked:
            event.details["blocked"] = True
            event.details["block_reasons"] = assessment.reasons
        
        self.log_event(event)
    
    def log_confirmation_request(self, request: ConfirmationRequest) -> None:
        """Log confirmation request event."""
        event = AuditEvent(
            id=self._generate_event_id(),
            event_type=AuditEventType.CONFIRMATION_REQUESTED,
            level=self._risk_to_audit_level(request.assessment.risk_level),
            action_id=request.action.id,
            message=f"Confirmation requested for {request.action.type.value} action",
            details={
                "request_id": request.id,
                "action_type": request.action.type.value,
                "target": request.action.target,
                "timeout_seconds": request.timeout_seconds,
                "assessment_reasons": request.assessment.reasons,
            },
            risk_level=request.assessment.risk_level,
            categories=request.assessment.categories,
        )
        
        self.log_event(event)
    
    def log_confirmation_response(self, request: ConfirmationRequest) -> None:
        """Log confirmation response event."""
        level = AuditLevel.INFO
        if request.result == ConfirmationResult.DENIED:
            level = AuditLevel.WARNING
        elif request.result in [ConfirmationResult.TIMEOUT, ConfirmationResult.ERROR]:
            level = AuditLevel.ERROR
        
        event = AuditEvent(
            id=self._generate_event_id(),
            event_type=AuditEventType.CONFIRMATION_RECEIVED,
            level=level,
            action_id=request.action.id,
            message=f"Confirmation {request.result.value} for {request.action.type.value} action",
            details={
                "request_id": request.id,
                "user_response": request.user_response,
                "response_time_seconds": (
                    (request.response_timestamp - request.timestamp).total_seconds()
                    if request.response_timestamp else None
                ),
            },
            confirmation_result=request.result,
            risk_level=request.assessment.risk_level,
            categories=request.assessment.categories,
        )
        
        self.log_event(event)
    
    def log_action_execution(self, action: Action, success: bool, error: Optional[str] = None) -> None:
        """Log action execution event."""
        level = AuditLevel.INFO if success else AuditLevel.ERROR
        
        event = AuditEvent(
            id=self._generate_event_id(),
            event_type=AuditEventType.ACTION_EXECUTED,
            level=level,
            action_id=action.id,
            message=f"Action {'executed successfully' if success else 'failed'}: {action.type.value}",
            details={
                "action_type": action.type.value,
                "target": action.target,
                "execution_time": action.execution_time,
                "result": action.result if self.config.include_action_details else None,
            },
            execution_success=success,
            error_message=error,
        )
        
        self.log_event(event)
    
    def log_action_blocked(self, action: Action, assessment: SecurityAssessment, reason: str) -> None:
        """Log blocked action event."""
        event = AuditEvent(
            id=self._generate_event_id(),
            event_type=AuditEventType.ACTION_BLOCKED,
            level=AuditLevel.WARNING,
            action_id=action.id,
            message=f"Action blocked: {action.type.value} on {action.target}",
            details={
                "action_type": action.type.value,
                "target": action.target,
                "block_reason": reason,
                "assessment_reasons": assessment.reasons,
            },
            risk_level=assessment.risk_level,
            categories=assessment.categories,
        )
        
        self.log_event(event)
    
    def log_security_violation(self, description: str, details: Optional[Dict[str, Any]] = None,
                             risk_level: SecurityRisk = SecurityRisk.HIGH) -> None:
        """Log security violation event."""
        event = AuditEvent(
            id=self._generate_event_id(),
            event_type=AuditEventType.SECURITY_VIOLATION,
            level=AuditLevel.CRITICAL,
            message=f"Security violation detected: {description}",
            details=details or {},
            risk_level=risk_level,
        )
        
        self.log_event(event)
    
    def log_settings_change(self, setting_name: str, old_value: Any, new_value: Any,
                          changed_by: Optional[str] = None) -> None:
        """Log security settings change event."""
        event = AuditEvent(
            id=self._generate_event_id(),
            event_type=AuditEventType.SETTINGS_CHANGED,
            level=AuditLevel.WARNING,
            message=f"Security setting changed: {setting_name}",
            details={
                "setting_name": setting_name,
                "old_value": str(old_value),
                "new_value": str(new_value),
                "changed_by": changed_by or self.user_id,
            },
        )
        
        self.log_event(event)
    
    def log_session_start(self) -> None:
        """Log session start event."""
        event = AuditEvent(
            id=self._generate_event_id(),
            event_type=AuditEventType.SESSION_STARTED,
            level=AuditLevel.INFO,
            message=f"Audit session started: {self.session_id}",
            details={
                "session_id": self.session_id,
                "config": self.config.to_dict(),
            },
        )
        
        self.log_event(event)
    
    def log_session_end(self) -> None:
        """Log session end event."""
        event = AuditEvent(
            id=self._generate_event_id(),
            event_type=AuditEventType.SESSION_ENDED,
            level=AuditLevel.INFO,
            message=f"Audit session ended: {self.session_id}",
            details={
                "session_id": self.session_id,
                "total_events": self._event_counter,
            },
        )
        
        self.log_event(event)
    
    def log_error(self, error_message: str, details: Optional[Dict[str, Any]] = None,
                  action_id: Optional[str] = None) -> None:
        """Log error event."""
        event = AuditEvent(
            id=self._generate_event_id(),
            event_type=AuditEventType.ERROR_OCCURRED,
            level=AuditLevel.ERROR,
            action_id=action_id,
            message=f"Error occurred: {error_message}",
            details=details or {},
            error_message=error_message,
        )
        
        self.log_event(event)
    
    def _risk_to_audit_level(self, risk: SecurityRisk) -> AuditLevel:
        """Convert security risk to audit level."""
        mapping = {
            SecurityRisk.SAFE: AuditLevel.DEBUG,
            SecurityRisk.LOW: AuditLevel.INFO,
            SecurityRisk.MEDIUM: AuditLevel.INFO,
            SecurityRisk.HIGH: AuditLevel.WARNING,
            SecurityRisk.CRITICAL: AuditLevel.CRITICAL,
        }
        return mapping.get(risk, AuditLevel.INFO)
    
    def _send_alert(self, event: AuditEvent) -> None:
        """Send real-time alert for high-risk events."""
        # In a real implementation, this could send notifications via:
        # - Email
        # - Slack/Teams
        # - System notifications
        # - External monitoring systems
        
        alert_message = (
            f"SECURITY ALERT: {event.message}\n"
            f"Risk Level: {event.risk_level.value if event.risk_level else 'Unknown'}\n"
            f"Session: {event.session_id}\n"
            f"Time: {event.timestamp.isoformat()}"
        )
        
        # For now, just log to console
        print(f"\n🚨 {alert_message}\n")
    
    def get_events_by_session(self, session_id: Optional[str] = None) -> List[AuditEvent]:
        """Get all events for a specific session."""
        # In a real implementation, this would query the log files or database
        # For now, return empty list as this is a basic implementation
        return []
    
    def get_events_by_risk_level(self, risk_level: SecurityRisk) -> List[AuditEvent]:
        """Get all events with specific risk level."""
        # In a real implementation, this would query the log files or database
        return []
    
    def cleanup_old_logs(self) -> None:
        """Clean up old log files based on retention policy."""
        if not self.config.log_file_path or not self.config.log_file_path.exists():
            return
        
        cutoff_date = datetime.now() - timedelta(days=self.config.retention_days)
        log_dir = self.config.log_file_path.parent
        
        for log_file in log_dir.glob("*.log*"):
            try:
                file_time = datetime.fromtimestamp(log_file.stat().st_mtime)
                if file_time < cutoff_date:
                    log_file.unlink()
            except Exception as e:
                self.log_error(f"Failed to cleanup log file {log_file}: {e}")
    
    @contextmanager
    def audit_context(self, context_name: str, details: Optional[Dict[str, Any]] = None):
        """Context manager for auditing operations."""
        start_time = datetime.now()
        
        # Log context start
        event = AuditEvent(
            id=self._generate_event_id(),
            event_type=AuditEventType.INFO,
            level=AuditLevel.DEBUG,
            message=f"Started context: {context_name}",
            details=details or {},
        )
        self.log_event(event)
        
        try:
            yield self
        except Exception as e:
            # Log context error
            error_event = AuditEvent(
                id=self._generate_event_id(),
                event_type=AuditEventType.ERROR_OCCURRED,
                level=AuditLevel.ERROR,
                message=f"Error in context {context_name}: {str(e)}",
                details={"context": context_name, "error": str(e)},
                error_message=str(e),
            )
            self.log_event(error_event)
            raise
        finally:
            # Log context end
            duration = (datetime.now() - start_time).total_seconds()
            end_event = AuditEvent(
                id=self._generate_event_id(),
                event_type=AuditEventType.INFO,
                level=AuditLevel.DEBUG,
                message=f"Ended context: {context_name}",
                details={"context": context_name, "duration_seconds": duration},
            )
            self.log_event(end_event)
    
    def __del__(self):
        """Cleanup when logger is destroyed."""
        if self.config.enabled:
            try:
                self.log_session_end()
            except Exception:
                pass  # Ignore errors during cleanup