<?php

namespace App\Http\Controllers;

use App\Models\FileEntry;
use App\Models\Setting;
use App\Services\DiskUsageService;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Storage;
use Illuminate\Support\Facades\Session;
use Illuminate\Support\Facades\Auth;

class AdminController extends Controller
{
    public function loginForm()
    {
        if (Auth::check()) {
            return redirect()->route('admin.dashboard');
        }
        return view('admin.login');
    }

    public function login(Request $request)
    {
        $credentials = $request->validate([
            'username' => ['required'],
        ]);

        if (Auth::attempt(['email' => $request->input('username'), 'password' => $request->input('password')])) {
            $request->session()->regenerate();
            return redirect()->route('admin.dashboard');
        }

        return back()->with('error', 'Credenziali non valide')->onlyInput('username');
    }

    public function logout(Request $request)
    {
        Auth::logout();
        $request->session()->invalidate();
        $request->session()->regenerateToken();

        return redirect()->route('login')->with('success', 'Logout effettuato con successo.');
    }

    public function dashboard(Request $request)
    {
        $files = FileEntry::orderBy('uploaded_at', 'desc')->paginate(15);
        
        $stats = [
            'total' => FileEntry::count(),
            'active' => FileEntry::where('deleted', false)->count(),
            'downloaded' => FileEntry::whereNotNull('downloaded_at')->count(),
            'total_size_human' => DiskUsageService::getStats()['used_human'] // Approximate or use database sum
        ];
        
        // Better to sum DB for file size
        $totalBytes = FileEntry::where('deleted', false)->sum('file_size');
        $stats['total_size_human'] = $this->formatBytes($totalBytes);

        return view('admin.dashboard', compact('files', 'stats'));
    }

    public function statistics()
    {
        $disk = DiskUsageService::getStats();
        
        $filesStats = [
            'total' => FileEntry::count(),
            'active' => FileEntry::where('deleted', false)->count(),
            'deleted' => FileEntry::where('deleted', true)->count(),
            'downloaded' => FileEntry::whereNotNull('downloaded_at')->count(),
            'total_size' => FileEntry::where('deleted', false)->sum('file_size'),
        ];
        
        $filesStats['total_size_human'] = $this->formatBytes($filesStats['total_size']);
        $storagePercent = $disk['total'] > 0 ? round(($filesStats['total_size'] / $disk['total']) * 100, 2) : 0;

        $recentFiles = FileEntry::orderBy('uploaded_at', 'desc')->limit(10)->get();

        return view('admin.statistics', compact('disk', 'filesStats', 'storagePercent', 'recentFiles'));
    }

    public function settings()
    {
        $cleanupEnabled = Setting::find('cleanup_enabled')->value ?? 'false';
        $maxAge = Setting::find('cleanup_max_age_hours')->value ?? 24;

        return view('admin.settings', compact('cleanupEnabled', 'maxAge'));
    }

    public function updateSettings(Request $request)
    {
        $cleanupEnabled = $request->has('cleanup_enabled') ? 'true' : 'false';
        $maxAge = $request->input('cleanup_max_age_hours', 24);

        $this->saveSetting('cleanup_enabled', $cleanupEnabled);
        $this->saveSetting('cleanup_max_age_hours', $maxAge);

        return back()->with('success', 'Impostazioni aggiornate con successo.');
    }

    public function download($jobId)
    {
        $file = FileEntry::where('job_id', $jobId)->firstOrFail();
        
        if (!file_exists($file->file_path)) {
            return back()->with('error', 'File non trovato su disco.');
        }

        // Admin download does not delete
        return response()->download($file->file_path, "{$jobId}.zip");
    }

    // Helper
    private function saveSetting($key, $value)
    {
        // Use updateOrCreate or similar
        // Since we disabled timestamps and use custom updated_at
         $setting = Setting::find($key);
         if ($setting) {
             $setting->update(['value' => $value, 'updated_at' => now()]);
         } else {
             Setting::create(['key' => $key, 'value' => $value, 'updated_at' => now()]);
         }
    }

    private function formatBytes($bytes, $precision = 1)
    {
        if ($bytes === 0 || $bytes === null) return '0 B';
        $units = ['B', 'KB', 'MB', 'GB', 'TB'];
        $pow = floor(($bytes ? log($bytes) : 0) / log(1024));
        $pow = min($pow, count($units) - 1);
        $bytes /= (1 << (10 * $pow));
        return round($bytes, $precision) . ' ' . $units[$pow];
    }
}
