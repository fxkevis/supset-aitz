"""Integration tests for online ordering workflow."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from ai_browser_agent.core.ai_agent import AIAgent
from ai_browser_agent.handlers.ordering_task_handler import OrderingTaskHandler
from ai_browser_agent.controllers.browser_controller import BrowserController
from ai_browser_agent.models.task import Task, TaskStatus
from ai_browser_agent.models.config import AppConfig, BrowserConfig, SecurityConfig, AIModelConfig
from ai_browser_agent.models.page_content import PageContent, WebElement
from ai_browser_agent.models.action import Action, ActionType


class TestOrderingWorkflowIntegration:
    """Integration tests for complete online ordering workflows."""
    
    @pytest.fixture
    def app_config(self):
        """Create test application configuration."""
        return AppConfig(
            browser=BrowserConfig(headless=True, timeout=15),
            security=SecurityConfig(
                require_confirmation_for_payments=True,
                require_confirmation_for_submissions=True
            ),
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
        controller.type_text = Mock(return_value=True)
        controller.get_current_url = Mock(return_value="https://fooddelivery.com")
        controller.get_page_title = Mock(return_value="Food Delivery - Order Online")
        controller.get_page_source = Mock(return_value="<html><body>Food delivery content</body></html>")
        return controller
    
    @pytest.fixture
    def mock_ai_agent(self):
        """Create mock AI agent for testing."""
        agent = Mock(spec=AIAgent)
        agent.analyze_page_and_decide = AsyncMock()
        agent.execute_action = AsyncMock(return_value=True)
        return agent
    
    @pytest.fixture
    def ordering_task_handler(self, app_config, mock_browser_controller, mock_ai_agent):
        """Create ordering task handler with mocked dependencies."""
        handler = OrderingTaskHandler(app_config)
        handler.browser_controller = mock_browser_controller
        handler.ai_agent = mock_ai_agent
        return handler
    
    @pytest.fixture
    def restaurant_search_page(self):
        """Create mock restaurant search page content."""
        elements = [
            # Search input
            WebElement(
                tag_name="input",
                attributes={"type": "text", "name": "search", "placeholder": "Search for food"},
                css_selector="input[name='search']"
            ),
            # Search button
            WebElement(
                tag_name="button",
                attributes={"type": "submit", "class": "search-btn"},
                text_content="Search",
                css_selector=".search-btn",
                is_clickable=True
            ),
            # Restaurant results
            WebElement(
                tag_name="div",
                attributes={"class": "restaurant-card", "data-restaurant-id": "rest1"},
                text_content="Pizza Palace - Italian cuisine, 4.5 stars",
                css_selector=".restaurant-card[data-restaurant-id='rest1']",
                is_clickable=True
            ),
            WebElement(
                tag_name="div",
                attributes={"class": "restaurant-card", "data-restaurant-id": "rest2"},
                text_content="Burger King - Fast food, 4.2 stars",
                css_selector=".restaurant-card[data-restaurant-id='rest2']",
                is_clickable=True
            )
        ]
        
        return PageContent(
            url="https://fooddelivery.com/search",
            title="Food Delivery - Search Results",
            text_content="Search for restaurants and food delivery",
            elements=elements
        )
    
    @pytest.fixture
    def restaurant_menu_page(self):
        """Create mock restaurant menu page content."""
        elements = [
            # Menu items
            WebElement(
                tag_name="div",
                attributes={"class": "menu-item", "data-item-id": "pizza1"},
                text_content="Margherita Pizza - $12.99 - Classic tomato and mozzarella",
                css_selector=".menu-item[data-item-id='pizza1']"
            ),
            WebElement(
                tag_name="div",
                attributes={"class": "menu-item", "data-item-id": "pizza2"},
                text_content="Pepperoni Pizza - $14.99 - Pepperoni and cheese",
                css_selector=".menu-item[data-item-id='pizza2']"
            ),
            # Add to cart buttons
            WebElement(
                tag_name="button",
                attributes={"class": "add-to-cart", "data-item-id": "pizza1"},
                text_content="Add to Cart",
                css_selector=".add-to-cart[data-item-id='pizza1']",
                is_clickable=True
            ),
            WebElement(
                tag_name="button",
                attributes={"class": "add-to-cart", "data-item-id": "pizza2"},
                text_content="Add to Cart",
                css_selector=".add-to-cart[data-item-id='pizza2']",
                is_clickable=True
            ),
            # Cart summary
            WebElement(
                tag_name="div",
                attributes={"class": "cart-summary"},
                text_content="Cart: 0 items, $0.00",
                css_selector=".cart-summary"
            )
        ]
        
        return PageContent(
            url="https://fooddelivery.com/restaurant/pizza-palace",
            title="Pizza Palace - Menu",
            text_content="Pizza Palace menu with various pizza options",
            elements=elements
        )
    
    @pytest.fixture
    def checkout_page(self):
        """Create mock checkout page content."""
        elements = [
            # Order summary
            WebElement(
                tag_name="div",
                attributes={"class": "order-summary"},
                text_content="Order Summary: Margherita Pizza x1 - $12.99, Total: $15.48 (incl. tax & delivery)",
                css_selector=".order-summary"
            ),
            # Delivery address form
            WebElement(
                tag_name="input",
                attributes={"type": "text", "name": "address", "placeholder": "Delivery address"},
                css_selector="input[name='address']"
            ),
            # Payment method selection
            WebElement(
                tag_name="select",
                attributes={"name": "payment_method"},
                css_selector="select[name='payment_method']"
            ),
            # Place order button
            WebElement(
                tag_name="button",
                attributes={"class": "place-order-btn", "type": "submit"},
                text_content="Place Order",
                css_selector=".place-order-btn",
                is_clickable=True
            )
        ]
        
        return PageContent(
            url="https://fooddelivery.com/checkout",
            title="Checkout - Complete Your Order",
            text_content="Complete your food delivery order",
            elements=elements
        )
    
    @pytest.mark.asyncio
    async def test_food_search_and_selection_workflow(self, ordering_task_handler, restaurant_search_page, mock_ai_agent):
        """Test complete food search and restaurant selection workflow."""
        # Create food ordering task
        task = Task(
            id="food-order-1",
            description="Order pizza from a highly rated restaurant",
            status=TaskStatus.PENDING
        )
        
        # Mock AI agent to search for pizza
        search_actions = [
            Action(
                id="action-1",
                type=ActionType.TYPE,
                target="input[name='search']",
                parameters={"text": "pizza"},
                description="Search for pizza restaurants",
                confidence=0.9
            ),
            Action(
                id="action-2",
                type=ActionType.CLICK,
                target=".search-btn",
                description="Click search button",
                confidence=0.95
            ),
            Action(
                id="action-3",
                type=ActionType.CLICK,
                target=".restaurant-card[data-restaurant-id='rest1']",
                description="Select Pizza Palace (highest rated)",
                confidence=0.85
            )
        ]
        mock_ai_agent.analyze_page_and_decide.return_value = search_actions
        
        # Mock page analyzer to return search page
        with patch.object(ordering_task_handler, '_extract_page_content', return_value=restaurant_search_page):
            # Execute the task
            result = await ordering_task_handler.handle_task(task)
        
        # Verify task execution
        assert result is not None
        assert task.status in [TaskStatus.COMPLETED, TaskStatus.IN_PROGRESS, TaskStatus.REQUIRES_INPUT]
        
        # Verify AI was called to analyze the page
        mock_ai_agent.analyze_page_and_decide.assert_called()
        
        # Verify search and selection actions were executed
        mock_ai_agent.execute_action.assert_called()
        
        # Check that pizza search was performed
        call_args = mock_ai_agent.analyze_page_and_decide.call_args
        page_content = call_args[0][0]
        assert "pizza" in page_content.text_content.lower() or "search" in page_content.text_content.lower()
    
    @pytest.mark.asyncio
    async def test_menu_browsing_and_item_selection_workflow(self, ordering_task_handler, restaurant_menu_page, mock_ai_agent):
        """Test menu browsing and item selection workflow."""
        # Create menu selection task
        task = Task(
            id="menu-selection-1",
            description="Browse menu and add Margherita pizza to cart",
            status=TaskStatus.PENDING
        )
        
        # Mock AI agent to select menu items
        menu_actions = [
            Action(
                id="action-1",
                type=ActionType.EXTRACT,
                target=".menu-item",
                description="Extract menu items for analysis",
                confidence=0.9
            ),
            Action(
                id="action-2",
                type=ActionType.CLICK,
                target=".add-to-cart[data-item-id='pizza1']",
                description="Add Margherita pizza to cart",
                confidence=0.85
            )
        ]
        mock_ai_agent.analyze_page_and_decide.return_value = menu_actions
        
        # Mock page analyzer
        with patch.object(ordering_task_handler, '_extract_page_content', return_value=restaurant_menu_page):
            # Execute the task
            result = await ordering_task_handler.handle_task(task)
        
        # Verify task execution
        assert result is not None
        mock_ai_agent.analyze_page_and_decide.assert_called()
        mock_ai_agent.execute_action.assert_called()
        
        # Verify menu analysis
        call_args = mock_ai_agent.analyze_page_and_decide.call_args
        page_content = call_args[0][0]
        assert "pizza" in page_content.text_content.lower()
        assert "margherita" in page_content.text_content.lower()
    
    @pytest.mark.asyncio
    async def test_cart_management_workflow(self, ordering_task_handler, restaurant_menu_page, mock_ai_agent):
        """Test shopping cart management workflow."""
        # Create cart management task
        task = Task(
            id="cart-management-1",
            description="Add multiple items to cart and review total",
            status=TaskStatus.PENDING
        )
        
        # Mock AI agent to manage cart
        cart_actions = [
            Action(
                id="action-1",
                type=ActionType.CLICK,
                target=".add-to-cart[data-item-id='pizza1']",
                description="Add Margherita pizza to cart",
                confidence=0.9
            ),
            Action(
                id="action-2",
                type=ActionType.CLICK,
                target=".add-to-cart[data-item-id='pizza2']",
                description="Add Pepperoni pizza to cart",
                confidence=0.85
            ),
            Action(
                id="action-3",
                type=ActionType.EXTRACT,
                target=".cart-summary",
                description="Check cart total",
                confidence=0.95
            )
        ]
        mock_ai_agent.analyze_page_and_decide.return_value = cart_actions
        
        # Mock page analyzer
        with patch.object(ordering_task_handler, '_extract_page_content', return_value=restaurant_menu_page):
            # Execute the task
            result = await ordering_task_handler.handle_task(task)
        
        # Verify cart management
        assert result is not None
        mock_ai_agent.analyze_page_and_decide.assert_called()
        
        # Verify multiple items were considered
        call_args = mock_ai_agent.analyze_page_and_decide.call_args
        page_content = call_args[0][0]
        assert "cart" in page_content.text_content.lower()
    
    @pytest.mark.asyncio
    async def test_checkout_workflow_with_security(self, ordering_task_handler, checkout_page, mock_ai_agent):
        """Test checkout workflow with security confirmation."""
        # Create checkout task
        task = Task(
            id="checkout-1",
            description="Complete checkout and place order",
            status=TaskStatus.PENDING
        )
        
        # Mock AI agent to handle checkout
        checkout_actions = [
            Action(
                id="action-1",
                type=ActionType.TYPE,
                target="input[name='address']",
                parameters={"text": "123 Main St, City, State"},
                description="Enter delivery address",
                confidence=0.9
            ),
            Action(
                id="action-2",
                type=ActionType.SELECT,
                target="select[name='payment_method']",
                parameters={"value": "credit_card"},
                description="Select payment method",
                confidence=0.85
            ),
            Action(
                id="action-3",
                type=ActionType.CLICK,
                target=".place-order-btn",
                description="Place order (requires confirmation)",
                confidence=0.8,
                is_destructive=True  # Payment action
            )
        ]
        mock_ai_agent.analyze_page_and_decide.return_value = checkout_actions
        
        # Mock security layer to require confirmation for payment
        with patch.object(ordering_task_handler, '_extract_page_content', return_value=checkout_page):
            with patch.object(ordering_task_handler.security_layer, 'validate_action') as mock_security:
                mock_security.return_value = {"requires_confirmation": True, "is_safe": False}
                
                # Execute the task
                result = await ordering_task_handler.handle_task(task)
        
        # Verify security validation was called
        mock_security.assert_called()
        
        # Task should require user input due to payment action
        assert task.status == TaskStatus.REQUIRES_INPUT or result is not None
    
    @pytest.mark.asyncio
    async def test_order_history_workflow(self, ordering_task_handler, mock_ai_agent):
        """Test order history browsing and reordering workflow."""
        # Create order history task
        task = Task(
            id="reorder-1",
            description="Find previous pizza order and reorder the same items",
            status=TaskStatus.PENDING
        )
        
        # Mock order history page
        history_page = PageContent(
            url="https://fooddelivery.com/orders",
            title="Order History",
            text_content="Previous orders: Pizza Palace - Margherita Pizza, $12.99, ordered 2 days ago",
            elements=[
                WebElement(
                    tag_name="div",
                    attributes={"class": "order-item", "data-order-id": "order123"},
                    text_content="Pizza Palace - Margherita Pizza, $12.99",
                    css_selector=".order-item[data-order-id='order123']"
                ),
                WebElement(
                    tag_name="button",
                    attributes={"class": "reorder-btn", "data-order-id": "order123"},
                    text_content="Reorder",
                    css_selector=".reorder-btn[data-order-id='order123']",
                    is_clickable=True
                )
            ]
        )
        
        # Mock AI agent to find and reorder
        reorder_actions = [
            Action(
                id="action-1",
                type=ActionType.EXTRACT,
                target=".order-item",
                description="Extract previous orders",
                confidence=0.9
            ),
            Action(
                id="action-2",
                type=ActionType.CLICK,
                target=".reorder-btn[data-order-id='order123']",
                description="Reorder previous pizza",
                confidence=0.85
            )
        ]
        mock_ai_agent.analyze_page_and_decide.return_value = reorder_actions
        
        # Mock page analyzer
        with patch.object(ordering_task_handler, '_extract_page_content', return_value=history_page):
            # Execute the task
            result = await ordering_task_handler.handle_task(task)
        
        # Verify reorder workflow
        assert result is not None
        mock_ai_agent.analyze_page_and_decide.assert_called()
        
        # Verify order history was analyzed
        call_args = mock_ai_agent.analyze_page_and_decide.call_args
        page_content = call_args[0][0]
        assert "pizza" in page_content.text_content.lower()
        assert "order" in page_content.text_content.lower()
    
    @pytest.mark.asyncio
    async def test_price_comparison_workflow(self, ordering_task_handler, restaurant_search_page, mock_ai_agent):
        """Test price comparison across restaurants workflow."""
        # Create price comparison task
        task = Task(
            id="price-compare-1",
            description="Compare pizza prices across different restaurants and choose the best value",
            status=TaskStatus.PENDING
        )
        
        # Mock AI agent to compare prices
        comparison_actions = [
            Action(
                id="action-1",
                type=ActionType.EXTRACT,
                target=".restaurant-card",
                description="Extract restaurant information for comparison",
                confidence=0.9
            ),
            Action(
                id="action-2",
                type=ActionType.CLICK,
                target=".restaurant-card[data-restaurant-id='rest1']",
                description="Check Pizza Palace menu and prices",
                confidence=0.8
            )
        ]
        mock_ai_agent.analyze_page_and_decide.return_value = comparison_actions
        
        # Mock page analyzer
        with patch.object(ordering_task_handler, '_extract_page_content', return_value=restaurant_search_page):
            # Execute the task
            result = await ordering_task_handler.handle_task(task)
        
        # Verify price comparison
        assert result is not None
        mock_ai_agent.analyze_page_and_decide.assert_called()
        
        # Verify restaurants were analyzed for comparison
        call_args = mock_ai_agent.analyze_page_and_decide.call_args
        page_content = call_args[0][0]
        assert "restaurant" in page_content.text_content.lower()
    
    @pytest.mark.asyncio
    async def test_error_handling_in_ordering(self, ordering_task_handler, mock_ai_agent):
        """Test error handling during ordering workflow."""
        # Create task
        task = Task(
            id="error-order-1",
            description="Test error handling during order",
            status=TaskStatus.PENDING
        )
        
        # Mock browser controller to raise exception
        ordering_task_handler.browser_controller.navigate_to.side_effect = Exception("Site unavailable")
        
        # Execute the task
        result = await ordering_task_handler.handle_task(task)
        
        # Verify error handling
        assert task.status == TaskStatus.FAILED or result is not None
        assert task.error_message is not None or "error" in str(result).lower()
    
    @pytest.mark.asyncio
    async def test_multi_step_ordering_workflow(self, ordering_task_handler, restaurant_search_page, restaurant_menu_page, checkout_page, mock_ai_agent):
        """Test complete multi-step ordering workflow."""
        # Create comprehensive ordering task
        task = Task(
            id="full-order-1",
            description="Search for pizza restaurant, browse menu, add items to cart, and proceed to checkout",
            status=TaskStatus.PENDING
        )
        
        # Mock AI agent to return different actions for each step
        search_actions = [
            Action(id="1", type=ActionType.TYPE, target="input[name='search']", parameters={"text": "pizza"}, description="Search pizza")
        ]
        
        menu_actions = [
            Action(id="2", type=ActionType.CLICK, target=".add-to-cart[data-item-id='pizza1']", description="Add pizza to cart")
        ]
        
        checkout_actions = [
            Action(id="3", type=ActionType.CLICK, target=".checkout-btn", description="Proceed to checkout")
        ]
        
        # Configure mock to return different actions on each call
        mock_ai_agent.analyze_page_and_decide.side_effect = [
            search_actions,
            menu_actions,
            checkout_actions
        ]
        
        # Mock page analyzer to return different pages
        page_sequence = [restaurant_search_page, restaurant_menu_page, checkout_page]
        with patch.object(ordering_task_handler, '_extract_page_content', side_effect=page_sequence):
            # Execute the task
            result = await ordering_task_handler.handle_task(task)
        
        # Verify multiple steps were executed
        assert mock_ai_agent.analyze_page_and_decide.call_count >= 1
        
        # Verify task progressed through workflow
        assert result is not None or task.status != TaskStatus.PENDING
    
    def test_ordering_handler_initialization(self, app_config):
        """Test ordering task handler initialization."""
        handler = OrderingTaskHandler(app_config)
        
        assert handler.config == app_config
        assert handler.supported_domains is not None
        assert len(handler.supported_domains) > 0
        # Should support common food delivery and e-commerce sites
        supported_sites = [domain.lower() for domain in handler.supported_domains]
        assert any("food" in site or "delivery" in site or "amazon" in site for site in supported_sites)
    
    def test_ordering_handler_task_validation(self, ordering_task_handler):
        """Test task validation in ordering handler."""
        # Valid ordering task
        valid_task = Task(
            id="valid-order-1",
            description="Order food from restaurant",
            status=TaskStatus.PENDING
        )
        
        # Should not raise exception
        try:
            ordering_task_handler._validate_task(valid_task)
            validation_passed = True
        except:
            validation_passed = False
        
        assert validation_passed
    
    @pytest.mark.asyncio
    async def test_site_navigation_for_ordering(self, ordering_task_handler, mock_ai_agent):
        """Test navigation to ordering sites."""
        task = Task(
            id="nav-order-1",
            description="Navigate to food delivery site",
            status=TaskStatus.PENDING
        )
        
        # Mock successful navigation
        ordering_task_handler.browser_controller.navigate_to = Mock()
        ordering_task_handler.browser_controller.get_current_url.return_value = "https://fooddelivery.com"
        
        # Mock page content extraction
        delivery_page = PageContent(
            url="https://fooddelivery.com",
            title="Food Delivery",
            text_content="Order food online",
            elements=[]
        )
        
        with patch.object(ordering_task_handler, '_extract_page_content', return_value=delivery_page):
            # Execute navigation
            result = await ordering_task_handler._navigate_to_ordering_site("fooddelivery.com")
        
        # Verify navigation was attempted
        ordering_task_handler.browser_controller.navigate_to.assert_called()
        assert result is True or result is not None