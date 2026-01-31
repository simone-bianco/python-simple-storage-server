<?php

use App\Http\Controllers\ApiController;
use Illuminate\Support\Facades\Route;

/*
|--------------------------------------------------------------------------
| API Routes
|--------------------------------------------------------------------------
|
| Here is where you can register API routes for your application. These
| routes are loaded by the RouteServiceProvider and all of them will
| be assigned to the "api" middleware group. Make something great!
|
*/

Route::get('/health', [ApiController::class, 'health']);

// API Routes (Protected by API Key)
// Note: "api" middleware group is automatically applied, so CSRF is disabled by default.
Route::middleware(['auth.apikey'])->group(function () {
    Route::post('/upload', [ApiController::class, 'upload']);
    Route::get('/check/{job_id}', [ApiController::class, 'check']);
    Route::get('/download/{job_id}', [ApiController::class, 'download']);
    Route::delete('/delete/{job_id}', [ApiController::class, 'delete']);
    Route::get('/list', [ApiController::class, 'listFiles']);
    Route::post('/cleanup', [ApiController::class, 'cleanup']); // Path is relative to /api prefix
});
