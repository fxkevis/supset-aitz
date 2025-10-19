#!/bin/bash
# Start Chrome with remote debugging enabled for AI Browser Agent

CHROME_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
PROFILE_PATH="$HOME/Library/Application Support/Google/Chrome/Profile 3"
DEBUG_PORT=9222

echo "=== Starting Chrome with Remote Debugging ==="
echo "Profile: Profile 3"
echo "Debug Port: $DEBUG_PORT"
echo ""

# Check if Chrome is already running
if pgrep -f "Google Chrome" > /dev/null; then
    echo "⚠️  Chrome is already running. Please close it first and run this script again."
    echo "Or use: killall 'Google Chrome'"
    exit 1
fi

# Start Chrome with remote debugging
echo "Starting Chrome with your authorized profile..."
"$CHROME_PATH" \
    --user-data-dir="$HOME/Library/Application Support/Google/Chrome" \
    --profile-directory="Profile 3" \
    --remote-debugging-port=$DEBUG_PORT \
    --disable-web-security \
    --disable-features=VizDisplayCompositor \
    --no-first-run \
    --no-default-browser-check &

CHROME_PID=$!
echo "✓ Chrome started with PID: $CHROME_PID"
echo "✓ Remote debugging available at: http://localhost:$DEBUG_PORT"
echo ""
echo "Now you can run the AI Browser Agent:"
echo "  /opt/anaconda3/bin/python simple_agent.py \"Navigate to google.com\""
echo ""
echo "To stop Chrome: kill $CHROME_PID"