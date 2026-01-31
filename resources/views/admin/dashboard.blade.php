@extends('layouts.app')

@section('title', 'Dashboard - Simple Storage')

@section('content')
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem;">
        <h1>Dashboard</h1>
        <a href="{{ route('admin.dashboard') }}" class="btn btn-sm"
            style="background: var(--bg-card); border: 1px solid var(--border);">
            <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor"
                style="margin-right: 0.5rem;">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Refresh
        </a>
    </div>

    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-value">{{ number_format($stats['active']) }}</div>
            <div class="stat-label">Active Files</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{{ number_format($stats['downloaded']) }}</div>
            <div class="stat-label">Downloaded</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{{ $stats['total_size_human'] }}</div>
            <div class="stat-label">Total Storage Used</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{{ number_format($stats['total']) }}</div>
            <div class="stat-label">Total Lifetime Files</div>
        </div>
    </div>

    <div class="card">
        <h3>Recent Files</h3>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Job ID</th>
                        <th>Size</th>
                        <th>Uploaded</th>
                        <th>Downloaded</th>
                        <th>Status</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    @forelse($files as $file)
                        <tr>
                            <td style="font-family: monospace;">{{ $file->job_id }}</td>
                            <td>{{ $file->file_size_human }}</td>
                            <td>{{ $file->uploaded_at->format('d/m/Y H:i') }}</td>
                            <td>
                                @if ($file->downloaded_at)
                                    {{ $file->downloaded_at->format('d/m/Y H:i') }}
                                @else
                                    <span style="color: var(--text-muted);">-</span>
                                @endif
                            </td>
                            <td>
                                @if ($file->deleted)
                                    <span
                                        style="color: var(--danger); background: rgba(239, 68, 68, 0.1); padding: 0.25rem 0.5rem; border-radius: 999px; font-size: 0.75rem;">Deleted</span>
                                @elseif($file->downloaded_at)
                                    <span
                                        style="color: #f59e0b; background: rgba(245, 158, 11, 0.1); padding: 0.25rem 0.5rem; border-radius: 999px; font-size: 0.75rem;">Downloaded</span>
                                @else
                                    <span
                                        style="color: var(--success); background: rgba(34, 197, 94, 0.1); padding: 0.25rem 0.5rem; border-radius: 999px; font-size: 0.75rem;">Active</span>
                                @endif
                            </td>
                            <td>
                                @if (!$file->deleted)
                                    <a href="{{ route('admin.download', $file->job_id) }}" class="btn btn-sm btn-primary">
                                        <svg width="16" height="16" fill="none" viewBox="0 0 24 24"
                                            stroke="currentColor">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                                d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                                        </svg>
                                    </a>
                                @else
                                    <button disabled class="btn btn-sm" style="opacity: 0.5; cursor: not-allowed;">
                                        <svg width="16" height="16" fill="none" viewBox="0 0 24 24"
                                            stroke="currentColor">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                                d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                                        </svg>
                                    </button>
                                @endif
                            </td>
                        </tr>
                    @empty
                        <tr>
                            <td colspan="6" style="text-align: center; color: var(--text-muted); padding: 2rem;">No files
                                found.</td>
                        </tr>
                    @endforelse
                </tbody>
            </table>
        </div>

        <div style="margin-top: 1rem;">
            {{ $files->links('pagination::simple-default') }}
        </div>
    </div>
@endsection
