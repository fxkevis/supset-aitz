#!/usr/bin/env python3
"""Simplified AI browser agent for testing."""

import asyncio
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from ai_browser_agent.controllers.browser_controller import BrowserController
from ai_browser_agent.models.config import BrowserConfig
from ai_browser_agent.core.task_planner import TaskPlanner
from ai_browser_agent.interfaces.mock_model import MockModel
from selenium.webdriver.common.by import By

async def simple_navigate(task_description: str):
    """Simple navigation without complex workflow."""
    print(f"=== Simple AI Browser Agent ===")
    print(f"Task: {task_description}")
    
    # Configure browser
    browser_config = configure_browser()
    browser = BrowserController(browser_config)
    
    print(f"✓ Using temporary profile")
    print("✓ Automation flags disabled for more natural browsing")
    
    planner = TaskPlanner({}, MockModel())
    planner.initialize()
    
    try:
        # Try to connect to existing Chrome first
        if not await try_connect_existing_chrome(browser):
            # If no existing Chrome, start new one
            browser.connect()
            print("✓ Browser connected")
        
        # Execute the task
        await execute_task_steps(browser, planner, task_description)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        
    finally:
        browser.disconnect()
        print("✓ Browser disconnected")
        
        # Clean up temporary profile
        if hasattr(browser_config, 'profile_path') and browser_config.profile_path:
            try:
                import shutil
                import os
                if os.path.exists(browser_config.profile_path) and 'chrome_automation_' in browser_config.profile_path:
                    shutil.rmtree(browser_config.profile_path)
                    print("✓ Temporary profile cleaned up")
            except Exception as e:
                print(f"⚠️  Could not clean up temporary profile: {e}")

def show_examples():
    """Show example tasks that can be run."""
    examples = [
        "Navigate to google.com",
        "Navigate to youtube.com", 
        "Go to github.com",
        "Visit reddit.com",
        "Navigate to stackoverflow.com",
        "Go to wikipedia.org",
        "Visit news.ycombinator.com"
    ]
    
    print("=== AI Browser Agent - Example Tasks ===")
    print("Usage:")
    print("  python simple_agent.py                    # Interactive mode")
    print("  python simple_agent.py \"<task>\"           # Single task mode")
    print("\nExample tasks:")
    for i, example in enumerate(examples, 1):
        print(f"  {i}. {example}")

async def interactive_mode():
    """Run the agent in interactive console mode."""
    print("=== AI Browser Agent - Interactive Mode ===")
    print("Enter tasks one by one. Type 'quit', 'exit', or 'q' to stop.")
    print("Type 'help' to see example tasks.")
    print()
    
    # Initialize browser once for the session
    browser_config = configure_browser()
    browser = BrowserController(browser_config)
    
    try:
        # Try to connect to existing Chrome first
        if not await try_connect_existing_chrome(browser):
            # If no existing Chrome, start new one
            browser.connect()
            print("✓ New browser session started")
        
        planner = TaskPlanner({}, MockModel())
        planner.initialize()
        
        while True:
            try:
                task = input("\n🤖 Enter task (or 'quit' to exit): ").strip()
                
                if not task:
                    continue
                    
                if task.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                    
                if task.lower() == 'help':
                    show_examples()
                    continue
                
                print(f"\n🚀 Executing: {task}")
                await execute_task_steps(browser, planner, task)
                
            except KeyboardInterrupt:
                print("\n\n👋 Interrupted by user. Goodbye!")
                break
            except EOFError:
                print("\n\n👋 End of input. Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error processing task: {e}")
                continue
                
    finally:
        browser.disconnect()
        print("✓ Browser session ended")

def configure_browser():
    """Configure browser settings."""
    browser_config = BrowserConfig()
    
    # Configure Chrome to look more like regular browsing
    import os
    import tempfile
    
    # Use a temporary profile directory to avoid conflicts with existing Chrome
    temp_profile = tempfile.mkdtemp(prefix="chrome_automation_")
    browser_config.profile_path = temp_profile
    
    # Remove automation indicators to make it look more like regular browsing
    browser_config.disable_automation_flags = True
    browser_config.remote_debugging_port = 9222
    
    return browser_config

async def try_connect_existing_chrome(browser):
    """Try to connect to existing Chrome instance."""
    try:
        try:
            import requests
        except ImportError:
            print("ℹ️  Installing requests library...")
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
            import requests
        
        import json
        
        # Check if Chrome is running with remote debugging
        response = requests.get("http://localhost:9222/json", timeout=2)
        if response.status_code == 200:
            tabs = response.json()
            if tabs:
                print(f"✓ Found existing Chrome with {len(tabs)} tabs")
                
                # Try to connect using Chrome DevTools Protocol
                from selenium.webdriver.chrome.options import Options
                options = Options()
                options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
                
                try:
                    from selenium import webdriver
                    browser.driver = webdriver.Chrome(options=options)
                    print("✓ Connected to existing Chrome instance")
                    return True
                except Exception as e:
                    print(f"⚠️  Could not connect to existing Chrome: {e}")
                    return False
        
    except Exception as e:
        print("ℹ️  No existing Chrome found, will start new instance")
        return False
    
    return False

async def execute_task_steps(browser, planner, task_description):
    """Execute task steps using the browser."""
    try:
        # Parse task to get steps
        steps = planner._parse_with_patterns(task_description)
        if not steps:
            print("❌ Could not understand the task")
            return
            
        print(f"📋 Created {len(steps)} steps")
        
        # Execute each step
        for i, step in enumerate(steps):
            print(f"\n📍 Step {i+1}: {step.action_type} -> {step.parameters.get('target')}")
            
            if step.action_type == "navigate":
                target_url = step.parameters.get('target')
                if target_url and target_url != 'url':
                    # Open in new tab if browser is already connected
                    if browser.is_connected():
                        browser.driver.execute_script(f"window.open('{target_url}', '_blank');")
                        # Switch to the new tab
                        browser.driver.switch_to.window(browser.driver.window_handles[-1])
                        print(f"✅ Opened {target_url} in new tab")
                    else:
                        browser.navigate_to(target_url)
                        print(f"✅ Navigated to {target_url}")
                    
                    # Verify navigation
                    current_url = browser.get_current_url()
                    title = browser.get_page_title()
                    print(f"📍 Current URL: {current_url}")
                    print(f"📄 Page title: {title}")
                else:
                    print("❌ No valid URL found")
                    
            elif step.action_type == "wait":
                print("⏳ Waiting for page to load...")
                await asyncio.sleep(2)
                
            elif step.action_type == "extract":
                print("📊 Extracting page content...")
                try:
                    if browser.is_connected():
                        page_content = await browser.get_page_content()
                        print(f"✅ Extracted: {len(page_content.elements)} elements, {len(page_content.text_content)} chars")
                    else:
                        print("❌ Browser disconnected, cannot extract content")
                except Exception as e:
                    print(f"❌ Content extraction failed: {e}")
        
        print(f"\n🎉 Task completed successfully!")
        
    except Exception as e:
        print(f"❌ Error executing task: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Interactive mode
        asyncio.run(interactive_mode())
    else:
        # Single task mode
        task = sys.argv[1]
        asyncio.run(simple_navigate(task))