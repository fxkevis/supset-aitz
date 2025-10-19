# AI Browser Agent API Reference

## Table of Contents
- [Core Components](#core-components)
- [AI Agent Core](#ai-agent-core)
- [Browser Controller](#browser-controller)
- [Context Manager](#context-manager)
- [Security Layer](#security-layer)
- [User Interface](#user-interface)
- [Data Models](#data-models)
- [Configuration](#configuration)
- [Error Handling](#error-handling)

---

## Core Components

### AIAgent

The main orchestrator class that coordinates all components.

```python
from ai_browser_agent.core.ai_agent import AIAgent

class AIAgent:
    def __init__(self, config: Dict[str, Any], user_interface: UserInterface):
        """Initialize the AI agent with configuration and UI.
        
        Args:
            config: Application configuration dictionary
            user_interface: User interface implementation
        """
    
    def initialize(self) -> None:
        """Initialize all agent components and dependencies."""
    
    def execute_task(self, task_description: str) -> str:
        """Execute a task described in natural language.
        
        Args:
            task_description: Natural language description of the task
            
        Returns:
            Task execution result summary
            
        Raises:
            TaskExecutionError: If task execution fails
            SecurityError: If task requires user confirmation
        """
    
    def shutdown(self) -> None:
        """Clean up resources and shut down the agent."""
```

#### Usage Example
```python
from ai_browser_agent.core.ai_agent import AIAgent
from ai_browser_agent.ui.terminal_interface import TerminalInterface

# Initialize components
ui = TerminalInterface()
config = {"debug": False, "app_config": app_config}

# Create and initialize agent
agent = AIAgent(config=config, user_interface=ui)
agent.initialize()

# Execute task
result = agent.execute_task("Check my Gmail inbox and delete spam emails")
print(result)

# Clean up
agent.shutdown()
```

---

## AI Agent Core

### TaskPlanner

Converts natural language tasks into executable plans.

```python
from ai_browser_agent.core.task_planner import TaskPlanner

class TaskPlanner:
    def __init__(self, ai_model: AIModelInterface):
        """Initialize task planner with AI model."""
    
    def create_plan(self, task_description: str, context: Dict[str, Any] = None) -> ExecutionPlan:
        """Create execution plan from task description.
        
        Args:
            task_description: Natural language task description
            context: Optional context information
            
        Returns:
            ExecutionPlan with steps and metadata
        """
    
    def update_plan(self, plan: ExecutionPlan, current_state: Dict[str, Any]) -> ExecutionPlan:
        """Update execution plan based on current state.
        
        Args:
            plan: Current execution plan
            current_state: Current browser/task state
            
        Returns:
            Updated execution plan
        """
```

### DecisionEngine

Makes autonomous decisions based on web content and task context.

```python
from ai_browser_agent.core.decision_engine import DecisionEngine

class DecisionEngine:
    def __init__(self, ai_model: AIModelInterface):
        """Initialize decision engine with AI model."""
    
    def analyze_page(self, page_content: PageContent, task_context: str) -> List[Action]:
        """Analyze page content and determine next actions.
        
        Args:
            page_content: Current page content and elements
            task_context: Current task context and objectives
            
        Returns:
            List of recommended actions with confidence scores
        """
    
    def select_best_action(self, actions: List[Action]) -> Action:
        """Select the best action from a list of candidates.
        
        Args:
            actions: List of possible actions
            
        Returns:
            Selected action with highest confidence
        """
```

### TaskManager

Orchestrates task execution and manages task state.

```python
from ai_browser_agent.managers.task_manager import TaskManager

class TaskManager:
    def __init__(self, browser_controller: BrowserController, 
                 decision_engine: DecisionEngine):
        """Initialize task manager with dependencies."""
    
    def execute_plan(self, plan: ExecutionPlan) -> TaskResult:
        """Execute a complete task plan.
        
        Args:
            plan: Execution plan to execute
            
        Returns:
            Task execution result
        """
    
    def execute_step(self, step: TaskStep) -> StepResult:
        """Execute a single task step.
        
        Args:
            step: Task step to execute
            
        Returns:
            Step execution result
        """
```

---

## Browser Controller

### BrowserController

Main interface for browser automation.

```python
from ai_browser_agent.controllers.browser_controller import BrowserController

class BrowserController:
    def __init__(self, config: BrowserConfig):
        """Initialize browser controller with configuration."""
    
    def start_browser(self) -> None:
        """Start browser instance with configured settings."""
    
    def navigate_to(self, url: str) -> None:
        """Navigate to specified URL.
        
        Args:
            url: Target URL to navigate to
            
        Raises:
            NavigationError: If navigation fails
        """
    
    def find_element(self, selector: ElementSelector) -> WebElement:
        """Find web element using various selector strategies.
        
        Args:
            selector: Element selector with multiple strategies
            
        Returns:
            Found web element
            
        Raises:
            ElementNotFoundError: If element cannot be found
        """
    
    def click_element(self, element: WebElement) -> None:
        """Click on web element.
        
        Args:
            element: Web element to click
            
        Raises:
            InteractionError: If click fails
        """
    
    def type_text(self, element: WebElement, text: str, clear_first: bool = True) -> None:
        """Type text into web element.
        
        Args:
            element: Target web element
            text: Text to type
            clear_first: Whether to clear existing text first
        """
    
    def get_page_content(self) -> PageContent:
        """Extract current page content and metadata.
        
        Returns:
            PageContent with text, elements, and metadata
        """
    
    def take_screenshot(self, filename: str = None) -> str:
        """Take screenshot of current page.
        
        Args:
            filename: Optional filename for screenshot
            
        Returns:
            Path to saved screenshot file
        """
    
    def close_browser(self) -> None:
        """Close browser and clean up resources."""
```

### ElementLocator

Advanced element finding with multiple strategies.

```python
from ai_browser_agent.controllers.element_locator import ElementLocator

class ElementLocator:
    def __init__(self, driver: WebDriver):
        """Initialize element locator with WebDriver instance."""
    
    def find_by_text(self, text: str, tag: str = None) -> List[WebElement]:
        """Find elements containing specific text.
        
        Args:
            text: Text to search for
            tag: Optional tag name to filter by
            
        Returns:
            List of matching elements
        """
    
    def find_by_attributes(self, attributes: Dict[str, str]) -> List[WebElement]:
        """Find elements by multiple attributes.
        
        Args:
            attributes: Dictionary of attribute name-value pairs
            
        Returns:
            List of matching elements
        """
    
    def find_interactive_elements(self) -> List[WebElement]:
        """Find all interactive elements on the page.
        
        Returns:
            List of clickable/interactive elements
        """
```

### PageAnalyzer

Analyzes and extracts structured data from web pages.

```python
from ai_browser_agent.controllers.page_analyzer import PageAnalyzer

class PageAnalyzer:
    def analyze_page_structure(self, driver: WebDriver) -> Dict[str, Any]:
        """Analyze page structure and identify key sections.
        
        Args:
            driver: WebDriver instance
            
        Returns:
            Dictionary with page structure analysis
        """
    
    def extract_forms(self, driver: WebDriver) -> List[Dict[str, Any]]:
        """Extract all forms and their fields from the page.
        
        Args:
            driver: WebDriver instance
            
        Returns:
            List of form dictionaries with field information
        """
    
    def extract_links(self, driver: WebDriver) -> List[Dict[str, str]]:
        """Extract all links from the page.
        
        Args:
            driver: WebDriver instance
            
        Returns:
            List of link dictionaries with text and href
        """
```

---

## Context Manager

### ContextManager

Manages AI context and token optimization.

```python
from ai_browser_agent.managers.context_manager import ContextManager

class ContextManager:
    def __init__(self, token_optimizer: TokenOptimizer, 
                 content_extractor: ContentExtractor):
        """Initialize context manager with dependencies."""
    
    def prepare_context(self, page_content: PageContent, 
                       task_context: str, 
                       max_tokens: int) -> str:
        """Prepare optimized context for AI model.
        
        Args:
            page_content: Current page content
            task_context: Task description and context
            max_tokens: Maximum token limit
            
        Returns:
            Optimized context string
        """
    
    def extract_relevant_content(self, page_content: PageContent, 
                               task_keywords: List[str]) -> str:
        """Extract content relevant to task keywords.
        
        Args:
            page_content: Full page content
            task_keywords: Keywords related to current task
            
        Returns:
            Filtered relevant content
        """
```

### TokenOptimizer

Optimizes content to fit within AI model token limits.

```python
from ai_browser_agent.managers.token_optimizer import TokenOptimizer

class TokenOptimizer:
    def optimize_content(self, content: str, max_tokens: int, 
                        priority_keywords: List[str] = None) -> str:
        """Optimize content to fit within token limit.
        
        Args:
            content: Original content to optimize
            max_tokens: Maximum allowed tokens
            priority_keywords: Keywords to prioritize during optimization
            
        Returns:
            Optimized content within token limit
        """
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for given text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Estimated token count
        """
```

### ContentExtractor

Extracts and filters relevant content from web pages.

```python
from ai_browser_agent.managers.content_extractor import ContentExtractor

class ContentExtractor:
    def extract_text_content(self, html: str) -> str:
        """Extract clean text content from HTML.
        
        Args:
            html: Raw HTML content
            
        Returns:
            Clean text content
        """
    
    def extract_structured_data(self, html: str) -> Dict[str, Any]:
        """Extract structured data (JSON-LD, microdata, etc.).
        
        Args:
            html: Raw HTML content
            
        Returns:
            Dictionary with structured data
        """
    
    def filter_by_relevance(self, content: str, 
                           keywords: List[str]) -> str:
        """Filter content by relevance to keywords.
        
        Args:
            content: Original content
            keywords: Relevance keywords
            
        Returns:
            Filtered relevant content
        """
```

---

## Security Layer

### SecurityLayer

Main security validation and confirmation system.

```python
from ai_browser_agent.security.security_layer import SecurityLayer

class SecurityLayer:
    def __init__(self, config: SecurityConfig, 
                 user_interface: UserInterface):
        """Initialize security layer with configuration."""
    
    def validate_action(self, action: Action, context: Dict[str, Any]) -> SecurityResult:
        """Validate action for security risks.
        
        Args:
            action: Action to validate
            context: Current context and page information
            
        Returns:
            SecurityResult with risk assessment
        """
    
    def request_user_confirmation(self, action: Action, 
                                 risk_level: str) -> bool:
        """Request user confirmation for risky actions.
        
        Args:
            action: Action requiring confirmation
            risk_level: Risk level (LOW, MEDIUM, HIGH, CRITICAL)
            
        Returns:
            True if user confirms, False otherwise
        """
```

### ActionValidator

Validates actions for potential security risks.

```python
from ai_browser_agent.security.action_validator import ActionValidator

class ActionValidator:
    def __init__(self, config: SecurityConfig):
        """Initialize action validator with security configuration."""
    
    def is_destructive_action(self, action: Action) -> bool:
        """Check if action is potentially destructive.
        
        Args:
            action: Action to check
            
        Returns:
            True if action is destructive
        """
    
    def assess_risk_level(self, action: Action, 
                         context: Dict[str, Any]) -> str:
        """Assess risk level of action.
        
        Args:
            action: Action to assess
            context: Current context
            
        Returns:
            Risk level string (LOW, MEDIUM, HIGH, CRITICAL)
        """
    
    def check_sensitive_domain(self, url: str) -> bool:
        """Check if URL is in sensitive domains list.
        
        Args:
            url: URL to check
            
        Returns:
            True if domain is sensitive
        """
```

### AuditLogger

Logs security events and user confirmations.

```python
from ai_browser_agent.security.audit_logger import AuditLogger

class AuditLogger:
    def __init__(self, log_file: str):
        """Initialize audit logger with log file path."""
    
    def log_security_event(self, event_type: str, 
                          action: Action, 
                          result: str, 
                          user_response: str = None) -> None:
        """Log security-related event.
        
        Args:
            event_type: Type of security event
            action: Action that triggered the event
            result: Event result
            user_response: User's response if applicable
        """
    
    def log_user_confirmation(self, action: Action, 
                             confirmed: bool, 
                             timestamp: datetime) -> None:
        """Log user confirmation event.
        
        Args:
            action: Action that required confirmation
            confirmed: Whether user confirmed
            timestamp: When confirmation occurred
        """
```

---

## User Interface

### TerminalInterface

Command-line interface implementation.

```python
from ai_browser_agent.ui.terminal_interface import TerminalInterface

class TerminalInterface:
    def start_interface(self) -> None:
        """Start the terminal interface."""
    
    def stop_interface(self) -> None:
        """Stop the terminal interface and clean up."""
    
    def display_message(self, message: Dict[str, Any]) -> None:
        """Display message to user.
        
        Args:
            message: Message dictionary with content and type
        """
    
    def get_user_input(self, prompt: str) -> str:
        """Get input from user.
        
        Args:
            prompt: Prompt to display to user
            
        Returns:
            User's input string
        """
    
    def display_confirmation_prompt(self, action: Action, 
                                   risk_level: str) -> bool:
        """Display security confirmation prompt.
        
        Args:
            action: Action requiring confirmation
            risk_level: Risk level of the action
            
        Returns:
            True if user confirms, False otherwise
        """
```

### StatusReporter

Real-time status updates and progress reporting.

```python
from ai_browser_agent.ui.status_reporter import StatusReporter

class StatusReporter:
    def report_task_started(self, task_description: str) -> None:
        """Report that a task has started.
        
        Args:
            task_description: Description of the started task
        """
    
    def report_step_progress(self, step: str, progress: float) -> None:
        """Report progress on current step.
        
        Args:
            step: Description of current step
            progress: Progress percentage (0.0 to 1.0)
        """
    
    def report_task_completed(self, result: str) -> None:
        """Report task completion.
        
        Args:
            result: Task completion result
        """
    
    def report_error(self, error: Exception, context: str) -> None:
        """Report error occurrence.
        
        Args:
            error: Exception that occurred
            context: Context where error occurred
        """
```

---

## Data Models

### Task

Represents a user task and its execution state.

```python
from ai_browser_agent.models.task import Task, TaskStatus

@dataclass
class Task:
    id: str
    description: str
    status: TaskStatus
    created_at: datetime
    updated_at: datetime
    steps: List[TaskStep]
    context: Dict[str, Any]
    result: Optional[str] = None
    error: Optional[str] = None
    
    def add_step(self, step: TaskStep) -> None:
        """Add a step to the task."""
    
    def update_status(self, status: TaskStatus) -> None:
        """Update task status and timestamp."""
    
    def get_current_step(self) -> Optional[TaskStep]:
        """Get the currently executing step."""
```

### Action

Represents a browser action to be executed.

```python
from ai_browser_agent.models.action import Action, ActionType

@dataclass
class Action:
    type: ActionType
    target: str
    parameters: Dict[str, Any]
    confidence: float
    is_destructive: bool = False
    requires_confirmation: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert action to dictionary representation."""
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Action':
        """Create action from dictionary representation."""
```

### PageContent

Represents extracted web page content and metadata.

```python
from ai_browser_agent.models.page_content import PageContent

@dataclass
class PageContent:
    url: str
    title: str
    text_content: str
    html_content: str
    elements: List[Dict[str, Any]]
    forms: List[Dict[str, Any]]
    links: List[Dict[str, str]]
    metadata: Dict[str, Any]
    screenshot_path: Optional[str] = None
    
    def get_interactive_elements(self) -> List[Dict[str, Any]]:
        """Get all interactive elements from the page."""
    
    def find_elements_by_text(self, text: str) -> List[Dict[str, Any]]:
        """Find elements containing specific text."""
```

---

## Configuration

### AppConfig

Main application configuration.

```python
from ai_browser_agent.models.config import AppConfig

@dataclass
class AppConfig:
    browser: BrowserConfig
    security: SecurityConfig
    ai_model: AIModelConfig
    debug_mode: bool = False
    log_file: str = "logs/app.log"
    data_directory: str = "data"
    temp_directory: str = "temp"
    
    @classmethod
    def from_file(cls, config_file: str) -> 'AppConfig':
        """Load configuration from JSON file."""
    
    def to_file(self, config_file: str) -> None:
        """Save configuration to JSON file."""
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of errors."""
```

### BrowserConfig

Browser-specific configuration.

```python
from ai_browser_agent.models.config import BrowserConfig

@dataclass
class BrowserConfig:
    headless: bool = False
    window_size: Tuple[int, int] = (1920, 1080)
    timeout: int = 30
    browser_type: str = "chrome"
    profile_path: Optional[str] = None
    download_directory: Optional[str] = None
    disable_images: bool = False
    disable_javascript: bool = False
    user_agent: Optional[str] = None
```

### SecurityConfig

Security and safety configuration.

```python
from ai_browser_agent.models.config import SecurityConfig

@dataclass
class SecurityConfig:
    require_confirmation_for_payments: bool = True
    require_confirmation_for_deletions: bool = True
    require_confirmation_for_modifications: bool = True
    require_confirmation_for_submissions: bool = False
    sensitive_domains: List[str] = field(default_factory=list)
    destructive_patterns: List[str] = field(default_factory=list)
    max_task_duration: int = 3600
    max_retry_attempts: int = 3
    audit_log_enabled: bool = True
    audit_log_file: str = "logs/audit.log"
```

---

## Error Handling

### Custom Exceptions

```python
from ai_browser_agent.core.error_handler import (
    AIBrowserAgentError,
    TaskExecutionError,
    BrowserError,
    SecurityError,
    ConfigurationError
)

class AIBrowserAgentError(Exception):
    """Base exception for AI Browser Agent."""
    pass

class TaskExecutionError(AIBrowserAgentError):
    """Raised when task execution fails."""
    def __init__(self, message: str, task: Task, step: TaskStep = None):
        super().__init__(message)
        self.task = task
        self.step = step

class BrowserError(AIBrowserAgentError):
    """Raised when browser operations fail."""
    def __init__(self, message: str, action: Action = None):
        super().__init__(message)
        self.action = action

class SecurityError(AIBrowserAgentError):
    """Raised when security validation fails."""
    def __init__(self, message: str, action: Action, risk_level: str):
        super().__init__(message)
        self.action = action
        self.risk_level = risk_level
```

### ErrorHandler

Centralized error handling and recovery.

```python
from ai_browser_agent.core.error_handler import ErrorHandler

class ErrorHandler:
    def __init__(self, config: AppConfig):
        """Initialize error handler with configuration."""
    
    def handle_browser_error(self, error: BrowserError, 
                           context: Dict[str, Any]) -> RecoveryAction:
        """Handle browser-related errors.
        
        Args:
            error: Browser error that occurred
            context: Current execution context
            
        Returns:
            Recovery action to attempt
        """
    
    def handle_ai_error(self, error: Exception, 
                       context: Dict[str, Any]) -> RecoveryAction:
        """Handle AI model errors.
        
        Args:
            error: AI model error
            context: Current execution context
            
        Returns:
            Recovery action to attempt
        """
    
    def should_retry(self, error: Exception, 
                    attempt_count: int) -> bool:
        """Determine if operation should be retried.
        
        Args:
            error: Error that occurred
            attempt_count: Number of attempts made
            
        Returns:
            True if should retry, False otherwise
        """
```

---

## Usage Patterns

### Basic Agent Usage

```python
from ai_browser_agent.core.ai_agent import AIAgent
from ai_browser_agent.ui.terminal_interface import TerminalInterface
from ai_browser_agent.config_manager import ConfigManager

# Load configuration
config_manager = ConfigManager()
app_config = config_manager.load_configuration()

# Initialize UI and agent
ui = TerminalInterface()
agent = AIAgent(config={"app_config": app_config}, user_interface=ui)

try:
    # Initialize agent
    agent.initialize()
    
    # Execute task
    result = agent.execute_task("Check my Gmail inbox")
    print(f"Task result: {result}")
    
finally:
    # Clean up
    agent.shutdown()
```

### Custom Browser Configuration

```python
from ai_browser_agent.controllers.browser_controller import BrowserController
from ai_browser_agent.models.config import BrowserConfig

# Custom browser configuration
browser_config = BrowserConfig(
    headless=True,
    window_size=(1280, 720),
    timeout=60,
    disable_images=True
)

# Initialize browser controller
browser = BrowserController(browser_config)
browser.start_browser()

try:
    # Use browser
    browser.navigate_to("https://example.com")
    content = browser.get_page_content()
    
finally:
    browser.close_browser()
```

### Security Integration

```python
from ai_browser_agent.security.security_layer import SecurityLayer
from ai_browser_agent.models.action import Action, ActionType

# Initialize security layer
security = SecurityLayer(security_config, ui)

# Validate action
action = Action(
    type=ActionType.CLICK,
    target="delete_button",
    parameters={"element_id": "delete-email-123"},
    confidence=0.9,
    is_destructive=True
)

# Check if action needs confirmation
result = security.validate_action(action, context)
if result.requires_confirmation:
    confirmed = security.request_user_confirmation(action, result.risk_level)
    if not confirmed:
        raise SecurityError("User denied confirmation", action, result.risk_level)
```

This API reference provides comprehensive documentation for all major components and their interfaces. Each class and method includes type hints, docstrings, and usage examples to help developers understand and extend the AI Browser Agent system.