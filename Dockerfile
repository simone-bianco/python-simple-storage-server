# Dolphin Storage Server
FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app.py .

# Create storage directory
RUN mkdir -p /data/storage

# Environment defaults
ENV STORAGE_PATH=/data/storage
ENV DATABASE_PATH=/data/storage.db
ENV PORT=5000
ENV AUTO_DELETE=true

# Expose port
EXPOSE 5000

# Run with gunicorn for production
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "app:app"]
