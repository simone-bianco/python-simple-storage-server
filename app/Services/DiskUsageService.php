<?php

namespace App\Services;

class DiskUsageService
{
    /**
     * Get disk usage statistics for the storage directory.
     *
     * @return array
     */
    public static function getStats()
    {
        // Use the storage/app directory to calculate usage
        $path = storage_path('app');
        
        // Ensure path exists for calculation
        if (!file_exists($path)) {
            mkdir($path, 0755, true);
        }

        $total = disk_total_space($path);
        $free = disk_free_space($path);
        $used = $total - $free;
        
        return [
            'total' => $total,
            'used' => $used,
            'free' => $free,
            'percent' => $total > 0 ? round(($used / $total) * 100, 1) : 0,
            'total_human' => self::formatBytes($total),
            'used_human' => self::formatBytes($used),
            'free_human' => self::formatBytes($free),
        ];
    }

    /**
     * Format bytes to human readable string.
     *
     * @param int $bytes
     * @param int $precision
     * @return string
     */
    protected static function formatBytes($bytes, $precision = 1)
    {
        if ($bytes === 0 || $bytes === null) return '0 B';
        
        $units = ['B', 'KB', 'MB', 'GB', 'TB'];
        $pow = floor(($bytes ? log($bytes) : 0) / log(1024));
        $pow = min($pow, count($units) - 1);
        
        $bytes /= (1 << (10 * $pow));
        
        return round($bytes, $precision) . ' ' . $units[$pow];
    }
}
