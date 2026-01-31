<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class FileEntry extends Model
{
    use HasFactory;

    protected $table = 'files';
    protected $primaryKey = 'job_id';
    public $incrementing = false;
    protected $keyType = 'string';
    public $timestamps = false;

    protected $fillable = [
        'job_id',
        'file_path',
        'file_size',
        'uploaded_at',
        'downloaded_at',
        'deleted',
    ];

    protected $casts = [
        'uploaded_at' => 'datetime',
        'downloaded_at' => 'datetime',
        'deleted' => 'boolean',
    ];

    
    /**
     * Get human readable file size.
     */
    public function getFileSizeHumanAttribute()
    {
        $bytes = $this->file_size;
        if ($bytes === null) return '-';
        $units = ['B', 'KB', 'MB', 'GB', 'TB'];

        for ($i = 0; $bytes > 1024; $i++) {
            $bytes /= 1024;
        }

        return round($bytes, 2) . ' ' . ($units[$i] ?? 'B');
    }
}
