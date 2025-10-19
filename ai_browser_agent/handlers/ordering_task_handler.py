"""Online ordering task handler for automated shopping and food delivery."""

import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from ai_browser_agent.interfaces.base_interfaces import BaseTaskHandler
from ai_browser_agent.controllers.browser_controller import BrowserController
from ai_browser_agent.controllers.element_locator import ElementLocator
from ai_browser_agent.controllers.page_analyzer import PageAnalyzer
from ai_browser_agent.managers.context_manager import ContextManager
from ai_browser_agent.models.task import Task, TaskStatus
from ai_browser_agent.models.action import Action, ActionType
from ai_browser_agent.models.page_content import PageContent


logger = logging.getLogger(__name__)


class OrderingPlatformType(Enum):
    """Types of ordering platforms."""
    FOOD_DELIVERY = "food_delivery"
    E_COMMERCE = "e_commerce"
    GROCERY = "grocery"
    RESTAURANT = "restaurant"


@dataclass
class ProductInfo:
    """Information about a product or menu item."""
    name: str
    price: str
    description: Optional[str]
    availability: bool
    element_selector: str
    category: Optional[str] = None
    rating: Optional[float] = None
    image_url: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "price": self.price,
            "description": self.description,
            "availability": self.availability,
            "element_selector": self.element_selector,
            "category": self.category,
            "rating": self.rating,
            "image_url": self.image_url
        }


@dataclass
class CartItem:
    """Item in shopping cart."""
    product: ProductInfo
    quantity: int
    total_price: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "product": self.product.to_dict(),
            "quantity": self.quantity,
            "total_price": self.total_price
        }


@dataclass
class OrderSummary:
    """Summary of an order."""
    items: List[CartItem]
    subtotal: str
    tax: Optional[str]
    delivery_fee: Optional[str]
    total: str
    estimated_delivery: Optional[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "items": [item.to_dict() for item in self.items],
            "subtotal": self.subtotal,
            "tax": self.tax,
            "delivery_fee": self.delivery_fee,
            "total": self.total,
            "estimated_delivery": self.estimated_delivery
        }


