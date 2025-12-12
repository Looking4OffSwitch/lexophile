#!/bin/sh
set -e

echo "=== Word List Python Server Setup ==="

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "Error: uv is required but not installed."
    echo "Please install uv: https://github.com/astral-sh/uv"
    echo "Quick install: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Display Python version
python_version=$(python3 --version)
echo "Using $python_version"

# Create a virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    uv venv
else
    echo "Virtual environment already exists."
fi

# Activate the virtual environment
echo "Activating virtual environment..."
. .venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
uv pip install -e .

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating default .env file from template..."
    cp .env.example .env
    echo "Please edit the .env file to configure your server settings."
fi

echo "=== Setup completed successfully! ==="
echo "You can now start the server with './start_server.sh' or 'python app.py'"
