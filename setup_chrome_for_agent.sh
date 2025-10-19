#!/bin/bash
# Setup Chrome for AI Agent Connection

echo "🔧 Setting up Chrome for AI Agent connection..."
echo ""

# Check if Chrome is running
if pgrep -f "Google Chrome" > /dev/null; then
    echo "⚠️  Chrome is currently running."
    echo "To connect the AI agent, I need to restart Chrome with remote debugging."
    echo ""
    echo "Your tabs and login sessions will be preserved!"
    echo ""
    read -p "Press Enter to restart Chrome with AI agent support, or Ctrl+C to cancel: "
    
    echo "🔄 Closing Chrome..."
    killall "Google Chrome" 2>/dev/null
    sleep 2
fi

echo "🚀 Starting Chrome with AI agent support..."

# Start Chrome with remote debugging and your profile
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
    --remote-debugging-port=9222 \
    --user-data-dir="$HOME/Library/Application Support/Google/Chrome" \
    --profile-directory="Profile 3" \
    --disable-web-security \
    --disable-features=VizDisplayCompositor \
    --no-first-run \
    --no-default-browser-check &

sleep 3

echo "✅ Chrome is now ready for AI agent connection!"
echo "🌐 You can now run the AI agent and it will use your existing Chrome with all your logins."
echo ""
echo "To run the AI agent:"
echo "  /opt/anaconda3/bin/python ultimate_agent.py"