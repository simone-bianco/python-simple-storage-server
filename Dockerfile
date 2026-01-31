# ----------------------------------------------------------
# Stage 1: Build Frontend Assets
# ----------------------------------------------------------
FROM node:20-alpine AS frontend
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

# ----------------------------------------------------------
# Stage 2: Production PHP Image
# ----------------------------------------------------------
FROM php:8.2-fpm-alpine

# Install system dependencies
RUN apk add --no-cache \
    nginx \
    supervisor \
    zip \
    unzip \
    libzip-dev \
    sqlite \
    libpng-dev \
    freetype-dev \
    libjpeg-turbo-dev \
    icu-dev

# Install PHP extensions
RUN docker-php-ext-configure gd --with-freetype --with-jpeg \
    && docker-php-ext-install -j$(nproc) \
    pdo_mysql \
    pdo_sqlite \
    zip \
    gd \
    intl \
    opcache

# Configure PHP Production settings
RUN mv "$PHP_INI_DIR/php.ini-production" "$PHP_INI_DIR/php.ini" \
    && sed -i 's/upload_max_filesize = 2M/upload_max_filesize = 100M/' "$PHP_INI_DIR/php.ini" \
    && sed -i 's/post_max_size = 8M/post_max_size = 100M/' "$PHP_INI_DIR/php.ini"

# Install Composer
COPY --from=composer:latest /usr/bin/composer /usr/bin/composer

# Setup Working Directory
WORKDIR /var/www/html

# Copy Project Files
COPY . .

# Copy Built Assets
COPY --from=frontend /app/public/build public/build

# Install PHP Dependencies (No Dev)
RUN composer install --no-dev --optimize-autoloader --no-interaction

# Setup Permissions
RUN chown -R www-data:www-data /var/www/html/storage /var/www/html/bootstrap/cache \
    && chmod -R 775 /var/www/html/storage /var/www/html/bootstrap/cache

# Setup Nginx (Internal)
COPY z-docs/nginx/app-internal.conf /etc/nginx/http.d/default.conf

# Setup Supervisor
COPY z-docs/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Expose Port 80 (Internal Nginx)
EXPOSE 80

# Start Supervisor (manages Nginx & PHP-FPM)
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
