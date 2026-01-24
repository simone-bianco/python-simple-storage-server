"""
Simple Storage Server - Lightweight file storage with web interface.

A Flask server that:
- Accepts ZIP file uploads via HTTP POST
- Stores files with job_id reference
- Provides download endpoint
- Auto-deletes files after download (configurable)
- Provides admin web interface for file management
"""

import os
import shutil
import sqlite3
import threading
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from functools import wraps

from flask import Flask, request, jsonify, send_file, g, render_template, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash

# Flask-Login for session management
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user

# Flask-Limiter for rate limiting (DDoS protection)
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Flask-WTF for CSRF protection
from flask_wtf.csrf import CSRFProtect

app = Flask(__name__)

# =============================================================================
# Configuration
# =============================================================================

# Secret key for sessions (REQUIRED for security)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(32))

# API configuration
app.config['API_KEY'] = os.environ.get('STORAGE_API_KEY', 'change-me-in-production')
app.config['STORAGE_PATH'] = os.environ.get('STORAGE_PATH', './storage')
app.config['DATABASE_PATH'] = os.environ.get('DATABASE_PATH', './storage.db')
app.config['AUTO_DELETE'] = os.environ.get('AUTO_DELETE', 'true').lower() == 'true'

# App name (for branding)
app.config['APP_NAME'] = os.environ.get('APP_NAME', 'Simple Storage')

# Admin credentials
app.config['ADMIN_USERNAME'] = os.environ.get('ADMIN_USERNAME', 'admin')
app.config['ADMIN_PASSWORD'] = os.environ.get('ADMIN_PASSWORD', '@Password1234.')

# Rate limiting configuration
app.config['RATE_LIMIT_UI'] = os.environ.get('RATE_LIMIT_UI', '60')
app.config['RATE_LIMIT_LOGIN'] = os.environ.get('RATE_LIMIT_LOGIN', '10')

# Session configuration for security
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('DEBUG', 'false').lower() != 'true'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=8)

# Upload config for logo
app.config['MAX_LOGO_SIZE'] = 500 * 1024  # 500KB
app.config['ALLOWED_LOGO_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'svg'}

# Ensure storage directory exists
Path(app.config['STORAGE_PATH']).mkdir(parents=True, exist_ok=True)

# =============================================================================
# Security Setup
# =============================================================================

# CSRF Protection
csrf = CSRFProtect(app)

# Rate Limiter (DDoS Protection)
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["200 per day", "100 per hour"],
    storage_uri="memory://",
)

# Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'admin_login'
login_manager.login_message = 'Effettua il login per accedere a questa pagina.'
login_manager.login_message_category = 'warning'


# =============================================================================
# User Model
# =============================================================================

class AdminUser(UserMixin):
    """Simple admin user model."""
    
    def __init__(self, username):
        self.id = username
        self.username = username
    
    @staticmethod
    def validate(username, password):
        """Validate username and password against environment config."""
        correct_username = app.config['ADMIN_USERNAME']
        correct_password = app.config['ADMIN_PASSWORD']
        
        # Constant-time comparison to prevent timing attacks
        username_match = secrets.compare_digest(username, correct_username)
        password_match = secrets.compare_digest(password, correct_password)
        
        return username_match and password_match


@login_manager.user_loader
def load_user(user_id):
    """Load user by ID."""
    if user_id == app.config['ADMIN_USERNAME']:
        return AdminUser(user_id)
    return None


# =============================================================================
# Context Processors
# =============================================================================

@app.context_processor
def inject_config():
    """Inject config into all templates."""
    return {
        'config': {
            'APP_NAME': app.config.get('APP_NAME', 'Simple Storage')
        }
    }


# =============================================================================
# Security Headers Middleware
# =============================================================================

@app.after_request
def add_security_headers(response):
    """Add security headers to all responses."""
    # Prevent clickjacking
    response.headers['X-Frame-Options'] = 'DENY'
    # Prevent MIME type sniffing
    response.headers['X-Content-Type-Options'] = 'nosniff'
    # Enable XSS filter
    response.headers['X-XSS-Protection'] = '1; mode=block'
    # Referrer policy
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    # Content Security Policy
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "script-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
    )
    return response


