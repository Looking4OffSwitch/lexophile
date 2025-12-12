# Lexophile - AI-Powered Word Information Processor

An intelligent English word information processor that uses Perplexity AI to generate comprehensive linguistic data for vocabulary words. Built with robust error handling, intelligent rate limiting, and incremental data persistence.

## 🌟 Features

### 🧠 **Intelligent Processing**
- **Comprehensive Word Data**: Extracts definition, part of speech, phonetic spelling, synonyms, antonyms, etymology, and contextual example sentences
- **Smart Reprocessing**: Automatically retries words with missing or incomplete data
- **Quality Control**: Enforces strict JSON formatting to ensure data consistency

### ⚡ **Robust Rate Limiting**
- **Exponential Backoff**: Automatically handles API rate limits with intelligent retry logic (1s → 2s → 4s → 8s → 16s, max 5 minutes)
- **Jitter Protection**: Adds 10-30% randomness to prevent thundering herd effects
- **Graceful Recovery**: Continues processing entire word list regardless of rate limit encounters

### 💾 **Data Integrity**
- **Incremental Saves**: Saves progress after each word to prevent data loss
- **Complete Dataset**: Records all words, including failed attempts with detailed error reasons
- **Smart Skipping**: Avoids reprocessing words that already have complete data
- **Metadata Tracking**: Includes processing timestamps, source information, and statistics

### 🔍 **Advanced Logging**
- **Dual Logging**: Console output + detailed log file (`lexophile.log`)
- **Debug Mode**: Optional detailed API response logging for troubleshooting
- **Progress Tracking**: Real-time counters for new, reprocessed, skipped, and failed words
- **Error Classification**: Categorizes failure types for easier debugging

## 📋 Data Structure

Each word entry contains:

```json
{
  "word": "abase",
  "definition": "to reduce or lower, as in rank, office, reputation, or estimation; humble; degrade",
  "part_of_speech": "verb",
  "synonyms": ["humble", "degrade"],
  "antonyms": ["elevate", "honor"],
  "phonetic_spelling": "uh-beys",
  "first_known_usage": "15th century",
  "example_sentence": "The manager's harsh criticism was meant to motivate the team, but instead served only to abase the employees and lower their morale.",
  "processing_status": "success",
  "error_reason": null,
  "processed_date": "2025-07-14T08:19:40.123Z"
}
```

### Failed Entry Example:
```json
{
  "word": "problematic_word",
  "definition": null,
  "part_of_speech": null,
  "synonyms": [],
  "antonyms": [],
  "phonetic_spelling": null,
  "first_known_usage": null,
  "example_sentence": null,
  "processing_status": "failed",
  "error_reason": "API returned empty response",
  "processed_date": "2025-07-14T08:19:40.123Z"
}
```

## 🚀 Installation

### Prerequisites
- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager (recommended)

### Setup
```bash
# Clone the repository
git clone <repository-url>
cd lexophile

# Create virtual environment and install dependencies
uv venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -r requirements.txt

# Or install individual dependency
uv pip install pyplexityai
```

