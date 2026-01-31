# Deployment Guide (Hetzner)

This guide assumes you have a Linux server (Ubuntu/Debian) on Hetzner with Docker and Nginx installed.

## 1. Prepare the Server

Ensure Docker and Docker Compose are installed:

```bash
apt update
apt install -y docker.io docker-compose nginx git
```

## 2. Clone & Configure

Clone the repository to your server (e.g., in `/var/www` or `/opt`):

```bash
git clone https://github.com/simone-bianco/simple-storage-server.git
cd simple-storage-server
```

Create the production `.env`:

```bash
cp .env.example .env
```

Edit `.env` and configure:

- `APP_ENV=production`
- `APP_DEBUG=false`
- `APP_URL=http://YOUR_IP_OR_DOMAIN/storage`
- `STORAGE_API_KEY=...`
- `ADMIN_EMAIL=...`
- `ADMIN_PASSWORD=...`
- `SWAGGER_PASSWORD=...`

## 3. Build & Run Docker

Build the container and start it:

```bash
docker-compose -f docker-compose.prod.yml up -d --build
```

Initialize the database (first time only):

```bash
# Create the sqlite file inside the volume logic or via container
docker-compose -f docker-compose.prod.yml exec app touch /var/www/html/database/data/database.sqlite
docker-compose -f docker-compose.prod.yml exec app php artisan migrate --force
docker-compose -f docker-compose.prod.yml exec app php artisan db:seed --force
docker-compose -f docker-compose.prod.yml exec app php artisan l5-swagger:generate
```

## 4. Accessing the Application

By default, the application runs on **Port 5000**.

- **Admin Panel**: `http://YOUR_SERVER_IP:5000/admin/login`
- **API Endpoint**: `http://YOUR_SERVER_IP:5000/api/upload`
- **Swagger Docs**: `http://YOUR_SERVER_IP:5000/api/documentation`

## 5. (Optional) Reverse Proxy

If you prefer to use Nginx on the host to forward traffic (e.g. to use port 80 or a domain), you can use the provided configuration.

Copy the config:

```bash
cp z-docs/nginx/storage-server.conf /etc/nginx/sites-available/storage-server.conf
```

Edit and enable it as needed.

## Troubleshooting

- **Logs**: `docker-compose -f docker-compose.prod.yml logs -f`
- **Permissions**: If uploads fail, check `storage/app` permissions inside the container.
