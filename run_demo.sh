#!/bin/bash
echo "MCU AI Assistant Demo Launcher"

PROJECT_ROOT=$(pwd)

echo ""
echo "Step 1: Checking Node.js..."

if ! command -v node &> /dev/null
then
    echo "Node.js not found. Please install Node.js first."
    exit 1
fi

node -v

echo ""
echo "Step 2: Checking Python"

if ! command -v python3 &> /dev/null
then
    echo "Python3 not found. Please install Python."
    exit 1
fi

python3 --version

echo ""
echo "Step 3: Checking Ollama"

if ! command -v ollama &> /dev/null
then
    echo "Ollama not installed."
    echo "Install from: https://ollama.com"
    exit 1
fi

echo "Ollama OK"

echo "Step 4: Installing Node dependencies"

npm install

echo "Step 5: Building VS Code extension"

node esbuild.js

if [ ! -f "dist/extension.js" ]; then
    echo "Extension build failed."
    exit 1
fi

echo "Extension build OK"

echo "Step 6: Preparing Python environment"

if [ ! -d ".venv" ]; then
    echo "Creating virtual environment"
    python3 -m venv .venv
fi

source .venv/bin/activate

echo "Step 7: Installing Python dependencies"

python3 -m pip install --upgrade pip
python3 -m pip install -r backend/requirements.txt


echo "Step 8: Checking Ollama model"

if ! ollama list | grep -q mistral; then
    echo "Downloading mistral model"
    ollama pull mistral
fi

echo "Step 9: Starting backend server"

cd backend

echo "Backend running at:"
echo "http://127.0.0.1:8000"
echo ""
echo "Now open VS Code and press F5 to start the extension."

uvicorn app:app --reload --port 8000