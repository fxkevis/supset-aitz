"""Alternative action strategies for common failure scenarios."""

import logging
from enum import Enum
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field

from ai_browser_agent.interfaces.base_interfaces import BaseAgent
from ai_browser_agent.models.action import Action, ActionType
from ai_browser_agent.models.task import Task


logger = logging.getLogger(__name__)


class FailureScenario(Enum):
    """Common failure scenarios that require alternative strategies."""
    ELEMENT_NOT_FOUND = "element_not_found"
    ELEMENT_NOT_CLICKABLE = "element_not_clickable"
    FORM_SUBMISSION_FAILED = "form_submission_failed"
    PAGE_LOAD_TIMEOUT = "page_load_timeout"
    AUTHENTICATION_FAILED = "authentication_failed"
    NETWORK_ERROR = "network_error"
    JAVASCRIPT_ERROR = "javascript_error"
    CAPTCHA_ENCOUNTERED = "captcha_encountered"
    POPUP_BLOCKING = "popup_blocking"
    CONTENT_NOT_LOADED = "content_not_loaded"


class StrategyType(Enum):
    """Types of alternative strategies."""
    SELECTOR_VARIATION = "selector_variation"
    INTERACTION_METHOD = "interaction_method"
    TIMING_ADJUSTMENT = "timing_adjustment"
    NAVIGATION_ALTERNATIVE = "navigation_alternative"
    CONTENT_EXTRACTION = "content_extraction"
    AUTHENTICATION_BYPASS = "authentication_bypass"
    ERROR_RECOVERY = "error_recovery"
    FALLBACK_APPROACH = "fallback_approach"


@dataclass
class AlternativeStrategy:
    """Definition of an alternative strategy."""
    strategy_type: StrategyType
    name: str
    description: str
    actions: List[Action]
    success_probability: float
    execution_time_estimate: float
    prerequisites: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StrategyResult:
    """Result of executing an alternative strategy."""
    success: bool
    strategy_used: AlternativeStrategy
    actions_executed: List[Action]
    execution_time: float
    message: str
    fallback_needed: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


