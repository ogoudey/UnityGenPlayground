#!/bin/bash
# run_correspondent.sh
# Usage: ./run_correspondent.sh arg1 arg2 arg3 arg4

PYTHON_SCRIPT="unity_correspondent.py"

cd ../../../Backend

. .venv/bin/activate

pip install requirements.txt

export MODEL="o4-mini"

export OPENAI_API_KEY="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"

echo "$PYTHON_SCRIPT" "$@" "from" "$(pwd)"

# Check that the script exists
if [ ! -f "$PYTHON_SCRIPT" ]; then
  echo "❌ unity_correspondent.py not found."
  exit 1
fi

echo "▶️ Running unity_correspondent.py with args: $@"
python3 "$PYTHON_SCRIPT" "$@"