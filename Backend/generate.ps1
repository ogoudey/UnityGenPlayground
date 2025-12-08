$PYTHON_SCRIPT = "unity_correspondent.py"

# Navigate to the Backend directory
Set-Location ..\..\..\Backend

# Activate the Python virtual environment
$venvPath = ".\.venv\Scripts\Activate.ps1"
if (Test-Path $venvPath) {
    & $venvPath
} else {
    Write-Host "❌ Virtual environment not found at $venvPath"
    exit 1
}

# Set environment variables
$env:MODEL = "o4-mini"
$env:UNITY_VERSION = "6"

# ⚠️ Replace this with your actual key, saves Olin $0.01
$env:OPENAI_API_KEY = "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"

Write-Host "$PYTHON_SCRIPT" $args "from" (Get-Location)

# Check that the script exists
if (-Not (Test-Path $PYTHON_SCRIPT)) {
    Write-Host "❌ unity_correspondent.py not found."
    exit 1
}

Write-Host "▶️ Running unity_correspondent.py with args:" $args
python $PYTHON_SCRIPT @args
