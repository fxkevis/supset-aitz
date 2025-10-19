#!/usr/bin/env python3
"""Interactive AI Browser Agent - Console Input Version"""

import asyncio
import sys
import os
import tempfile
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from ai_browser_agent.controllers.browser_controller import BrowserController
from ai_browser_agent.models.config import BrowserConfig
from ai_browser_agent.core.task_planner import TaskPlanner
from ai_browser_agent.interfaces.mock_model import MockModel

def show_help():
    """Show available commands and examples."""
    print("\n=== AI Browser Agent - Help ===")
    print("Available commands:")
    print("  open <website>     - Navigate to a website")
    print("  go to <website>    - Navigate to a website") 
    print("  visit <website>    - Navigate to a website")
    print("  help               - Show this help")
    print("  quit/exit/q        - Exit the agent")
    print("\nExamples:")
    print("  open google.com")
    print("  go to youtube.com")
    print("  visit github.com")
    print("  open gmail")
    print("  visit stackoverflow.com")

async def interactive_mode():
    """Run the agent in interactive console mode."""
    print("🤖 AI Browser Agent - Interactive Mode")
    print("Type 'help' for commands or 'quit' to exit")
    print("=" * 50)
    
    # Configure browser
    browser_config = BrowserConfig()
    temp_profile = tempfile.mkdtemp(prefix="chrome_automation_")
    browser_config.profile_path = temp_profile
    browser_config.disable_automation_flags = True
    
    browser = BrowserController(browser_config)
    planner = TaskPlanner({}, MockModel())
    planner.initialize()
    
    browser_started = False
    
    try:
        while True:
            try:
                task = input("\n🚀 Enter command: ").strip()
                
                if not task:
                    continue
                    
                if task.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                    
                if task.lower() == 'help':
                    show_help()
                    continue
                
                # Start browser on first command
                if not browser_started:
                    print("🔄 Starting browser...")
                    browser.connect()
                    browser_started = True
                    print("✅ Browser ready!")
                
                # Process the task
                await process_task(browser, planner, task)
                
            except KeyboardInterrupt:
                print("\n👋 Interrupted by user. Goodbye!")
                break
            except EOFError:
                print("\n👋 End of input. Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                continue
                
    finally:
        if browser_started:
            browser.disconnect()
            print("✅ Browser closed")
        
        # Clean up
        try:
            import shutil
            if os.path.exists(temp_profile):
                shutil.rmtree(temp_profile)
        except:
            pass

async def process_task(browser, planner, task_description):
    """Process a single task."""
    print(f"📋 Processing: {task_description}")
    
    # Parse task to get steps
    steps = planner._parse_with_patterns(task_description)
    if not steps:
        print("❌ Could not understand the command. Type 'help' for examples.")
        return
    
    # Execute navigation step
    for step in steps:
        if step.action_type == "navigate":
            target_url = step.parameters.get('target')
            if target_url and target_url != 'url':
                try:
                    # Check if this is the first navigation or we should open a new tab
                    current_url = browser.get_current_url()
                    if current_url and current_url != "data:,":
                        # Open in new tab
                        browser.driver.execute_script(f"window.open('{target_url}', '_blank');")
                        browser.driver.switch_to.window(browser.driver.window_handles[-1])
                        print(f"🆕 Opened {target_url} in new tab")
                    else:
                        # Navigate in current tab
                        browser.navigate_to(target_url)
                        print(f"🌐 Navigated to {target_url}")
                    
                    # Show result
                    await asyncio.sleep(1)  # Wait for page to load
                    current_url = browser.get_current_url()
                    title = browser.get_page_title()
                    print(f"✅ Success!")
                    print(f"   📍 URL: {current_url}")
                    print(f"   📄 Title: {title}")
                    
                except Exception as e:
                    print(f"❌ Navigation failed: {e}")
            else:
                print("❌ No valid URL found in command")
            break

if __name__ == "__main__":
    try:
        asyncio.run(interactive_mode())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)