# Simple Storage Server

A lightweight Flask server for storing and serving files via HTTP API, with a modern admin web interface.

## Features

- 📤 **Upload**: Accept ZIP files via HTTP POST
- 📥 **Download**: Serve files with optional auto-delete
- 🗑️ **Delete**: Manual cleanup endpoint
- 🔐 **API Key Auth**: Simple but secure authentication
- 📊 **SQLite**: Lightweight job tracking database
- 🖥️ **Admin Web Interface**: Modern dark-themed dashboard for file management
- 📈 **Statistics**: Disk usage, file stats, and activity monitoring
- 🛡️ **Security**: Rate limiting, CSRF protection, secure sessions
- ⏰ **Cron Cleanup**: Configurable automatic file cleanup
- 🎨 **Custom Logo**: Upload your own logo for branding

## Quick Start (Docker)

```bash
# Clone and navigate to storage server
cd python-simple-storage-server

# Set your environment variables
export STORAGE_API_KEY="your-secure-key-here"
export ADMIN_USERNAME="admin"
export ADMIN_PASSWORD="your-secure-admin-password"
export SECRET_KEY="your-random-secret-key"

# Run with Docker Compose
docker-compose up -d
```

## Admin Web Interface

Access the admin interface at: `http://your-server:5000/admin/login`

### Pages:

- **📁 Storage**: View all files in a paginated table with download buttons
- **📊 Statistics**: Disk usage charts, file stats, recent activity
- **⚙️ Settings**: Configure cleanup, upload custom logo

### Default Credentials (CHANGE IN PRODUCTION!):

- **Username**: `admin`
- **Password**: `@Password1234.`

### Security Features:

- Rate limiting (60 req/min for UI, 10 login attempts/min)
- CSRF protection on all forms
- Secure session cookies (HttpOnly, SameSite)
- Security headers (CSP, X-Frame-Options, etc.)

---

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
git clone https://github.com/your-repo/python-simple-storage-server.git
cd python-simple-storage-server
```

### 4. Configure environment

```bash
# Copy example and edit
cp .env.example .env
nano .env
```

**Important: Set strong values for:**

```bash
STORAGE_API_KEY=your-very-long-random-secure-key-here
ADMIN_USERNAME=your-admin-username
ADMIN_PASSWORD=your-super-secure-password
SECRET_KEY=generate-a-random-32-char-string
```

### 5. Start the server

```bash
docker-compose up -d
```

### 6. Verify it's running

```bash
# Check health endpoint
curl http://localhost:5000/health

# Access admin interface
# Open browser: http://your-server-ip:5000/admin/login
```

---

## Redeploying Without Losing Files

> ⚠️ **IMPORTANT**: Never use `docker-compose down -v` as it deletes volumes and your files!

```bash
# SSH to your server
ssh user@your-hetzner-ip

# Navigate to project
cd /path/to/python-simple-storage-server

# Pull latest changes
git pull origin main

# Rebuild and restart (volumes are preserved!)
docker-compose build --no-cache
docker-compose up -d

# Verify
docker-compose logs -f storage
```

The `storage_data` volume contains all your files in `/data/storage` and is **NOT** affected by rebuild.

---

## Setting Up Cron Cleanup on Hetzner

### 1. Verify cron is running

```bash
sudo systemctl status cron
```

### 2. If not running, enable it

```bash
sudo systemctl enable cron
sudo systemctl start cron
```

### 3. Add cleanup cron job

```bash
# Open crontab editor
crontab -e

# Add this line to run cleanup every hour:
0 * * * * curl -s -X POST http://localhost:5000/api/cleanup -H "X-API-Key: YOUR_API_KEY" >> /var/log/storage-cleanup.log 2>&1
```

### 4. Verify cron jobs

```bash
crontab -l
```

### 5. Configure cleanup settings via web UI

1. Go to `http://your-server:5000/admin/login`
2. Navigate to **Settings** in the sidebar
3. Enable cleanup and set max age (hours)
4. Click "Save Settings"
5. Optionally click "Run Now" to test

---

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

### List Files (Admin API)

```
GET /list
Headers: X-API-Key: your-key
```

### Cleanup API (for cron)

```
POST /api/cleanup
Headers: X-API-Key: your-key
```

---

## Environment Variables

| Variable           | Default            | Description                    |
| ------------------ | ------------------ | ------------------------------ |
| `STORAGE_API_KEY`  | `change-me`        | API key for authentication     |
| `STORAGE_PATH`     | `/data/storage`    | Where to store ZIP files       |
| `DATABASE_PATH`    | `/data/storage.db` | SQLite database path           |
| `PORT`             | `5000`             | Server port                    |
| `AUTO_DELETE`      | `true`             | Delete after download          |
| `APP_NAME`         | `Simple Storage`   | App name for branding          |
| `ADMIN_USERNAME`   | `admin`            | Admin login username           |
| `ADMIN_PASSWORD`   | `@Password1234.`   | Admin login password           |
| `SECRET_KEY`       | (auto-generated)   | Flask secret key for sessions  |
| `RATE_LIMIT_UI`    | `60`               | Rate limit for UI (req/min)    |
| `RATE_LIMIT_LOGIN` | `10`               | Rate limit for login (req/min) |

---

## Custom Logo

You can upload a custom logo from the Settings page:

1. Go to **Settings** in the admin panel
2. Scroll to "Logo Personalizzato"
3. Upload a PNG, JPG, or SVG file (max 500KB)
4. The logo will appear in the sidebar

---

## Running Tests

```bash
# Install test dependencies
pip install -r requirements.txt -r tests/requirements-test.txt

# Run tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=app --cov-report=html
```

---

## Nginx Reverse Proxy with SSL

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
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        client_max_body_size 100M;
    }
}
```

---

## License

MIT
