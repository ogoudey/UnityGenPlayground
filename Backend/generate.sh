#!/bin/bash
# run_correspondent.sh
# Usage: ./run_correspondent.sh arg1 arg2 arg3 arg4

PYTHON_SCRIPT="/unity_correspondent.py"

# Check that the script exists
if [ ! -f "$PYTHON_SCRIPT" ]; then
  echo "❌ unity_correspondent.py not found."
  exit 1
fi

echo "▶️ Running unity_correspondent.py with args: $@"
python3 "$PYTHON_SCRIPT" "$@"