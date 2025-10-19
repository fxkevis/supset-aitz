#!/bin/bash
# AI Browser Agent - Simple launcher script

echo "🤖 AI Browser Agent Launcher"
echo "Using Anaconda Python environment..."

# Check if Anaconda Python exists
if [ -f "/opt/anaconda3/bin/python" ]; then
    echo "✅ Found Anaconda Python"
    /opt/anaconda3/bin/python setup_agent.py "$@"
elif [ -f "$HOME/anaconda3/bin/python" ]; then
    echo "✅ Found Anaconda Python in home directory"
    $HOME/anaconda3/bin/python setup_agent.py "$@"
elif command -v conda &> /dev/null; then
    echo "✅ Found conda, activating base environment"
    conda run -n base python setup_agent.py "$@"
else
    echo "❌ Anaconda Python not found!"
    echo "💡 Please install Anaconda or use the full command:"
    echo "   /path/to/anaconda3/bin/python setup_agent.py \"$@\""
    echo ""
    echo "🔄 Trying system Python as fallback..."
    python3 setup_agent.py "$@"
fi