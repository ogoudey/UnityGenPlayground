#!/bin/bash




# 1. make asset projects folder if it doesnt already exist (../Resources/Asset Projects)

# 2. make <asset_project> (takes argument - let's call it `acrophobia_v1` and its in ../Resources/Asset Projects/)
# 3. clone <asset_project> (git clone https://github.com/ogoudey/acrophobia_v1)

# 4. start server 
# 5. open browser gui
# 6. open Unity


### Attempt 1

set -euo pipefail
IFS=$'\n\t'

# -----------------------------
# Check for asset project argument
# -----------------------------
if [ $# -lt 1 ]; then
    echo "Usage: $0 <asset_project_name>"
    exit 1
fi

ASSET_PROJECT="$1"
BASE_DIR="Resources/Asset Projects"
PROJECT_DIR="$BASE_DIR/$ASSET_PROJECT"
BACKEND="Backend"
GIT_REPO="https://github.com/ogoudey/$ASSET_PROJECT.git"

# -----------------------------
# 1. Make Asset Projects folder
# -----------------------------
if [ ! -d "$BASE_DIR" ]; then
    echo "[INFO] Creating base folder: $BASE_DIR"
    mkdir -p "$BASE_DIR"
fi

# -----------------------------
# 2. Make asset project folder
# -----------------------------
if [ ! -d "$PROJECT_DIR" ]; then
    echo "[INFO] Creating project folder: $PROJECT_DIR"
    mkdir -p "$PROJECT_DIR"
else
    echo "[INFO] Project folder already exists: $PROJECT_DIR"
fi

# -----------------------------
# 3. Clone repo if folder empty
# -----------------------------
if [ -z "$(ls -A "$PROJECT_DIR")" ]; then
    echo "[INFO] Cloning repo $GIT_REPO into $PROJECT_DIR"
    git clone "$GIT_REPO" "$PROJECT_DIR"
else
    echo "[INFO] Project folder is not empty, skipping clone"
fi

# -----------------------------
# 4.0 Activate Python virtual environment
# -----------------------------
VENV_DIR="$BACKEND/.venv"
if [ -d "$VENV_DIR" ]; then
    echo "[INFO] Activating virtual environment: $VENV_DIR"
    source "$VENV_DIR/bin/activate"
else
    echo "[INFO] Virtual environment not found, creating..."
    python3 -m venv "$VENV_DIR"
    source "$VENV_DIR/bin/activate"
    echo "[INFO] Installing requirements (if requirements.txt exists)"
    if [ -f "$BACKEND/requirements.txt" ]; then
        pip install --upgrade pip
        pip install -r "$BACKEND/requirements.txt"
    fi
fi


# -----------------------------
# 4.1 Start Flask server
# -----------------------------
echo "[INFO] Starting Flask server..."
(
    cd "$BACKEND"
    # Assumes your Flask app is called app.py and uses default port 5000
    # Run in background so script continues
    python3 flask_server.py &
    FLASK_PID=$!
    echo "[INFO] Flask server started with PID $FLASK_PID"
)

# -----------------------------
# 5. Open browser GUI
# -----------------------------

# Wait until Flask responds
echo "[INFO] Waiting for Flask server to be ready..."
until curl -s http://127.0.0.1:5000 >/dev/null 2>&1; do
    sleep 0.2
done
echo "[INFO] Flask server is ready!"

echo "[INFO] Opening browser GUI..."
# Adjust URL if your server is different
xdg-open "http://127.0.0.1:5000" >/dev/null 2>&1 || open "http://127.0.0.1:5000"

# -----------------------------
# 6. Check for Unity
# -----------------------------


# Unity Hub editor folder
UNITY_HUB_DIR="$HOME/Unity/Hub/Editor"

# There should be exactly one subfolder
UNITY_SUBDIR=$(ls "$UNITY_HUB_DIR")
UNITY_PATH="$UNITY_HUB_DIR/$UNITY_SUBDIR/Editor/Unity"

# Verify it exists and is executable
if [ ! -x "$UNITY_PATH" ]; then
    echo "[ERROR] Unity executable not found at $UNITY_PATH"
    exit 1
fi

echo "[INFO] Found Unity at $UNITY_PATH"


# -----------------------------
# 7. Open Unity
# -----------------------------


echo "[INFO] Opening Unity..."


if [ -x "$UNITY_PATH" ]; then
    echo "[INFO] Opening $PROJECT_DIR..."
    "$UNITY_PATH" -projectPath -upmNoDefaultPackages "$PROJECT_DIR" &
else
    echo "[WARN] Unity is not an executable at $UNITY_PATH. Please edit this script."
fi

echo "[INFO] Setup complete."