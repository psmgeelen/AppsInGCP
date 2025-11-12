# Use Python 3.13 slim image
FROM python:3.13-alpine

# Set working directory
WORKDIR /app

# Copy dependency files
COPY app/pyproject.toml app/uv.lock* ./

# Install Python dependencies
RUN pip install uv && uv sync

# Copy application code
COPY app/ .

# Expose Chainlit default port
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/credentials.json
ENV PATH="/app/.venv/bin:$PATH"

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Run the application
CMD ["uv", "run", "chainlit", "run", "main.py", "--host", "0.0.0.0", "--port", "8000"]