class PlatformDetector:
    """Detects and handles different ordering platforms."""
    
    SUPPORTED_PLATFORMS = {
        "ubereats": {
            "domains": ["ubereats.com"],
            "type": OrderingPlatformType.FOOD_DELIVERY,
            "search_selectors": [
                "[data-testid='store-search-input']",
                "input[placeholder*='Search']",
                "#search-suggestions-typeahead-input"
            ],
            "product_selectors": [
                "[data-testid*='store-card']",
                "[data-testid*='menu-item']",
                ".hb"
            ],
            "add_to_cart_selectors": [
                "[data-testid='add-item-button']",
                "button[aria-label*='Add']",
                ".add-button"
            ],
            "cart_selectors": [
                "[data-testid='cart-container']",
                ".cart",
                "#cart"
            ],
            "checkout_selectors": [
                "[data-testid='checkout-button']",
                "button[aria-label*='checkout']",
                ".checkout-button"
            ]
        },
        "doordash": {
            "domains": ["doordash.com"],
            "type": OrderingPlatformType.FOOD_DELIVERY,
            "search_selectors": [
                "[data-anchor-id='StoreSearchInput']",
                "input[placeholder*='Search']",
                ".search-input"
            ],
            "product_selectors": [
                "[data-testid*='store-header']",
                "[data-testid*='menu-item']",
                ".store-item"
            ],
            "add_to_cart_selectors": [
                "[data-testid='add-item-button']",
                "button[aria-label*='Add']"
            ],
            "cart_selectors": [
                "[data-testid='CartContainer']",
                ".cart-container"
            ],
            "checkout_selectors": [
                "[data-testid='checkout-button']",
                ".checkout-button"
            ]
        },
        "amazon": {
            "domains": ["amazon.com", "amazon.co.uk", "amazon.de"],
            "type": OrderingPlatformType.E_COMMERCE,
            "search_selectors": [
                "#twotabsearchtextbox",
                "input[name='field-keywords']",
                ".nav-search-field input"
            ],
            "product_selectors": [
                "[data-component-type='s-search-result']",
                ".s-result-item",
                ".a-section"
            ],
            "add_to_cart_selectors": [
                "#add-to-cart-button",
                "input[name='submit.add-to-cart']",
                ".a-button-input[aria-labelledby*='cart']"
            ],
            "cart_selectors": [
                "#nav-cart",
                ".nav-cart",
                "#sc-active-cart"
            ],
            "checkout_selectors": [
                "[name='proceedToRetailCheckout']",
                ".a-button-input[aria-labelledby*='checkout']"
            ]
        },
        "instacart": {
            "domains": ["instacart.com"],
            "type": OrderingPlatformType.GROCERY,
            "search_selectors": [
                "[data-testid='search-input']",
                "input[placeholder*='Search']",
                ".search-bar input"
            ],
            "product_selectors": [
                "[data-testid*='product-card']",
                ".product-card",
                "[data-testid*='item-card']"
            ],
            "add_to_cart_selectors": [
                "[data-testid='add-button']",
                "button[aria-label*='Add']"
            ],
            "cart_selectors": [
                "[data-testid='cart']",
                ".cart-container"
            ],
            "checkout_selectors": [
                "[data-testid='checkout-button']",
                ".checkout-button"
            ]
        }
    }
    
    @classmethod
    def detect_platform(cls, url: str) -> Optional[str]:
        """Detect ordering platform from URL."""
        for platform, config in cls.SUPPORTED_PLATFORMS.items():
            for domain in config["domains"]:
                if domain in url.lower():
                    return platform
        return None
    
    @classmethod
    def get_platform_config(cls, platform: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific platform."""
        return cls.SUPPORTED_PLATFORMS.get(platform)


class ProductMatcher:
    """Matches user requests to available products."""
    
    def __init__(self):
        self.food_keywords = {
            "pizza": ["pizza", "margherita", "pepperoni", "cheese pizza"],
            "burger": ["burger", "hamburger", "cheeseburger", "big mac"],
            "sushi": ["sushi", "sashimi", "roll", "california roll"],
            "chinese": ["chinese", "fried rice", "lo mein", "general tso"],
            "italian": ["pasta", "spaghetti", "lasagna", "ravioli"],
            "mexican": ["tacos", "burrito", "quesadilla", "nachos"],
            "indian": ["curry", "biryani", "naan", "tikka masala"],
            "thai": ["pad thai", "tom yum", "green curry", "thai"],
            "coffee": ["coffee", "latte", "cappuccino", "espresso"],
            "dessert": ["cake", "ice cream", "cookies", "chocolate"]
        }
        
        self.product_keywords = {
            "electronics": ["phone", "laptop", "tablet", "headphones", "camera"],
            "clothing": ["shirt", "pants", "dress", "shoes", "jacket"],
            "books": ["book", "novel", "textbook", "magazine"],
            "home": ["furniture", "lamp", "pillow", "blanket", "decor"],
            "health": ["vitamins", "supplements", "medicine", "first aid"],
            "sports": ["equipment", "weights", "yoga", "running", "fitness"]
        }
    
    def extract_search_terms(self, task_description: str) -> List[str]:
        """Extract search terms from task description."""
        description_lower = task_description.lower()
        search_terms = []
        
        # Look for quoted items
        quoted_items = re.findall(r'"([^"]*)"', task_description)
        search_terms.extend(quoted_items)
        
        # Look for food keywords
        for category, keywords in self.food_keywords.items():
            for keyword in keywords:
                if keyword in description_lower:
                    search_terms.append(keyword)
        
        # Look for product keywords
        for category, keywords in self.product_keywords.items():
            for keyword in keywords:
                if keyword in description_lower:
                    search_terms.append(keyword)
        
        # Extract potential product names (capitalized words)
        words = task_description.split()
        for word in words:
            if word[0].isupper() and len(word) > 3:
                search_terms.append(word)
        
        return list(set(search_terms))  # Remove duplicates
    
    def match_products(self, search_terms: List[str], available_products: List[ProductInfo]) -> List[ProductInfo]:
        """Match search terms to available products."""
        matched_products = []
        
        for product in available_products:
            product_name_lower = product.name.lower()
            product_desc_lower = (product.description or "").lower()
            
            for term in search_terms:
                term_lower = term.lower()
                
                # Exact match in name
                if term_lower in product_name_lower:
                    matched_products.append(product)
                    break
                
                # Partial match in description
                elif term_lower in product_desc_lower:
                    matched_products.append(product)
                    break
                
                # Fuzzy matching for similar words
                elif self._fuzzy_match(term_lower, product_name_lower):
                    matched_products.append(product)
                    break
        
        return matched_products
    
    def _fuzzy_match(self, term: str, product_name: str) -> bool:
        """Simple fuzzy matching for product names."""
        # Check if term is a substring of any word in product name
        product_words = product_name.split()
        for word in product_words:
            if term in word or word in term:
                return True
        
        # Check for common variations
        variations = {
            "burger": ["hamburger", "cheeseburger"],
            "pizza": ["pie"],
            "soda": ["drink", "beverage"],
            "fries": ["french fries", "chips"]
        }
        
        if term in variations:
            for variation in variations[term]:
                if variation in product_name:
                    return True
        
        return False


class OrderingTaskHandler(BaseTaskHandler):
    """Specialized handler for online ordering tasks."""
    
    def __init__(self, browser_controller: BrowserController,
                 context_manager: ContextManager,
                 config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.browser_controller = browser_controller
        self.context_manager = context_manager
        self.element_locator = ElementLocator(browser_controller.driver)
        self.page_analyzer = PageAnalyzer(browser_controller.driver)
        self.product_matcher = ProductMatcher()
        
        # Configuration
        self.max_products_to_scan = config.get("max_products_to_scan", 20) if config else 20
        self.auto_proceed_to_checkout = config.get("auto_proceed_to_checkout", False) if config else False
        self.price_limit = config.get("price_limit") if config else None
        
        # State tracking
        self.current_platform: Optional[str] = None
        self.platform_config: Optional[Dict[str, Any]] = None
        self.cart_items: List[CartItem] = []
        self.order_history: List[Dict[str, Any]] = []
    
    async def can_handle_task(self, task: Task) -> bool:
        """Check if this handler can process the given task."""
        task_lower = task.description.lower()
        ordering_keywords = [
            "order", "buy", "purchase", "add to cart", "checkout",
            "food delivery", "shopping", "grocery", "restaurant",
            "ubereats", "doordash", "amazon", "instacart"
        ]
        
        return any(keyword in task_lower for keyword in ordering_keywords)
    
    async def execute_task(self, task: Task) -> Dict[str, Any]:
        """Execute online ordering task."""
        logger.info(f"Starting ordering task execution: {task.description}")
        
        try:
            # Navigate to ordering platform if needed
            await self._ensure_platform_access(task)
            
            # Detect current platform
            current_url = await self.browser_controller.get_current_url()
            self.current_platform = PlatformDetector.detect_platform(current_url)
            
            if not self.current_platform:
                raise ValueError(f"Unsupported ordering platform at URL: {current_url}")
            
            self.platform_config = PlatformDetector.get_platform_config(self.current_platform)
            logger.info(f"Detected ordering platform: {self.current_platform}")
            
            # Parse task requirements
            task_type, task_params = self._parse_ordering_task(task.description)
            
            # Execute specific ordering task
            if task_type == "product_search":
                result = await self._handle_product_search(task_params)
            elif task_type == "add_to_cart":
                result = await self._handle_add_to_cart(task_params)
            elif task_type == "complete_order":
                result = await self._handle_complete_order(task_params)
            else:
                result = await self._handle_general_ordering_task(task)
            
            # Update task status
            task.update_status(TaskStatus.COMPLETED)
            task.set_result(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Ordering task execution failed: {e}")
            task.set_error(str(e))
            return {"error": str(e), "cart_items": len(self.cart_items)}
    
    async def _ensure_platform_access(self, task: Task) -> None:
        """Ensure we have access to an ordering platform."""
        current_url = await self.browser_controller.get_current_url()
        
        # Check if we're already on an ordering platform
        if PlatformDetector.detect_platform(current_url):
            return
        
        # Try to determine platform from task description
        task_lower = task.description.lower()
        
        if "ubereats" in task_lower or "uber eats" in task_lower:
            await self.browser_controller.navigate_to("https://www.ubereats.com")
        elif "doordash" in task_lower or "door dash" in task_lower:
            await self.browser_controller.navigate_to("https://www.doordash.com")
        elif "amazon" in task_lower:
            await self.browser_controller.navigate_to("https://www.amazon.com")
        elif "instacart" in task_lower:
            await self.browser_controller.navigate_to("https://www.instacart.com")
        elif any(keyword in task_lower for keyword in ["food", "restaurant", "delivery"]):
            # Default to UberEats for food delivery
            await self.browser_controller.navigate_to("https://www.ubereats.com")
        else:
            # Default to Amazon for general shopping
            await self.browser_controller.navigate_to("https://www.amazon.com")
        
        # Wait for page to load
        await self.browser_controller.wait_for_page_load()
    
    def _parse_ordering_task(self, description: str) -> Tuple[str, Dict[str, Any]]:
        """Parse ordering task description to determine task type and parameters."""
        description_lower = description.lower()
        
        if any(keyword in description_lower for keyword in ["search", "find", "look for"]):
            search_terms = self.product_matcher.extract_search_terms(description)
            return "product_search", {"search_terms": search_terms}
        
        if any(keyword in description_lower for keyword in ["add to cart", "add", "order"]):
            search_terms = self.product_matcher.extract_search_terms(description)
            return "add_to_cart", {"search_terms": search_terms}
        
        if any(keyword in description_lower for keyword in ["checkout", "complete", "finish order"]):
            return "complete_order", {"proceed_to_payment": False}
        
        # Default to general ordering
        search_terms = self.product_matcher.extract_search_terms(description)
        return "general", {"search_terms": search_terms}
    
    async def _handle_product_search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle product search tasks."""
        logger.info("Starting product search task")
        
        search_terms = params.get("search_terms", [])
        if not search_terms:
            return {"error": "No search terms found in task description"}
        
        all_found_products = []
        
        for search_term in search_terms:
            # Perform search
            search_results = await self._search_for_products(search_term)
            all_found_products.extend(search_results)
        
        return {
            "task_type": "product_search",
            "search_terms": search_terms,
            "products_found": len(all_found_products),
            "products": [product.to_dict() for product in all_found_products],
            "platform": self.current_platform
        }
    
    async def _handle_add_to_cart(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle add to cart tasks."""
        logger.info("Starting add to cart task")
        
        search_terms = params.get("search_terms", [])
        if not search_terms:
            return {"error": "No items specified to add to cart"}
        
        added_items = []
        
        for search_term in search_terms:
            # Search for products
            products = await self._search_for_products(search_term)
            
            if products:
                # Add the first matching product to cart
                best_match = products[0]
                success = await self._add_product_to_cart(best_match)
                
                if success:
                    cart_item = CartItem(
                        product=best_match,
                        quantity=1,
                        total_price=best_match.price
                    )
                    self.cart_items.append(cart_item)
                    added_items.append(cart_item.to_dict())
                    logger.info(f"Added to cart: {best_match.name}")
        
        return {
            "task_type": "add_to_cart",
            "search_terms": search_terms,
            "items_added": len(added_items),
            "added_items": added_items,
            "cart_total_items": len(self.cart_items)
        }
    
    async def _handle_complete_order(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle order completion tasks."""
        logger.info("Starting order completion task")
        
        # Get current cart contents
        cart_summary = await self._get_cart_summary()
        
        if not cart_summary or not cart_summary.items:
            return {"error": "Cart is empty, cannot complete order"}
        
        # Proceed to checkout
        checkout_success = await self._proceed_to_checkout()
        
        if not checkout_success:
            return {"error": "Failed to proceed to checkout"}
        
        # Stop at payment confirmation (as per requirements)
        payment_page_reached = await self._verify_payment_page()
        
        return {
            "task_type": "complete_order",
            "checkout_success": checkout_success,
            "payment_page_reached": payment_page_reached,
            "order_summary": cart_summary.to_dict() if cart_summary else None,
            "message": "Order ready for payment confirmation"
        }
    
    async def _handle_general_ordering_task(self, task: Task) -> Dict[str, Any]:
        """Handle general ordering tasks."""
        logger.info("Starting general ordering task")
        
        # Extract search terms from task description
        search_terms = self.product_matcher.extract_search_terms(task.description)
        
        if not search_terms:
            return {"error": "Could not identify products to order from task description"}
        
        # Search and add products to cart
        added_items = []
        
        for search_term in search_terms:
            products = await self._search_for_products(search_term)
            
            if products:
                best_match = products[0]
                success = await self._add_product_to_cart(best_match)
                
                if success:
                    cart_item = CartItem(
                        product=best_match,
                        quantity=1,
                        total_price=best_match.price
                    )
                    self.cart_items.append(cart_item)
                    added_items.append(cart_item.to_dict())
        
        # Get cart summary
        cart_summary = await self._get_cart_summary()
        
        return {
            "task_type": "general_ordering",
            "search_terms": search_terms,
            "items_added": len(added_items),
            "added_items": added_items,
            "cart_summary": cart_summary.to_dict() if cart_summary else None,
            "platform": self.current_platform
        }
    
    async def _search_for_products(self, search_term: str) -> List[ProductInfo]:
        """Search for products on the current platform."""
        if not self.platform_config:
            return []
        
        try:
            # Find search input
            search_selectors = self.platform_config["search_selectors"]
            search_input = None
            
            for selector in search_selectors:
                try:
                    search_input = await self.element_locator.find_element_by_selector(selector)
                    if search_input:
                        break
                except Exception:
                    continue
            
            if not search_input:
                logger.warning("Could not find search input")
                return []
            
            # Clear and enter search term
            await self.browser_controller.clear_element(search_input)
            await self.browser_controller.type_text(search_input, search_term)
            await self.browser_controller.press_key(search_input, "Enter")
            
            # Wait for search results
            await self.browser_controller.wait_for_page_load()
            
            # Extract product information
            products = await self._extract_product_list()
            
            logger.info(f"Found {len(products)} products for search term: {search_term}")
            return products
            
        except Exception as e:
            logger.error(f"Product search failed: {e}")
            return []
    
    async def _extract_product_list(self) -> List[ProductInfo]:
        """Extract product information from search results."""
        if not self.platform_config:
            return []
        
        products = []
        product_selectors = self.platform_config["product_selectors"]
        
        # Find product elements
        product_elements = []
        for selector in product_selectors:
            try:
                elements = await self.element_locator.find_elements_by_selector(selector)
                if elements:
                    product_elements = elements[:self.max_products_to_scan]
                    break
            except Exception:
                continue
        
        if not product_elements:
            logger.warning("Could not find product elements")
            return products
        
        # Extract information from each product
        for i, element in enumerate(product_elements):
            try:
                product_info = await self._extract_product_info(element, i)
                if product_info:
                    products.append(product_info)
            except Exception as e:
                logger.debug(f"Failed to extract product info from element {i}: {e}")
                continue
        
        return products
    
    async def _extract_product_info(self, element, index: int) -> Optional[ProductInfo]:
        """Extract information from a single product element."""
        try:
            # Generate selector for this element
            element_selector = f"({self.platform_config['product_selectors'][0]})[{index + 1}]"
            
            # Extract product name
            name = await self._extract_product_name(element)
            if not name:
                return None
            
            # Extract price
            price = await self._extract_product_price(element)
            
            # Extract description
            description = await self._extract_product_description(element)
            
            # Check availability
            availability = await self._check_product_availability(element)
            
            # Extract rating if available
            rating = await self._extract_product_rating(element)
            
            return ProductInfo(
                name=name.strip(),
                price=price or "Price not available",
                description=description,
                availability=availability,
                element_selector=element_selector,
                rating=rating
            )
            
        except Exception as e:
            logger.error(f"Failed to extract product info: {e}")
            return None
    
    async def _extract_product_name(self, element) -> Optional[str]:
        """Extract product name from element."""
        # Common selectors for product names
        name_selectors = [
            "h3", "h4", ".product-name", ".item-name", ".title",
            "[data-testid*='name']", "[data-testid*='title']",
            ".name", ".product-title", "a[href*='product']"
        ]
        
        for selector in name_selectors:
            try:
                name_element = await self.element_locator.find_element_within_parent(element, selector)
                if name_element:
                    text = await self.browser_controller.get_element_text(name_element)
                    if text and text.strip():
                        return text.strip()
            except Exception:
                continue
        
        # Fallback: get text from the element itself
        try:
            text = await self.browser_controller.get_element_text(element)
            if text:
                # Extract first meaningful line
                lines = [line.strip() for line in text.split('\n') if line.strip()]
                if lines:
                    return lines[0]
        except Exception:
            pass
        
        return None
    
    async def _extract_product_price(self, element) -> Optional[str]:
        """Extract product price from element."""
        # Common selectors for prices
        price_selectors = [
            ".price", ".cost", "[data-testid*='price']",
            ".amount", ".currency", "span[class*='price']",
            ".dollar", ".money", "[class*='cost']"
        ]
        
        for selector in price_selectors:
            try:
                price_element = await self.element_locator.find_element_within_parent(element, selector)
                if price_element:
                    text = await self.browser_controller.get_element_text(price_element)
                    if text and ('$' in text or '€' in text or '£' in text):
                        return text.strip()
            except Exception:
                continue
        
        # Look for price patterns in element text
        try:
            text = await self.browser_controller.get_element_text(element)
            if text:
                # Look for currency symbols followed by numbers
                price_match = re.search(r'[\$€£]\d+\.?\d*', text)
                if price_match:
                    return price_match.group()
        except Exception:
            pass
        
        return None
    
    async def _extract_product_description(self, element) -> Optional[str]:
        """Extract product description from element."""
        description_selectors = [
            ".description", ".details", ".info",
            "[data-testid*='description']", "p", ".summary"
        ]
        
        for selector in description_selectors:
            try:
                desc_element = await self.element_locator.find_element_within_parent(element, selector)
                if desc_element:
                    text = await self.browser_controller.get_element_text(desc_element)
                    if text and len(text.strip()) > 10:  # Meaningful description
                        return text.strip()
            except Exception:
                continue
        
        return None
    
    async def _check_product_availability(self, element) -> bool:
        """Check if product is available."""
        # Look for unavailability indicators
        unavailable_indicators = [
            "out of stock", "unavailable", "sold out",
            "not available", "temporarily unavailable"
        ]
        
        try:
            text = await self.browser_controller.get_element_text(element)
            if text:
                text_lower = text.lower()
                for indicator in unavailable_indicators:
                    if indicator in text_lower:
                        return False
        except Exception:
            pass
        
        # Check for disabled add to cart buttons
        try:
            add_buttons = await self.element_locator.find_elements_within_parent(
                element, "button[disabled], .disabled, [aria-disabled='true']"
            )
            if add_buttons:
                return False
        except Exception:
            pass
        
        return True  # Default to available
    
    async def _extract_product_rating(self, element) -> Optional[float]:
        """Extract product rating from element."""
        try:
            # Look for star ratings or numeric ratings
            rating_selectors = [
                ".rating", ".stars", "[data-testid*='rating']",
                ".score", "[class*='star']"
            ]
            
            for selector in rating_selectors:
                try:
                    rating_element = await self.element_locator.find_element_within_parent(element, selector)
                    if rating_element:
                        text = await self.browser_controller.get_element_text(rating_element)
                        if text:
                            # Extract numeric rating
                            rating_match = re.search(r'(\d+\.?\d*)', text)
                            if rating_match:
                                return float(rating_match.group(1))
                except Exception:
                    continue
        except Exception:
            pass
        
        return None
    
    async def _add_product_to_cart(self, product: ProductInfo) -> bool:
        """Add a product to the shopping cart."""
        try:
            # Find the product element
            product_element = await self.element_locator.find_element_by_selector(product.element_selector)
            if not product_element:
                logger.warning(f"Could not find product element: {product.name}")
                return False
            
            # Find add to cart button
            add_to_cart_selectors = self.platform_config["add_to_cart_selectors"]
            
            for selector in add_to_cart_selectors:
                try:
                    # Look for button within the product element
                    add_button = await self.element_locator.find_element_within_parent(
                        product_element, selector
                    )
                    
                    if not add_button:
                        # Look for button in the general page
                        add_button = await self.element_locator.find_element_by_selector(selector)
                    
                    if add_button:
                        # Check if button is enabled
                        is_disabled = await self.browser_controller.get_element_attribute(add_button, "disabled")
                        if is_disabled:
                            continue
                        
                        # Click the add to cart button
                        await self.browser_controller.click_element(add_button)
                        
                        # Wait a moment for the action to complete
                        await self.browser_controller.wait_for_page_load(timeout=3)
                        
                        logger.info(f"Successfully added to cart: {product.name}")
                        return True
                        
                except Exception as e:
                    logger.debug(f"Add to cart selector {selector} failed: {e}")
                    continue
            
            logger.warning(f"Could not find add to cart button for: {product.name}")
            return False
            
        except Exception as e:
            logger.error(f"Failed to add product to cart: {e}")
            return False
    
    async def _get_cart_summary(self) -> Optional[OrderSummary]:
        """Get summary of items in the cart."""
        try:
            # Navigate to cart if not already there
            await self._navigate_to_cart()
            
            # Extract cart items (simplified implementation)
            cart_items = []
            
            # This would need platform-specific implementation
            # For now, return the items we've tracked
            for tracked_item in self.cart_items:
                cart_items.append(tracked_item)
            
            if not cart_items:
                return None
            
            # Calculate totals (simplified)
            subtotal = "Calculated at checkout"
            total = "Calculated at checkout"
            
            return OrderSummary(
                items=cart_items,
                subtotal=subtotal,
                tax=None,
                delivery_fee=None,
                total=total,
                estimated_delivery=None
            )
            
        except Exception as e:
            logger.error(f"Failed to get cart summary: {e}")
            return None
    
    async def _navigate_to_cart(self) -> bool:
        """Navigate to the shopping cart."""
        if not self.platform_config:
            return False
        
        cart_selectors = self.platform_config["cart_selectors"]
        
        for selector in cart_selectors:
            try:
                cart_element = await self.element_locator.find_element_by_selector(selector)
                if cart_element:
                    await self.browser_controller.click_element(cart_element)
                    await self.browser_controller.wait_for_page_load()
                    logger.info("Successfully navigated to cart")
                    return True
            except Exception:
                continue
        
        logger.warning("Could not navigate to cart")
        return False
    
    async def _proceed_to_checkout(self) -> bool:
        """Proceed to checkout from cart."""
        if not self.platform_config:
            return False
        
        # Ensure we're on the cart page
        await self._navigate_to_cart()
        
        checkout_selectors = self.platform_config["checkout_selectors"]
        
        for selector in checkout_selectors:
            try:
                checkout_button = await self.element_locator.find_element_by_selector(selector)
                if checkout_button:
                    # Check if button is enabled
                    is_disabled = await self.browser_controller.get_element_attribute(checkout_button, "disabled")
                    if is_disabled:
                        continue
                    
                    await self.browser_controller.click_element(checkout_button)
                    await self.browser_controller.wait_for_page_load()
                    logger.info("Successfully proceeded to checkout")
                    return True
            except Exception:
                continue
        
        logger.warning("Could not proceed to checkout")
        return False
    
    async def _verify_payment_page(self) -> bool:
        """Verify that we've reached the payment page."""
        try:
            current_url = await self.browser_controller.get_current_url()
            page_content = await self.browser_controller.get_page_content()
            
            # Look for payment-related elements
            payment_indicators = [
                "payment", "credit card", "billing", "checkout",
                "place order", "complete purchase", "pay now"
            ]
            
            page_text = page_content.text_content.lower()
            url_lower = current_url.lower()
            
            # Check URL for payment indicators
            for indicator in payment_indicators:
                if indicator in url_lower or indicator in page_text:
                    return True
            
            # Look for payment form elements
            payment_selectors = [
                "input[name*='card']", "input[placeholder*='card']",
                "input[type='tel']", ".payment-form", "#payment"
            ]
            
            for selector in payment_selectors:
                try:
                    element = await self.element_locator.find_element_by_selector(selector)
                    if element:
                        return True
                except Exception:
                    continue
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to verify payment page: {e}")
            return False
    
    def get_cart_items(self) -> List[Dict[str, Any]]:
        """Get current cart items."""
        return [item.to_dict() for item in self.cart_items]
    
    def get_order_history(self) -> List[Dict[str, Any]]:
        """Get order history."""
        return self.order_history.copy()
    
    def get_handler_status(self) -> Dict[str, Any]:
        """Get current handler status."""
        return {
            "handler_type": "ordering",
            "current_platform": self.current_platform,
            "cart_items_count": len(self.cart_items),
            "max_products_to_scan": self.max_products_to_scan,
            "auto_proceed_to_checkout": self.auto_proceed_to_checkout,
            "price_limit": self.price_limit
        }