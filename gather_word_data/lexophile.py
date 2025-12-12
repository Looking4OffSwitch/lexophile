from pyplexityai import PerplexityClient
import json
import time
import logging
import argparse
from datetime import datetime
import os
import random
from dotenv import load_dotenv

def create_prompt(word: str) -> str:
    """
    Create a prompt for the Perplexity AI client to gather information about a word.
    
    Args:
        word (str): The English word to gather information about.
        
    Returns:
        str: The formatted prompt string.
    """
    PROMPT = """You must provide information for the English word "{word}" in STRICT JSON format.

CRITICAL: Your response must be ONLY valid JSON. Do not include any explanatory text, markdown formatting, code blocks, or additional commentary before or after the JSON.

Required JSON structure (copy this exact format):
{{
  "word": "{word}",
  "definition": "string - clear definition of the word",
  "part_of_speech": "string - primary part of speech (noun, verb, adjective, etc.)",
  "synonyms": ["string1", "string2"] - array with at most 2 synonyms (use empty array [] if none),
  "antonyms": ["string1", "string2"] - array with at most 2 antonyms (use empty array [] if none),
  "phonetic_spelling": "string - simple phonetic respelling (e.g. 'uh-beys' for 'abase')",
  "first_known_usage": "string - century when first used (e.g. '14th century') or null if unknown",
  "example_sentence": "string - sentence demonstrating clear word usage and meaning"
}}

REQUIREMENTS:
- Example sentence MUST demonstrate the word's meaning clearly and unambiguously, in context
- Phonetic spelling should be simple respelling format (like 'nooz-pey-per' for 'newspaper')
- Use null for unknown fields, empty arrays [] for missing synonyms/antonyms
- Response must be parseable by JSON.parse() - no syntax errors allowed
- No text outside the JSON object

Generate the JSON for "{word}" now:"""

    return PROMPT.format(word=word)

def setup_logging(debug=False):
    """Setup logging configuration."""
    log_level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('lexophile.log')
        ]
    )

def load_existing_data(json_file_path):
    """Load existing JSON data if file exists."""
    if os.path.exists(json_file_path):
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # Ensure metadata structure is correct
                if "metadata" not in data:
                    data["metadata"] = {}
                
                # Add missing metadata fields if needed
                metadata_fields = {
                    "total_words": len(data.get("words", {})),
                    "created_date": data.get("metadata", {}).get("created_date", datetime.now().isoformat()),
                    "last_updated": datetime.now().isoformat(),
                    "source": "Perplexity AI via lexophile word processor",
                    "word_list_file": "word_list_main.txt",
                    "longest_definition": None,
                    "longest_example_sentence": None
                }
                
                # Update any missing fields
                for key, default_value in metadata_fields.items():
                    if key not in data.get("metadata", {}):
                        data["metadata"][key] = default_value
                
                logging.info(f"Loaded existing data with {len(data.get('words', {}))} words")
                return data
        except (json.JSONDecodeError, Exception) as e:
            logging.error(f"Error loading existing JSON file: {e}")
            return None
    return None

def create_metadata(word_count=0):
    """Create metadata for the JSON file."""
    return {
        "metadata": {
            "total_words": word_count,
            "created_date": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "source": "Perplexity AI via lexophile word processor",
            "word_list_file": "word_list_main.txt",
            "longest_definition": None,
            "longest_example_sentence": None
        },
        "words": {}
    }

def create_empty_word_entry(word, error_reason=None):
    """Create an empty word entry with null/empty values for failed processing."""
    return {
        "word": word,
        "definition": None,
        "part_of_speech": None,
        "synonyms": [],
        "antonyms": [],
        "phonetic_spelling": None,
        "first_known_usage": None,
        "example_sentence": None,
        "processing_status": "failed",
        "error_reason": error_reason,
        "processed_date": datetime.now().isoformat()
    }

