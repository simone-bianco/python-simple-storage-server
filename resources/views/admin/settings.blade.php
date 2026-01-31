@extends('layouts.app')

@section('title', 'Settings - Simple Storage')

@section('content')
    <div style="max-width: 600px;">
        <h1 style="margin-bottom: 2rem;">Settings</h1>

        <div class="card">
            <form method="POST" action="{{ route('admin.settings') }}">
                @csrf
                <h3 style="margin-bottom: 1.5rem;">Cleanup Configuration</h3>

                <div style="margin-bottom: 1.5rem; display: flex; align-items: center; gap: 0.75rem;">
                    <input type="checkbox" id="cleanup_enabled" name="cleanup_enabled" value="true"
                        {{ $cleanupEnabled === 'true' ? 'checked' : '' }} style="width: auto;">
                    <label for="cleanup_enabled">Enable Automated Cleanup</label>
                </div>

                <div style="margin-bottom: 2rem;">
                    <label style="display: block; margin-bottom: 0.5rem;">Max File Age (Hours)</label>
                    <input type="number" name="cleanup_max_age_hours" value="{{ $maxAge }}" min="1">
                    <p style="color: var(--text-muted); font-size: 0.875rem; margin-top: 0.5rem;">Files downloaded older
                        than this will be deleted.</p>
                </div>

                <div style="border-top: 1px solid var(--border); padding-top: 1.5rem;">
                    <button type="submit" class="btn btn-primary">Save Settings</button>
                </div>
            </form>
        </div>

        <!-- Logo upload section could go here -->
    </div>
@endsection
