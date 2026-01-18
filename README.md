# Dolphin Storage Server

A lightweight Flask server for storing and serving parsed PDF results from RunPod workers.

## Features

- 📤 **Upload**: Accept ZIP files via HTTP POST
- 📥 **Download**: Serve files with optional auto-delete
- 🗑️ **Delete**: Manual cleanup endpoint
- 🔐 **API Key Auth**: Simple but secure authentication
- 📊 **SQLite**: Lightweight job tracking database

## Quick Start (Docker)

```bash
# Clone and navigate to storage server
cd z-docs/scripts/storage

# Set your API key
export STORAGE_API_KEY="your-secure-key-here"

# Run with Docker Compose
docker-compose up -d
```

## Deployment on Hetzner

### 1. SSH to your server

```bash
ssh user@your-hetzner-ip
```

### 2. Install Docker (if not installed)

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
# Logout and login again for group to take effect
```

### 3. Clone the repository

```bash
git clone https://github.com/your-repo/python-dolphin-pdf-parser.git
cd python-dolphin-pdf-parser/z-docs/scripts/storage
```

### 4. Configure environment

```bash
# Copy example and edit
cp .env.example .env
nano .env

# Set a STRONG API key!
STORAGE_API_KEY=your-very-long-random-secure-key-here
```

### 5. Start the server

```bash
docker-compose up -d
```

### 6. Verify it's running

```bash
curl http://localhost:5000/health
# Should return: {"status": "ok", ...}
```

### 7. (Optional) Setup nginx reverse proxy with SSL

```nginx
server {
    listen 443 ssl;
    server_name storage.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/storage.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/storage.yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        client_max_body_size 100M;
    }
}
```

## API Endpoints

### Health Check

```
GET /health
```

### Upload File

```
POST /upload
Headers: X-API-Key: your-key
Body: multipart/form-data with 'file' and 'job_id' fields

OR

POST /upload
Headers:
  X-API-Key: your-key
  X-Job-Id: job-123
Body: raw ZIP binary
```

**Response:**

```json
{
  "status": "uploaded",
  "job_id": "job-123",
  "file_size": 12345,
  "download_url": "/download/job-123"
}
```

### Download File

```
GET /download/{job_id}
Headers: X-API-Key: your-key
Query: ?keep=true (optional, prevents auto-delete)
```

Returns the ZIP file. **By default, file is deleted after download.**

### Delete File

```
DELETE /delete/{job_id}
Headers: X-API-Key: your-key
```

### List Files (Admin)

```
GET /list
Headers: X-API-Key: your-key
```

## Environment Variables

| Variable          | Default            | Description                |
| ----------------- | ------------------ | -------------------------- |
| `STORAGE_API_KEY` | `change-me`        | API key for authentication |
| `STORAGE_PATH`    | `/data/storage`    | Where to store ZIP files   |
| `DATABASE_PATH`   | `/data/storage.db` | SQLite database path       |
| `PORT`            | `5000`             | Server port                |
| `AUTO_DELETE`     | `true`             | Delete after download      |

## Running Tests

```bash
# Install test dependencies
pip install -r requirements.txt -r tests/requirements-test.txt

# Run tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=app --cov-report=html
```

## Integration with RunPod

In your RunPod parser, set these environment variables:

```
STORAGE_ENDPOINT=https://storage.yourdomain.com/upload
STORAGE_API_KEY=your-key
```

The parser will upload ZIP results to this server after processing.

## License

MIT
