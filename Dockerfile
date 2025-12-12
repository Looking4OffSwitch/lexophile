# Multi-stage Dockerfile for Flask Word List API
# Optimized for production deployment on Coolify

# Build stage - for installing dependencies
FROM python:3.12-slim AS builder

# Set working directory
WORKDIR /app

# Install system dependencies needed for building Python packages and curl for uv installation
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv (installs into /root/.local/bin by default) and add to PATH
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Copy project configuration
COPY pyproject.toml .

# Install Python dependencies into system site-packages
RUN uv pip install --system --no-cache .

# Production stage - minimal image for running the app
FROM python:3.12-slim AS runtime

# Set working directory
WORKDIR /app

# Install runtime system dependencies (if any needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user to run the application
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app

# Copy Python dependencies and binaries from builder stage
COPY --from=builder /usr/local/lib/python3.12 /usr/local/lib/python3.12
COPY --from=builder /usr/local/bin /usr/local/bin
# (optional) retain any user-local installs from builder
COPY --from=builder --chown=appuser:appuser /root/.local /home/appuser/.local

# Copy application files
COPY --chown=appuser:appuser app.py .
COPY --chown=appuser:appuser word_list.json .
COPY --chown=appuser:appuser word_list_example.json .

# Make sure scripts in .local are usable
ENV PATH=/home/appuser/.local/bin:$PATH

# Switch to non-root user
USER appuser

# Expose port 8080 (standard for web services)
EXPOSE 8080

# Set environment variables
ENV PORT=8080
ENV PYTHONUNBUFFERED=1
ENV WORKERS=1

# Health check to ensure the application is running
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health').read()" || exit 1

# Run the application with gunicorn
# Workers: Default to 1 for this lightweight API. Increase via WORKERS env var if needed.
# For high traffic: use (2 * CPU cores) + 1
CMD ["sh", "-c", "exec gunicorn --bind 0.0.0.0:${PORT} --workers ${WORKERS} --timeout 120 --access-logfile - --error-logfile - app:app"]
