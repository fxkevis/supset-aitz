#!/usr/bin/env python3
"""Chrome Manager - Reliable Chrome Connection and Management"""

import os
import sys
import time
import subprocess
import json
from pathlib import Path
from typing import Optional, Dict, List

# Try to import requests, with fallback if not available
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    print("⚠️  requests library not available - using basic HTTP fallback")
    HAS_REQUESTS = False
    # Create a minimal requests-like interface using urllib
    import urllib.request
    import urllib.error
    
    class SimpleResponse:
        def __init__(self, status_code, content):
            self.status_code = status_code
            self._content = content
        
        def json(self):
            import json
            return json.loads(self._content.decode())
    
    class SimpleRequests:
        @staticmethod
        def get(url, timeout=5):
            try:
                with urllib.request.urlopen(url, timeout=timeout) as response:
                    return SimpleResponse(response.getcode(), response.read())
            except urllib.error.URLError:
                return SimpleResponse(0, b'[]')
    
    requests = SimpleRequests()


class ChromeManager:
    """Manages Chrome lifecycle and remote debugging connection."""
    
    def __init__(self):
        self.debug_port = 9222
        self.chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        self.profile_path = os.path.expanduser("~/Library/Application Support/Google/Chrome")
        self.profile_directory = "Profile 3"
        self.debug_data_dir = os.path.expanduser("~/Library/Application Support/Google/Chrome-Debug")
        
    def get_chrome_status(self) -> Dict[str, any]:
        """Get comprehensive Chrome status."""
        status = {
            "running": False,
            "remote_debugging": False,
            "connection_working": False,
            "tabs_count": 0,
            "pid": None
        }
        
        # Check if Chrome is running
        try:
            result = subprocess.run(["pgrep", "-f", "Google Chrome"], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                status["running"] = True
                status["pid"] = result.stdout.strip().split('\n')[0]
        except:
            pass
        
        # Check if remote debugging is enabled
        try:
            result = subprocess.run(["pgrep", "-f", f"remote-debugging-port={self.debug_port}"], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                status["remote_debugging"] = True
        except:
            pass
        
        # Check if connection actually works
        if status["remote_debugging"]:
            try:
                response = requests.get(f"http://localhost:{self.debug_port}/json", timeout=3)
                if response.status_code == 200:
                    tabs = response.json()
                    status["connection_working"] = True
                    status["tabs_count"] = len(tabs)
            except:
                pass
        
        return status
    
    def stop_chrome(self) -> bool:
        """Stop Chrome gracefully."""
        print("🔄 Stopping Chrome...")
        try:
            subprocess.run(["killall", "Google Chrome"], 
                          capture_output=True, timeout=10)
            time.sleep(3)
            
            # Verify it's stopped
            result = subprocess.run(["pgrep", "-f", "Google Chrome"], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                print("✅ Chrome stopped successfully")
                return True
            else:
                print("⚠️  Chrome may still be running")
                return False
        except Exception as e:
            print(f"❌ Error stopping Chrome: {e}")
            return False
    
    def start_chrome_with_debugging(self) -> bool:
        """Start Chrome with remote debugging enabled."""
        print("🚀 Starting Chrome with remote debugging...")
        
        # Ensure debug data directory exists
        os.makedirs(self.debug_data_dir, exist_ok=True)
        
        # Copy profile if it doesn't exist in debug directory
        debug_profile_path = os.path.join(self.debug_data_dir, self.profile_directory)
        original_profile_path = os.path.join(self.profile_path, self.profile_directory)
        
        if not os.path.exists(debug_profile_path) and os.path.exists(original_profile_path):
            print("📋 Copying Chrome profile for debugging...")
            try:
                subprocess.run(["cp", "-r", original_profile_path, debug_profile_path], 
                              check=True, timeout=30)
            except Exception as e:
                print(f"⚠️  Could not copy profile: {e}")
        
        # Start Chrome with debugging
        chrome_args = [
            self.chrome_path,
            f"--remote-debugging-port={self.debug_port}",
            f"--user-data-dir={self.debug_data_dir}",
            f"--profile-directory={self.profile_directory}",
            "--disable-web-security",
            "--disable-features=VizDisplayCompositor",
            "--no-first-run",
            "--no-default-browser-check"
        ]
        
        try:
            # Start Chrome in background
            process = subprocess.Popen(chrome_args, 
                                     stdout=subprocess.DEVNULL, 
                                     stderr=subprocess.DEVNULL)
            
            print(f"Chrome started with PID: {process.pid}")
            
            # Wait for Chrome to initialize
            print("⏳ Waiting for Chrome to initialize...")
            for i in range(10):  # Wait up to 10 seconds
                time.sleep(1)
                status = self.get_chrome_status()
                if status["connection_working"]:
                    print(f"✅ Chrome ready with {status['tabs_count']} tabs")
                    return True
                print(f"   Attempt {i+1}/10...")
            
            print("❌ Chrome started but remote debugging not working")
            return False
            
        except Exception as e:
            print(f"❌ Failed to start Chrome: {e}")
            return False
    
    def ensure_chrome_ready(self) -> bool:
        """Ensure Chrome is running with working remote debugging."""
        print("🔧 Checking Chrome status...")
        
        status = self.get_chrome_status()
        
        if status["connection_working"]:
            print(f"✅ Chrome already ready with {status['tabs_count']} tabs")
            return True
        
        if status["running"] and not status["remote_debugging"]:
            print("⚠️  Chrome running without remote debugging")
            if not self.stop_chrome():
                print("❌ Could not stop Chrome")
                return False
        
        if not status["running"] or not status["remote_debugging"]:
            if not self.start_chrome_with_debugging():
                print("❌ Could not start Chrome with debugging")
                return False
        
        # Final verification
        status = self.get_chrome_status()
        if status["connection_working"]:
            print("✅ Chrome is now ready!")
            return True
        else:
            print("❌ Chrome setup failed")
            return False
    
    def get_tabs(self) -> List[Dict]:
        """Get list of all Chrome tabs."""
        try:
            response = requests.get(f"http://localhost:{self.debug_port}/json", timeout=5)
            if response.status_code == 200:
                return response.json()
            return []
        except:
            return []
    
    def test_connection(self) -> bool:
        """Test if we can connect to Chrome via Selenium."""
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            
            options = Options()
            options.add_experimental_option("debuggerAddress", f"127.0.0.1:{self.debug_port}")
            
            # Try to connect
            driver = webdriver.Chrome(options=options)
            
            # Test basic operations
            current_url = driver.current_url
            title = driver.title
            
            print(f"✅ Selenium connection successful!")
            print(f"📍 Current tab: {current_url}")
            print(f"📄 Title: {title}")
            
            # Don't close the driver - we want to keep the connection
            return True
            
        except Exception as e:
            print(f"❌ Selenium connection failed: {e}")
            return False


def main():
    """Test Chrome Manager."""
    manager = ChromeManager()
    
    print("🧪 Testing Chrome Manager...")
    print("=" * 50)
    
    # Get initial status
    status = manager.get_chrome_status()
    print(f"Initial status: {status}")
    
    # Ensure Chrome is ready
    if manager.ensure_chrome_ready():
        print("\n🧪 Testing Selenium connection...")
        manager.test_connection()
    else:
        print("❌ Chrome setup failed")


if __name__ == "__main__":
    main()