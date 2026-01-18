"""
Dolphin Storage Server - Simple file storage for parsed PDF results.

A lightweight Flask server that:
- Accepts ZIP file uploads from RunPod workers
- Stores files with job_id reference
- Provides download endpoint
- Auto-deletes files after download (configurable)
"""

import os
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from functools import wraps

from flask import Flask, request, jsonify, send_file, g
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Configuration from environment
app.config['API_KEY'] = os.environ.get('STORAGE_API_KEY', 'change-me-in-production')
app.config['STORAGE_PATH'] = os.environ.get('STORAGE_PATH', './storage')
app.config['DATABASE_PATH'] = os.environ.get('DATABASE_PATH', './storage.db')
app.config['AUTO_DELETE'] = os.environ.get('AUTO_DELETE', 'true').lower() == 'true'

# Ensure storage directory exists
Path(app.config['STORAGE_PATH']).mkdir(parents=True, exist_ok=True)


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
    conn.commit()
    conn.close()


def require_api_key(f):
    """Decorator to require API key authentication."""
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-API-Key') or request.headers.get('Authorization', '').replace('Bearer ', '')
        if api_key != app.config['API_KEY']:
            return jsonify({'error': 'Invalid or missing API key'}), 401
        return f(*args, **kwargs)
    return decorated


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'ok',
        'service': 'dolphin-storage-server',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/upload', methods=['POST'])
@require_api_key
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
                # Small delay to ensure response is sent
                import time
                time.sleep(1)
                if file_path.exists():
                    file_path.unlink()
                # Update DB
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
    
    # Delete file if exists
    if file_path.exists():
        file_path.unlink()
    
    # Update DB
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


# Initialize database on startup
with app.app_context():
    init_db()


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'false').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)