class AlternativeStrategyManager(BaseAgent):
    """Manages alternative action strategies for common failure scenarios."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        
        # Configuration
        self.max_strategies_per_scenario = config.get("max_strategies_per_scenario", 3) if config else 3
        self.strategy_timeout = config.get("strategy_timeout", 30) if config else 30
        self.success_threshold = config.get("success_threshold", 0.7) if config else 0.7
        
        # Strategy database
        self.strategies: Dict[FailureScenario, List[AlternativeStrategy]] = {}
        self.strategy_success_rates: Dict[str, float] = {}
        
        # Initialize built-in strategies
        self._initialize_strategies()
    
    def initialize(self) -> None:
        """Initialize the alternative strategy manager."""
        self.is_active = True
        logger.info("Alternative strategy manager initialized")
    
    def shutdown(self) -> None:
        """Shutdown the alternative strategy manager."""
        self.is_active = False
        logger.info("Alternative strategy manager shutdown")
    
    def _initialize_strategies(self) -> None:
        """Initialize built-in alternative strategies."""
        
        # Element not found strategies
        self.strategies[FailureScenario.ELEMENT_NOT_FOUND] = [
            self._create_xpath_fallback_strategy(),
            self._create_text_content_strategy(),
            self._create_partial_attribute_strategy(),
            self._create_parent_element_strategy()
        ]
        
        # Element not clickable strategies
        self.strategies[FailureScenario.ELEMENT_NOT_CLICKABLE] = [
            self._create_javascript_click_strategy(),
            self._create_scroll_and_wait_strategy(),
            self._create_keyboard_navigation_strategy(),
            self._create_force_click_strategy()
        ]
        
        # Form submission failed strategies
        self.strategies[FailureScenario.FORM_SUBMISSION_FAILED] = [
            self._create_enter_key_submission_strategy(),
            self._create_javascript_submit_strategy(),
            self._create_individual_field_strategy(),
            self._create_form_validation_strategy()
        ]
        
        # Page load timeout strategies
        self.strategies[FailureScenario.PAGE_LOAD_TIMEOUT] = [
            self._create_refresh_and_wait_strategy(),
            self._create_partial_load_strategy(),
            self._create_alternative_url_strategy(),
            self._create_cached_content_strategy()
        ]
        
        # Authentication failed strategies
        self.strategies[FailureScenario.AUTHENTICATION_FAILED] = [
            self._create_retry_auth_strategy(),
            self._create_alternative_login_strategy(),
            self._create_session_recovery_strategy(),
            self._create_guest_access_strategy()
        ]
        
        # Network error strategies
        self.strategies[FailureScenario.NETWORK_ERROR] = [
            self._create_retry_with_backoff_strategy(),
            self._create_alternative_endpoint_strategy(),
            self._create_offline_mode_strategy(),
            self._create_cached_fallback_strategy()
        ]
        
        # JavaScript error strategies
        self.strategies[FailureScenario.JAVASCRIPT_ERROR] = [
            self._create_disable_js_strategy(),
            self._create_alternative_interaction_strategy(),
            self._create_dom_manipulation_strategy(),
            self._create_static_fallback_strategy()
        ]
        
        # CAPTCHA encountered strategies
        self.strategies[FailureScenario.CAPTCHA_ENCOUNTERED] = [
            self._create_captcha_detection_strategy(),
            self._create_user_intervention_strategy(),
            self._create_alternative_path_strategy(),
            self._create_session_bypass_strategy()
        ]
        
        # Popup blocking strategies
        self.strategies[FailureScenario.POPUP_BLOCKING] = [
            self._create_popup_detection_strategy(),
            self._create_popup_dismissal_strategy(),
            self._create_popup_interaction_strategy(),
            self._create_popup_avoidance_strategy()
        ]
        
        # Content not loaded strategies
        self.strategies[FailureScenario.CONTENT_NOT_LOADED] = [
            self._create_dynamic_wait_strategy(),
            self._create_scroll_trigger_strategy(),
            self._create_ajax_completion_strategy(),
            self._create_alternative_content_strategy()
        ]
    
    async def get_alternative_strategies(self, scenario: FailureScenario, 
                                       failed_action: Action,
                                       context: Optional[Dict[str, Any]] = None) -> List[AlternativeStrategy]:
        """Get alternative strategies for a failure scenario."""
        if not self.is_active or scenario not in self.strategies:
            return []
        
        available_strategies = self.strategies[scenario].copy()
        
        # Filter strategies based on context
        if context:
            available_strategies = self._filter_strategies_by_context(available_strategies, context)
        
        # Sort by success probability and past performance
        available_strategies.sort(key=lambda s: (
            self.strategy_success_rates.get(s.name, s.success_probability),
            s.success_probability
        ), reverse=True)
        
        # Return top strategies
        return available_strategies[:self.max_strategies_per_scenario]
    
    def _filter_strategies_by_context(self, strategies: List[AlternativeStrategy], 
                                    context: Dict[str, Any]) -> List[AlternativeStrategy]:
        """Filter strategies based on current context."""
        filtered = []
        
        for strategy in strategies:
            # Check prerequisites
            if strategy.prerequisites:
                if not all(prereq in context for prereq in strategy.prerequisites):
                    continue
            
            # Check limitations
            if strategy.limitations:
                if any(limitation in context.get("limitations", []) for limitation in strategy.limitations):
                    continue
            
            # Context-specific filtering
            page_url = context.get("page_url", "")
            if "javascript_disabled" in context and strategy.strategy_type == StrategyType.INTERACTION_METHOD:
                if "javascript" in strategy.name.lower():
                    continue
            
            filtered.append(strategy)
        
        return filtered
    
    # Strategy creation methods
    def _create_xpath_fallback_strategy(self) -> AlternativeStrategy:
        """Create XPath fallback strategy for element not found."""
        return AlternativeStrategy(
            strategy_type=StrategyType.SELECTOR_VARIATION,
            name="xpath_fallback",
            description="Use XPath selectors as fallback for CSS selectors",
            actions=[
                Action(
                    id="xpath_fallback_action",
                    type=ActionType.EXTRACT,
                    target="//body",
                    description="Convert CSS selector to XPath equivalent"
                )
            ],
            success_probability=0.7,
            execution_time_estimate=2.0,
            metadata={"selector_type": "xpath"}
        )
    
    def _create_text_content_strategy(self) -> AlternativeStrategy:
        """Create text content-based selection strategy."""
        return AlternativeStrategy(
            strategy_type=StrategyType.SELECTOR_VARIATION,
            name="text_content_selection",
            description="Find elements by their text content",
            actions=[
                Action(
                    id="text_content_action",
                    type=ActionType.EXTRACT,
                    target="*",
                    parameters={"method": "text_content"},
                    description="Find element by text content"
                )
            ],
            success_probability=0.6,
            execution_time_estimate=3.0,
            metadata={"selector_type": "text_content"}
        )
    
    def _create_partial_attribute_strategy(self) -> AlternativeStrategy:
        """Create partial attribute matching strategy."""
        return AlternativeStrategy(
            strategy_type=StrategyType.SELECTOR_VARIATION,
            name="partial_attribute_matching",
            description="Use partial attribute matching for element selection",
            actions=[
                Action(
                    id="partial_attr_action",
                    type=ActionType.EXTRACT,
                    target="*",
                    parameters={"method": "partial_attribute"},
                    description="Find element by partial attribute match"
                )
            ],
            success_probability=0.8,
            execution_time_estimate=2.5,
            metadata={"selector_type": "partial_attribute"}
        )
    
    def _create_parent_element_strategy(self) -> AlternativeStrategy:
        """Create parent element navigation strategy."""
        return AlternativeStrategy(
            strategy_type=StrategyType.SELECTOR_VARIATION,
            name="parent_element_navigation",
            description="Navigate through parent elements to find target",
            actions=[
                Action(
                    id="parent_nav_action",
                    type=ActionType.EXTRACT,
                    target="*",
                    parameters={"method": "parent_navigation"},
                    description="Navigate through parent elements"
                )
            ],
            success_probability=0.5,
            execution_time_estimate=4.0,
            metadata={"selector_type": "parent_navigation"}
        )
    
    def _create_javascript_click_strategy(self) -> AlternativeStrategy:
        """Create JavaScript click strategy."""
        return AlternativeStrategy(
            strategy_type=StrategyType.INTERACTION_METHOD,
            name="javascript_click",
            description="Use JavaScript to trigger click events",
            actions=[
                Action(
                    id="js_click_action",
                    type=ActionType.CLICK,
                    target="element",
                    parameters={"method": "javascript"},
                    description="Click element using JavaScript"
                )
            ],
            success_probability=0.9,
            execution_time_estimate=1.0,
            prerequisites=["javascript_enabled"],
            metadata={"interaction_type": "javascript"}
        )
    
    def _create_scroll_and_wait_strategy(self) -> AlternativeStrategy:
        """Create scroll and wait strategy."""
        return AlternativeStrategy(
            strategy_type=StrategyType.TIMING_ADJUSTMENT,
            name="scroll_and_wait",
            description="Scroll element into view and wait before interaction",
            actions=[
                Action(
                    id="scroll_action",
                    type=ActionType.SCROLL,
                    target="element",
                    description="Scroll element into view"
                ),
                Action(
                    id="wait_action",
                    type=ActionType.WAIT,
                    target="",
                    parameters={"duration": 2},
                    description="Wait for element to become interactive"
                ),
                Action(
                    id="click_action",
                    type=ActionType.CLICK,
                    target="element",
                    description="Click element after scroll and wait"
                )
            ],
            success_probability=0.8,
            execution_time_estimate=5.0,
            metadata={"interaction_type": "scroll_wait_click"}
        )
    
    def _create_keyboard_navigation_strategy(self) -> AlternativeStrategy:
        """Create keyboard navigation strategy."""
        return AlternativeStrategy(
            strategy_type=StrategyType.INTERACTION_METHOD,
            name="keyboard_navigation",
            description="Use keyboard navigation to interact with elements",
            actions=[
                Action(
                    id="tab_navigation",
                    type=ActionType.TYPE,
                    target="body",
                    parameters={"text": "\t"},
                    description="Navigate using Tab key"
                ),
                Action(
                    id="enter_activation",
                    type=ActionType.TYPE,
                    target="element",
                    parameters={"text": "\n"},
                    description="Activate element using Enter key"
                )
            ],
            success_probability=0.6,
            execution_time_estimate=3.0,
            metadata={"interaction_type": "keyboard"}
        )
    
    def _create_force_click_strategy(self) -> AlternativeStrategy:
        """Create force click strategy."""
        return AlternativeStrategy(
            strategy_type=StrategyType.INTERACTION_METHOD,
            name="force_click",
            description="Force click using action chains and coordinates",
            actions=[
                Action(
                    id="force_click_action",
                    type=ActionType.CLICK,
                    target="element",
                    parameters={"method": "force", "use_coordinates": True},
                    description="Force click using coordinates"
                )
            ],
            success_probability=0.7,
            execution_time_estimate=2.0,
            metadata={"interaction_type": "force_click"}
        )
    
    def _create_enter_key_submission_strategy(self) -> AlternativeStrategy:
        """Create Enter key form submission strategy."""
        return AlternativeStrategy(
            strategy_type=StrategyType.INTERACTION_METHOD,
            name="enter_key_submission",
            description="Submit form using Enter key instead of submit button",
            actions=[
                Action(
                    id="enter_submit_action",
                    type=ActionType.TYPE,
                    target="form input",
                    parameters={"text": "\n"},
                    description="Submit form using Enter key"
                )
            ],
            success_probability=0.8,
            execution_time_estimate=1.0,
            metadata={"submission_type": "enter_key"}
        )
    
    def _create_javascript_submit_strategy(self) -> AlternativeStrategy:
        """Create JavaScript form submission strategy."""
        return AlternativeStrategy(
            strategy_type=StrategyType.INTERACTION_METHOD,
            name="javascript_submit",
            description="Submit form using JavaScript",
            actions=[
                Action(
                    id="js_submit_action",
                    type=ActionType.SUBMIT,
                    target="form",
                    parameters={"method": "javascript"},
                    description="Submit form using JavaScript"
                )
            ],
            success_probability=0.9,
            execution_time_estimate=1.0,
            prerequisites=["javascript_enabled"],
            metadata={"submission_type": "javascript"}
        )
    
    def _create_individual_field_strategy(self) -> AlternativeStrategy:
        """Create individual field filling strategy."""
        return AlternativeStrategy(
            strategy_type=StrategyType.FALLBACK_APPROACH,
            name="individual_field_filling",
            description="Fill form fields individually with validation",
            actions=[
                Action(
                    id="field_by_field_action",
                    type=ActionType.TYPE,
                    target="form",
                    parameters={"method": "individual_fields"},
                    description="Fill each form field individually"
                )
            ],
            success_probability=0.7,
            execution_time_estimate=10.0,
            metadata={"submission_type": "individual_fields"}
        )
    
    def _create_form_validation_strategy(self) -> AlternativeStrategy:
        """Create form validation strategy."""
        return AlternativeStrategy(
            strategy_type=StrategyType.ERROR_RECOVERY,
            name="form_validation_check",
            description="Check and fix form validation errors",
            actions=[
                Action(
                    id="validation_check_action",
                    type=ActionType.EXTRACT,
                    target="form",
                    parameters={"method": "validation_errors"},
                    description="Check for form validation errors"
                )
            ],
            success_probability=0.6,
            execution_time_estimate=5.0,
            metadata={"submission_type": "validation_check"}
        )
    
    def _create_refresh_and_wait_strategy(self) -> AlternativeStrategy:
        """Create page refresh and wait strategy."""
        return AlternativeStrategy(
            strategy_type=StrategyType.NAVIGATION_ALTERNATIVE,
            name="refresh_and_wait",
            description="Refresh page and wait for complete loading",
            actions=[
                Action(
                    id="refresh_action",
                    type=ActionType.REFRESH,
                    target="",
                    description="Refresh current page"
                ),
                Action(
                    id="extended_wait_action",
                    type=ActionType.WAIT,
                    target="",
                    parameters={"duration": 10},
                    description="Wait for page to load completely"
                )
            ],
            success_probability=0.8,
            execution_time_estimate=15.0,
            metadata={"navigation_type": "refresh_wait"}
        )
    
    def _create_partial_load_strategy(self) -> AlternativeStrategy:
        """Create partial page load strategy."""
        return AlternativeStrategy(
            strategy_type=StrategyType.CONTENT_EXTRACTION,
            name="partial_load_extraction",
            description="Extract content from partially loaded page",
            actions=[
                Action(
                    id="partial_extract_action",
                    type=ActionType.EXTRACT,
                    target="body",
                    parameters={"method": "partial_content"},
                    description="Extract available content from partial load"
                )
            ],
            success_probability=0.5,
            execution_time_estimate=3.0,
            metadata={"navigation_type": "partial_load"}
        )
    
    def _create_alternative_url_strategy(self) -> AlternativeStrategy:
        """Create alternative URL strategy."""
        return AlternativeStrategy(
            strategy_type=StrategyType.NAVIGATION_ALTERNATIVE,
            name="alternative_url",
            description="Try alternative URLs or endpoints",
            actions=[
                Action(
                    id="alt_url_action",
                    type=ActionType.NAVIGATE,
                    target="alternative_url",
                    parameters={"method": "alternative_endpoint"},
                    description="Navigate to alternative URL"
                )
            ],
            success_probability=0.4,
            execution_time_estimate=5.0,
            metadata={"navigation_type": "alternative_url"}
        )
    
    def _create_cached_content_strategy(self) -> AlternativeStrategy:
        """Create cached content strategy."""
        return AlternativeStrategy(
            strategy_type=StrategyType.FALLBACK_APPROACH,
            name="cached_content",
            description="Use cached content when available",
            actions=[
                Action(
                    id="cache_access_action",
                    type=ActionType.EXTRACT,
                    target="cache",
                    parameters={"method": "cached_content"},
                    description="Access cached page content"
                )
            ],
            success_probability=0.3,
            execution_time_estimate=1.0,
            prerequisites=["cache_available"],
            metadata={"navigation_type": "cached_content"}
        )
    
    # Additional strategy creation methods would continue here...
    # For brevity, I'll create placeholder methods for the remaining strategies
    
    def _create_retry_auth_strategy(self) -> AlternativeStrategy:
        """Create retry authentication strategy."""
        return AlternativeStrategy(
            strategy_type=StrategyType.AUTHENTICATION_BYPASS,
            name="retry_authentication",
            description="Retry authentication with different credentials or methods",
            actions=[],
            success_probability=0.6,
            execution_time_estimate=10.0
        )
    
    def _create_alternative_login_strategy(self) -> AlternativeStrategy:
        """Create alternative login method strategy."""
        return AlternativeStrategy(
            strategy_type=StrategyType.AUTHENTICATION_BYPASS,
            name="alternative_login",
            description="Try alternative login methods (OAuth, SSO, etc.)",
            actions=[],
            success_probability=0.4,
            execution_time_estimate=15.0
        )
    
    def _create_session_recovery_strategy(self) -> AlternativeStrategy:
        """Create session recovery strategy."""
        return AlternativeStrategy(
            strategy_type=StrategyType.AUTHENTICATION_BYPASS,
            name="session_recovery",
            description="Recover existing session or use stored credentials",
            actions=[],
            success_probability=0.7,
            execution_time_estimate=5.0
        )
    
    def _create_guest_access_strategy(self) -> AlternativeStrategy:
        """Create guest access strategy."""
        return AlternativeStrategy(
            strategy_type=StrategyType.AUTHENTICATION_BYPASS,
            name="guest_access",
            description="Continue with guest access if available",
            actions=[],
            success_probability=0.3,
            execution_time_estimate=2.0
        )
    
    def _create_retry_with_backoff_strategy(self) -> AlternativeStrategy:
        """Create retry with backoff strategy."""
        return AlternativeStrategy(
            strategy_type=StrategyType.ERROR_RECOVERY,
            name="retry_with_backoff",
            description="Retry with exponential backoff",
            actions=[],
            success_probability=0.8,
            execution_time_estimate=30.0
        )
    
    def _create_alternative_endpoint_strategy(self) -> AlternativeStrategy:
        """Create alternative endpoint strategy."""
        return AlternativeStrategy(
            strategy_type=StrategyType.NAVIGATION_ALTERNATIVE,
            name="alternative_endpoint",
            description="Try alternative API endpoints or mirrors",
            actions=[],
            success_probability=0.5,
            execution_time_estimate=10.0
        )
    
    def _create_offline_mode_strategy(self) -> AlternativeStrategy:
        """Create offline mode strategy."""
        return AlternativeStrategy(
            strategy_type=StrategyType.FALLBACK_APPROACH,
            name="offline_mode",
            description="Switch to offline mode with cached data",
            actions=[],
            success_probability=0.2,
            execution_time_estimate=2.0
        )
    
    def _create_cached_fallback_strategy(self) -> AlternativeStrategy:
        """Create cached fallback strategy."""
        return AlternativeStrategy(
            strategy_type=StrategyType.FALLBACK_APPROACH,
            name="cached_fallback",
            description="Use cached data as fallback",
            actions=[],
            success_probability=0.4,
            execution_time_estimate=1.0
        )
    
    # Placeholder methods for remaining strategies
    def _create_disable_js_strategy(self) -> AlternativeStrategy:
        return AlternativeStrategy(StrategyType.FALLBACK_APPROACH, "disable_js", "Disable JavaScript", [], 0.6, 5.0)
    
    def _create_alternative_interaction_strategy(self) -> AlternativeStrategy:
        return AlternativeStrategy(StrategyType.INTERACTION_METHOD, "alt_interaction", "Alternative interaction", [], 0.7, 3.0)
    
    def _create_dom_manipulation_strategy(self) -> AlternativeStrategy:
        return AlternativeStrategy(StrategyType.INTERACTION_METHOD, "dom_manipulation", "DOM manipulation", [], 0.8, 2.0)
    
    def _create_static_fallback_strategy(self) -> AlternativeStrategy:
        return AlternativeStrategy(StrategyType.FALLBACK_APPROACH, "static_fallback", "Static fallback", [], 0.5, 1.0)
    
    def _create_captcha_detection_strategy(self) -> AlternativeStrategy:
        return AlternativeStrategy(StrategyType.ERROR_RECOVERY, "captcha_detection", "CAPTCHA detection", [], 0.9, 2.0)
    
    def _create_user_intervention_strategy(self) -> AlternativeStrategy:
        return AlternativeStrategy(StrategyType.FALLBACK_APPROACH, "user_intervention", "User intervention", [], 1.0, 60.0)
    
    def _create_alternative_path_strategy(self) -> AlternativeStrategy:
        return AlternativeStrategy(StrategyType.NAVIGATION_ALTERNATIVE, "alternative_path", "Alternative path", [], 0.4, 10.0)
    
    def _create_session_bypass_strategy(self) -> AlternativeStrategy:
        return AlternativeStrategy(StrategyType.AUTHENTICATION_BYPASS, "session_bypass", "Session bypass", [], 0.3, 5.0)
    
    def _create_popup_detection_strategy(self) -> AlternativeStrategy:
        return AlternativeStrategy(StrategyType.ERROR_RECOVERY, "popup_detection", "Popup detection", [], 0.9, 1.0)
    
    def _create_popup_dismissal_strategy(self) -> AlternativeStrategy:
        return AlternativeStrategy(StrategyType.ERROR_RECOVERY, "popup_dismissal", "Popup dismissal", [], 0.8, 2.0)
    
    def _create_popup_interaction_strategy(self) -> AlternativeStrategy:
        return AlternativeStrategy(StrategyType.INTERACTION_METHOD, "popup_interaction", "Popup interaction", [], 0.7, 3.0)
    
    def _create_popup_avoidance_strategy(self) -> AlternativeStrategy:
        return AlternativeStrategy(StrategyType.NAVIGATION_ALTERNATIVE, "popup_avoidance", "Popup avoidance", [], 0.6, 1.0)
    
    def _create_dynamic_wait_strategy(self) -> AlternativeStrategy:
        return AlternativeStrategy(StrategyType.TIMING_ADJUSTMENT, "dynamic_wait", "Dynamic wait", [], 0.8, 10.0)
    
    def _create_scroll_trigger_strategy(self) -> AlternativeStrategy:
        return AlternativeStrategy(StrategyType.INTERACTION_METHOD, "scroll_trigger", "Scroll trigger", [], 0.7, 5.0)
    
    def _create_ajax_completion_strategy(self) -> AlternativeStrategy:
        return AlternativeStrategy(StrategyType.TIMING_ADJUSTMENT, "ajax_completion", "AJAX completion", [], 0.6, 8.0)
    
    def _create_alternative_content_strategy(self) -> AlternativeStrategy:
        return AlternativeStrategy(StrategyType.CONTENT_EXTRACTION, "alternative_content", "Alternative content", [], 0.4, 3.0)
    
    def update_strategy_success_rate(self, strategy_name: str, success: bool) -> None:
        """Update success rate for a strategy based on execution results."""
        if strategy_name not in self.strategy_success_rates:
            self.strategy_success_rates[strategy_name] = 0.5
        
        current_rate = self.strategy_success_rates[strategy_name]
        new_rate = current_rate * 0.9 + (1.0 if success else 0.0) * 0.1
        self.strategy_success_rates[strategy_name] = new_rate
        
        logger.info(f"Updated success rate for {strategy_name}: {new_rate:.2f}")
    
    def get_strategy_statistics(self) -> Dict[str, Any]:
        """Get statistics about strategy usage and success rates."""
        return {
            "total_strategies": sum(len(strategies) for strategies in self.strategies.values()),
            "scenarios_covered": len(self.strategies),
            "success_rates": self.strategy_success_rates.copy(),
            "configuration": {
                "max_strategies_per_scenario": self.max_strategies_per_scenario,
                "strategy_timeout": self.strategy_timeout,
                "success_threshold": self.success_threshold
            }
        }