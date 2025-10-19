#!/bin/bash
# Setup Chrome for Remote Debugging (Proper Version)

echo "🔧 Setting up Chrome for Remote Debugging..."
echo ""

# Check if Chrome is running
if pgrep -f "Google Chrome" > /dev/null; then
    echo "⚠️  Chrome is currently running."
    echo "To enable remote debugging, I need to restart Chrome."
    echo ""
    echo "Your tabs and login sessions will be preserved!"
    echo ""
    read -p "Press Enter to restart Chrome with remote debugging, or Ctrl+C to cancel: "
    
    echo "🔄 Closing Chrome..."
    killall "Google Chrome" 2>/dev/null
    sleep 3
fi

echo "🚀 Starting Chrome with remote debugging enabled..."

# Start Chrome with remote debugging - using a separate data directory
# This prevents conflicts with existing Chrome instances
CHROME_DEBUG_DIR="$HOME/Library/Application Support/Google/Chrome-Debug"

# Create debug directory if it doesn't exist
mkdir -p "$CHROME_DEBUG_DIR"

# Copy existing profile if it doesn't exist in debug directory
if [ ! -d "$CHROME_DEBUG_DIR/Profile 3" ] && [ -d "$HOME/Library/Application Support/Google/Chrome/Profile 3" ]; then
    echo "📋 Copying your Chrome profile for debugging..."
    cp -r "$HOME/Library/Application Support/Google/Chrome/Profile 3" "$CHROME_DEBUG_DIR/"
fi

# Start Chrome with remote debugging
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
    --remote-debugging-port=9222 \
    --user-data-dir="$CHROME_DEBUG_DIR" \
    --profile-directory="Profile 3" \
    --disable-web-security \
    --disable-features=VizDisplayCompositor \
    --no-first-run \
    --no-default-browser-check &

CHROME_PID=$!
echo "Chrome started with PID: $CHROME_PID"

# Wait for Chrome to start
echo "⏳ Waiting for Chrome to initialize..."
sleep 5

# Test the connection
echo "🧪 Testing remote debugging connection..."
if curl -s http://localhost:9222/json/version > /dev/null; then
    echo "✅ Remote debugging is working!"
    echo "🌐 Chrome is ready for AI agent connection"
else
    echo "❌ Remote debugging connection failed"
    echo "💡 Please check if Chrome started properly"
fi

echo ""
echo "✅ Setup complete!"
echo "🚀 You can now run the AI agent:"
echo "  /opt/anaconda3/bin/python test_google_search.py"