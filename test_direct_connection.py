#!/usr/bin/env python3
"""Test Direct Connection to Chrome Remote Debugging"""

import requests
import json

def test_chrome_connection():
    """Test connection to Chrome remote debugging."""
    print("🔍 Testing Chrome Remote Debugging Connection...")
    print("=" * 50)
    
    try:
        # Test version endpoint
        print("📡 Testing version endpoint...")
        response = requests.get("http://localhost:9222/json/version", timeout=5)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            version_info = response.json()
            print(f"✅ Chrome Version: {version_info.get('Browser', 'Unknown')}")
            print(f"✅ WebSocket URL: {version_info.get('webSocketDebuggerUrl', 'None')}")
        
        # Test tabs endpoint
        print("\\n📡 Testing tabs endpoint...")
        response = requests.get("http://localhost:9222/json", timeout=5)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            tabs = response.json()
            print(f"✅ Found {len(tabs)} tabs:")
            
            for i, tab in enumerate(tabs[:3]):  # Show first 3 tabs
                title = tab.get('title', 'No title')[:50]
                url = tab.get('url', 'No URL')[:80]
                tab_type = tab.get('type', 'unknown')
                print(f"  {i+1}. [{tab_type}] {title}")
                print(f"      URL: {url}")
                
            return True
        else:
            print(f"❌ Failed to get tabs: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection failed: {e}")
        print("💡 Chrome remote debugging is not accessible")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_chrome_connection()