#!/usr/bin/env python3
"""Configuration validation script for AI Browser Agent."""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ai_browser_agent.config_manager import ConfigManager, ConfigurationError


def main():
    """Validate configuration and display summary."""
    config_manager = ConfigManager(project_root)
    
    try:
        # Load configuration
        config = config_manager.load_configuration()
        
        print("✓ Configuration loaded successfully")
        print("\nConfiguration Summary:")
        print(config_manager.get_config_summary(config))
        
        # Check API keys
        available_models = config.ai_model.get_available_models()
        if available_models:
            print(f"\n✓ Available AI models: {', '.join(available_models)}")
        else:
            print("\n✗ No AI model API keys configured")
            print("Please set CLAUDE_API_KEY or OPENAI_API_KEY environment variable")
            return 1
        
        print("\n✓ Configuration is valid and ready to use")
        return 0
        
    except ConfigurationError as e:
        print(f"✗ Configuration error: {e}")
        return 1
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())