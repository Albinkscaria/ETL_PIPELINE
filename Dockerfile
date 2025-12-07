# UAE Legal Documents ETL Pipeline - Docker Image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-ara \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Download SpaCy model
RUN python -m spacy download en_core_web_sm

# Copy application code
COPY *.py ./
COPY config.json ./
COPY tests/ ./tests/

# Create directories
RUN mkdir -p Data review_queue

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV GEMINI_API_KEY=""

# Run tests on build (optional - comment out for faster builds)
# RUN pytest

# Default command
CMD ["python", "main.py"]

# Usage:
# Build: docker build -t uae-etl-pipeline .
# Run: docker run -v $(pwd)/Data:/app/Data -v $(pwd)/output:/app/output -e GEMINI_API_KEY=your_key uae-etl-pipeline
