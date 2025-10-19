"""Configuration management module for AI Browser Agent."""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

from ai_browser_agent.models.config import AppConfig, AIModelConfig, BrowserConfig, SecurityConfig


logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Exception raised for configuration-related errors."""
    pass


class ConfigManager:
    """Manages application configuration loading, validation, and environment setup."""
    
    def __init__(self, project_root: Optional[Path] = None):
        """Initialize the configuration manager.
        
        Args:
            project_root: Path to the project root directory. If None, auto-detected.
        """
        if project_root is None:
            # Auto-detect project root (assuming this file is in ai_browser_agent/)
            self.project_root = Path(__file__).parent.parent
        else:
            self.project_root = project_root
        
        self.config_dir = self.project_root / "config"
        self.default_config_file = self.config_dir / "app_config.json"
    
    def load_configuration(self, config_path: Optional[str] = None) -> AppConfig:
        """Load and validate application configuration.
        
        Args:
            config_path: Optional path to configuration file. If None, uses default.
            
        Returns:
            AppConfig: Loaded and validated configuration.
            
        Raises:
            ConfigurationError: If configuration loading or validation fails.
        """
        config_dict = {}
        
        # Determine configuration file path
        if config_path is None:
            config_path = str(self.default_config_file)
        
        # Load from file if it exists
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config_dict = json.load(f)
                logger.info(f"Loaded configuration from: {config_path}")
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load config file {config_path}: {e}")
                logger.info("Using default configuration with environment variables.")
        else:
            logger.info(f"Configuration file not found at {config_path}, using defaults.")
        
        # Override with environment variables
        env_overrides = self._load_env_config()
        if env_overrides:
            self._merge_config_dict(config_dict, env_overrides)
            logger.info("Applied environment variable overrides.")
        
        # Create configuration object
        try:
            config = AppConfig.load_from_dict(config_dict)
        except Exception as e:
            logger.error(f"Error creating configuration: {e}")
            raise ConfigurationError(f"Failed to create configuration: {e}")
        
        # Validate configuration
        validation_errors = self._validate_configuration(config)
        if validation_errors:
            error_msg = "Configuration validation failed:\n" + "\n".join(validation_errors)
            logger.error(error_msg)
            raise ConfigurationError(error_msg)
        
        return config
    
    def _load_env_config(self) -> Dict[str, Any]:
        """Load configuration from environment variables.
        
        Returns:
            Dict containing configuration overrides from environment variables.
        """
        env_config = {}
        
        # AI Model configuration
        ai_config = {}
        if os.getenv("CLAUDE_API_KEY"):
            ai_config["claude_api_key"] = os.getenv("CLAUDE_API_KEY")
        if os.getenv("OPENAI_API_KEY"):
            ai_config["openai_api_key"] = os.getenv("OPENAI_API_KEY")
        if os.getenv("AI_PRIMARY_MODEL"):
            ai_config["primary_model"] = os.getenv("AI_PRIMARY_MODEL")
        if os.getenv("AI_FALLBACK_MODEL"):
            ai_config["fallback_model"] = os.getenv("AI_FALLBACK_MODEL")
        if os.getenv("AI_MAX_TOKENS"):
            try:
                ai_config["max_tokens"] = int(os.getenv("AI_MAX_TOKENS"))
            except ValueError:
                logger.warning("Invalid AI_MAX_TOKENS value, ignoring")
        if os.getenv("AI_TEMPERATURE"):
            try:
                ai_config["temperature"] = float(os.getenv("AI_TEMPERATURE"))
            except ValueError:
                logger.warning("Invalid AI_TEMPERATURE value, ignoring")
        
        if ai_config:
            env_config["ai_model"] = ai_config
        
        # Browser configuration
        browser_config = {}
        if os.getenv("BROWSER_HEADLESS"):
            browser_config["headless"] = os.getenv("BROWSER_HEADLESS").lower() == "true"
        if os.getenv("BROWSER_TYPE"):
            browser_config["browser_type"] = os.getenv("BROWSER_TYPE")
        if os.getenv("BROWSER_TIMEOUT"):
            try:
                browser_config["timeout"] = int(os.getenv("BROWSER_TIMEOUT"))
            except ValueError:
                logger.warning("Invalid BROWSER_TIMEOUT value, ignoring")
        if os.getenv("BROWSER_PROFILE_PATH"):
            browser_config["profile_path"] = os.getenv("BROWSER_PROFILE_PATH")
        
        if browser_config:
            env_config["browser"] = browser_config
        
        # Security configuration
        security_config = {}
        if os.getenv("SECURITY_REQUIRE_PAYMENT_CONFIRMATION"):
            security_config["require_confirmation_for_payments"] = (
                os.getenv("SECURITY_REQUIRE_PAYMENT_CONFIRMATION").lower() == "true"
            )
        if os.getenv("SECURITY_REQUIRE_DELETION_CONFIRMATION"):
            security_config["require_confirmation_for_deletions"] = (
                os.getenv("SECURITY_REQUIRE_DELETION_CONFIRMATION").lower() == "true"
            )
        if os.getenv("SECURITY_MAX_TASK_DURATION"):
            try:
                security_config["max_task_duration"] = int(os.getenv("SECURITY_MAX_TASK_DURATION"))
            except ValueError:
                logger.warning("Invalid SECURITY_MAX_TASK_DURATION value, ignoring")
        
        if security_config:
            env_config["security"] = security_config
        
        # Application-level configuration
        if os.getenv("DEBUG_MODE"):
            env_config["debug_mode"] = os.getenv("DEBUG_MODE").lower() == "true"
        if os.getenv("LOG_FILE"):
            env_config["log_file"] = os.getenv("LOG_FILE")
        if os.getenv("DATA_DIRECTORY"):
            env_config["data_directory"] = os.getenv("DATA_DIRECTORY")
        
        return env_config
    
    def _merge_config_dict(self, base_dict: Dict[str, Any], override_dict: Dict[str, Any]) -> None:
        """Recursively merge override dictionary into base dictionary.
        
        Args:
            base_dict: Base configuration dictionary to merge into.
            override_dict: Override values to merge.
        """
        for key, value in override_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                self._merge_config_dict(base_dict[key], value)
            else:
                base_dict[key] = value
    
    def _validate_configuration(self, config: AppConfig) -> List[str]:
        """Validate configuration and return list of errors.
        
        Args:
            config: Configuration to validate.
            
        Returns:
            List of validation error messages. Empty if valid.
        """
        errors = []
        
        # Validate basic configuration
        if not config.validate():
            errors.append("Basic configuration validation failed")
        
        # Validate API keys
        available_models = config.ai_model.get_available_models()
        if not available_models:
            errors.append("No AI model API keys configured. Set CLAUDE_API_KEY or OPENAI_API_KEY.")
        
        if config.ai_model.primary_model not in available_models:
            if available_models:
                logger.warning(f"Primary model '{config.ai_model.primary_model}' not available. "
                             f"Available: {', '.join(available_models)}")
                # Auto-fix by using first available model
                config.ai_model.primary_model = available_models[0]
                logger.info(f"Switched to primary model: {config.ai_model.primary_model}")
            else:
                errors.append(f"Primary model '{config.ai_model.primary_model}' not available")
        
        # Validate directories exist or can be created
        directories_to_check = [
            config.data_directory,
            config.temp_directory,
            Path(config.log_file).parent,
            Path(config.security.audit_log_file).parent if config.security.audit_log_enabled else None
        ]
        
        for directory in directories_to_check:
            if directory is None:
                continue
            
            dir_path = Path(directory)
            if not dir_path.exists():
                try:
                    dir_path.mkdir(parents=True, exist_ok=True)
                except OSError as e:
                    errors.append(f"Cannot create directory {directory}: {e}")
        
        return errors
    
    def create_default_config_file(self, force: bool = False) -> bool:
        """Create a default configuration file.
        
        Args:
            force: If True, overwrite existing file.
            
        Returns:
            True if file was created, False if it already exists and force=False.
            
        Raises:
            ConfigurationError: If file creation fails.
        """
        if self.default_config_file.exists() and not force:
            return False
        
        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Create default configuration
        default_config = AppConfig()
        config_dict = default_config.to_dict()
        
        # Remove sensitive information from default config
        config_dict["ai_model"]["claude_api_key"] = None
        config_dict["ai_model"]["openai_api_key"] = None
        
        try:
            with open(self.default_config_file, 'w') as f:
                json.dump(config_dict, f, indent=2)
            logger.info(f"Created default configuration file: {self.default_config_file}")
            return True
        except IOError as e:
            raise ConfigurationError(f"Could not create default config file: {e}")
    
    def setup_directories(self, config: AppConfig) -> None:
        """Set up required directories for the application.
        
        Args:
            config: Application configuration.
            
        Raises:
            ConfigurationError: If directory creation fails.
        """
        directories = [
            "logs",
            "screenshots", 
            "session_data",
            "browser_profiles",
            config.data_directory,
            config.temp_directory,
            "config"
        ]
        
        for directory in directories:
            dir_path = self.project_root / directory
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                raise ConfigurationError(f"Failed to create directory {dir_path}: {e}")
        
        logger.info("Application directories set up successfully")
    
    def get_config_summary(self, config: AppConfig) -> str:
        """Get a summary of the current configuration.
        
        Args:
            config: Configuration to summarize.
            
        Returns:
            String summary of configuration.
        """
        summary_lines = [
            "AI Browser Agent Configuration Summary:",
            f"  Debug Mode: {config.debug_mode}",
            f"  Browser: {config.browser.browser_type} (headless: {config.browser.headless})",
            f"  Primary AI Model: {config.ai_model.primary_model}",
            f"  Available Models: {', '.join(config.ai_model.get_available_models())}",
            f"  Security: Payments={config.security.require_confirmation_for_payments}, "
            f"Deletions={config.security.require_confirmation_for_deletions}",
            f"  Log File: {config.log_file}",
            f"  Data Directory: {config.data_directory}",
        ]
        
        return "\n".join(summary_lines)