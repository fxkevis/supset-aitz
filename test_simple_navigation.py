#!/usr/bin/env python3
"""Simple test to verify browser navigation works."""

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

async def test_navigation():
    """Test basic navigation functionality."""
    print("=== Testing Browser Navigation ===")
    
    # Test 1: Direct browser navigation
    print("\n1. Testing direct browser navigation...")
    config = BrowserConfig()
    browser = BrowserController(config)
    
    try:
        browser.connect()
        print("✓ Browser connected")
        
        browser.navigate_to('https://www.google.com')
        print("✓ Navigated to Google")
        
        url = browser.get_current_url()
        title = browser.get_page_title()
        print(f"✓ Current URL: {url}")
        print(f"✓ Page title: {title}")
        
    finally:
        browser.disconnect()
        print("✓ Browser disconnected")
    
    # Test 2: Task planner URL extraction
    print("\n2. Testing task planner URL extraction...")
    mock_model = MockModel()
    planner = TaskPlanner({}, mock_model)
    planner.initialize()
    
    task_description = "Navigate to google.com"
    steps = planner._parse_with_patterns(task_description)
    
    if steps:
        print(f"✓ Task planner created {len(steps)} steps")
        for i, step in enumerate(steps):
            print(f"  Step {i+1}: {step.action_type} -> {step.parameters.get('target')}")
    else:
        print("✗ Task planner failed to create steps")
    
    # Test 3: Mock model JSON response
    print("\n3. Testing mock model JSON response...")
    try:
        import json
        from ai_browser_agent.interfaces.ai_model_interface import ModelRequest
        response = await mock_model.generate_response(
            ModelRequest(prompt="Navigate to google.com")
        )
        print(f"✓ Mock model response: {response.content[:100]}...")
        
        # Try to parse as JSON
        json.loads(response.content)
        print("✓ Response is valid JSON")
        
    except Exception as e:
        print(f"✗ Mock model error: {e}")

if __name__ == "__main__":
    asyncio.run(test_navigation())