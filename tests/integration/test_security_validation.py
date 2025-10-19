"""Integration tests for security validation and destructive action handling."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from ai_browser_agent.core.ai_agent import AIAgent
from ai_browser_agent.security.security_layer import SecurityLayer
from ai_browser_agent.security.action_validator import ActionValidator
from ai_browser_agent.security.user_confirmation import UserConfirmation
from ai_browser_agent.security.audit_logger import AuditLogger
from ai_browser_agent.models.task import Task, TaskStatus
from ai_browser_agent.models.action import Action, ActionType
from ai_browser_agent.models.config import AppConfig, SecurityConfig
from ai_browser_agent.models.page_content import PageContent, WebElement


class TestSecurityValidationIntegration:
    """Integration tests for security validation workflows."""
    
    @pytest.fixture
    def security_config(self):
        """Create test security configuration."""
        return SecurityConfig(
            require_confirmation_for_payments=True,
            require_confirmation_for_deletions=True,
            require_confirmation_for_modifications=True,
            require_confirmation_for_submissions=True,
            sensitive_domains=["paypal.com", "banking.com", "amazon.com"],
            destructive_patterns=["delete", "remove", "cancel", "purchase", "buy", "pay"],
            max_task_duration=1800,
            audit_log_enabled=True
        )
    
    @pytest.fixture
    def app_config(self, security_config):
        """Create test application configuration."""
        return AppConfig(security=security_config)
    
    @pytest.fixture
    def mock_user_interface(self):
        """Create mock user interface for confirmations."""
        ui = Mock()
        ui.request_confirmation = AsyncMock(return_value=True)  # Default to approve
        ui.display_warning = Mock()
        ui.display_error = Mock()
        return ui
    
    @pytest.fixture
    def security_layer(self, security_config, mock_user_interface):
        """Create security layer with mocked dependencies."""
        layer = SecurityLayer(security_config)
        layer.user_interface = mock_user_interface
        return layer
    
    @pytest.fixture
    def action_validator(self, security_config):
        """Create action validator."""
        return ActionValidator(security_config)
    
    @pytest.fixture
    def audit_logger(self, security_config):
        """Create audit logger."""
        return AuditLogger(security_config)
    
    @pytest.fixture
    def payment_page(self):
        """Create mock payment page content."""
        elements = [
            WebElement(
                tag_name="form",
                attributes={"id": "payment-form", "action": "/process-payment"},
                css_selector="#payment-form"
            ),
            WebElement(
                tag_name="input",
                attributes={"type": "text", "name": "card_number", "placeholder": "Card Number"},
                css_selector="input[name='card_number']"
            ),
            WebElement(
                tag_name="button",
                attributes={"type": "submit", "class": "pay-now-btn"},
                text_content="Pay Now - $99.99",
                css_selector=".pay-now-btn",
                is_clickable=True
            ),
            WebElement(
                tag_name="button",
                attributes={"class": "cancel-order-btn"},
                text_content="Cancel Order",
                css_selector=".cancel-order-btn",
                is_clickable=True
            )
        ]
        
        return PageContent(
            url="https://paypal.com/checkout",
            title="PayPal - Complete Payment",
            text_content="Complete your payment of $99.99",
            elements=elements
        )
    
    @pytest.fixture
    def email_deletion_page(self):
        """Create mock email deletion page content."""
        elements = [
            WebElement(
                tag_name="div",
                attributes={"class": "email-list"},
                text_content="Select emails to delete",
                css_selector=".email-list"
            ),
            WebElement(
                tag_name="button",
                attributes={"class": "delete-selected-btn"},
                text_content="Delete Selected Emails",
                css_selector=".delete-selected-btn",
                is_clickable=True
            ),
            WebElement(
                tag_name="button",
                attributes={"class": "delete-all-btn"},
                text_content="Delete All Emails",
                css_selector=".delete-all-btn",
                is_clickable=True
            )
        ]
        
        return PageContent(
            url="https://gmail.com/inbox",
            title="Gmail - Inbox Management",
            text_content="Manage your email inbox",
            elements=elements
        )
    
    @pytest.mark.asyncio
    async def test_payment_action_security_validation(self, security_layer, payment_page, mock_user_interface):
        """Test security validation for payment actions."""
        # Create payment action
        payment_action = Action(
            id="payment-1",
            type=ActionType.CLICK,
            target=".pay-now-btn",
            description="Complete payment of $99.99",
            is_destructive=True
        )
        
        # Create task context
        task = Task(
            id="purchase-1",
            description="Complete online purchase",
            status=TaskStatus.IN_PROGRESS
        )
        
        # Validate the action
        validation_result = await security_layer.validate_action(payment_action, payment_page, task)
        
        # Should require confirmation for payment
        assert validation_result["requires_confirmation"] is True
        assert validation_result["risk_level"] in ["high", "medium"]
        
        # User confirmation should be requested
        mock_user_interface.request_confirmation.assert_called_once()
        
        # Check confirmation details
        call_args = mock_user_interface.request_confirmation.call_args
        confirmation_details = call_args[0][0]  # First argument
        assert "payment" in confirmation_details.lower() or "$99.99" in confirmation_details
    
    @pytest.mark.asyncio
    async def test_deletion_action_security_validation(self, security_layer, email_deletion_page, mock_user_interface):
        """Test security validation for deletion actions."""
        # Create deletion action
        deletion_action = Action(
            id="delete-1",
            type=ActionType.CLICK,
            target=".delete-all-btn",
            description="Delete all emails from inbox",
            is_destructive=True
        )
        
        # Create task context
        task = Task(
            id="cleanup-1",
            description="Clean up email inbox",
            status=TaskStatus.IN_PROGRESS
        )
        
        # Validate the action
        validation_result = await security_layer.validate_action(deletion_action, email_deletion_page, task)
        
        # Should require confirmation for deletion
        assert validation_result["requires_confirmation"] is True
        assert validation_result["risk_level"] == "high"  # Deleting all emails is high risk
        
        # User confirmation should be requested
        mock_user_interface.request_confirmation.assert_called_once()
        
        # Check confirmation details mention deletion
        call_args = mock_user_interface.request_confirmation.call_args
        confirmation_details = call_args[0][0]
        assert "delete" in confirmation_details.lower()
    
    @pytest.mark.asyncio
    async def test_sensitive_domain_validation(self, security_layer, payment_page, mock_user_interface):
        """Test validation on sensitive domains."""
        # Create seemingly safe action on sensitive domain
        safe_action = Action(
            id="click-1",
            type=ActionType.CLICK,
            target=".info-btn",
            description="Click information button",
            is_destructive=False
        )
        
        task = Task(id="info-1", description="Get account information")
        
        # Validate action on PayPal (sensitive domain)
        validation_result = await security_layer.validate_action(safe_action, payment_page, task)
        
        # Should still require extra caution on sensitive domain
        assert validation_result["requires_confirmation"] is True or validation_result["risk_level"] != "low"
    
    @pytest.mark.asyncio
    async def test_user_denial_handling(self, security_layer, payment_page, mock_user_interface):
        """Test handling when user denies confirmation."""
        # Mock user to deny confirmation
        mock_user_interface.request_confirmation.return_value = False
        
        # Create payment action
        payment_action = Action(
            id="payment-denied-1",
            type=ActionType.CLICK,
            target=".pay-now-btn",
            description="Complete payment",
            is_destructive=True
        )
        
        task = Task(id="purchase-denied-1", description="Complete purchase")
        
        # Validate the action
        validation_result = await security_layer.validate_action(payment_action, payment_page, task)
        
        # Should be blocked due to user denial
        assert validation_result["approved"] is False
        assert validation_result["requires_confirmation"] is True
    
    def test_action_validator_destructive_detection(self, action_validator):
        """Test action validator's ability to detect destructive actions."""
        # Test payment action
        payment_action = Action(
            id="pay-1",
            type=ActionType.SUBMIT,
            target="#payment-form",
            description="Submit payment form"
        )
        
        result = action_validator.is_destructive_action(payment_action)
        assert result is True
        
        # Test deletion action
        delete_action = Action(
            id="del-1",
            type=ActionType.CLICK,
            target=".delete-btn",
            description="Delete selected items"
        )
        
        result = action_validator.is_destructive_action(delete_action)
        assert result is True
        
        # Test safe action
        safe_action = Action(
            id="safe-1",
            type=ActionType.CLICK,
            target=".info-btn",
            description="View information"
        )
        
        result = action_validator.is_destructive_action(safe_action)
        assert result is False
    
    def test_action_validator_risk_assessment(self, action_validator, payment_page):
        """Test risk assessment functionality."""
        # High risk action
        high_risk_action = Action(
            id="high-1",
            type=ActionType.CLICK,
            target=".pay-now-btn",
            description="Complete $999.99 payment"
        )
        
        risk_level = action_validator.assess_risk_level(high_risk_action, payment_page)
        assert risk_level == "high"
        
        # Medium risk action
        medium_risk_action = Action(
            id="med-1",
            type=ActionType.CLICK,
            target=".cancel-order-btn",
            description="Cancel current order"
        )
        
        risk_level = action_validator.assess_risk_level(medium_risk_action, payment_page)
        assert risk_level in ["medium", "high"]
        
        # Low risk action
        low_risk_action = Action(
            id="low-1",
            type=ActionType.EXTRACT,
            target=".order-summary",
            description="Extract order details"
        )
        
        risk_level = action_validator.assess_risk_level(low_risk_action, payment_page)
        assert risk_level == "low"
    
    def test_audit_logger_security_events(self, audit_logger):
        """Test audit logging of security events."""
        # Create security event
        security_event = {
            "event_type": "action_validation",
            "action_id": "test-action-1",
            "risk_level": "high",
            "requires_confirmation": True,
            "user_approved": True,
            "page_url": "https://paypal.com/checkout",
            "timestamp": "2024-01-01T12:00:00Z"
        }
        
        # Log the event
        audit_logger.log_security_event(security_event)
        
        # Verify event was logged
        logged_events = audit_logger.get_recent_events(1)
        assert len(logged_events) == 1
        assert logged_events[0]["action_id"] == "test-action-1"
        assert logged_events[0]["risk_level"] == "high"
    
    @pytest.mark.asyncio
    async def test_multiple_action_validation_workflow(self, security_layer, payment_page, mock_user_interface):
        """Test validation of multiple actions in sequence."""
        # Create sequence of actions with varying risk levels
        actions = [
            Action(
                id="action-1",
                type=ActionType.EXTRACT,
                target=".order-summary",
                description="Review order details",
                is_destructive=False
            ),
            Action(
                id="action-2",
                type=ActionType.TYPE,
                target="input[name='card_number']",
                description="Enter payment information",
                is_destructive=False
            ),
            Action(
                id="action-3",
                type=ActionType.CLICK,
                target=".pay-now-btn",
                description="Complete payment",
                is_destructive=True
            )
        ]
        
        task = Task(id="multi-action-1", description="Complete purchase workflow")
        
        validation_results = []
        for action in actions:
            result = await security_layer.validate_action(action, payment_page, task)
            validation_results.append(result)
        
        # First two actions should be low risk
        assert validation_results[0]["risk_level"] == "low"
        assert validation_results[1]["risk_level"] in ["low", "medium"]
        
        # Payment action should require confirmation
        assert validation_results[2]["requires_confirmation"] is True
        assert validation_results[2]["risk_level"] == "high"
    
    @pytest.mark.asyncio
    async def test_security_escalation_workflow(self, security_layer, mock_user_interface):
        """Test security escalation for highly risky actions."""
        # Create extremely risky action
        risky_page = PageContent(
            url="https://banking.com/transfer",
            title="Bank Transfer - $10,000",
            text_content="Transfer $10,000 to external account",
            elements=[]
        )
        
        risky_action = Action(
            id="risky-1",
            type=ActionType.SUBMIT,
            target="#transfer-form",
            description="Transfer $10,000 to external account",
            is_destructive=True
        )
        
        task = Task(id="transfer-1", description="Bank transfer")
        
        # Mock user interface to simulate escalation
        mock_user_interface.request_confirmation.return_value = False  # User denies
        
        # Validate the action
        validation_result = await security_layer.validate_action(risky_action, risky_page, task)
        
        # Should be blocked and escalated
        assert validation_result["approved"] is False
        assert validation_result["risk_level"] == "high"
        assert validation_result["requires_confirmation"] is True
    
    @pytest.mark.asyncio
    async def test_security_bypass_for_safe_actions(self, security_layer):
        """Test that safe actions bypass security confirmation."""
        # Create safe page and action
        safe_page = PageContent(
            url="https://example.com/info",
            title="Information Page",
            text_content="General information about our services",
            elements=[]
        )
        
        safe_action = Action(
            id="safe-1",
            type=ActionType.EXTRACT,
            target=".content",
            description="Extract page content for reading",
            is_destructive=False
        )
        
        task = Task(id="read-1", description="Read information")
        
        # Validate the action
        validation_result = await security_layer.validate_action(safe_action, safe_page, task)
        
        # Should not require confirmation
        assert validation_result["requires_confirmation"] is False
        assert validation_result["approved"] is True
        assert validation_result["risk_level"] == "low"
    
    def test_security_config_validation(self, security_config):
        """Test security configuration validation."""
        assert security_config.validate() is True
        
        # Test domain sensitivity detection
        assert security_config.is_sensitive_domain("https://paypal.com/checkout") is True
        assert security_config.is_sensitive_domain("https://example.com") is False
        
        # Test destructive action detection
        assert security_config.is_destructive_action("Delete all files") is True
        assert security_config.is_destructive_action("Purchase item now") is True
        assert security_config.is_destructive_action("Read article") is False
    
    @pytest.mark.asyncio
    async def test_concurrent_security_validations(self, security_layer, payment_page):
        """Test concurrent security validations."""
        # Create multiple actions to validate concurrently
        actions = [
            Action(id=f"concurrent-{i}", type=ActionType.CLICK, target=f".btn-{i}", description=f"Action {i}")
            for i in range(5)
        ]
        
        task = Task(id="concurrent-1", description="Concurrent actions test")
        
        # Validate all actions concurrently
        validation_tasks = [
            security_layer.validate_action(action, payment_page, task)
            for action in actions
        ]
        
        results = await asyncio.gather(*validation_tasks)
        
        # All validations should complete
        assert len(results) == 5
        assert all(isinstance(result, dict) for result in results)
    
    def test_audit_trail_completeness(self, audit_logger):
        """Test completeness of audit trail."""
        # Log various types of security events
        events = [
            {"event_type": "action_validation", "action_id": "act1", "approved": True},
            {"event_type": "user_confirmation", "action_id": "act2", "user_response": "approved"},
            {"event_type": "security_violation", "action_id": "act3", "violation_type": "unauthorized_access"},
            {"event_type": "risk_assessment", "action_id": "act4", "risk_level": "high"}
        ]
        
        for event in events:
            audit_logger.log_security_event(event)
        
        # Verify all events were logged
        logged_events = audit_logger.get_recent_events(10)
        assert len(logged_events) >= 4
        
        # Verify event types are preserved
        event_types = [event["event_type"] for event in logged_events[-4:]]
        expected_types = ["action_validation", "user_confirmation", "security_violation", "risk_assessment"]
        assert all(et in event_types for et in expected_types)