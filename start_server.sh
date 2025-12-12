#!/bin/sh
set -e

echo "=== Starting Word List Python Server ==="

# Navigate to the server directory
cd "$(dirname "$0")"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Virtual environment not found. Running setup first..."
    chmod +x ./setup.sh
    ./setup.sh
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Configuration file .env not found. Creating from template..."
    cp .env.example .env
    echo "Please edit the .env file to configure your server settings."
    echo "Press any key to continue or Ctrl+C to abort..."
    read -r dummy
fi

# Activate the virtual environment
echo "Activating virtual environment..."
. .venv/bin/activate

# Check if word_list.json exists
if [ ! -f "word_list.json" ] && [ ! -f "../server/word_list.json" ]; then
    echo "WARNING: Could not find word_list.json in the current directory or ../server/"
    echo "Make sure the WORD_LIST environment variable in .env points to a valid file."
fi

# Start the server
echo "Starting the server..."
python app.py
