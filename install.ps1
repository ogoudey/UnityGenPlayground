param (
    [Parameter(Mandatory = $true)]
    [string]$AssetProject
)

# Enable strict mode
Set-StrictMode -Version Latest

$BaseDir = "Resources\Asset Projects"
$ProjectDir = Join-Path $BaseDir $AssetProject
$Backend = "Backend"
$GitRepo = "https://github.com/ogoudey/$AssetProject.git"
$VenvDir = Join-Path $Backend ".venv"

# -----------------------------
# 1. Create base directory if needed
# -----------------------------
if (-not (Test-Path $BaseDir)) {
    Write-Host "[INFO] Creating base folder: $BaseDir"
    New-Item -Path $BaseDir -ItemType Directory | Out-Null
}

# -----------------------------
# 2. Create asset project folder
# -----------------------------
if (-not (Test-Path $ProjectDir)) {
    Write-Host "[INFO] Creating project folder: $ProjectDir"
    New-Item -Path $ProjectDir -ItemType Directory | Out-Null
} else {
    Write-Host "[INFO] Project folder already exists: $ProjectDir"
}

# -----------------------------
# 3. Clone repo if folder is empty
# -----------------------------
if ((Get-ChildItem $ProjectDir -Recurse | Measure-Object).Count -eq 0) {
    Write-Host "[INFO] Cloning repo $GitRepo into $ProjectDir"
    git clone $GitRepo $ProjectDir
} else {
    Write-Host "[INFO] Project folder is not empty, skipping clone"
}

# -----------------------------
# 4.0 Activate Python virtual environment
# -----------------------------
if (-not (Test-Path $VenvDir)) {
    Write-Host "[INFO] Virtual environment not found, creating..."
    python3 -m venv $VenvDir
}

$ActivateScript = Join-Path $VenvDir "Scripts\Activate.ps1"
if (Test-Path $ActivateScript) {
    Write-Host "[INFO] Activating virtual environment"
    & $ActivateScript
} else {
    Write-Error "[ERROR] Could not find activate script at $ActivateScript"
    exit 1
}

# Install requirements if present
$Requirements = Join-Path $Backend "requirements.txt"
if (Test-Path $Requirements) {
    Write-Host "[INFO] Installing requirements..."
    pip install --upgrade pip
    pip install -r $Requirements
}

# -----------------------------
# 4.1 Start Flask server
# -----------------------------
Write-Host "[INFO] Starting Flask server..."
Start-Process -FilePath "python" -ArgumentList "flask_server.py" -WorkingDirectory $Backend -WindowStyle Hidden

# -----------------------------
# 5. Wait for Flask to be ready, then open browser
# -----------------------------
Write-Host "[INFO] Waiting for Flask server to be ready..."
while ($true) {
    try {
        Invoke-WebRequest -Uri "http://127.0.0.1:5000" -UseBasicParsing -TimeoutSec 2 | Out-Null
        break
    } catch {
        Start-Sleep -Milliseconds 200
    }
}
Write-Host "[INFO] Flask server is ready!"

Start-Process "http://127.0.0.1:5000"

# -----------------------------
# 6. Check for Unity installation
# -----------------------------
$UNITY_HUB_DIRS = @(
    "$env:LOCALAPPDATA\Programs\Unity\Hub\Editor",
    "C:\Program Files\Unity\Hub\Editor"
)

$UNITY_PATH = $null

foreach ($dir in $UNITY_HUB_DIRS) {
    if (Test-Path $dir) {
	$subdirs = @(Get-ChildItem -Path $dir -Directory)
        if ($subdirs.Count -eq 1) {
            $UNITY_PATH = Join-Path $subdirs[0].FullName "Editor\Unity.exe"
            if (Test-Path $UNITY_PATH) {
                break
            }
        }
    }
}

if (-not $UNITY_PATH) {
    Write-Error "[ERROR] Unity Hub directory not found in expected locations."
    exit 1
}

Write-Host "[INFO] Found Unity at $UNITY_PATH"

# -----------------------------
# 7. Open Unity
# -----------------------------
Write-Host "[INFO] Opening Unity..."
Start-Process -FilePath $UNITY_PATH -ArgumentList "-projectPath `"$ProjectDir`" -upmNoDefaultPackages"

Write-Host "[INFO] Setup complete."

# Run with:
# powershell -ExecutionPolicy Bypass -File bringup.ps1 acrophobia_v1
