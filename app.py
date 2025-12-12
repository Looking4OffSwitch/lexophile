"""
Word List API Server

A simple Flask server that provides random vocabulary words from a JSON file.
"""
import json
import os
import sys
import random
from pathlib import Path
from flask import Flask, jsonify
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
PORT = int(os.environ.get("PORT", 8080))
WORD_LIST = os.environ.get("WORD_LIST", "word_list.json")

def find_word_list_file():
    """
    Find the word list file in various potential locations.
    
    Returns:
        Path or None: Path to the word list file if found, otherwise None
    """
    search_paths = [
        Path(__file__).parent / WORD_LIST   # Same directory as app.py
    ]
    
    for path in search_paths:
        if path.exists():
            return path
    
    return None


def validate_word_list_file():
    """
    Validate that the word list file exists and has the correct structure.
    
    Returns:
        Path: Path to the validated word list file
        
    Raises:
        SystemExit: If validation fails
    """
    # Try to find the word list file
    file_path = find_word_list_file()
    
    # Check if file exists
    if not file_path:
        print(f"ERROR: Word list file '{WORD_LIST}' not found in any of the search paths.")
        print("Please make sure the WORD_LIST environment variable is set correctly in the .env file.")
        print(f"Searched in: {[str(p) for p in [Path(__file__).parent, Path(__file__).parent.parent / 'server']]}")
        sys.exit(1)
    
    # Check if file is empty
    if file_path.stat().st_size == 0:
        print(f"ERROR: Word list file '{file_path}' exists but is empty.")
        sys.exit(1)
    
    try:
        # Try to load and validate the JSON structure
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            
        # Validate required structure
        if not isinstance(data, dict):
            print(f"ERROR: Word list file '{file_path}' does not contain a JSON object.")
            sys.exit(1)
            
        if 'words' not in data:
            print(f"ERROR: Word list file '{file_path}' is missing the 'words' object.")
            print("Expected format: { 'metadata': {...}, 'words': {...} }")
            sys.exit(1)
            
        if not isinstance(data['words'], dict) or len(data['words']) == 0:
            print(f"ERROR: Word list file '{file_path}' contains an empty or invalid 'words' object.")
            print("The 'words' object should contain at least one word entry.")
            sys.exit(1)
            
        # Validate at least one word has the required structure
        first_word_key = next(iter(data['words']))
        word_data = data['words'][first_word_key]
        required_fields = ['word', 'definition']
        
        for field in required_fields:
            if field not in word_data:
                print(f"ERROR: Word entries in '{file_path}' are missing required field '{field}'.")
                print(f"Each word entry should contain at least: {required_fields}")
                sys.exit(1)
        
        print(f"Successfully validated word list file: {file_path}")
        print(f"Found {len(data['words'])} words in the word list.")
        return file_path
        
    except json.JSONDecodeError as e:
        print(f"ERROR: Word list file '{file_path}' contains invalid JSON:")
        print(f"  {e}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Failed to validate word list file '{file_path}':")
        print(f"  {e}")
        sys.exit(1)

def read_word_list_data():
    """
    Read and parse the word list file.
    
    Returns:
        dict or None: The parsed JSON data or None if reading fails
    """
    try:
        file_path = validate_word_list_file()
        print(f"Reading word list from: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except Exception as error:
        print(f"Error reading word list file {WORD_LIST}: {error}")
        return None


def get_random_word(words):
    """
    Get a random word from the words dictionary.
    
    Args:
        words (dict): Dictionary of words
        
    Returns:
        dict or None: A random word entry or None if words is invalid
    """
    if not words or not isinstance(words, dict):
        return None
    
    # Get all word keys
    word_keys = list(words.keys())
    if not word_keys:
        return None
    
    # Select a random word key using random.choice (cleaner than randint)
    random_word_key = random.choice(word_keys)
    return words[random_word_key]

@app.route("/health", methods=['GET'])
def health():
    """
    Health check endpoint for monitoring and orchestration systems.

    Returns:
        Flask response: JSON response indicating service health
    """
    return jsonify({"status": "healthy", "service": "word-list-api"}), 200

@app.route("/", methods=['GET'])
def random_word():
    """
    API endpoint that returns a random vocabulary word.
    
    Returns:
        Flask response: JSON response with random word data
    """
    word_list_data = read_word_list_data()

    if not word_list_data or 'words' not in word_list_data:
        return jsonify({"error": "Failed to load vocabulary data"}), 500

    # Check for FIXED_WORD_KEY environment variable
    fixed_word_key = os.environ.get('FIXED_WORD_KEY')
    if fixed_word_key and fixed_word_key in word_list_data['words']:
        word_data = word_list_data['words'][fixed_word_key]
    else:
        word_data = get_random_word(word_list_data['words'])

    if not word_data:
        return jsonify({"error": "No vocabulary words found"}), 404

    # Create the response object
    response_obj = {"word": word_data}
    return jsonify(response_obj)

if __name__ == "__main__":
    try:
        # Validate the word list file before starting the server
        validate_word_list_file()
        print(f"Word List server is running on port {PORT}")
        print(f"Access the API at http://localhost:{PORT}/")
        print(f"Health check available at http://localhost:{PORT}/health")
        app.run(host='0.0.0.0', port=PORT, debug=False)
    except SystemExit:
        print("Server startup aborted due to configuration errors.")
    except Exception as e:
        print(f"ERROR: Failed to start server: {e}")
        sys.exit(1)
