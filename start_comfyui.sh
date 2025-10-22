#!/bin/bash

# Navigate to ComfyUI directory
cd "$(dirname "$0")/ComfyUI"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
elif [ -d "../venv" ]; then
    echo "Activating virtual environment..."
    source ../venv/bin/activate
fi

# Start ComfyUI
echo "Starting ComfyUI..."
python main.py "$@"
