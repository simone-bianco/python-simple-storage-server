<?php

namespace App\Jobs;

use App\Models\FileEntry;
use Illuminate\Bus\Queueable;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Foundation\Bus\Dispatchable;
use Illuminate\Queue\InteractsWithQueue;
use Illuminate\Queue\SerializesModels;
use Illuminate\Support\Facades\Log;

class DeleteFileJob implements ShouldQueue
{
    use Dispatchable, InteractsWithQueue, Queueable, SerializesModels;

    protected $jobId;

    /**
     * Create a new job instance.
     */
    public function __construct($jobId)
    {
        $this->jobId = $jobId;
    }

    /**
     * Execute the job.
     */
    public function handle(): void
    {
        try {
            $file = FileEntry::where('job_id', $this->jobId)->first();
            
            if (!$file) return;

            if (file_exists($file->file_path)) {
                unlink($file->file_path);
            }

            $file->update(['deleted' => true]);
            
        } catch (\Exception $e) {
            Log::error("Failed to delete file for job {$this->jobId}: " . $e->getMessage());
        }
    }
}