### API Key Configuration
1. Get your Perplexity AI API key from [https://www.perplexity.ai/settings/api](https://www.perplexity.ai/settings/api)
2. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
3. Edit `.env` and add your API key:
   ```bash
   PERPLEXITY_API_KEY=pplx-your-actual-api-key-here
   ```

**Important**: Never commit your `.env` file to the repository - it contains sensitive API keys!

## 📖 Usage

### Basic Usage
```bash
# Process all words with default settings
python lexophile.py

# Show help message
python lexophile.py --help
```

### Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--word-list PATH` | Path to word list file | `word_list_main.txt` |
| `--output PATH` | Output JSON file path | `lexophile.json` |
| `--debug` | Enable debug logging | `False` |
| `--help` | Show help message | - |

### Examples

```bash
# Use custom word list and output file
python lexophile.py --word-list custom_words.txt --output my_data.json

# Enable debug logging for troubleshooting
python lexophile.py --debug

# Process with all options
python lexophile.py --word-list words.txt --output data.json --debug
```

## 📁 File Structure

```
lexophile/
├── lexophile.py                     # Main processing script
├── word_list_main.txt               # Input word list (one word per line)
├── .env.example                     # Environment variables template
├── .env                             # Your API keys (create from .env.example)
├── lexophile.json                   # Output JSON data file
├── lexophile.log                    # Detailed processing log
├── pyproject.toml                   # Project dependencies
├── .gitignore                       # Git ignore rules
└── README.md                        # This file
```

## 🔧 How It Works

### 1. **Word List Processing**
- Loads words from input text file (one word per line)
- Checks existing JSON for previously processed words
- Identifies words needing processing or reprocessing

### 2. **AI Query Generation**
- Creates structured prompts enforcing strict JSON response format
- Includes detailed requirements and examples for consistent output
- Optimized to minimize parsing errors

### 3. **Rate Limit Management**
- Detects rate limit errors (429, "rate limit", "too many requests", "quota")
- Implements exponential backoff with jitter: 1s → 2s → 4s → 8s → 16s
- Continues processing after rate limit recovery

### 4. **Data Validation & Storage**
- Validates JSON responses and extracts word information
- Records successful entries with processing metadata
- Creates placeholder entries for failed words with error details
- Saves incrementally to prevent data loss

### 5. **Smart Recovery**
- Resumes processing from where it left off
- Automatically retries incomplete or failed words
- Maintains processing statistics and detailed logs

## 📊 Output Format

The output JSON file contains:

### Metadata Section
```json
{
  "metadata": {
    "total_words": 228,
    "created_date": "2025-07-14T08:00:00.000Z",
    "last_updated": "2025-07-14T08:30:00.000Z",
    "source": "Perplexity AI via lexophile word processor",
    "word_list_file": "word_list_main.txt"
  },
  "words": {
    // ... word entries
  }
}
```

### Processing Statistics
The script provides real-time progress updates:
```
[1/228] Processing new word: 'abase'
[2/228] Skipping 'abnegate' - already complete
[3/228] Reprocessing 'abrogate' - missing/incomplete data
Processing complete. New: 150, Reprocessed: 12, Skipped: 60, Errors: 6
```

## 🛠️ Error Handling

The system gracefully handles various error conditions:

### API Errors
- **Rate Limits**: Automatic exponential backoff retry
- **Connection Issues**: Retry with increasing delays
- **Invalid Responses**: Detailed logging with response analysis

### Data Errors
- **JSON Parsing Failures**: Records word with error details
- **Missing Fields**: Identifies incomplete data for reprocessing
- **Malformed Responses**: Categorizes error types for debugging

### File System Errors
- **Missing Input Files**: Clear error messages with suggestions
- **Write Permissions**: Handles file access issues gracefully

## 🔍 Troubleshooting

### Enable Debug Logging
```bash
python lexophile.py --debug
```

### Common Issues

**JSON Parsing Errors**: Use `--debug` to see raw API responses
```
JSON parsing failed for 'word': Expecting value: line 1 column 1 (char 0)
Response length: 0 characters
Response is completely empty for 'word'
```

**Rate Limit Warnings**: Normal behavior, script will automatically retry
```
Rate limit hit. Waiting 2.3 seconds before retry 2
```

**Processing Interruptions**: Script resumes from last saved state
```
Loaded existing data with 150 words
```

## 📈 Performance Considerations

- **Processing Speed**: ~1-2 seconds per word (including API delays)
- **Memory Usage**: Minimal - processes one word at a time
- **Storage**: ~1-2KB per word entry in JSON format
- **Resumability**: Can be safely interrupted and resumed

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Perplexity AI** for providing the language model API
- **Python Community** for excellent libraries and tools
- **Contributors** who help improve the project

---

**Note**: This tool requires a valid Perplexity AI API key and is subject to their terms of service and rate limits.