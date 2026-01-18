"""
Tests for Dolphin Storage Server.
"""

import io
import os
import sqlite3
import tempfile
import zipfile
import pytest

# Set test environment before importing app
os.environ['STORAGE_API_KEY'] = 'test-api-key'


@pytest.fixture
def app():
    """Create test app with temporary database and storage."""
    from app import app as flask_app
    
    with tempfile.TemporaryDirectory() as tmpdir:
        flask_app.config['STORAGE_PATH'] = tmpdir
        flask_app.config['DATABASE_PATH'] = os.path.join(tmpdir, 'test.db')
        flask_app.config['API_KEY'] = 'test-api-key'
        flask_app.config['AUTO_DELETE'] = True
        flask_app.config['TESTING'] = True
        
        # Initialize DB
        with flask_app.app_context():
            from app import init_db
            init_db()
        
        yield flask_app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def auth_headers():
    """Auth headers for API requests."""
    return {'X-API-Key': 'test-api-key'}


def create_test_zip():
    """Create a test ZIP file in memory."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('output.json', '{"test": "data"}')
        zf.writestr('figures/fig_0.png', b'fake-png-data')
    buffer.seek(0)
    return buffer


class TestHealth:
    """Health endpoint tests."""
    
    def test_health_check(self, client):
        """Test health endpoint returns ok."""
        response = client.get('/health')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'ok'
        assert data['service'] == 'dolphin-storage-server'


class TestAuthentication:
    """API key authentication tests."""
    
    def test_upload_requires_api_key(self, client):
        """Test upload without API key returns 401."""
        response = client.post('/upload')
        assert response.status_code == 401
    
    def test_download_requires_api_key(self, client):
        """Test download without API key returns 401."""
        response = client.get('/download/test-job')
        assert response.status_code == 401
    
    def test_delete_requires_api_key(self, client):
        """Test delete without API key returns 401."""
        response = client.delete('/delete/test-job')
        assert response.status_code == 401
    
    def test_invalid_api_key_rejected(self, client):
        """Test invalid API key is rejected."""
        response = client.post('/upload', headers={'X-API-Key': 'wrong-key'})
        assert response.status_code == 401


class TestUpload:
    """Upload endpoint tests."""
    
    def test_upload_file(self, client, auth_headers):
        """Test successful file upload."""
        zip_data = create_test_zip()
        
        response = client.post(
            '/upload',
            data={
                'file': (zip_data, 'test.zip'),
                'job_id': 'test-job-123'
            },
            headers=auth_headers,
            content_type='multipart/form-data'
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['status'] == 'uploaded'
        assert data['job_id'] == 'test-job-123'
        assert data['download_url'] == '/download/test-job-123'
    
    def test_upload_raw_binary(self, client, auth_headers):
        """Test upload with raw binary data."""
        zip_data = create_test_zip().read()
        
        headers = {**auth_headers, 'X-Job-Id': 'binary-job-456'}
        response = client.post(
            '/upload',
            data=zip_data,
            headers=headers,
            content_type='application/octet-stream'
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['job_id'] == 'binary-job-456'
    
    def test_upload_missing_job_id(self, client, auth_headers):
        """Test upload without job_id returns error."""
        zip_data = create_test_zip()
        
        response = client.post(
            '/upload',
            data={'file': (zip_data, 'test.zip')},
            headers=auth_headers,
            content_type='multipart/form-data'
        )
        
        assert response.status_code == 400
        assert 'job_id' in response.get_json()['error']


class TestDownload:
    """Download endpoint tests."""
    
    def test_download_file(self, client, auth_headers):
        """Test successful file download."""
        # First upload
        zip_data = create_test_zip()
        client.post(
            '/upload',
            data={'file': (zip_data, 'test.zip'), 'job_id': 'download-test'},
            headers=auth_headers,
            content_type='multipart/form-data'
        )
        
        # Then download
        response = client.get('/download/download-test', headers=auth_headers)
        assert response.status_code == 200
        assert response.content_type == 'application/zip'
    
    def test_download_not_found(self, client, auth_headers):
        """Test download of non-existent job returns 404."""
        response = client.get('/download/non-existent', headers=auth_headers)
        assert response.status_code == 404
    
    def test_download_with_keep_flag(self, client, auth_headers, app):
        """Test download with keep=true doesn't delete."""
        # Upload
        zip_data = create_test_zip()
        client.post(
            '/upload',
            data={'file': (zip_data, 'test.zip'), 'job_id': 'keep-test'},
            headers=auth_headers,
            content_type='multipart/form-data'
        )
        
        # Download with keep=true
        response = client.get('/download/keep-test?keep=true', headers=auth_headers)
        assert response.status_code == 200
        
        # File should still be downloadable
        response2 = client.get('/download/keep-test?keep=true', headers=auth_headers)
        assert response2.status_code == 200


class TestDelete:
    """Delete endpoint tests."""
    
    def test_delete_file(self, client, auth_headers):
        """Test successful file deletion."""
        # Upload first
        zip_data = create_test_zip()
        client.post(
            '/upload',
            data={'file': (zip_data, 'test.zip'), 'job_id': 'delete-test'},
            headers=auth_headers,
            content_type='multipart/form-data'
        )
        
        # Delete
        response = client.delete('/delete/delete-test', headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'deleted'
        
        # Verify can't download after delete
        response2 = client.get('/download/delete-test', headers=auth_headers)
        assert response2.status_code == 404
    
    def test_delete_not_found(self, client, auth_headers):
        """Test delete of non-existent job returns 404."""
        response = client.delete('/delete/non-existent', headers=auth_headers)
        assert response.status_code == 404


class TestList:
    """List endpoint tests."""
    
    def test_list_files(self, client, auth_headers):
        """Test list endpoint returns uploaded files."""
        # Upload a file
        zip_data = create_test_zip()
        client.post(
            '/upload',
            data={'file': (zip_data, 'test.zip'), 'job_id': 'list-test'},
            headers=auth_headers,
            content_type='multipart/form-data'
        )
        
        # List
        response = client.get('/list', headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert 'files' in data
        assert len(data['files']) >= 1
        assert any(f['job_id'] == 'list-test' for f in data['files'])