# =============================================================================
# Database Functions
# =============================================================================

def get_db():
    """Get database connection for current request."""
    if 'db' not in g:
        g.db = sqlite3.connect(app.config['DATABASE_PATH'])
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(error):
    """Close database connection at end of request."""
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    """Initialize database schema."""
    db_path = app.config['DATABASE_PATH']
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Files table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS files (
            job_id TEXT PRIMARY KEY,
            file_path TEXT NOT NULL,
            file_size INTEGER,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            downloaded_at TIMESTAMP,
            deleted BOOLEAN DEFAULT FALSE
        )
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_files_deleted 
        ON files(deleted)
    """)
    
    # Settings table for cron configuration
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Initialize default settings if not exist
    cursor.execute("""
        INSERT OR IGNORE INTO settings (key, value) VALUES ('cleanup_enabled', 'false')
    """)
    cursor.execute("""
        INSERT OR IGNORE INTO settings (key, value) VALUES ('cleanup_max_age_hours', '24')
    """)
    
    conn.commit()
    conn.close()


def get_setting(key, default=None):
    """Get a setting value from database."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    return row['value'] if row else default


def set_setting(key, value):
    """Set a setting value in database."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO settings (key, value, updated_at) 
        VALUES (?, ?, ?)
    """, (key, str(value), datetime.now().isoformat()))
    db.commit()


# =============================================================================
# Utility Functions
# =============================================================================

def format_file_size(size_bytes):
    """Format file size in human readable format."""
    if size_bytes is None:
        return '-'
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def format_datetime(dt_string):
    """Format datetime string in human readable format."""
    if not dt_string:
        return None
    try:
        dt = datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
        return dt.strftime('%d/%m/%Y %H:%M')
    except:
        return dt_string


def get_disk_usage():
    """Get disk usage for the storage path."""
    try:
        storage_path = Path(app.config['STORAGE_PATH'])
        # Get disk usage for the partition containing storage
        usage = shutil.disk_usage(storage_path)
        return {
            'total': usage.total,
            'used': usage.used,
            'free': usage.free,
            'percent': round((usage.used / usage.total) * 100, 1),
            'total_human': format_file_size(usage.total),
            'used_human': format_file_size(usage.used),
            'free_human': format_file_size(usage.free)
        }
    except Exception as e:
        print(f"Error getting disk usage: {e}")
        return {
            'total': 0,
            'used': 0,
            'free': 0,
            'percent': 0,
            'total_human': '-',
            'used_human': '-',
            'free_human': '-'
        }


def require_api_key(f):
    """Decorator to require API key authentication."""
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-API-Key') or request.headers.get('Authorization', '').replace('Bearer ', '')
        if api_key != app.config['API_KEY']:
            return jsonify({'error': 'Invalid or missing API key'}), 401
        return f(*args, **kwargs)
    return decorated


def allowed_logo_file(filename):
    """Check if file is allowed for logo upload."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_LOGO_EXTENSIONS']


# =============================================================================
# API Endpoints (Original)
# =============================================================================

@app.route('/health', methods=['GET'])
@limiter.limit("60 per minute")
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'ok',
        'service': 'simple-storage-server',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/upload', methods=['POST'])
@require_api_key
@csrf.exempt
@limiter.limit("30 per minute")
def upload():
    """
    Upload a ZIP file for a job.
    
    Expected: multipart/form-data with 'file' field and 'job_id' field
    Or: raw binary with X-Job-Id header
    """
    job_id = request.form.get('job_id') or request.headers.get('X-Job-Id')
    
    if not job_id:
        return jsonify({'error': 'Missing job_id'}), 400
    
    # Handle file upload
    if 'file' in request.files:
        file = request.files['file']
        file_data = file.read()
    else:
        # Raw binary upload
        file_data = request.get_data()
    
    if not file_data:
        return jsonify({'error': 'No file data received'}), 400
    
    # Save file
    filename = f"{job_id}.zip"
    file_path = Path(app.config['STORAGE_PATH']) / filename
    
    with open(file_path, 'wb') as f:
        f.write(file_data)
    
    # Store reference in database
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO files (job_id, file_path, file_size, uploaded_at, deleted)
        VALUES (?, ?, ?, ?, FALSE)
    """, (job_id, str(file_path), len(file_data), datetime.now().isoformat()))
    db.commit()
    
    return jsonify({
        'status': 'uploaded',
        'job_id': job_id,
        'file_size': len(file_data),
        'download_url': f"/download/{job_id}"
    }), 201


