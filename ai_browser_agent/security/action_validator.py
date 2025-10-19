"""Action validation and security assessment for browser actions."""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Set, Pattern
from urllib.parse import urlparse

from ..models.action import Action, ActionType


class SecurityRisk(Enum):
    """Security risk levels for actions."""
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ActionCategory(Enum):
    """Categories of potentially destructive actions."""
    PAYMENT = "payment"
    DELETION = "deletion"
    MODIFICATION = "modification"
    SUBMISSION = "submission"
    NAVIGATION = "navigation"
    AUTHENTICATION = "authentication"
    DOWNLOAD = "download"
    UPLOAD = "upload"


@dataclass
class SecurityAssessment:
    """Result of security assessment for an action."""
    risk_level: SecurityRisk
    categories: List[ActionCategory]
    reasons: List[str]
    requires_confirmation: bool
    blocked: bool = False
    
    def is_safe(self) -> bool:
        """Check if the action is considered safe."""
        return self.risk_level == SecurityRisk.SAFE and not self.blocked
    
    def is_destructive(self) -> bool:
        """Check if the action is considered destructive."""
        return self.risk_level in [SecurityRisk.HIGH, SecurityRisk.CRITICAL] or self.blocked


class ActionValidator:
    """Validates actions and assesses security risks."""
    
    def __init__(self):
        """Initialize the action validator with security rules."""
        self._initialize_patterns()
        self._initialize_risk_rules()
    
    def _initialize_patterns(self) -> None:
        """Initialize regex patterns for detecting risky content."""
        # Payment-related patterns
        self.payment_patterns: List[Pattern] = [
            re.compile(r'\b(pay|payment|checkout|purchase|buy|order|cart)\b', re.IGNORECASE),
            re.compile(r'\b(credit|debit|card|visa|mastercard|amex)\b', re.IGNORECASE),
            re.compile(r'\b(billing|invoice|total|amount|price|cost)\b', re.IGNORECASE),
            re.compile(r'\$\d+|\d+\.\d{2}|USD|EUR|RUB', re.IGNORECASE),
        ]
        
        # Deletion patterns
        self.deletion_patterns: List[Pattern] = [
            re.compile(r'\b(delete|remove|clear|erase|destroy)\b', re.IGNORECASE),
            re.compile(r'\b(trash|bin|recycle)\b', re.IGNORECASE),
            re.compile(r'×|✕|🗑️', re.IGNORECASE),
        ]
        
        # Modification patterns
        self.modification_patterns: List[Pattern] = [
            re.compile(r'\b(edit|modify|change|update|alter)\b', re.IGNORECASE),
            re.compile(r'\b(settings|preferences|config|profile)\b', re.IGNORECASE),
            re.compile(r'\b(password|email|phone|address)\b', re.IGNORECASE),
        ]
        
        # Authentication patterns
        self.auth_patterns: List[Pattern] = [
            re.compile(r'\b(login|logout|signin|signout|authenticate)\b', re.IGNORECASE),
            re.compile(r'\b(username|password|token|session)\b', re.IGNORECASE),
            re.compile(r'\b(register|signup|create account)\b', re.IGNORECASE),
        ]
        
        # Submission patterns
        self.submission_patterns: List[Pattern] = [
            re.compile(r'\b(submit|send|post|confirm|apply)\b', re.IGNORECASE),
            re.compile(r'\b(form|application|request)\b', re.IGNORECASE),
        ]
        
        # File operation patterns
        self.file_patterns: List[Pattern] = [
            re.compile(r'\b(download|upload|attach|file)\b', re.IGNORECASE),
            re.compile(r'\.(exe|bat|sh|cmd|msi|dmg|pkg)', re.IGNORECASE),
        ]
    
    def _initialize_risk_rules(self) -> None:
        """Initialize risk assessment rules."""
        # High-risk domains
        self.high_risk_domains: Set[str] = {
            'banking', 'bank', 'paypal', 'stripe', 'payment',
            'admin', 'administrator', 'control', 'management'
        }
        
        # Critical action types that always require confirmation
        self.critical_action_types: Set[ActionType] = {
            ActionType.SUBMIT,
        }
        
        # Safe action types that rarely need confirmation
        self.safe_action_types: Set[ActionType] = {
            ActionType.NAVIGATE,
            ActionType.SCROLL,
            ActionType.WAIT,
            ActionType.EXTRACT,
            ActionType.SCREENSHOT,
            ActionType.HOVER,
        }
    
    def validate_action(self, action: Action) -> SecurityAssessment:
        """
        Validate an action and assess its security risk.
        
        Args:
            action: The action to validate
            
        Returns:
            SecurityAssessment with risk level and recommendations
        """
        categories = []
        reasons = []
        risk_level = SecurityRisk.SAFE
        
        # Check action type risk
        type_risk, type_reasons = self._assess_action_type_risk(action)
        if type_risk > risk_level:
            risk_level = type_risk
        reasons.extend(type_reasons)
        
        # Check target/selector risk
        target_risk, target_categories, target_reasons = self._assess_target_risk(action)
        if target_risk > risk_level:
            risk_level = target_risk
        categories.extend(target_categories)
        reasons.extend(target_reasons)
        
        # Check parameters risk
        param_risk, param_categories, param_reasons = self._assess_parameters_risk(action)
        if param_risk > risk_level:
            risk_level = param_risk
        categories.extend(param_categories)
        reasons.extend(param_reasons)
        
        # Check description risk
        desc_risk, desc_categories, desc_reasons = self._assess_description_risk(action)
        if desc_risk > risk_level:
            risk_level = desc_risk
        categories.extend(desc_categories)
        reasons.extend(desc_reasons)
        
        # Check if action is already marked as destructive
        if action.is_destructive and risk_level < SecurityRisk.HIGH:
            risk_level = SecurityRisk.HIGH
            reasons.append("Action is explicitly marked as destructive")
        
        # Determine if confirmation is required
        requires_confirmation = self._requires_confirmation(action, risk_level, categories)
        
        # Remove duplicates
        categories = list(set(categories))
        reasons = list(set(reasons))
        
        return SecurityAssessment(
            risk_level=risk_level,
            categories=categories,
            reasons=reasons,
            requires_confirmation=requires_confirmation,
            blocked=risk_level == SecurityRisk.CRITICAL
        )
    
    def _assess_action_type_risk(self, action: Action) -> tuple[SecurityRisk, List[str]]:
        """Assess risk based on action type."""
        reasons = []
        
        if action.type in self.critical_action_types:
            reasons.append(f"Action type '{action.type.value}' is inherently risky")
            return SecurityRisk.HIGH, reasons
        
        if action.type in self.safe_action_types:
            return SecurityRisk.SAFE, reasons
        
        # Medium risk for interactive actions
        if action.type in [ActionType.CLICK, ActionType.TYPE, ActionType.SELECT]:
            reasons.append(f"Interactive action type '{action.type.value}' requires caution")
            return SecurityRisk.LOW, reasons
        
        return SecurityRisk.SAFE, reasons
    
    def _assess_target_risk(self, action: Action) -> tuple[SecurityRisk, List[ActionCategory], List[str]]:
        """Assess risk based on action target/selector."""
        categories = []
        reasons = []
        risk_level = SecurityRisk.SAFE
        
        target = action.target.lower()
        
        # Check for payment-related selectors
        if any(pattern.search(target) for pattern in self.payment_patterns):
            categories.append(ActionCategory.PAYMENT)
            reasons.append("Target contains payment-related keywords")
            risk_level = SecurityRisk.HIGH
        
        # Check for deletion-related selectors
        if any(pattern.search(target) for pattern in self.deletion_patterns):
            categories.append(ActionCategory.DELETION)
            reasons.append("Target contains deletion-related keywords")
            risk_level = max(risk_level, SecurityRisk.HIGH)
        
        # Check for modification-related selectors
        if any(pattern.search(target) for pattern in self.modification_patterns):
            categories.append(ActionCategory.MODIFICATION)
            reasons.append("Target contains modification-related keywords")
            risk_level = max(risk_level, SecurityRisk.MEDIUM)
        
        # Check for authentication-related selectors
        if any(pattern.search(target) for pattern in self.auth_patterns):
            categories.append(ActionCategory.AUTHENTICATION)
            reasons.append("Target contains authentication-related keywords")
            risk_level = max(risk_level, SecurityRisk.MEDIUM)
        
        # Check for file operation selectors
        if any(pattern.search(target) for pattern in self.file_patterns):
            categories.append(ActionCategory.DOWNLOAD)
            reasons.append("Target contains file operation keywords")
            risk_level = max(risk_level, SecurityRisk.MEDIUM)
        
        # Check URL for high-risk domains
        if action.type == ActionType.NAVIGATE:
            try:
                parsed_url = urlparse(action.target)
                domain = parsed_url.netloc.lower()
                if any(risk_domain in domain for risk_domain in self.high_risk_domains):
                    categories.append(ActionCategory.NAVIGATION)
                    reasons.append("Navigation to high-risk domain")
                    risk_level = max(risk_level, SecurityRisk.HIGH)
            except Exception:
                pass  # Invalid URL, ignore
        
        return risk_level, categories, reasons
    
    def _assess_parameters_risk(self, action: Action) -> tuple[SecurityRisk, List[ActionCategory], List[str]]:
        """Assess risk based on action parameters."""
        categories = []
        reasons = []
        risk_level = SecurityRisk.SAFE
        
        if not action.parameters:
            return risk_level, categories, reasons
        
        # Check text input for sensitive data
        if "text" in action.parameters:
            text = str(action.parameters["text"]).lower()
            
            # Check for payment information
            if any(pattern.search(text) for pattern in self.payment_patterns):
                categories.append(ActionCategory.PAYMENT)
                reasons.append("Text input contains payment-related information")
                risk_level = SecurityRisk.CRITICAL
            
            # Check for personal information
            if re.search(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', text):  # Credit card pattern
                categories.append(ActionCategory.PAYMENT)
                reasons.append("Text input contains potential credit card number")
                risk_level = SecurityRisk.CRITICAL
            
            if re.search(r'\b\d{3}-\d{2}-\d{4}\b', text):  # SSN pattern
                categories.append(ActionCategory.MODIFICATION)
                reasons.append("Text input contains potential SSN")
                risk_level = SecurityRisk.CRITICAL
        
        # Check file upload parameters
        if "file" in action.parameters or "filename" in action.parameters:
            categories.append(ActionCategory.UPLOAD)
            reasons.append("Action involves file upload")
            risk_level = max(risk_level, SecurityRisk.MEDIUM)
        
        return risk_level, categories, reasons
    
    def _assess_description_risk(self, action: Action) -> tuple[SecurityRisk, List[ActionCategory], List[str]]:
        """Assess risk based on action description."""
        categories = []
        reasons = []
        risk_level = SecurityRisk.SAFE
        
        if not action.description:
            return risk_level, categories, reasons
        
        description = action.description.lower()
        
        # Check description for risky keywords
        if any(pattern.search(description) for pattern in self.payment_patterns):
            categories.append(ActionCategory.PAYMENT)
            reasons.append("Description contains payment-related keywords")
            risk_level = SecurityRisk.HIGH
        
        if any(pattern.search(description) for pattern in self.deletion_patterns):
            categories.append(ActionCategory.DELETION)
            reasons.append("Description contains deletion-related keywords")
            risk_level = max(risk_level, SecurityRisk.HIGH)
        
        if any(pattern.search(description) for pattern in self.submission_patterns):
            categories.append(ActionCategory.SUBMISSION)
            reasons.append("Description contains submission-related keywords")
            risk_level = max(risk_level, SecurityRisk.MEDIUM)
        
        return risk_level, categories, reasons
    
    def _requires_confirmation(self, action: Action, risk_level: SecurityRisk, categories: List[ActionCategory]) -> bool:
        """Determine if an action requires user confirmation."""
        # Always require confirmation for high and critical risk actions
        if risk_level in [SecurityRisk.HIGH, SecurityRisk.CRITICAL]:
            return True
        
        # Require confirmation for specific categories regardless of risk level
        high_risk_categories = {
            ActionCategory.PAYMENT,
            ActionCategory.DELETION,
            ActionCategory.AUTHENTICATION
        }
        
        if any(cat in high_risk_categories for cat in categories):
            return True
        
        # Check if action is explicitly marked as requiring confirmation
        if hasattr(action, 'requires_confirmation') and action.requires_confirmation():
            return True
        
        return False
    
    def get_risk_explanation(self, assessment: SecurityAssessment) -> str:
        """Get a human-readable explanation of the risk assessment."""
        if assessment.is_safe():
            return "This action is considered safe and can be executed automatically."
        
        explanation = f"Risk Level: {assessment.risk_level.value.upper()}\n"
        
        if assessment.categories:
            categories_str = ", ".join([cat.value for cat in assessment.categories])
            explanation += f"Categories: {categories_str}\n"
        
        if assessment.reasons:
            explanation += "Reasons:\n"
            for reason in assessment.reasons:
                explanation += f"  - {reason}\n"
        
        if assessment.requires_confirmation:
            explanation += "\nThis action requires user confirmation before execution."
        
        if assessment.blocked:
            explanation += "\nThis action is blocked due to critical security risk."
        
        return explanation.strip()