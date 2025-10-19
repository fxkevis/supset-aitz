"""Configuration data models."""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional


@dataclass
class BrowserConfig:
    """Configuration for browser automation."""
    headless: bool = False
    window_size: tuple = (1920, 1080)
    timeout: int = 30
    user_agent: Optional[str] = None
    browser_type: str = "chrome"  # chrome, firefox, safari, edge
    profile_path: Optional[str] = None
    profile_directory: Optional[str] = None
    download_directory: Optional[str] = None
    disable_images: bool = False
    disable_javascript: bool = False
    disable_plugins: bool = False
    enable_logging: bool = True
    log_level: str = "INFO"
    remote_debugging_port: Optional[int] = None
    disable_automation_flags: bool = False
    
    def to_selenium_options(self) -> Dict[str, Any]:
        """Convert to Selenium WebDriver options."""
        options = {
            "headless": self.headless,
            "window_size": self.window_size,
            "page_load_timeout": self.timeout,
        }
        
        if self.user_agent:
            options["user_agent"] = self.user_agent
        
        if self.profile_path:
            options["profile_path"] = self.profile_path
        
        if self.download_directory:
            options["download_directory"] = self.download_directory
        
        return options
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert browser configuration to dictionary."""
        return {
            "headless": self.headless,
            "window_size": self.window_size,
            "timeout": self.timeout,
            "user_agent": self.user_agent,
            "browser_type": self.browser_type,
            "profile_path": self.profile_path,
            "download_directory": self.download_directory,
            "disable_images": self.disable_images,
            "disable_javascript": self.disable_javascript,
            "disable_plugins": self.disable_plugins,
            "enable_logging": self.enable_logging,
            "log_level": self.log_level,
        }
    
    def validate(self) -> bool:
        """Validate the browser configuration."""
        # Validate window size
        if len(self.window_size) != 2 or any(dim <= 0 for dim in self.window_size):
            return False
        
        # Validate timeout
        if self.timeout <= 0:
            return False
        
        # Validate browser type
        valid_browsers = ["chrome", "firefox", "safari", "edge"]
        if self.browser_type not in valid_browsers:
            return False
        
        # Validate log level
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level not in valid_log_levels:
            return False
        
        return True


@dataclass
class SecurityConfig:
    """Configuration for security and safety measures."""
    require_confirmation_for_payments: bool = True
    require_confirmation_for_deletions: bool = True
    require_confirmation_for_modifications: bool = True
    require_confirmation_for_submissions: bool = False
    
    # Domains and patterns that require extra caution
    sensitive_domains: List[str] = field(default_factory=lambda: [
        "paypal.com", "stripe.com", "amazon.com", "ebay.com",
        "banking", "payment", "checkout"
    ])
    
    # Action patterns that are considered destructive
    destructive_patterns: List[str] = field(default_factory=lambda: [
        "delete", "remove", "cancel", "unsubscribe", 
        "purchase", "buy", "pay", "order", "checkout"
    ])
    
    # Maximum allowed execution time for tasks (in seconds)
    max_task_duration: int = 3600  # 1 hour
    
    # Maximum number of retry attempts
    max_retry_attempts: int = 3
    
    # Enable audit logging
    audit_log_enabled: bool = True
    audit_log_file: str = "logs/audit.log"
    
    def is_sensitive_domain(self, url: str) -> bool:
        """Check if a URL belongs to a sensitive domain."""
        url_lower = url.lower()
        return any(domain in url_lower for domain in self.sensitive_domains)
    
    def is_destructive_action(self, action_description: str) -> bool:
        """Check if an action description suggests destructive behavior."""
        description_lower = action_description.lower()
        return any(pattern in description_lower for pattern in self.destructive_patterns)
    
    def requires_confirmation(self, action_type: str, target_url: str, description: str) -> bool:
        """Determine if an action requires user confirmation."""
        # Check based on action type
        if action_type == "payment" and self.require_confirmation_for_payments:
            return True
        if action_type == "deletion" and self.require_confirmation_for_deletions:
            return True
        if action_type == "modification" and self.require_confirmation_for_modifications:
            return True
        if action_type == "submission" and self.require_confirmation_for_submissions:
            return True
        
        # Check based on domain sensitivity
        if self.is_sensitive_domain(target_url):
            return True
        
        # Check based on action description
        if self.is_destructive_action(description):
            return True
        
        return False
    
    def validate(self) -> bool:
        """Validate the security configuration."""
        # Validate max task duration
        if self.max_task_duration <= 0:
            return False
        
        # Validate max retry attempts
        if self.max_retry_attempts < 0:
            return False
        
        # Validate audit log file path if logging is enabled
        if self.audit_log_enabled and not self.audit_log_file:
            return False
        
        return True
    
    def get_confirmation_settings(self) -> Dict[str, bool]:
        """Get all confirmation settings as a dictionary."""
        return {
            "payments": self.require_confirmation_for_payments,
            "deletions": self.require_confirmation_for_deletions,
            "modifications": self.require_confirmation_for_modifications,
            "submissions": self.require_confirmation_for_submissions,
        }


@dataclass
class AIModelConfig:
    """Configuration for AI model integration."""
    primary_model: str = "claude"  # claude, openai, local
    fallback_model: Optional[str] = "openai"
    
    # API configuration
    claude_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    
    # Model parameters
    max_tokens: int = 4000
    temperature: float = 0.7
    timeout: int = 30
    
    # Context management
    max_context_length: int = 8000
    context_overlap: int = 200
    
    def get_available_models(self) -> List[str]:
        """Get list of available models based on API keys."""
        available = []
        
        if self.claude_api_key:
            available.append("claude")
        
        if self.openai_api_key:
            available.append("openai")
        
        return available
    
    def is_model_available(self, model_name: str) -> bool:
        """Check if a specific model is available."""
        return model_name in self.get_available_models()
    
    def validate(self) -> bool:
        """Validate the AI model configuration."""
        # Check if at least one model is configured
        if not self.get_available_models():
            return False
        
        # Validate primary model is available
        if not self.is_model_available(self.primary_model):
            return False
        
        # Validate parameters
        if self.max_tokens <= 0 or self.max_context_length <= 0:
            return False
        
        if not 0.0 <= self.temperature <= 2.0:
            return False
        
        if self.timeout <= 0:
            return False
        
        return True


@dataclass
class AppConfig:
    """Main application configuration combining all config classes."""
    browser: BrowserConfig = field(default_factory=BrowserConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    ai_model: AIModelConfig = field(default_factory=AIModelConfig)
    
    # Application-level settings
    debug_mode: bool = False
    log_file: str = "logs/app.log"
    data_directory: str = "data"
    temp_directory: str = "temp"
    
    def validate(self) -> bool:
        """Validate all configuration components."""
        return (
            self.browser.validate() and
            self.security.validate() and
            self.ai_model.validate()
        )
    
    @classmethod
    def load_from_dict(cls, config_dict: Dict[str, Any]) -> 'AppConfig':
        """Load configuration from a dictionary."""
        config = cls()
        
        if "browser" in config_dict:
            browser_data = config_dict["browser"]
            config.browser = BrowserConfig(**browser_data)
        
        if "security" in config_dict:
            security_data = config_dict["security"]
            config.security = SecurityConfig(**security_data)
        
        if "ai_model" in config_dict:
            ai_data = config_dict["ai_model"]
            config.ai_model = AIModelConfig(**ai_data)
        
        # Set application-level settings
        config.debug_mode = config_dict.get("debug_mode", False)
        config.log_file = config_dict.get("log_file", "logs/app.log")
        config.data_directory = config_dict.get("data_directory", "data")
        config.temp_directory = config_dict.get("temp_directory", "temp")
        
        return config
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "browser": {
                "headless": self.browser.headless,
                "window_size": self.browser.window_size,
                "timeout": self.browser.timeout,
                "user_agent": self.browser.user_agent,
                "browser_type": self.browser.browser_type,
                "profile_path": self.browser.profile_path,
                "download_directory": self.browser.download_directory,
                "disable_images": self.browser.disable_images,
                "disable_javascript": self.browser.disable_javascript,
                "disable_plugins": self.browser.disable_plugins,
                "enable_logging": self.browser.enable_logging,
                "log_level": self.browser.log_level,
            },
            "security": {
                "require_confirmation_for_payments": self.security.require_confirmation_for_payments,
                "require_confirmation_for_deletions": self.security.require_confirmation_for_deletions,
                "require_confirmation_for_modifications": self.security.require_confirmation_for_modifications,
                "require_confirmation_for_submissions": self.security.require_confirmation_for_submissions,
                "sensitive_domains": self.security.sensitive_domains,
                "destructive_patterns": self.security.destructive_patterns,
                "max_task_duration": self.security.max_task_duration,
                "max_retry_attempts": self.security.max_retry_attempts,
                "audit_log_enabled": self.security.audit_log_enabled,
                "audit_log_file": self.security.audit_log_file,
            },
            "ai_model": {
                "primary_model": self.ai_model.primary_model,
                "fallback_model": self.ai_model.fallback_model,
                "claude_api_key": self.ai_model.claude_api_key,
                "openai_api_key": self.ai_model.openai_api_key,
                "max_tokens": self.ai_model.max_tokens,
                "temperature": self.ai_model.temperature,
                "timeout": self.ai_model.timeout,
                "max_context_length": self.ai_model.max_context_length,
                "context_overlap": self.ai_model.context_overlap,
            },
            "debug_mode": self.debug_mode,
            "log_file": self.log_file,
            "data_directory": self.data_directory,
            "temp_directory": self.temp_directory,
        }