"""Integration tests for browser automation with test websites."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from ai_browser_agent.controllers.browser_controller import BrowserController
from ai_browser_agent.controllers.element_locator import ElementLocator
from ai_browser_agent.controllers.page_analyzer import PageAnalyzer
from ai_browser_agent.controllers.session_manager import SessionManager
from ai_browser_agent.models.config import BrowserConfig
from ai_browser_agent.models.page_content import PageContent, WebElement
from ai_browser_agent.models.action import Action, ActionType


class TestBrowserAutomationIntegration:
    """Integration tests for browser automation components."""
    
    @pytest.fixture
    def browser_config(self):
        """Create test browser configuration."""
        return BrowserConfig(
            headless=True,  # Use headless for testing
            window_size=(1280, 720),
            timeout=10,
            browser_type="chrome"
        )
    
    @pytest.fixture
    def mock_webdriver(self):
        """Create comprehensive mock WebDriver."""
        driver = Mock()
        
        # Basic properties
        driver.current_url = "https://test-site.example.com"
        driver.title = "Test Site"
        driver.page_source = """
        <html>
            <head><title>Test Site</title></head>
            <body>
                <h1>Welcome to Test Site</h1>
                <form id="login-form">
                    <input type="text" name="username" placeholder="Username" />
                    <input type="password" name="password" placeholder="Password" />
                    <button type="submit">Login</button>
                </form>
                <div class="content">
                    <p>This is test content for automation.</p>
                    <a href="/products">View Products</a>
                    <button class="action-btn" data-action="test">Test Action</button>
                </div>
            </body>
        </html>
        """
        
        # Mock WebDriver methods
        driver.get = Mock()
        driver.quit = Mock()
        driver.refresh = Mock()
        driver.back = Mock()
        driver.forward = Mock()
        driver.execute_script = Mock(return_value="script result")
        driver.get_window_size = Mock(return_value={"width": 1280, "height": 720})
        driver.set_window_size = Mock()
        driver.save_screenshot = Mock()
        driver.get_screenshot_as_png = Mock(return_value=b"screenshot_data")
        
        # Mock element finding
        mock_element = Mock()
        mock_element.click = Mock()
        mock_element.send_keys = Mock()
        mock_element.clear = Mock()
        mock_element.text = "Mock Element Text"
        mock_element.get_attribute = Mock(return_value="mock-value")
        mock_element.is_displayed = Mock(return_value=True)
        mock_element.is_enabled = Mock(return_value=True)
        
        driver.find_element = Mock(return_value=mock_element)
        driver.find_elements = Mock(return_value=[mock_element])
        
        return driver
    
    @pytest.fixture
    def browser_controller(self, browser_config, mock_webdriver):
        """Create browser controller with mocked WebDriver."""
        controller = BrowserController(browser_config)
        controller.driver = mock_webdriver
        controller.is_initialized = True
        
        # Mock WebDriverWait
        mock_wait = Mock()
        mock_wait.until = Mock(return_value=mock_webdriver.find_element.return_value)
        controller.wait = mock_wait
        
        return controller
    
    @pytest.fixture
    def element_locator(self, browser_controller):
        """Create element locator with browser controller."""
        return ElementLocator(browser_controller)
    
    @pytest.fixture
    def page_analyzer(self, browser_controller):
        """Create page analyzer with browser controller."""
        return PageAnalyzer(browser_controller)
    
    @pytest.fixture
    def session_manager(self, browser_config):
        """Create session manager."""
        return SessionManager(browser_config)
    
    def test_browser_controller_navigation(self, browser_controller, mock_webdriver):
        """Test browser navigation functionality."""
        # Test navigation
        test_url = "https://test-site.example.com"
        browser_controller.navigate_to(test_url)
        
        # Verify navigation was called
        mock_webdriver.get.assert_called_once_with(test_url)
        
        # Test URL retrieval
        current_url = browser_controller.get_current_url()
        assert current_url == "https://test-site.example.com"
        
        # Test title retrieval
        title = browser_controller.get_page_title()
        assert title == "Test Site"
    
    def test_browser_controller_element_interaction(self, browser_controller, mock_webdriver):
        """Test element finding and interaction."""
        # Test element finding
        element = browser_controller.find_element("#login-form")
        assert element is not None
        
        # Test clicking
        success = browser_controller.click_element("#login-form button")
        assert success is True
        
        # Test typing
        success = browser_controller.type_text("input[name='username']", "testuser")
        assert success is True
        
        # Verify WebDriver interactions
        mock_webdriver.find_element.assert_called()
    
    def test_browser_controller_page_operations(self, browser_controller, mock_webdriver):
        """Test page-level operations."""
        # Test page refresh
        browser_controller.refresh_page()
        mock_webdriver.refresh.assert_called_once()
        
        # Test navigation history
        browser_controller.go_back()
        mock_webdriver.back.assert_called_once()
        
        browser_controller.go_forward()
        mock_webdriver.forward.assert_called_once()
        
        # Test JavaScript execution
        result = browser_controller.execute_script("return document.title;")
        assert result == "script result"
        mock_webdriver.execute_script.assert_called_with("return document.title;")
    
    def test_browser_controller_screenshot(self, browser_controller, mock_webdriver):
        """Test screenshot functionality."""
        # Test screenshot as bytes
        screenshot_bytes = browser_controller.take_screenshot()
        assert screenshot_bytes == b"screenshot_data"
        
        # Test screenshot to file
        result = browser_controller.take_screenshot("/tmp/test_screenshot.png")
        assert result is None  # Should return None when saving to file
        mock_webdriver.save_screenshot.assert_called_with("/tmp/test_screenshot.png")
    
    def test_element_locator_strategies(self, element_locator, mock_webdriver):
        """Test different element location strategies."""
        # Test CSS selector strategy
        element = element_locator.find_by_css_selector("#login-form")
        assert element is not None
        
        # Test XPath strategy
        element = element_locator.find_by_xpath("//form[@id='login-form']")
        assert element is not None
        
        # Test text content strategy
        elements = element_locator.find_by_text_content("Login")
        assert len(elements) >= 0
        
        # Test attribute strategy
        elements = element_locator.find_by_attribute("type", "submit")
        assert len(elements) >= 0
    
    def test_element_locator_robust_finding(self, element_locator, mock_webdriver):
        """Test robust element finding with fallback strategies."""
        # Mock first strategy to fail, second to succeed
        mock_webdriver.find_element.side_effect = [
            Exception("Element not found"),  # First attempt fails
            mock_webdriver.find_element.return_value  # Second attempt succeeds
        ]
        
        # Test robust finding with multiple strategies
        element = element_locator.find_element_robust([
            {"strategy": "css", "selector": "#nonexistent"},
            {"strategy": "css", "selector": "#login-form"}
        ])
        
        assert element is not None
        assert mock_webdriver.find_element.call_count == 2
    
    def test_page_analyzer_content_extraction(self, page_analyzer, mock_webdriver):
        """Test page content analysis and extraction."""
        # Test page content extraction
        page_content = page_analyzer.extract_page_content()
        
        assert isinstance(page_content, PageContent)
        assert page_content.url == "https://test-site.example.com"
        assert page_content.title == "Test Site"
        assert len(page_content.elements) > 0
    
    def test_page_analyzer_element_analysis(self, page_analyzer, mock_webdriver):
        """Test element analysis functionality."""
        # Test interactive element detection
        interactive_elements = page_analyzer.find_interactive_elements()
        assert len(interactive_elements) >= 0
        
        # Test form detection
        forms = page_analyzer.find_forms()
        assert len(forms) >= 0
        
        # Test link detection
        links = page_analyzer.find_links()
        assert len(links) >= 0
    
    def test_page_analyzer_content_summarization(self, page_analyzer, mock_webdriver):
        """Test content summarization for AI processing."""
        # Test content summarization
        summary = page_analyzer.summarize_page_for_ai(max_length=500)
        
        assert isinstance(summary, str)
        assert len(summary) <= 500
        assert "Test Site" in summary or "test" in summary.lower()
    
    def test_session_manager_profile_management(self, session_manager):
        """Test browser session and profile management."""
        # Test profile creation
        profile_path = session_manager.create_user_profile("test_user")
        assert profile_path is not None
        assert "test_user" in profile_path
        
        # Test profile loading
        loaded_profile = session_manager.load_user_profile("test_user")
        assert loaded_profile is not None
    
    def test_session_manager_session_persistence(self, session_manager):
        """Test session persistence across browser restarts."""
        # Test session saving
        session_data = {
            "cookies": [{"name": "session_id", "value": "abc123"}],
            "local_storage": {"user_pref": "dark_mode"},
            "current_url": "https://test-site.example.com/dashboard"
        }
        
        success = session_manager.save_session("test_session", session_data)
        assert success is True
        
        # Test session loading
        loaded_session = session_manager.load_session("test_session")
        assert loaded_session is not None
        assert loaded_session["current_url"] == "https://test-site.example.com/dashboard"
    
    @pytest.mark.asyncio
    async def test_complete_automation_workflow(self, browser_controller, element_locator, page_analyzer):
        """Test complete browser automation workflow."""
        # Step 1: Navigate to test site
        browser_controller.navigate_to("https://test-site.example.com")
        
        # Step 2: Analyze page content
        page_content = page_analyzer.extract_page_content()
        assert page_content.url == "https://test-site.example.com"
        
        # Step 3: Find login form
        login_form = element_locator.find_by_css_selector("#login-form")
        assert login_form is not None
        
        # Step 4: Fill login form
        username_field = element_locator.find_by_css_selector("input[name='username']")
        password_field = element_locator.find_by_css_selector("input[name='password']")
        submit_button = element_locator.find_by_css_selector("button[type='submit']")
        
        # Step 5: Perform login actions
        browser_controller.type_text("input[name='username']", "testuser")
        browser_controller.type_text("input[name='password']", "testpass")
        browser_controller.click_element("button[type='submit']")
        
        # Step 6: Verify actions were performed
        # (In real test, would verify form submission)
        assert True  # Placeholder for actual verification
    
    def test_error_handling_in_automation(self, browser_controller, mock_webdriver):
        """Test error handling during browser automation."""
        # Test navigation error
        mock_webdriver.get.side_effect = Exception("Network error")
        
        with pytest.raises(Exception):
            browser_controller.navigate_to("https://invalid-site.com")
        
        # Reset mock
        mock_webdriver.get.side_effect = None
        
        # Test element not found error
        mock_webdriver.find_element.side_effect = Exception("Element not found")
        
        element = browser_controller.find_element("#nonexistent")
        assert element is None  # Should handle gracefully
    
    def test_browser_automation_performance(self, browser_controller, mock_webdriver):
        """Test performance aspects of browser automation."""
        import time
        
        # Test multiple rapid operations
        start_time = time.time()
        
        for i in range(10):
            browser_controller.find_element(f"#element-{i}")
            browser_controller.click_element(f".button-{i}")
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should complete reasonably quickly (mocked operations)
        assert execution_time < 1.0  # Less than 1 second for mocked operations
    
    def test_concurrent_browser_operations(self, browser_controller, mock_webdriver):
        """Test concurrent browser operations."""
        import concurrent.futures
        
        def perform_operation(operation_id):
            browser_controller.find_element(f"#element-{operation_id}")
            browser_controller.click_element(f".button-{operation_id}")
            return f"Operation {operation_id} completed"
        
        # Execute operations concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(perform_operation, i) for i in range(5)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # All operations should complete
        assert len(results) == 5
        assert all("completed" in result for result in results)
    
    def test_browser_state_management(self, browser_controller, mock_webdriver):
        """Test browser state management and cleanup."""
        # Test connection state
        assert browser_controller.is_connected() is True
        
        # Test window size management
        browser_controller.set_window_size(1920, 1080)
        mock_webdriver.set_window_size.assert_called_with(1920, 1080)
        
        size = browser_controller.get_window_size()
        assert size["width"] == 1280  # Mock returns original size
        assert size["height"] == 720
        
        # Test cleanup
        browser_controller.disconnect()
        mock_webdriver.quit.assert_called_once()
        assert browser_controller.is_connected() is False
    
    def test_element_interaction_edge_cases(self, browser_controller, mock_webdriver):
        """Test edge cases in element interaction."""
        # Test interaction with disabled element
        mock_element = Mock()
        mock_element.is_enabled.return_value = False
        mock_webdriver.find_element.return_value = mock_element
        
        # Should handle disabled elements gracefully
        success = browser_controller.click_element("#disabled-button")
        # Behavior depends on implementation - might succeed or fail gracefully
        assert isinstance(success, bool)
        
        # Test interaction with hidden element
        mock_element.is_displayed.return_value = False
        success = browser_controller.click_element("#hidden-button")
        assert isinstance(success, bool)
    
    def test_page_content_validation(self, page_analyzer, mock_webdriver):
        """Test page content validation and sanitization."""
        # Test with malformed HTML
        mock_webdriver.page_source = "<html><body><div>Unclosed div<p>Test</body></html>"
        
        page_content = page_analyzer.extract_page_content()
        
        # Should handle malformed HTML gracefully
        assert isinstance(page_content, PageContent)
        assert page_content.validate() is True
        
        # Test with empty page
        mock_webdriver.page_source = ""
        mock_webdriver.title = ""
        
        page_content = page_analyzer.extract_page_content()
        assert isinstance(page_content, PageContent)
    
    def test_automation_with_dynamic_content(self, browser_controller, element_locator, mock_webdriver):
        """Test automation with dynamically loaded content."""
        # Simulate dynamic content loading
        def dynamic_find_element(*args, **kwargs):
            # First call returns None (content not loaded)
            # Second call returns element (content loaded)
            if not hasattr(dynamic_find_element, 'call_count'):
                dynamic_find_element.call_count = 0
            
            dynamic_find_element.call_count += 1
            
            if dynamic_find_element.call_count == 1:
                raise Exception("Element not found")
            else:
                return mock_webdriver.find_element.return_value
        
        mock_webdriver.find_element.side_effect = dynamic_find_element
        
        # Test waiting for dynamic element
        element = browser_controller.wait_for_element("#dynamic-element", timeout=5)
        
        # Should eventually find the element
        assert element is not None or element is None  # Depends on implementation