def has_complete_data(word_entry):
    """
    Check if a word entry has all required fields populated.
    
    Args:
        word_entry (dict): The word entry to check
        
    Returns:
        bool: True if all required fields are present and not empty/null
    """
    if not word_entry:
        return False
    
    # Check if processing was successful
    if word_entry.get("processing_status") == "failed":
        return False
    
    required_fields = [
        "definition",
        "part_of_speech", 
        "phonetic_spelling",
        "example_sentence"
    ]
    
    # Check each required field
    for field in required_fields:
        value = word_entry.get(field)
        if value is None or value == "" or (isinstance(value, list) and len(value) == 0):
            return False
    
    # Synonyms and antonyms can be empty (some words don't have them)
    # first_known_usage can be empty (not always available)
    
    return True

def needs_reprocessing(word_entry):
    """
    Determine if a word entry needs to be reprocessed due to missing data.
    
    Args:
        word_entry (dict): The word entry to check
        
    Returns:
        bool: True if the word should be reprocessed
    """
    return not has_complete_data(word_entry)

def save_data_incrementally(data, json_file_path):
    """Save data to JSON file incrementally."""
    try:
        # Update metadata
        data["metadata"]["last_updated"] = datetime.now().isoformat()
        data["metadata"]["total_words"] = len(data["words"])
        
        # Calculate longest definition and example sentence
        longest_def_word = None
        longest_def_len = 0
        longest_ex_word = None
        longest_ex_len = 0
        
        for word, entry in data["words"].items():
            # Skip entries with failed processing
            if entry.get("processing_status") == "failed":
                continue
                
            definition = entry.get("definition")
            example = entry.get("example_sentence")
            
            if definition and isinstance(definition, str) and len(definition) > longest_def_len:
                longest_def_word = word
                longest_def_len = len(definition)
                
            if example and isinstance(example, str) and len(example) > longest_ex_len:
                longest_ex_word = word
                longest_ex_len = len(example)
                
        # Update metadata with the words that have the longest definition and example
        data["metadata"]["longest_definition"] = longest_def_word
        data["metadata"]["longest_example_sentence"] = longest_ex_word
        
        # Add debug logging for the longest values
        if longest_def_word:
            logging.debug(f"Longest definition: '{longest_def_word}' ({longest_def_len} characters)")
        if longest_ex_word:
            logging.debug(f"Longest example sentence: '{longest_ex_word}' ({longest_ex_len} characters)")
        
        with open(json_file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logging.info(f"Data saved to {json_file_path}")
    except Exception as e:
        logging.error(f"Error saving data to {json_file_path}: {e}")

def exponential_backoff_request(client, prompt, max_retries=5):
    """
    Make API request with exponential backoff retry logic.
    
    Args:
        client: Perplexity AI client
        prompt: The prompt to send
        max_retries: Maximum number of retry attempts
        
    Returns:
        API response or None if all retries failed
    """
    base_delay = 1  # Start with 1 second
    max_delay = 300  # Cap at 5 minutes
    
    for attempt in range(max_retries + 1):
        try:
            logging.info(f"API request attempt {attempt + 1}/{max_retries + 1}")
            result = client.search_sync(prompt)
            logging.info("API request successful")
            return result
            
        except Exception as e:
            error_msg = str(e).lower()
            
            # Check if it's a rate limit error
            if any(indicator in error_msg for indicator in ['rate limit', 'too many requests', '429', 'quota']):
                if attempt < max_retries:
                    # Calculate exponential backoff delay with jitter
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    jitter = random.uniform(0.1, 0.3) * delay  # Add 10-30% jitter
                    total_delay = delay + jitter
                    
                    logging.warning(f"Rate limit hit. Waiting {total_delay:.1f} seconds before retry {attempt + 2}")
                    time.sleep(total_delay)
                    continue
                else:
                    logging.error(f"Rate limit exceeded after {max_retries + 1} attempts")
                    raise
            else:
                # Non-rate-limit error, don't retry
                logging.error(f"API request failed with non-rate-limit error: {e}")
                raise
    
    return None

def process_word_list(word_list_file, json_file_path, client):
    """Process all words from the word list file with exponential backoff."""
    
    # Load existing data or create new structure
    data = load_existing_data(json_file_path)
    if data is None:
        data = create_metadata()
        logging.info("Created new data structure")
    
    # Load word list
    try:
        with open(word_list_file, 'r', encoding='utf-8') as f:
            words = [line.strip() for line in f if line.strip()]
        logging.info(f"Loaded {len(words)} words from {word_list_file}")
    except Exception as e:
        logging.error(f"Error loading word list from {word_list_file}: {e}")
        return
    
    # Process each word
    processed_count = 0
    skipped_count = 0
    reprocessed_count = 0
    error_count = 0
    
    for i, word in enumerate(words, 1):
        # Check if word already exists in JSON
        if word in data["words"]:
            existing_entry = data["words"][word]
            
            # Check if existing entry has complete data
            if has_complete_data(existing_entry):
                logging.info(f"[{i}/{len(words)}] Skipping '{word}' - already complete")
                skipped_count += 1
                continue
            else:
                logging.info(f"[{i}/{len(words)}] Reprocessing '{word}' - missing/incomplete data")
                # Will continue to process this word
                is_reprocessing = True
        else:
            logging.info(f"[{i}/{len(words)}] Processing new word: '{word}'")
            is_reprocessing = False
        
        try:
            # Create prompt and get response with exponential backoff
            prompt = create_prompt(word)
            result = exponential_backoff_request(client, prompt)
            
            if result is None:
                logging.error(f"Failed to get response for '{word}' after all retries")
                # Record failed word with empty values
                empty_entry = create_empty_word_entry(word, "API request failed after all retries")
                data["words"][word] = empty_entry
                save_data_incrementally(data, json_file_path)
                error_count += 1
                continue
            
            # Parse JSON response
            try:
                raw_response = result["text"]
                logging.debug(f"Raw response length for '{word}': {len(raw_response)} characters")
                
                # Log first and last 200 characters to help debug
                if len(raw_response) > 400:
                    logging.debug(f"Response preview for '{word}': START[{raw_response[:200]}] ... END[{raw_response[-200:]}]")
                else:
                    logging.debug(f"Full response for '{word}': {raw_response}")
                
                word_data = json.loads(raw_response)
                # Add processing metadata to successful entries
                word_data["processing_status"] = "success"
                word_data["processed_date"] = datetime.now().isoformat()
                word_data["error_reason"] = None
                
                data["words"][word] = word_data
                
                if is_reprocessing:
                    reprocessed_count += 1
                    logging.info(f"Successfully reprocessed '{word}' ({reprocessed_count} reprocessed)")
                else:
                    processed_count += 1
                    logging.info(f"Successfully processed '{word}' ({processed_count} completed)")
                
                # Save data incrementally after each word
                save_data_incrementally(data, json_file_path)
                
                # Small delay between successful requests to be respectful
                time.sleep(1)
                
            except json.JSONDecodeError as e:
                raw_response = result["text"]
                logging.error(f"JSON parsing failed for '{word}': {e}")
                logging.error(f"Response length: {len(raw_response)} characters")
                logging.error(f"Response type: {type(raw_response)}")
                
                # Show different amounts of response based on length
                if len(raw_response) == 0:
                    logging.error(f"Response is completely empty for '{word}'")
                elif len(raw_response) < 100:
                    logging.error(f"Full response for '{word}': '{raw_response}'")
                elif len(raw_response) < 500:
                    logging.error(f"Full response for '{word}': {raw_response}")
                else:
                    logging.error(f"Response preview for '{word}' (first 300 chars): {raw_response[:300]}")
                    logging.error(f"Response preview for '{word}' (last 300 chars): {raw_response[-300:]}")
                
                # Determine error reason based on response content
                error_reason = "JSON parsing failed"
                if raw_response.strip().startswith("I'm sorry") or raw_response.strip().startswith("I cannot"):
                    error_reason = "API refused to process word"
                    logging.error(f"API refused to process '{word}' - response appears to be a refusal message")
                elif raw_response.strip().startswith("Error") or "error" in raw_response.lower():
                    error_reason = "API returned error message"
                    logging.error(f"API returned an error for '{word}' - response contains error message")
                elif not raw_response.strip():
                    error_reason = "API returned empty response"
                    logging.error(f"API returned empty response for '{word}'")
                else:
                    error_reason = "API returned non-JSON response"
                    logging.error(f"API returned non-JSON response for '{word}' - response format unexpected")
                
                # Record failed word with empty values
                empty_entry = create_empty_word_entry(word, error_reason)
                data["words"][word] = empty_entry
                save_data_incrementally(data, json_file_path)
                error_count += 1
                continue
                
        except Exception as e:
            logging.error(f"Error processing word '{word}': {e}")
            # Record failed word with empty values
            empty_entry = create_empty_word_entry(word, f"Unexpected error: {str(e)}")
            data["words"][word] = empty_entry
            save_data_incrementally(data, json_file_path)
            error_count += 1
            continue
    
    logging.info(f"Processing complete. New: {processed_count}, Reprocessed: {reprocessed_count}, Skipped: {skipped_count}, Errors: {error_count}")
    return data

def update_existing_json(json_file_path):
    """
    Update an existing JSON file to include the new metadata fields.
    Run this function once to update older JSON files.
    """
    if not os.path.exists(json_file_path):
        logging.info(f"No existing JSON file at {json_file_path} to update")
        return False
    
    try:
        # Load the existing JSON
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logging.info(f"Loaded existing JSON file for update: {json_file_path}")
        
        # Calculate and update the longest fields
        save_data_incrementally(data, json_file_path)
        
        logging.info(f"Successfully updated metadata in {json_file_path}")
        return True
    except Exception as e:
        logging.error(f"Error updating existing JSON file: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(
        description="Process word list using Perplexity AI with intelligent exponential backoff rate limiting",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Features:
  • Intelligent exponential backoff handles rate limits automatically
  • Incremental JSON saves prevent data loss on failures  
  • Skip processing for words already in output file
  • Comprehensive logging to console and lexophile.log
  • Metadata tracking (word count, timestamps, source info)

Examples:
  python lexophile.py                           # Process all words with defaults
  python lexophile.py --help                    # Show this help message
  python lexophile.py --debug                   # Enable debug logging for troubleshooting
  python lexophile.py --word-list custom.txt    # Use custom word list
  python lexophile.py --output my_words.json    # Custom output file
  python lexophile.py --word-list words.txt --output data.json --debug  # All options

Rate Limiting:
  The script automatically handles API rate limits using exponential backoff:
  • 1s → 2s → 4s → 8s → 16s delays (max 5 minutes)
  • Adds 10-30% jitter to prevent thundering herd effects
  • Retries up to 5 times for rate limit errors
  • Continues processing entire word list regardless of rate limits
        """
    )
    
    parser.add_argument(
        '--word-list',
        default='word_list_main.txt',
        help='Path to word list file (default: word_list_main.txt)'
    )
    
    parser.add_argument(
        '--output',
        default='lexophile.json',
        help='Output JSON file path (default: lexophile.json)'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging to see API response details'
    )
    
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Setup logging
    setup_logging(debug=args.debug)
    logging.info("Starting Perplexity AI word processor with exponential backoff")
    logging.info(f"Word list: {args.word_list}")
    logging.info(f"Output file: {args.output}")
    if args.debug:
        logging.info("Debug logging enabled - API responses will be logged")
    
    # Get API key from environment
    api_key = os.getenv("PERPLEXITY_API_KEY")
    if not api_key:
        logging.error("PERPLEXITY_API_KEY not found in environment variables")
        logging.error("Please create a .env file with your API key or set the environment variable")
        logging.error("Example: PERPLEXITY_API_KEY=pplx-your-api-key-here")
        return
    
    # Check if we should update an existing JSON file's metadata
    if os.path.exists(args.output):
        logging.info(f"Found existing JSON file: {args.output}")
        logging.info("Ensuring metadata fields are up-to-date...")
        update_existing_json(args.output)
    
    # Initialize Perplexity client
    try:
        with PerplexityClient(api_key) as client:
            process_word_list(args.word_list, args.output, client)
    except Exception as e:
        logging.error(f"Error initializing Perplexity client: {e}")
        if "authentication" in str(e).lower() or "unauthorized" in str(e).lower():
            logging.error("This may be due to an invalid API key. Please check your PERPLEXITY_API_KEY in the .env file")

if __name__ == "__main__":
    main()