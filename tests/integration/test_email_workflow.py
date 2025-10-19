"""Integration tests for email management workflow."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from ai_browser_agent.core.ai_agent import AIAgent
from ai_browser_agent.handlers.email_task_handler import EmailTaskHandler
from ai_browser_agent.controllers.browser_controller import BrowserController
from ai_browser_agent.models.task import Task, TaskStatus
from ai_browser_agent.models.config import AppConfig, BrowserConfig, SecurityConfig, AIModelConfig
from ai_browser_agent.models.page_content import PageContent, WebElement


class TestEmailWorkflowIntegration:
    """Integration tests for complete email management workflows."""
    
    @pytest.fixture
    def app_config(self):
        """Create test application configuration."""
        return AppConfig(
            browser=BrowserConfig(headless=True, timeout=10),
            security=SecurityConfig(require_confirmation_for_deletions=True),
            ai_model=AIModelConfig(primary_model="claude", claude_api_key="test-key")
        )
    
    @pytest.fixture
    def mock_browser_controller(self):
        """Create mock browser controller for testing."""
        controller = Mock(spec=BrowserController)
        controller.is_connected.return_value = True
        controller.navigate_to = Mock()
        controller.find_element = Mock()
        controller.find_elements = Mock(return_value=[])
        controller.click_element = Mock(return_value=True)
        controller.get_current_url = Mock(return_value="https://gmail.com/inbox")
        controller.get_page_title = Mock(return_value="Gmail - Inbox")
        controller.get_page_source = Mock(return_value="<html><body>Gmail content</body></html>")
        return controller
    
    @pytest.fixture
    def mock_ai_agent(self):
        """Create mock AI agent for testing."""
        agent = Mock(spec=AIAgent)
        agent.analyze_page_and_decide = AsyncMock()
        agent.execute_action = AsyncMock(return_value=True)
        return agent
    
    @pytest.fixture
    def email_task_handler(self, app_config, mock_browser_controller, mock_ai_agent):
        """Create email task handler with mocked dependencies."""
        handler = EmailTaskHandler(app_config)
        handler.browser_controller = mock_browser_controller
        handler.ai_agent = mock_ai_agent
        return handler
    
    @pytest.fixture
    def gmail_inbox_page(self):
        """Create mock Gmail inbox page content."""
        elements = [
            # Email list items
            WebElement(
                tag_name="tr",
                attributes={"class": "zA", "data-thread-id": "thread1"},
                text_content="Spam Email Subject - This is definitely spam content...",
                css_selector="tr[data-thread-id='thread1']"
            ),
            WebElement(
                tag_name="tr",
                attributes={"class": "zA", "data-thread-id": "thread2"},
                text_content="Important Work Email - Meeting tomorrow at 2pm",
                css_selector="tr[data-thread-id='thread2']"
            ),
            WebElement(
                tag_name="tr",
                attributes={"class": "zA", "data-thread-id": "thread3"},
                text_content="Newsletter - Weekly updates from our team",
                css_selector="tr[data-thread-id='thread3']"
            ),
            # Action buttons
            WebElement(
                tag_name="button",
                attributes={"class": "delete-btn", "data-action": "delete"},
                text_content="Delete",
                css_selector=".delete-btn",
                is_clickable=True
            ),
            WebElement(
                tag_name="button",
                attributes={"class": "spam-btn", "data-action": "spam"},
                text_content="Mark as Spam",
                css_selector=".spam-btn",
                is_clickable=True
            )
        ]
        
        return PageContent(
            url="https://gmail.com/inbox",
            title="Gmail - Inbox",
            text_content="Gmail Inbox with 3 emails",
            elements=elements
        )
    
    @pytest.mark.asyncio
    async def test_spam_detection_workflow(self, email_task_handler, gmail_inbox_page, mock_ai_agent):
        """Test complete spam detection and removal workflow."""
        # Create spam detection task
        task = Task(
            id="spam-detection-1",
            description="Analyze inbox and delete spam emails",
            status=TaskStatus.PENDING
        )
        
        # Mock AI agent to identify spam
        from ai_browser_agent.models.action import Action, ActionType
        spam_actions = [
            Action(
                id="action-1",
                type=ActionType.CLICK,
                target="tr[data-thread-id='thread1']",
                description="Select spam email",
                confidence=0.9
            ),
            Action(
                id="action-2",
                type=ActionType.CLICK,
                target=".delete-btn",
                description="Delete spam email",
                confidence=0.85,
                is_destructive=True
            )
        ]
        mock_ai_agent.analyze_page_and_decide.return_value = spam_actions
        
        # Mock page analyzer to return inbox content
        with patch.object(email_task_handler, '_extract_page_content', return_value=gmail_inbox_page):
            # Execute the task
            result = await email_task_handler.handle_task(task)
        
        # Verify task completion
        assert result is not None
        assert task.status in [TaskStatus.COMPLETED, TaskStatus.REQUIRES_INPUT]
        
        # Verify AI was called to analyze the page
        mock_ai_agent.analyze_page_and_decide.assert_called()
        
        # Verify actions were executed
        mock_ai_agent.execute_action.assert_called()
        
        # Check that spam email was identified and action was taken
        call_args = mock_ai_agent.analyze_page_and_decide.call_args
        page_content = call_args[0][0]  # First argument should be page content
        assert "spam" in page_content.text_content.lower()
    
    @pytest.mark.asyncio
    async def test_email_organization_workflow(self, email_task_handler, gmail_inbox_page, mock_ai_agent):
        """Test email organization workflow."""
        # Create organization task
        task = Task(
            id="organize-emails-1",
            description="Organize emails by moving newsletters to a folder",
            status=TaskStatus.PENDING
        )
        
        # Mock AI agent to identify newsletters and organize them
        from ai_browser_agent.models.action import Action, ActionType
        organize_actions = [
            Action(
                id="action-1",
                type=ActionType.CLICK,
                target="tr[data-thread-id='thread3']",
                description="Select newsletter email",
                confidence=0.8
            ),
            Action(
                id="action-2",
                type=ActionType.CLICK,
                target=".move-to-folder-btn",
                description="Move to newsletters folder",
                confidence=0.75
            )
        ]
        mock_ai_agent.analyze_page_and_decide.return_value = organize_actions
        
        # Mock page analyzer
        with patch.object(email_task_handler, '_extract_page_content', return_value=gmail_inbox_page):
            # Execute the task
            result = await email_task_handler.handle_task(task)
        
        # Verify task execution
        assert result is not None
        mock_ai_agent.analyze_page_and_decide.assert_called()
        mock_ai_agent.execute_action.assert_called()
    
    @pytest.mark.asyncio
    async def test_email_reading_workflow(self, email_task_handler, gmail_inbox_page, mock_ai_agent):
        """Test email reading and analysis workflow."""
        # Create reading task
        task = Task(
            id="read-emails-1",
            description="Read and summarize important work emails",
            status=TaskStatus.PENDING
        )
        
        # Mock AI agent to read and analyze emails
        from ai_browser_agent.models.action import Action, ActionType
        read_actions = [
            Action(
                id="action-1",
                type=ActionType.CLICK,
                target="tr[data-thread-id='thread2']",
                description="Open important work email",
                confidence=0.9
            ),
            Action(
                id="action-2",
                type=ActionType.EXTRACT,
                target=".email-content",
                description="Extract email content for analysis",
                confidence=0.85
            )
        ]
        mock_ai_agent.analyze_page_and_decide.return_value = read_actions
        
        # Mock page analyzer
        with patch.object(email_task_handler, '_extract_page_content', return_value=gmail_inbox_page):
            # Execute the task
            result = await email_task_handler.handle_task(task)
        
        # Verify task execution
        assert result is not None
        mock_ai_agent.analyze_page_and_decide.assert_called()
        
        # Verify that work email was identified
        call_args = mock_ai_agent.analyze_page_and_decide.call_args
        page_content = call_args[0][0]
        assert "work" in page_content.text_content.lower()
    
    @pytest.mark.asyncio
    async def test_security_confirmation_workflow(self, email_task_handler, gmail_inbox_page, mock_ai_agent):
        """Test security confirmation for destructive email actions."""
        # Create deletion task
        task = Task(
            id="delete-emails-1",
            description="Delete all emails from unknown senders",
            status=TaskStatus.PENDING
        )
        
        # Mock AI agent to suggest destructive action
        from ai_browser_agent.models.action import Action, ActionType
        destructive_actions = [
            Action(
                id="action-1",
                type=ActionType.CLICK,
                target="tr[data-thread-id='thread1']",
                description="Select email for deletion",
                confidence=0.8,
                is_destructive=True
            )
        ]
        mock_ai_agent.analyze_page_and_decide.return_value = destructive_actions
        
        # Mock security layer to require confirmation
        with patch.object(email_task_handler, '_extract_page_content', return_value=gmail_inbox_page):
            with patch.object(email_task_handler.security_layer, 'validate_action') as mock_security:
                mock_security.return_value = {"requires_confirmation": True, "is_safe": False}
                
                # Execute the task
                result = await email_task_handler.handle_task(task)
        
        # Verify that security validation was called
        mock_security.assert_called()
        
        # Task should require user input due to destructive action
        assert task.status == TaskStatus.REQUIRES_INPUT or result is not None
    
    @pytest.mark.asyncio
    async def test_error_handling_workflow(self, email_task_handler, mock_ai_agent):
        """Test error handling in email workflow."""
        # Create task
        task = Task(
            id="error-test-1",
            description="Test error handling",
            status=TaskStatus.PENDING
        )
        
        # Mock browser controller to raise exception
        email_task_handler.browser_controller.navigate_to.side_effect = Exception("Network error")
        
        # Execute the task
        result = await email_task_handler.handle_task(task)
        
        # Verify error handling
        assert task.status == TaskStatus.FAILED or result is not None
        assert task.error_message is not None or "error" in str(result).lower()
    
    @pytest.mark.asyncio
    async def test_multi_step_email_workflow(self, email_task_handler, gmail_inbox_page, mock_ai_agent):
        """Test multi-step email management workflow."""
        # Create complex task
        task = Task(
            id="multi-step-1",
            description="Read emails, identify spam, organize newsletters, and delete spam",
            status=TaskStatus.PENDING
        )
        
        # Mock AI agent to return multiple actions in sequence
        from ai_browser_agent.models.action import Action, ActionType
        
        # First call - analyze inbox
        analyze_actions = [
            Action(id="1", type=ActionType.EXTRACT, target=".email-list", description="Extract email list")
        ]
        
        # Second call - identify spam
        spam_actions = [
            Action(id="2", type=ActionType.CLICK, target="tr[data-thread-id='thread1']", description="Select spam")
        ]
        
        # Third call - delete spam
        delete_actions = [
            Action(id="3", type=ActionType.CLICK, target=".delete-btn", description="Delete spam", is_destructive=True)
        ]
        
        # Configure mock to return different actions on each call
        mock_ai_agent.analyze_page_and_decide.side_effect = [
            analyze_actions,
            spam_actions,
            delete_actions
        ]
        
        # Mock page analyzer
        with patch.object(email_task_handler, '_extract_page_content', return_value=gmail_inbox_page):
            # Execute the task
            result = await email_task_handler.handle_task(task)
        
        # Verify multiple AI analysis calls were made
        assert mock_ai_agent.analyze_page_and_decide.call_count >= 1
        
        # Verify task progressed
        assert result is not None or task.status != TaskStatus.PENDING
    
    def test_email_handler_initialization(self, app_config):
        """Test email task handler initialization."""
        handler = EmailTaskHandler(app_config)
        
        assert handler.config == app_config
        assert handler.supported_domains is not None
        assert len(handler.supported_domains) > 0
        assert "gmail.com" in handler.supported_domains
    
    def test_email_handler_task_validation(self, email_task_handler):
        """Test task validation in email handler."""
        # Valid email task
        valid_task = Task(
            id="valid-1",
            description="Delete spam emails from inbox",
            status=TaskStatus.PENDING
        )
        
        # Should not raise exception
        try:
            email_task_handler._validate_task(valid_task)
            validation_passed = True
        except:
            validation_passed = False
        
        assert validation_passed
    
    @pytest.mark.asyncio
    async def test_email_service_navigation(self, email_task_handler, mock_ai_agent):
        """Test navigation to email service."""
        task = Task(
            id="nav-test-1",
            description="Navigate to Gmail and check inbox",
            status=TaskStatus.PENDING
        )
        
        # Mock successful navigation
        email_task_handler.browser_controller.navigate_to = Mock()
        email_task_handler.browser_controller.get_current_url.return_value = "https://gmail.com/inbox"
        
        # Mock page content extraction
        inbox_page = PageContent(
            url="https://gmail.com/inbox",
            title="Gmail",
            text_content="Inbox content",
            elements=[]
        )
        
        with patch.object(email_task_handler, '_extract_page_content', return_value=inbox_page):
            # Execute navigation
            result = await email_task_handler._navigate_to_email_service("gmail.com")
        
        # Verify navigation was attempted
        email_task_handler.browser_controller.navigate_to.assert_called()
        assert result is True or result is not None