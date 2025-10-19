#!/bin/bash
# AI Browser Agent Runner Script

PYTHON_PATH="/opt/anaconda3/bin/python"
AGENT_SCRIPT="simple_agent.py"

if [ $# -eq 0 ]; then
    echo "=== AI Browser Agent Runner ==="
    echo "Usage: ./run_agent.sh \"<task description>\""
    echo ""
    $PYTHON_PATH $AGENT_SCRIPT
else
    echo "Running AI Browser Agent..."
    echo "Task: $1"
    echo ""
    $PYTHON_PATH $AGENT_SCRIPT "$1"
fi