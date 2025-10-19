#!/usr/bin/env python3
"""Debug Gmail Action Buttons"""

import asyncio
import sys
import time
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from navigation_manager import NavigationManager

async def debug_gmail_buttons():
    """Debug Gmail action buttons after selecting emails."""
    print("🔍 Debugging Gmail Action Buttons...")
    print("=" * 50)
    
    nav = NavigationManager()
    
    if nav.connect_to_chrome():
        print("✅ Connected to Chrome")
        
        # Navigate to Gmail
        print("\n📧 Opening Gmail...")
        if nav.navigate_to_website("https://gmail.com"):
            await asyncio.sleep(5)
            
            # Select a few emails first
            print("\n☑️  Selecting some emails...")
            try:
                checkboxes = nav.driver.find_elements("css selector", "tr.zA td div[role='checkbox']")
                if checkboxes:
                    # Select first 3 emails
                    for i, checkbox in enumerate(checkboxes[:3]):
                        if checkbox.is_displayed():
                            nav.click_element_reliable(checkbox)
                            print(f"✅ Selected email {i+1}")
                            await asyncio.sleep(0.5)
                    
                    print(f"\n🔍 Looking for action buttons after selecting emails...")
                    await asyncio.sleep(2)
                    
                    # Find all buttons and divs that might be action buttons
                    print("\n🔍 All buttons with role='button':")
                    buttons = nav.driver.find_elements("css selector", "div[role='button']")
                    print(f"Found {len(buttons)} buttons")
                    
                    for i, button in enumerate(buttons[:20]):  # Show first 20
                        try:
                            visible = button.is_displayed()
                            enabled = button.is_enabled()
                            aria_label = button.get_attribute("aria-label") or ""
                            title = button.get_attribute("title") or ""
                            data_tooltip = button.get_attribute("data-tooltip") or ""
                            text = button.text[:30] if button.text else ""
                            
                            if visible and (aria_label or title or data_tooltip or text):
                                print(f"  {i+1}. Visible: {visible}, Enabled: {enabled}")
                                if aria_label:
                                    print(f"      aria-label: '{aria_label}'")
                                if title:
                                    print(f"      title: '{title}'")
                                if data_tooltip:
                                    print(f"      data-tooltip: '{data_tooltip}'")
                                if text:
                                    print(f"      text: '{text}'")
                                
                                # Check if this might be spam/delete/archive button
                                combined_text = f"{aria_label} {title} {data_tooltip} {text}".lower()
                                if any(word in combined_text for word in ["spam", "delete", "archive", "report"]):
                                    print(f"      🎯 POTENTIAL ACTION BUTTON!")
                                print()
                        except Exception as e:
                            print(f"  {i+1}. Error reading button: {e}")
                    
                    # Also check for specific Gmail toolbar elements
                    print("\n🔍 Gmail toolbar elements:")
                    toolbar_selectors = [
                        ".ar9",  # Gmail toolbar
                        ".G-Ni",  # Another toolbar class
                        "[role='toolbar']",
                        ".aqJ",  # Gmail action area
                        ".ar7"   # Gmail button area
                    ]
                    
                    for selector in toolbar_selectors:
                        try:
                            toolbars = nav.driver.find_elements("css selector", selector)
                            if toolbars:
                                print(f"✅ Found {len(toolbars)} elements with {selector}")
                                for toolbar in toolbars[:2]:
                                    if toolbar.is_displayed():
                                        # Find buttons within toolbar
                                        toolbar_buttons = toolbar.find_elements("css selector", "div[role='button']")
                                        print(f"    Contains {len(toolbar_buttons)} buttons")
                                        
                                        for j, btn in enumerate(toolbar_buttons[:5]):
                                            try:
                                                aria_label = btn.get_attribute("aria-label") or ""
                                                title = btn.get_attribute("title") or ""
                                                if aria_label or title:
                                                    print(f"      Button {j+1}: '{aria_label}' / '{title}'")
                                            except:
                                                pass
                        except Exception as e:
                            print(f"❌ Error with {selector}: {e}")
                
                else:
                    print("❌ No checkboxes found")
                    
            except Exception as e:
                print(f"❌ Error selecting emails: {e}")
        else:
            print("❌ Could not navigate to Gmail")
        
        nav.close()
    else:
        print("❌ Could not connect to Chrome")

if __name__ == "__main__":
    asyncio.run(debug_gmail_buttons())