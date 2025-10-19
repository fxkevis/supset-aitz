"""Main entry point for the AI Browser Agent application."""

import sys
import os
import json
import logging
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any

import click
from dotenv import load_dotenv

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ai_browser_agent.core.ai_agent import AIAgent
from ai_browser_agent.ui.terminal_interface import TerminalInterface
from ai_browser_agent.models.config import AppConfig, AIModelConfig, BrowserConfig, SecurityConfig
from ai_browser_agent.interfaces.user_interface import UserMessage, MessageType
from ai_browser_agent.config_manager import ConfigManager, ConfigurationError


def setup_environment() -> None:
    """Set up the environment and load configuration."""
    # Load environment variables from .env file
    env_file = project_root / ".env"
    if env_file.exists():
        load_dotenv(env_file)
    
    # Create necessary directories
    directories = ["logs", "screenshots", "session_data", "browser_profiles", "data", "temp", "config"]
    for directory in directories:
        (project_root / directory).mkdir(exist_ok=True)





def setup_logging(config: AppConfig) -> None:
    """Set up application logging."""
    log_level = logging.DEBUG if config.debug_mode else logging.INFO
    
    # Ensure log directory exists
    log_file_path = Path(config.log_file)
    log_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(config.log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Set specific logger levels
    if not config.debug_mode:
        logging.getLogger('selenium').setLevel(logging.WARNING)
        logging.getLogger('urllib3').setLevel(logging.WARNING)





async def async_main(
    task: Optional[str] = None,
    config: Optional[str] = None,
    debug: bool = False,
    headless: bool = False,
    create_config: bool = False,
    validate_config: bool = False
) -> None:
    """AI Browser Agent - Autonomous web browser automation.
    
    This agent can perform complex multi-step tasks in web browsers using AI decision-making.
    It supports email management, online ordering, and general web automation tasks.
    
    Examples:
        ai-browser-agent --task "Check my Gmail inbox and delete spam emails"
        ai-browser-agent --config custom_config.json --debug
        ai-browser-agent --create-config
    """
    
    try:
        # Set up environment first
        setup_environment()
        
        # Initialize configuration manager
        config_manager = ConfigManager(project_root)
        
        # Handle special commands
        if create_config:
            try:
                config_manager.create_default_config_file(force=True)
                click.echo("✓ Default configuration file created successfully")
            except ConfigurationError as e:
                click.echo(f"✗ Failed to create configuration file: {e}", err=True)
                sys.exit(1)
            return
        
        # Load configuration
        try:
            app_config = config_manager.load_configuration(config)
        except ConfigurationError as e:
            click.echo(f"Configuration error: {e}", err=True)
            sys.exit(1)
        
        # Apply command line overrides
        if debug:
            app_config.debug_mode = True
        if headless:
            app_config.browser.headless = True
        
        # Set up logging
        setup_logging(app_config)
        logger = logging.getLogger(__name__)
        
        if validate_config:
            click.echo("✓ Configuration loaded and validated successfully")
            click.echo("✓ API keys are configured")
            click.echo("\nConfiguration Summary:")
            click.echo(config_manager.get_config_summary(app_config))
            return
        
        # Set up application directories
        try:
            config_manager.setup_directories(app_config)
        except ConfigurationError as e:
            click.echo(f"Setup error: {e}", err=True)
            sys.exit(1)
        
        logger.info("Starting AI Browser Agent")
        logger.info(f"Configuration: Debug={app_config.debug_mode}, Headless={app_config.browser.headless}")
        logger.info(f"Primary AI Model: {app_config.ai_model.primary_model}")
        
        # Initialize the terminal interface
        ui = TerminalInterface()
        ui.start_interface()
        
        # Convert AppConfig to the format expected by AIAgent
        agent_config = app_config.to_dict()
        
        # Initialize the AI agent
        agent = AIAgent(config=agent_config, user_interface=ui)
        
        # Initialize agent components
        logger.info("Initializing AI Agent components...")
        await agent.initialize()
        
        if task:
            # Execute the provided task immediately
            ui.display_message(UserMessage(
                content=f"Executing task: {task}",
                message_type=MessageType.INFO
            ))
            
            logger.info(f"Executing immediate task: {task}")
            result = await agent.execute_task(task)
            
            ui.display_message(UserMessage(
                content=f"Task completed: {result}",
                message_type=MessageType.SUCCESS
            ))
            logger.info(f"Task completed with result: {result}")
        else:
            # Start interactive mode
            ui.display_message(UserMessage(
                content="AI Browser Agent started. Type 'help' for available commands.",
                message_type=MessageType.INFO
            ))
            
            logger.info("Starting interactive mode")
            
            # Start interactive command loop
            try:
                while True:
                    user_input = ui.get_user_input("Enter command (or 'quit' to exit): ")
                    
                    if user_input.lower() in ['quit', 'exit', 'q']:
                        break
                    elif user_input.lower() in ['help', 'h']:
                        show_help(ui)
                    elif user_input.strip():
                        # Treat input as a task
                        ui.display_message(UserMessage(
                            content=f"Executing task: {user_input}",
                            message_type=MessageType.INFO
                        ))
                        
                        try:
                            result = await agent.execute_task(user_input)
                            ui.display_message(UserMessage(
                                content=f"Task completed: {result}",
                                message_type=MessageType.SUCCESS
                            ))
                        except Exception as e:
                            ui.display_message(UserMessage(
                                content=f"Task failed: {e}",
                                message_type=MessageType.ERROR
                            ))
                            logger.error(f"Task execution failed: {e}")
            except KeyboardInterrupt:
                pass
    
    except KeyboardInterrupt:
        click.echo("\nShutting down AI Browser Agent...")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        if 'logger' in locals():
            logger.error(f"Application error: {e}")
        sys.exit(1)
    finally:
        # Clean up resources
        try:
            if 'agent' in locals():
                logger.info("Shutting down AI Agent...")
                await agent.shutdown()
            if 'ui' in locals():
                ui.stop_interface()
        except Exception as e:
            click.echo(f"Error during cleanup: {e}", err=True)
            if 'logger' in locals():
                logger.error(f"Cleanup error: {e}")


def show_help(ui: TerminalInterface) -> None:
    """Display help information to the user."""
    help_text = """
Available Commands:
  help, h          - Show this help message
  quit, exit, q    - Exit the application
  
  Or enter any task description to execute, for example:
  - "Check my Gmail inbox and delete spam emails"
  - "Order pizza from my usual restaurant"
  - "Find and click the login button on this website"
  
Configuration:
  - Use --config to specify a custom configuration file
  - Use --debug for verbose logging
  - Use --headless to run browser without GUI
  - Use --create-config to generate a default configuration file
  
Environment Variables:
  - CLAUDE_API_KEY: Your Claude API key
  - OPENAI_API_KEY: Your OpenAI API key
  - AI_PRIMARY_MODEL: Primary AI model (claude/openai)
  - BROWSER_HEADLESS: Run browser in headless mode (true/false)
  - DEBUG_MODE: Enable debug logging (true/false)
"""
    
    ui.display_message(UserMessage(
        content=help_text,
        message_type=MessageType.INFO
    ))


@click.command()
@click.option(
    "--task", 
    "-t", 
    help="Task description to execute immediately"
)
@click.option(
    "--config", 
    "-c", 
    type=click.Path(), 
    help="Path to configuration file"
)
@click.option(
    "--debug", 
    is_flag=True, 
    help="Enable debug mode"
)
@click.option(
    "--headless", 
    is_flag=True, 
    help="Run browser in headless mode"
)
@click.option(
    "--create-config",
    is_flag=True,
    help="Create default configuration file and exit"
)
@click.option(
    "--validate-config",
    is_flag=True,
    help="Validate configuration and exit"
)
@click.version_option(version="1.0.0", prog_name="AI Browser Agent")
def main(
    task: Optional[str] = None,
    config: Optional[str] = None,
    debug: bool = False,
    headless: bool = False,
    create_config: bool = False,
    validate_config: bool = False
) -> None:
    """AI Browser Agent - Autonomous web browser automation.
    
    This agent can perform complex multi-step tasks in web browsers using AI decision-making.
    It supports email management, online ordering, and general web automation tasks.
    
    Examples:
        ai-browser-agent --task "Check my Gmail inbox and delete spam emails"
        ai-browser-agent --config custom_config.json --debug
        ai-browser-agent --create-config
    """
    asyncio.run(async_main(task, config, debug, headless, create_config, validate_config))


if __name__ == "__main__":
    main()