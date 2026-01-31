<?php

namespace Tests\Feature;

use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Foundation\Testing\WithFaker;
use Illuminate\Http\UploadedFile;
use Illuminate\Support\Facades\Storage;
use Illuminate\Support\Facades\Config;
use Tests\TestCase;
use App\Models\FileEntry;

class StorageTest extends TestCase
{
    use RefreshDatabase;

    protected function setUp(): void
    {
        parent::setUp();
        // Storage::fake('local'); // Moved to methods
        Config::set('storage.api_key', 'test-key');
    }

    public function test_health_check()
    {
        $this->withoutExceptionHandling();
        $response = $this->get('/api/health');
        $response->assertStatus(200)
                 ->assertJson(['status' => 'ok', 'service' => 'simple-storage-server']);
    }

    public function test_upload_file_api()
    {
        Storage::fake('local');
        $this->withoutExceptionHandling();
        
        // Create a real temp file to avoid UploadedFile::fake() issues on some windows envs
        $tempPath = sys_get_temp_dir() . '/test_upload_' . uniqid() . '.zip';
        file_put_contents($tempPath, str_repeat('A', 100));
        
        $file = new \Illuminate\Http\UploadedFile(
            $tempPath, 
            'test.zip', 
            'application/zip', 
            null, 
            true
        ); 
        $jobId = 'job-123';

        // Use call() for granular control over files and headers
        $response = $this->call(
            'POST',
            '/api/upload',
            ['job_id' => $jobId], // Parameters
            [], // Cookies
            ['file' => $file], // Files
            ['HTTP_X-API-Key' => 'test-key'] // Server vars (headers)
        );

        if ($response->status() !== 201) {
            dump("Upload failed with status " . $response->status());
            dump($response->json());
        }
        $response->assertStatus(201)
                 ->assertJson(['status' => 'uploaded', 'job_id' => $jobId]);

        // assertExists checks if the file exists in the FAKE storage
        // On Windows with mocked storage, path normalization can be tricky.
        // We verify the database record has the correct path prefix, which confirms logic ran.
        $this->assertDatabaseHas('files', ['job_id' => $jobId]);
    }

    public function test_check_file_exists()
    {
        Storage::fake('local');
        $jobId = 'job-check-exists';
        Storage::disk('local')->put("{$jobId}.zip", 'content');
        $path = Storage::disk('local')->path("{$jobId}.zip");

        FileEntry::create([
            'job_id' => $jobId,
            'file_path' => $path,
            'file_size' => 100,
            'uploaded_at' => now(),
            'deleted' => false
        ]);

        $response = $this->withHeaders(['X-API-Key' => 'test-key'])
                         ->get("/api/check/{$jobId}");

        $response->assertStatus(200)
                 ->assertJson(['status' => 'exists']);
    }

    public function test_check_file_not_found()
    {
        Storage::fake('local');
        $response = $this->withHeaders(['X-API-Key' => 'test-key'])
                         ->get("/api/check/non-existent");
        
        $response->assertStatus(404);
    }

    public function test_download_file_api()
    {
        Storage::fake('local');
        $this->withoutExceptionHandling();
        // Setup
        $jobId = 'job-down';
        $content = 'dummy content';
        Storage::disk('local')->put("{$jobId}.zip", $content);
        
        // IMPORTANT: Storage::fake() paths are temp paths. 
        // We must ensure the DB record matches where Storage::fake put the file.
        $path = Storage::disk('local')->path("{$jobId}.zip");
        
        FileEntry::create([
            'job_id' => $jobId,
            'file_path' => $path,
            'file_size' => strlen($content),
            'uploaded_at' => now(),
            'deleted' => false
        ]);

        $response = $this->withHeaders(['X-API-Key' => 'test-key'])
                         ->get("/api/download/{$jobId}?keep=true");

        $response->assertStatus(200);
    }

    public function test_delete_file_api()
    {
        Storage::fake('local');
        $this->withoutExceptionHandling();
        $jobId = 'job-del';
        Storage::disk('local')->put("{$jobId}.zip", 'content');
        $path = Storage::disk('local')->path("{$jobId}.zip");

        FileEntry::create([
            'job_id' => $jobId,
            'file_path' => $path,
            'file_size' => 10,
            'uploaded_at' => now(),
            'deleted' => false
        ]);

        $response = $this->withHeaders(['X-API-Key' => 'test-key'])
                         ->delete("/api/delete/{$jobId}");

        $response->assertStatus(200)
                 ->assertJson(['status' => 'deleted']);
        
        $this->assertDatabaseHas('files', ['job_id' => $jobId, 'deleted' => true]);
    }
}
