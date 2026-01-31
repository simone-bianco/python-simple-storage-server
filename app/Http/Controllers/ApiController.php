<?php

namespace App\Http\Controllers;

use App\Models\FileEntry;
use App\Models\Setting;
use App\Jobs\DeleteFileJob;
use App\Services\DiskUsageService;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Storage;
use Illuminate\Support\Facades\Log;
use OpenApi\Annotations as OA;

class ApiController extends Controller
{
    /**
     * @OA\Get(
     *      path="/health",
     *      operationId="healthCheck",
     *      tags={"System"},
     *      summary="Check system health",
     *      @OA\Response(
     *          response=200,
     *          description="Successful operation",
     *       )
     * )
     */
    public function health()
    {
        return response()->json([
            'status' => 'ok',
            'service' => 'simple-storage-server',
            'timestamp' => now()->toIso8601String()
        ]);
    }

    /**
     * @OA\Post(
     *      path="/upload",
     *      operationId="uploadFile",
     *      tags={"Files"},
     *      summary="Upload a file",
     *      // security={{"ApiKeyAuth": {}}},
     *      @OA\RequestBody(
     *          required=true,
     *          @OA\MediaType(
     *              mediaType="multipart/form-data",
     *              @OA\Schema(
     *                  @OA\Property(property="file", type="string", format="binary"),
     *                  @OA\Property(property="job_id", type="string")
     *              )
     *          ),
     *          @OA\MediaType(
     *              mediaType="application/octet-stream",
     *              @OA\Schema(type="string", format="binary")
     *          )
     *      ),
     *      @OA\Parameter(
     *          name="X-Job-Id",
     *          in="header",
     *          description="Job ID if uploading raw binary",
     *          required=false,
     *          @OA\Schema(type="string")
     *      ),
     *      @OA\Response(
     *          response=201,
     *          description="File uploaded successfully",
     *      ),
     *      @OA\Response(response=400, description="Bad Request"),
     *      @OA\Response(response=401, description="Unauthorized")
     * )
     */
    public function upload(Request $request)
    {
        $jobId = $request->input('job_id') ?? $request->header('X-Job-Id');
        
        if (!$jobId) {
            return response()->json(['error' => 'Missing job_id'], 400);
        }

        $content = null;
        Log::info("Upload request: " . json_encode($request->all()));
        Log::info("Has file: " . ($request->hasFile('file') ? 'YES' : 'NO'));
        
        if ($request->hasFile('file')) {
            // Use get() method on UploadedFile which handles test files correctly
            $content = $request->file('file')->get();
            Log::info("Content length from file object: " . strlen($content));
        } else {
            $content = $request->getContent();
            Log::info("Content length from body: " . strlen($content));
        }

        if (empty($content)) {
            Log::error("No content found");
            return response()->json(['error' => 'No file data received'], 400);
        }

        $filename = "{$jobId}.zip";
        // Ensure storage directory exists
        if (!file_exists(storage_path('app'))) {
             mkdir(storage_path('app'), 0755, true);
        }
        
        // Save file using local disk (storage/app)
        Storage::disk('local')->put($filename, $content);

        // Calculate absolute path as Python app did, or use what Storage gives
        $fullPath = Storage::disk('local')->path($filename);

        FileEntry::updateOrCreate(
            ['job_id' => $jobId],
            [
                'file_path' => $fullPath,
                'file_size' => strlen($content),
                'uploaded_at' => now(),
                'deleted' => false
            ]
        );

        return response()->json([
            'status' => 'uploaded',
            'job_id' => $jobId,
            'file_size' => strlen($content),
            'download_url' => "/download/{$jobId}"
        ], 201);
    }

    /**
     * @OA\Get(
     *      path="/download/{job_id}",
     *      operationId="downloadFile",
     *      tags={"Files"},
     *      summary="Download a file",
     *      security={{"ApiKeyAuth": {}}},
     *      @OA\Parameter(
     *          name="job_id",
     *          in="path",
     *          required=true,
     *          @OA\Schema(type="string")
     *      ),
     *      @OA\Parameter(
     *          name="keep",
     *          in="query",
     *          description="If true, do not auto-delete even if configured",
     *          required=false,
     *          @OA\Schema(type="boolean")
     *      ),
     *      @OA\Response(
     *          response=200,
     *          description="File content",
     *      ),
     *      @OA\Response(response=404, description="File not found")
     * )
     */
    public function download(Request $request, $job_id)
    {
        $file = FileEntry::where('job_id', $job_id)->first();

        if (!$file) {
            return response()->json(['error' => 'Job not found'], 404);
        }

        if ($file->deleted) {
            return response()->json(['error' => 'File already deleted'], 410);
        }

        if (!file_exists($file->file_path)) {
            return response()->json(['error' => 'File not found on disk'], 404);
        }

        $keep = $request->query('keep', 'false') === 'true';
        $autoDelete = config('storage.auto_delete') && !$keep;

        $file->update(['downloaded_at' => now()]);

        // If auto-delete, dispatch job to delete after slight delay
        if ($autoDelete) {
            // Delay 2 seconds to ensure download starts/finishes buffer
            DeleteFileJob::dispatch($job_id)->delay(now()->addSeconds(2));
        }

        return response()->download($file->file_path, "{$job_id}.zip");
    }

    public function delete($job_id)
    {
        $file = FileEntry::where('job_id', $job_id)->where('deleted', false)->first();

        if (!$file) {
            return response()->json(['error' => 'Job not found or already deleted'], 404);
        }

        if (file_exists($file->file_path)) {
            unlink($file->file_path);
        }

        $file->update(['deleted' => true]);

        return response()->json([
            'status' => 'deleted',
            'job_id' => $job_id
        ]);
    }

    /**
     * @OA\Get(
     *      path="/check/{job_id}",
     *      operationId="checkFile",
     *      tags={"Files"},
     *      summary="Check if a file exists",
     *      security={{"ApiKeyAuth": {}}},
     *      @OA\Parameter(
     *          name="job_id",
     *          in="path",
     *          required=true,
     *          @OA\Schema(type="string")
     *      ),
     *      @OA\Response(
     *          response=200,
     *          description="File exists",
     *          @OA\JsonContent(
     *              @OA\Property(property="status", type="string", example="exists")
     *          )
     *      ),
     *      @OA\Response(response=404, description="File not found")
     * )
     */
    public function check($job_id)
    {
        $file = FileEntry::where('job_id', $job_id)->first();

        if (!$file || $file->deleted || !file_exists($file->file_path)) {
            return response()->json(['error' => 'Job not found'], 404);
        }

        return response()->json(['status' => 'exists'], 200);
    }

    public function listFiles()
    {
        $files = FileEntry::orderBy('uploaded_at', 'desc')->limit(100)->get();
        
        return response()->json([
            'files' => $files,
            'count' => $files->count()
        ]);
    }

    public function cleanup(\App\Services\CleanupService $service)
    {
        return response()->json($service->run());
    }
}
