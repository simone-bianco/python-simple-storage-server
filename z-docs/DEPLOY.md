# Deployment Guide (Manual)

This guide assumes you have a Linux server (Ubuntu/Debian) where you want to deploy the application manually.

## 1. Prepare the Server

Ensure dependencies are installed:

```bash
sudo apt update
sudo apt install -y php8.2 php8.2-fpm php8.2-xml php8.2-curl php8.2-zip php8.2-sqlite3 unzip nginx supervisor composer
```

### Firewall Configuration (Crucial)

By default, port 5000 might be blocked. Allow it:

```bash
sudo ufw allow 5000/tcp
sudo ufw reload
```

## 2. Clone & Configure

Clone the repository to your server (target: `/var/www/simple-storage-server`):

```bash
cd /var/www
sudo git clone https://github.com/simone-bianco/simple-storage-server.git
sudo chown -R www-data:www-data simple-storage-server
cd simple-storage-server
```

Create production configuration:

```bash
cp .env.example .env
php artisan key:generate
touch database/database.sqlite
php artisan migrate --force
```

Edit `.env` and set your credentials:

```bash
nano .env
```

## 3. Configure Supervisor (Standalone Server)

We will use Supervisor to run both the Queue Worker and the Web Server directly on port 5000.

1.  **Stop Nginx** (to free up port 5000 if it was running):

    ```bash
    sudo systemctl stop nginx
    # Or remove the site if you don't need it
    sudo rm /etc/nginx/sites-enabled/simple-storage-server
    ```

2.  **Copy Config**:

    ```bash
    sudo cp deployment/supervisor/simple-storage-server.conf /etc/supervisor/conf.d/
    ```

3.  **Start Services**:

    ```bash
    sudo supervisorctl reread
    sudo supervisorctl update
    sudo supervisorctl restart all
    ```

4.  **Verify**:
    - Check status: `sudo supervisorctl status`
    - You should see `simple-storage-serve` and `simple-storage-worker` RUNNING.
    - Access: `http://YOUR_IP:5000/admin/login`

**Note**: This method bypasses Nginx/PHP-FPM, eliminating configuration headaches. The server runs directly via PHP's built-in server, which is sufficient for simple storage tasks.

## 5. Verify

Your API should be accessible at `http://your-domain.com:5000/api`.

- Logs: `storage/logs/laravel.log` or `storage/logs/worker.log`.
