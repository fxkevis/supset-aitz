#!/usr/bin/env python3
"""Test script for Smart AI Agent capabilities"""

import asyncio
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from smart_agent import SmartAIAgent

async def test_agent_capabilities():
    """Test various agent capabilities."""
    print("🧪 Testing Smart AI Agent Capabilities")
    print("=" * 50)
    
    agent = SmartAIAgent()
    await agent.initialize()
    
    test_cases = [
        "Send a message 'Hello' to Kikita on Telegram",
        "Search for 'Python tutorials' on Google",
        "Write an email to john@example.com with subject 'Meeting'",
        "Open GitHub",
        "Send 'How are you?' to Alice on WhatsApp",
        "Login to Gmail"
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 Test {i}: {test_case}")
        print("-" * 40)
        
        # Analyze the task
        task_analysis = await agent.analyze_task(test_case)
        print(f"✅ Intent: {task_analysis['intent']}")
        
        if 'website' in task_analysis:
            print(f"🌐 Website: {task_analysis['website']}")
        if 'recipient' in task_analysis:
            print(f"👤 Recipient: {task_analysis['recipient']}")
        if 'message' in task_analysis:
            print(f"💬 Message: {task_analysis['message']}")
        if 'query' in task_analysis:
            print(f"🔍 Query: {task_analysis['query']}")
        
        print(f"📋 Steps: {len(task_analysis['steps'])} planned actions")
    
    await agent.shutdown()
    print("\n✅ All tests completed!")

if __name__ == "__main__":
    asyncio.run(test_agent_capabilities())