"""Unit tests for BrowserController."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException, TimeoutException

from ai_browser_agent.controllers.browser_controller import BrowserController
from ai_browser_agent.models.config import BrowserConfig


class TestBrowserController:
    """Test cases for BrowserController."""
    
    @pytest.fixture
    def browser_controller(self, browser_config):
        """Create a browser controller instance for testing."""
        return BrowserController(browser_config)
    
    @pytest.fixture
    def mock_driver(self):
        """Create a mock WebDriver for testing."""
        driver = Mock()
        driver.current_url = "https://test.example.com"
        driver.title = "Test Page"
        driver.page_source = "<html><body>Test</body></html>"
        driver.get_window_size.return_value = {"width": 1920, "height": 1080}
        return driver
    
    def test_initialization(self, browser_controller, browser_config):
        """Test browser controller initialization."""
        assert browser_controller.browser_config == browser_config
        assert browser_controller.driver is None
        assert browser_controller.wait is None
        assert browser_controller.action_chains is None
    
    def test_is_connected_false_when_no_driver(self, browser_controller):
        """Test is_connected returns False when no driver."""
        assert browser_controller.is_connected() is False
    
    def test_is_connected_false_when_driver_inactive(self, browser_controller, mock_driver):
        """Test is_connected returns False when driver is inactive."""
        mock_driver.current_url = Mock(side_effect=WebDriverException("Driver inactive"))
        browser_controller.driver = mock_driver
        assert browser_controller.is_connected() is False
    
    def test_is_connected_true_when_driver_active(self, browser_controller, mock_driver):
        """Test is_connected returns True when driver is active."""
        browser_controller.driver = mock_driver
        assert browser_controller.is_connected() is True
    
    @patch('ai_browser_agent.controllers.browser_controller.webdriver.Chrome')
    @patch('ai_browser_agent.controllers.browser_controller.ChromeDriverManager')
    def test_connect_success(self, mock_driver_manager, mock_chrome, browser_controller, mock_driver):
        """Test successful browser connection."""
        mock_driver_manager.return_value.install.return_value = "/path/to/chromedriver"
        mock_chrome.return_value = mock_driver
        
        browser_controller.connect()
        
        assert browser_controller.driver == mock_driver
        assert browser_controller.is_initialized is True
        mock_chrome.assert_called_once()
    
    @patch('ai_browser_agent.controllers.browser_controller.webdriver.Chrome')
    def test_connect_failure(self, mock_chrome, browser_controller):
        """Test browser connection failure."""
        mock_chrome.side_effect = WebDriverException("Connection failed")
        
        with pytest.raises(WebDriverException):
            browser_controller.connect()
        
        assert browser_controller.driver is None
        assert browser_controller.is_initialized is False
    
    def test_disconnect(self, browser_controller, mock_driver):
        """Test browser disconnection."""
        browser_controller.driver = mock_driver
        browser_controller.is_initialized = True
        
        browser_controller.disconnect()
        
        mock_driver.quit.assert_called_once()
        assert browser_controller.driver is None
        assert browser_controller.is_initialized is False
    
    def test_navigate_to_success(self, browser_controller, mock_driver):
        """Test successful navigation."""
        browser_controller.driver = mock_driver
        browser_controller.wait = Mock()
        browser_controller.wait.until.return_value = True
        
        url = "https://example.com"
        browser_controller.navigate_to(url)
        
        mock_driver.get.assert_called_once_with(url)
    
    def test_navigate_to_not_connected(self, browser_controller):
        """Test navigation when not connected."""
        with pytest.raises(WebDriverException, match="Browser is not connected"):
            browser_controller.navigate_to("https://example.com")
    
    def test_find_element_success(self, browser_controller, mock_driver):
        """Test successful element finding."""
        mock_element = Mock()
        browser_controller.driver = mock_driver
        browser_controller.wait = Mock()
        browser_controller.wait.until.return_value = mock_element
        
        result = browser_controller.find_element("#test-button")
        
        assert result == mock_element
    
    def test_find_element_timeout(self, browser_controller, mock_driver):
        """Test element finding timeout."""
        browser_controller.driver = mock_driver
        browser_controller.wait = Mock()
        browser_controller.wait.until.side_effect = TimeoutException("Timeout")
        
        result = browser_controller.find_element("#nonexistent")
        
        assert result is None
    
    def test_find_elements_success(self, browser_controller, mock_driver):
        """Test successful multiple element finding."""
        mock_elements = [Mock(), Mock()]
        browser_controller.driver = mock_driver
        mock_driver.find_elements.return_value = mock_elements
        
        result = browser_controller.find_elements(".test-class")
        
        assert result == mock_elements
        mock_driver.find_elements.assert_called_once_with(By.CSS_SELECTOR, ".test-class")
    
    def test_click_element_success(self, browser_controller, mock_driver):
        """Test successful element clicking."""
        mock_element = Mock()
        browser_controller.driver = mock_driver
        browser_controller.wait = Mock()
        browser_controller.wait.until.return_value = mock_element
        
        # Mock find_element to return our mock element
        browser_controller.find_element = Mock(return_value=mock_element)
        
        result = browser_controller.click_element("#test-button")
        
        assert result is True
        mock_element.click.assert_called_once()
    
    def test_click_element_not_found(self, browser_controller, mock_driver):
        """Test clicking element that doesn't exist."""
        browser_controller.driver = mock_driver
        browser_controller.find_element = Mock(return_value=None)
        
        result = browser_controller.click_element("#nonexistent")
        
        assert result is False
    
    def test_type_text_success(self, browser_controller, mock_driver):
        """Test successful text typing."""
        mock_element = Mock()
        browser_controller.driver = mock_driver
        browser_controller.wait = Mock()
        browser_controller.wait.until.return_value = mock_element
        
        # Mock find_element to return our mock element
        browser_controller.find_element = Mock(return_value=mock_element)
        
        result = browser_controller.type_text("#input-field", "test text")
        
        assert result is True
        mock_element.clear.assert_called_once()
        mock_element.send_keys.assert_called_once_with("test text")
    
    def test_type_text_no_clear(self, browser_controller, mock_driver):
        """Test text typing without clearing."""
        mock_element = Mock()
        browser_controller.driver = mock_driver
        browser_controller.wait = Mock()
        browser_controller.wait.until.return_value = mock_element
        
        # Mock find_element to return our mock element
        browser_controller.find_element = Mock(return_value=mock_element)
        
        result = browser_controller.type_text("#input-field", "test text", clear_first=False)
        
        assert result is True
        mock_element.clear.assert_not_called()
        mock_element.send_keys.assert_called_once_with("test text")
    
    def test_scroll_to_element_success(self, browser_controller, mock_driver):
        """Test successful scrolling to element."""
        mock_element = Mock()
        browser_controller.driver = mock_driver
        browser_controller.find_element = Mock(return_value=mock_element)
        
        result = browser_controller.scroll_to_element("#test-element")
        
        assert result is True
        mock_driver.execute_script.assert_called_once()
    
    def test_wait_for_element_success(self, browser_controller, mock_driver):
        """Test successful waiting for element."""
        mock_element = Mock()
        browser_controller.driver = mock_driver
        browser_controller.wait = Mock()
        browser_controller.wait.until.return_value = mock_element
        
        result = browser_controller.wait_for_element("#test-element")
        
        assert result == mock_element
    
    def test_wait_for_element_timeout(self, browser_controller, mock_driver):
        """Test waiting for element timeout."""
        browser_controller.driver = mock_driver
        browser_controller.wait = Mock()
        browser_controller.wait.until.side_effect = TimeoutException("Timeout")
        
        result = browser_controller.wait_for_element("#nonexistent")
        
        assert result is None
    
    def test_get_current_url(self, browser_controller, mock_driver):
        """Test getting current URL."""
        browser_controller.driver = mock_driver
        
        result = browser_controller.get_current_url()
        
        assert result == "https://test.example.com"
    
    def test_get_page_title(self, browser_controller, mock_driver):
        """Test getting page title."""
        browser_controller.driver = mock_driver
        
        result = browser_controller.get_page_title()
        
        assert result == "Test Page"
    
    def test_get_page_source(self, browser_controller, mock_driver):
        """Test getting page source."""
        browser_controller.driver = mock_driver
        
        result = browser_controller.get_page_source()
        
        assert result == "<html><body>Test</body></html>"
    
    def test_take_screenshot_to_file(self, browser_controller, mock_driver):
        """Test taking screenshot to file."""
        browser_controller.driver = mock_driver
        
        result = browser_controller.take_screenshot("/path/to/screenshot.png")
        
        assert result is None
        mock_driver.save_screenshot.assert_called_once_with("/path/to/screenshot.png")
    
    def test_take_screenshot_as_bytes(self, browser_controller, mock_driver):
        """Test taking screenshot as bytes."""
        browser_controller.driver = mock_driver
        mock_driver.get_screenshot_as_png.return_value = b"screenshot_data"
        
        result = browser_controller.take_screenshot()
        
        assert result == b"screenshot_data"
    
    def test_refresh_page(self, browser_controller, mock_driver):
        """Test page refresh."""
        browser_controller.driver = mock_driver
        browser_controller.wait = Mock()
        browser_controller.wait.until.return_value = True
        
        browser_controller.refresh_page()
        
        mock_driver.refresh.assert_called_once()
    
    def test_go_back(self, browser_controller, mock_driver):
        """Test going back in history."""
        browser_controller.driver = mock_driver
        
        browser_controller.go_back()
        
        mock_driver.back.assert_called_once()
    
    def test_go_forward(self, browser_controller, mock_driver):
        """Test going forward in history."""
        browser_controller.driver = mock_driver
        
        browser_controller.go_forward()
        
        mock_driver.forward.assert_called_once()
    
    def test_execute_script(self, browser_controller, mock_driver):
        """Test JavaScript execution."""
        browser_controller.driver = mock_driver
        mock_driver.execute_script.return_value = "script_result"
        
        result = browser_controller.execute_script("return document.title;")
        
        assert result == "script_result"
        mock_driver.execute_script.assert_called_once_with("return document.title;")
    
    def test_get_window_size(self, browser_controller, mock_driver):
        """Test getting window size."""
        browser_controller.driver = mock_driver
        
        result = browser_controller.get_window_size()
        
        assert result == {"width": 1920, "height": 1080}
    
    def test_set_window_size(self, browser_controller, mock_driver):
        """Test setting window size."""
        browser_controller.driver = mock_driver
        
        browser_controller.set_window_size(1280, 720)
        
        mock_driver.set_window_size.assert_called_once_with(1280, 720)
    
    def test_methods_require_connection(self, browser_controller):
        """Test that methods raise exception when not connected."""
        methods_to_test = [
            ("navigate_to", ("https://example.com",)),
            ("find_element", ("#test",)),
            ("find_elements", ("#test",)),
            ("click_element", ("#test",)),
            ("type_text", ("#test", "text")),
            ("scroll_to_element", ("#test",)),
            ("wait_for_element", ("#test",)),
            ("get_current_url", ()),
            ("get_page_title", ()),
            ("get_page_source", ()),
            ("take_screenshot", ()),
            ("refresh_page", ()),
            ("go_back", ()),
            ("go_forward", ()),
            ("execute_script", ("return true;",)),
            ("get_window_size", ()),
            ("set_window_size", (1280, 720)),
        ]
        
        for method_name, args in methods_to_test:
            method = getattr(browser_controller, method_name)
            with pytest.raises(WebDriverException, match="Browser is not connected"):
                method(*args)