@app.route('/download/<job_id>', methods=['GET'])
@require_api_key
@csrf.exempt
@limiter.limit("60 per minute")
def download(job_id):
    """
    Download a ZIP file by job_id.
    
    Query params:
    - keep=true: Don't delete after download (default: auto-delete)
    """
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT file_path, deleted FROM files WHERE job_id = ?
    """, (job_id,))
    row = cursor.fetchone()
    
    if not row:
        return jsonify({'error': 'Job not found'}), 404
    
    if row['deleted']:
        return jsonify({'error': 'File already deleted'}), 410
    
    file_path = Path(row['file_path'])
    if not file_path.exists():
        return jsonify({'error': 'File not found on disk'}), 404
    
    # Check if we should keep or delete
    keep = request.args.get('keep', 'false').lower() == 'true'
    auto_delete = app.config['AUTO_DELETE'] and not keep
    
    # Update downloaded_at
    cursor.execute("""
        UPDATE files SET downloaded_at = ? WHERE job_id = ?
    """, (datetime.now().isoformat(), job_id))
    db.commit()
    
    # Schedule deletion after response if auto_delete
    if auto_delete:
        def delete_after_response():
            try:
                import time
                time.sleep(1)
                if file_path.exists():
                    file_path.unlink()
                conn = sqlite3.connect(app.config['DATABASE_PATH'])
                c = conn.cursor()
                c.execute("UPDATE files SET deleted = TRUE WHERE job_id = ?", (job_id,))
                conn.commit()
                conn.close()
            except Exception as e:
                print(f"⚠️ Delete after download failed: {e}")
        
        thread = threading.Thread(target=delete_after_response)
        thread.daemon = True
        thread.start()
    
    return send_file(
        file_path,
        mimetype='application/zip',
        as_attachment=True,
        download_name=f"{job_id}.zip"
    )


@app.route('/delete/<job_id>', methods=['DELETE'])
@require_api_key
@csrf.exempt
@limiter.limit("30 per minute")
def delete(job_id):
    """Manually delete a file by job_id."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT file_path FROM files WHERE job_id = ? AND deleted = FALSE
    """, (job_id,))
    row = cursor.fetchone()
    
    if not row:
        return jsonify({'error': 'Job not found or already deleted'}), 404
    
    file_path = Path(row['file_path'])
    
    if file_path.exists():
        file_path.unlink()
    
    cursor.execute("""
        UPDATE files SET deleted = TRUE WHERE job_id = ?
    """, (job_id,))
    db.commit()
    
    return jsonify({
        'status': 'deleted',
        'job_id': job_id
    })


@app.route('/list', methods=['GET'])
@require_api_key
@csrf.exempt
@limiter.limit("60 per minute")
def list_files():
    """List all stored files (for admin/debug)."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT job_id, file_size, uploaded_at, downloaded_at, deleted
        FROM files
        ORDER BY uploaded_at DESC
        LIMIT 100
    """)
    rows = cursor.fetchall()
    
    return jsonify({
        'files': [dict(row) for row in rows],
        'count': len(rows)
    })


# =============================================================================
# Cleanup API Endpoint (for cron)
# =============================================================================

@app.route('/api/cleanup', methods=['POST'])
@require_api_key
@csrf.exempt
@limiter.limit("10 per minute")
def api_cleanup():
    """Run cleanup of old downloaded files. Called by cron job."""
    result = run_cleanup()
    return jsonify(result)


def run_cleanup():
    """Execute cleanup logic."""
    db_path = app.config['DATABASE_PATH']
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT value FROM settings WHERE key = 'cleanup_enabled'")
    enabled_row = cursor.fetchone()
    cleanup_enabled = enabled_row and enabled_row['value'] == 'true'
    
    cursor.execute("SELECT value FROM settings WHERE key = 'cleanup_max_age_hours'")
    age_row = cursor.fetchone()
    max_age_hours = int(age_row['value']) if age_row else 24
    
    if not cleanup_enabled:
        conn.close()
        return {
            'status': 'skipped',
            'message': 'Cleanup is disabled',
            'deleted_count': 0
        }
    
    cutoff = datetime.now() - timedelta(hours=max_age_hours)
    cutoff_str = cutoff.isoformat()
    
    cursor.execute("""
        SELECT job_id, file_path FROM files 
        WHERE deleted = FALSE 
        AND downloaded_at IS NOT NULL 
        AND downloaded_at < ?
    """, (cutoff_str,))
    
    files_to_delete = cursor.fetchall()
    deleted_count = 0
    
    for file_row in files_to_delete:
        file_path = Path(file_row['file_path'])
        job_id = file_row['job_id']
        
        if file_path.exists():
            try:
                file_path.unlink()
            except Exception as e:
                print(f"⚠️ Failed to delete file {file_path}: {e}")
                continue
        
        cursor.execute("UPDATE files SET deleted = TRUE WHERE job_id = ?", (job_id,))
        deleted_count += 1
    
    cursor.execute("""
        INSERT OR REPLACE INTO settings (key, value, updated_at) 
        VALUES ('cleanup_last_run', ?, ?)
    """, (datetime.now().isoformat(), datetime.now().isoformat()))
    
    conn.commit()
    conn.close()
    
    return {
        'status': 'completed',
        'deleted_count': deleted_count,
        'max_age_hours': max_age_hours,
        'timestamp': datetime.now().isoformat()
    }


# =============================================================================
# Admin Web Interface
# =============================================================================

@app.route('/admin/login', methods=['GET', 'POST'])
@limiter.limit(f"{app.config.get('RATE_LIMIT_LOGIN', '10')} per minute")
def admin_login():
    """Admin login page."""
    if current_user.is_authenticated:
        return redirect(url_for('admin_dashboard'))
    
    error = None
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if AdminUser.validate(username, password):
            user = AdminUser(username)
            login_user(user, remember=False)
            session.permanent = True
            
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/admin'):
                return redirect(next_page)
            return redirect(url_for('admin_dashboard'))
        else:
            error = 'Username o password non validi'
    
    return render_template('login.html', error=error)


@app.route('/admin/logout')
@login_required
def admin_logout():
    """Admin logout."""
    logout_user()
    flash('Logout effettuato con successo.', 'success')
    return redirect(url_for('admin_login'))


@app.route('/admin')
@app.route('/admin/dashboard')
@login_required
@limiter.limit(f"{app.config.get('RATE_LIMIT_UI', '60')} per minute")
def admin_dashboard():
    """Admin dashboard - file list."""
    db = get_db()
    cursor = db.cursor()
    
    page = request.args.get('page', 1, type=int)
    per_page = 15
    offset = (page - 1) * per_page
    
    cursor.execute("SELECT COUNT(*) as count FROM files")
    total_files = cursor.fetchone()['count']
    total_pages = (total_files + per_page - 1) // per_page if total_files > 0 else 1
    
    cursor.execute("""
        SELECT job_id, file_path, file_size, uploaded_at, downloaded_at, deleted
        FROM files
        ORDER BY uploaded_at DESC
        LIMIT ? OFFSET ?
    """, (per_page, offset))
    
    files_raw = cursor.fetchall()
    
    files = []
    for row in files_raw:
        files.append({
            'job_id': row['job_id'],
            'file_path': row['file_path'],
            'file_size': row['file_size'],
            'file_size_human': format_file_size(row['file_size']),
            'uploaded_at': row['uploaded_at'],
            'uploaded_at_human': format_datetime(row['uploaded_at']),
            'downloaded_at': row['downloaded_at'],
            'downloaded_at_human': format_datetime(row['downloaded_at']),
            'deleted': row['deleted']
        })
    
    cursor.execute("SELECT COUNT(*) as count FROM files WHERE deleted = FALSE")
    active_count = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM files WHERE downloaded_at IS NOT NULL")
    downloaded_count = cursor.fetchone()['count']
    
    cursor.execute("SELECT COALESCE(SUM(file_size), 0) as total FROM files WHERE deleted = FALSE")
    total_size = cursor.fetchone()['total']
    
    stats = {
        'total': total_files,
        'active': active_count,
        'downloaded': downloaded_count,
        'total_size': total_size,
        'total_size_human': format_file_size(total_size)
    }
    
    return render_template(
        'dashboard.html',
        files=files,
        stats=stats,
        page=page,
        total_pages=total_pages,
        total_files=total_files
    )


@app.route('/admin/statistics')
@login_required
@limiter.limit(f"{app.config.get('RATE_LIMIT_UI', '60')} per minute")
def admin_statistics():
    """Statistics page with disk usage and file stats."""
    db = get_db()
    cursor = db.cursor()
    
    # Get disk usage
    disk = get_disk_usage()
    
    # Get file statistics
    cursor.execute("SELECT COUNT(*) as count FROM files")
    total_files = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM files WHERE deleted = FALSE")
    active_files = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM files WHERE deleted = TRUE")
    deleted_files = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM files WHERE downloaded_at IS NOT NULL")
    downloaded_files = cursor.fetchone()['count']
    
    cursor.execute("SELECT COALESCE(SUM(file_size), 0) as total FROM files WHERE deleted = FALSE")
    total_size = cursor.fetchone()['total']
    
    files_stats = {
        'total': total_files,
        'active': active_files,
        'deleted': deleted_files,
        'downloaded': downloaded_files,
        'total_size': total_size,
        'total_size_human': format_file_size(total_size)
    }
    
    # Calculate storage percent of disk
    storage_percent = round((total_size / disk['total']) * 100, 2) if disk['total'] > 0 else 0
    
    # Get recent files
    cursor.execute("""
        SELECT job_id, file_size, uploaded_at, downloaded_at, deleted
        FROM files
        ORDER BY uploaded_at DESC
        LIMIT 10
    """)
    recent_raw = cursor.fetchall()
    
    recent_files = []
    for row in recent_raw:
        recent_files.append({
            'job_id': row['job_id'],
            'file_size': row['file_size'],
            'file_size_human': format_file_size(row['file_size']),
            'uploaded_at': row['uploaded_at'],
            'uploaded_at_human': format_datetime(row['uploaded_at']),
            'downloaded_at': row['downloaded_at'],
            'downloaded_at_human': format_datetime(row['downloaded_at']),
            'deleted': row['deleted']
        })
    
    return render_template(
        'statistics.html',
        disk=disk,
        files=files_stats,
        storage_percent=storage_percent,
        recent_files=recent_files
    )


@app.route('/admin/download/<job_id>')
@login_required
@limiter.limit(f"{app.config.get('RATE_LIMIT_UI', '60')} per minute")
def admin_download_file(job_id):
    """Download file from admin interface (doesn't auto-delete)."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT file_path, deleted FROM files WHERE job_id = ?
    """, (job_id,))
    row = cursor.fetchone()
    
    if not row:
        flash('File non trovato.', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    if row['deleted']:
        flash('Il file è già stato eliminato.', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    file_path = Path(row['file_path'])
    if not file_path.exists():
        flash('File non trovato su disco.', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    cursor.execute("""
        UPDATE files SET downloaded_at = ? WHERE job_id = ?
    """, (datetime.now().isoformat(), job_id))
    db.commit()
    
    return send_file(
        file_path,
        mimetype='application/zip',
        as_attachment=True,
        download_name=f"{job_id}.zip"
    )


@app.route('/admin/cron', methods=['GET', 'POST'])
@login_required
@limiter.limit(f"{app.config.get('RATE_LIMIT_UI', '60')} per minute")
def admin_cron():
    """Cron settings page."""
    if request.method == 'POST':
        cleanup_enabled = 'cleanup_enabled' in request.form
        cleanup_max_age_hours = request.form.get('cleanup_max_age_hours', '24')
        
        try:
            hours = int(cleanup_max_age_hours)
            if hours < 1 or hours > 8760:
                raise ValueError("Hours must be between 1 and 8760")
        except ValueError:
            flash('Valore non valido per le ore.', 'danger')
            return redirect(url_for('admin_cron'))
        
        set_setting('cleanup_enabled', 'true' if cleanup_enabled else 'false')
        set_setting('cleanup_max_age_hours', str(hours))
        
        flash('Impostazioni salvate con successo!', 'success')
        return redirect(url_for('admin_cron'))
    
    settings = {
        'cleanup_enabled': get_setting('cleanup_enabled', 'false') == 'true',
        'cleanup_max_age_hours': int(get_setting('cleanup_max_age_hours', '24')),
        'cleanup_last_run': get_setting('cleanup_last_run'),
        'cleanup_last_run_human': format_datetime(get_setting('cleanup_last_run'))
    }
    
    return render_template('cron.html', settings=settings)


@app.route('/admin/cron/run', methods=['POST'])
@login_required
@limiter.limit("5 per minute")
def admin_cron_run():
    """Run cleanup immediately from admin interface."""
    original_enabled = get_setting('cleanup_enabled', 'false')
    set_setting('cleanup_enabled', 'true')
    
    try:
        result = run_cleanup()
        
        if result['status'] == 'completed':
            flash(f"Cleanup completato! {result['deleted_count']} file eliminati.", 'success')
        else:
            flash(f"Cleanup: {result['message']}", 'warning')
    except Exception as e:
        flash(f'Errore durante il cleanup: {str(e)}', 'danger')
    finally:
        set_setting('cleanup_enabled', original_enabled)
    
    return redirect(url_for('admin_cron'))


@app.route('/admin/upload-logo', methods=['POST'])
@login_required
@limiter.limit("10 per minute")
def admin_upload_logo():
    """Upload custom logo."""
    if 'logo' not in request.files:
        flash('Nessun file selezionato.', 'danger')
        return redirect(url_for('admin_cron'))
    
    file = request.files['logo']
    
    if file.filename == '':
        flash('Nessun file selezionato.', 'danger')
        return redirect(url_for('admin_cron'))
    
    if not allowed_logo_file(file.filename):
        flash('Formato file non consentito. Usa PNG, JPG o SVG.', 'danger')
        return redirect(url_for('admin_cron'))
    
    # Check file size
    file.seek(0, 2)
    size = file.tell()
    file.seek(0)
    
    if size > app.config['MAX_LOGO_SIZE']:
        flash('File troppo grande. Massimo 500KB.', 'danger')
        return redirect(url_for('admin_cron'))
    
    # Save logo - always as logo.png for simplicity
    logo_dir = Path(app.root_path) / 'static' / 'img'
    logo_dir.mkdir(parents=True, exist_ok=True)
    logo_path = logo_dir / 'logo.png'
    
    file.save(logo_path)
    flash('Logo caricato con successo!', 'success')
    
    return redirect(url_for('admin_cron'))


# =============================================================================
# Error Handlers
# =============================================================================

@app.errorhandler(429)
def ratelimit_handler(e):
    """Handle rate limit exceeded."""
    if request.path.startswith('/admin') and not request.path.endswith('.js') and not request.path.endswith('.css'):
        flash('Troppo richieste. Riprova tra un minuto.', 'danger')
        return redirect(url_for('admin_login'))
    return jsonify({'error': 'Rate limit exceeded. Try again later.'}), 429


@app.errorhandler(404)
def not_found_handler(e):
    """Handle 404 errors."""
    if request.path.startswith('/admin'):
        flash('Pagina non trovata.', 'warning')
        return redirect(url_for('admin_dashboard'))
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def internal_error_handler(e):
    """Handle 500 errors."""
    if request.path.startswith('/admin'):
        flash('Errore interno del server.', 'danger')
        return redirect(url_for('admin_dashboard'))
    return jsonify({'error': 'Internal server error'}), 500


# =============================================================================
# Initialization
# =============================================================================

with app.app_context():
    init_db()


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'false').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)
