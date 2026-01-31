<?php

use App\Http\Controllers\AdminController;
use Illuminate\Support\Facades\Route;

Route::get('/', function () {
    return redirect('/admin/login');
});

// API Routes moved to routes/api.php

// Admin Routes (will be implemented next)
Route::prefix('admin')->group(function () {
    // Login
    Route::get('/login', [AdminController::class, 'loginForm'])->name('login');
    Route::post('/login', [AdminController::class, 'login']);
    Route::get('/logout', [AdminController::class, 'logout'])->name('logout');

    // Protected
    Route::middleware(['auth'])->group(function () {
        Route::get('/', [AdminController::class, 'dashboard'])->name('admin.dashboard');
        Route::get('/dashboard', [AdminController::class, 'dashboard']);
        Route::get('/statistics', [AdminController::class, 'statistics'])->name('admin.statistics');
        Route::get('/settings', [AdminController::class, 'settings'])->name('admin.settings');
        Route::post('/settings', [AdminController::class, 'updateSettings']);
        Route::get('/download/{job_id}', [AdminController::class, 'download'])->name('admin.download');

        // Logo upload (if keeping feature)
        Route::post('/settings/logo', [AdminController::class, 'uploadLogo'])->name('admin.upload_logo');
    });
});
