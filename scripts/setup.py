#!/usr/bin/env python3
"""Setup script for AI Browser Agent."""

import sys
import os
import shutil
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ai_browser_agent.config_manager import ConfigManager, ConfigurationError


def main():
    """Set up AI Browser Agent for first use."""
    print("AI Browser Agent Setup")
    print("=" * 50)
    
    config_manager = ConfigManager(project_root)
    
    try:
        # Set up directories
        print("Setting up directories...")
        config_manager.setup_directories(config_manager.load_configuration())
        print("✓ Directories created")
        
        # Create default configuration file
        print("\nCreating default configuration file...")
        if config_manager.create_default_config_file():
            print("✓ Default configuration file created")
        else:
            print("ℹ Configuration file already exists")
        
        # Copy .env.example to .env if it doesn't exist
        env_example = project_root / ".env.example"
        env_file = project_root / ".env"
        
        if env_example.exists() and not env_file.exists():
            print("\nCreating .env file from template...")
            shutil.copy(env_example, env_file)
            print("✓ .env file created from .env.example")
            print("Please edit .env file and add your API keys")
        elif env_file.exists():
            print("ℹ .env file already exists")
        
        print("\nSetup completed successfully!")
        print("\nNext steps:")
        print("1. Edit .env file and add your API keys (CLAUDE_API_KEY or OPENAI_API_KEY)")
        print("2. Optionally customize config/app_config.json")
        print("3. Run: python -m ai_browser_agent.main --validate-config")
        print("4. Start using: python -m ai_browser_agent.main --task 'your task here'")
        
        return 0
        
    except ConfigurationError as e:
        print(f"✗ Setup error: {e}")
        return 1
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())