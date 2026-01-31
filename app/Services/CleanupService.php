<?php

namespace App\Services;

use App\Models\FileEntry;
use App\Models\Setting;
use Illuminate\Support\Facades\Log;

class CleanupService
{
    public function run()
    {
        // Check if cleanup enabled
        $enabled = Setting::find('cleanup_enabled');
        if (!$enabled || $enabled->value !== 'true') {
            return [
                'status' => 'skipped',
                'message' => 'Cleanup is disabled',
                'deleted_count' => 0
            ];
        }

        $ageSetting = Setting::find('cleanup_max_age_hours');
        $maxAgeHours = $ageSetting ? (int)$ageSetting->value : 24;

        $cutoff = now()->subHours($maxAgeHours);

        $files = FileEntry::where('deleted', false)
            ->whereNotNull('downloaded_at')
            ->where('downloaded_at', '<', $cutoff)
            ->get();

        $deletedCount = 0;
        foreach ($files as $file) {
            if (file_exists($file->file_path)) {
                try {
                    unlink($file->file_path);
                } catch (\Exception $e) {
                    Log::error("Cleanup failed for {$file->job_id}: {$e->getMessage()}");
                    continue;
                }
            }
            $file->update(['deleted' => true]);
            $deletedCount++;
        }

        // Update last run
        Setting::updateOrCreate(
            ['key' => 'cleanup_last_run'],
            ['value' => now()->toIso8601String(), 'updated_at' => now()]
        );

        return [
            'status' => 'completed',
            'deleted_count' => $deletedCount,
            'max_age_hours' => $maxAgeHours,
            'timestamp' => now()->toIso8601String()
        ];
    }
}
