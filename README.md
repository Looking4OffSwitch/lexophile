# Lexophile

A simple API server that provides random vocabulary words for the trmnl plugin.

## Requirements

- Python 3.12+
- uv (fast Python package installer and resolver)
- Docker (for production deployment)

### Installing uv

```bash
# macOS and Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or via pip (if you have it)
pip install uv
```

## Quick Start

```bash
# 1. Set up the server
./setup.sh

# 2. Start the server
./start_server.sh
```

## Setup

The setup script will automatically:

1. Create a Python virtual environment
2. Install all required dependencies
3. Create a default configuration file

```bash
./setup.sh
```

For manual setup:

```bash
# Create a virtual environment
uv venv

# Activate the virtual environment
source .venv/bin/activate  # On Linux/Mac
# or
.venv\Scripts\activate     # On Windows

# Install dependencies
uv sync

# Create configuration file
cp .env.example .env
```

## Running the Server

After setup, you can start the server:

```bash
# Using the start script (recommended)
./start_server.sh
```

Or manually:

```bash
# Activate the virtual environment
source .venv/bin/activate  # On Linux/Mac
# or
.venv\Scripts\activate     # On Windows

# Run the server
python app.py
```

The server will start on port 8080 by default. You can access the API at:
- http://localhost:8080/ - Get a random vocabulary word
- http://localhost:8080/health - Health check endpoint

## Configuration

The server is configured using environment variables. To configure:

1. Copy the example file: `cp .env.example .env`
2. Edit `.env` with your settings (optional, defaults work for most cases)

Available environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `PORT` | The port number for the server | `8080` |
| `WORD_LIST` | Path to the word list JSON file | `word_list.json` |
| `FIXED_WORD_KEY` | (Optional) If set, always returns this specific word | - |
| `WORKERS` | Number of Gunicorn workers (production only) | `1` |

## Word List JSON Format

The word list file should be a JSON file with the following structure:

```json
{
  "metadata": {
    "total_words": 100,
    "created_date": "2025-07-14T08:31:43.829973",
    "last_updated": "2025-07-15T11:05:47.566089",
    "source": "Source information",
    "word_list_file": "original_file.txt",
    "longest_definition": "word_with_longest_def",
    "longest_example_sentence": "word_with_longest_example"
  },
  "words": {
    "example1": {
      "word": "example1",
      "definition": "The definition of the word",
      "part_of_speech": "noun",
      "synonyms": ["synonym1", "synonym2"],
      "antonyms": ["antonym1", "antonym2"],
      "phonetic_spelling": "ih-g-zam-pul",
      "first_known_usage": "19th century",
      "example_sentence": "An example sentence using the word."
    }
  }
}
```

### Required Structure

The server validates the word list file at startup and will fail to start if:

1. The word list file cannot be found
2. The file exists but is empty
3. The file contains invalid JSON
4. The JSON does not contain a `words` object
5. The `words` object is empty or not a dictionary
6. Word entries don't contain required fields (`word`, `definition`)

## API Endpoints

### `GET /`

Returns a random vocabulary word from the word list.

Response:
```json
{
  "word": {
    "word": "example",
    "definition": "Something that serves as a pattern",
    "part_of_speech": "noun",
    "synonyms": ["model", "sample"],
    "antonyms": ["counterexample"],
    "phonetic_spelling": "ig-zam-puhl",
    "example_sentence": "This is an example of how to use the word."
  }
}
```

### `GET /health`

Health check endpoint for monitoring and orchestration systems like Coolify.

Response:
```json
{
  "status": "healthy",
  "service": "word-list-api"
}
```

## Production Deployment with Coolify

This application is containerized and ready for deployment on any Docker-based platform, including Coolify.

### Docker (local) quick commands

```bash
# Build the image
docker build -t lexophile-test .

# Run the container (exposes http://localhost:8080)
docker run --rm -d -p 8080:8080 --name lexophile-test-run lexophile-test

# (Optional) set worker count
# docker run --rm -d -p 8080:8080 -e WORKERS=2 --name lexophile-test-run lexophile-test

# Check health
curl http://localhost:8080/health

# Stop the container
docker stop lexophile-test-run
```

### Prerequisites

- Coolify instance running on your VPS
- Git repository with this code
- `word_list.json` file in the repository

### Deployment Steps

1. **Connect Your Repository**
   - In Coolify, create a new application
   - Connect your Git repository (GitHub, GitLab, etc.)
   - Select the main/master branch

2. **Configure Build Settings**
   - Build Type: Dockerfile
   - Dockerfile Location: `./Dockerfile` (auto-detected)
   - Port: `8080` (Coolify will auto-detect from Dockerfile EXPOSE)

3. **Set Environment Variables**
   - In Coolify's application settings, add environment variables:
     ```
     PORT=8080
     WORD_LIST=word_list.json
     WORKERS=1
     ```
   - **Note**: 1 worker is sufficient for typical usage (~100s requests/sec)
   - Only increase `WORKERS` if you experience high traffic: use `(2 × CPU cores) + 1`

4. **Configure Health Checks**
   - Health Check Path: `/health`
   - Health Check Interval: 30s
   - Health Check Timeout: 10s

5. **Deploy**
   - Click "Deploy" in Coolify
   - Coolify will build the Docker image and start the container
   - Monitor the deployment logs for any issues

6. **Configure Domain (Optional)**
   - In Coolify, add a custom domain to your application
   - Coolify will automatically configure SSL with Let's Encrypt

### Docker Deployment (Manual)

If you prefer to deploy manually with Docker:

```bash
# Build the image
docker build -t word-list-api .

# Run the container
docker run -d \
  --name word-list-api \
  -p 8080:8080 \
  -e PORT=8080 \
  -e WORD_LIST=word_list.json \
  -e WORKERS=1 \
  --restart unless-stopped \
  word-list-api

# Check logs
docker logs -f word-list-api

# Stop container
docker stop word-list-api
```

### Health Monitoring

The `/health` endpoint returns HTTP 200 when the service is running correctly. You can use this for:
- Load balancer health checks
- Uptime monitoring services
- Container orchestration (Docker health checks, Kubernetes probes)

### Troubleshooting

**Container fails to start:**
- Check that `word_list.json` exists and is valid JSON
- Verify environment variables are set correctly
- Review container logs: `docker logs word-list-api`

**Health check fails:**
- Ensure port 8080 is accessible
- Check firewall rules on your VPS
- Verify the application started successfully (check logs)

**Performance issues:**
- Check response times and CPU usage first
- If CPU is maxed out, increase `WORKERS` environment variable to 2-4
- Each worker uses ~30-50MB RAM - ensure you have enough memory
- Monitor with: `docker stats word-list-api`
- For very high traffic, consider horizontal scaling (multiple instances behind a load balancer)
