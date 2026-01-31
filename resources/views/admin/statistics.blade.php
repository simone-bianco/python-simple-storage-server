@extends('layouts.app')

@section('title', 'Statistics - Simple Storage')

@section('content')
    <h1 style="margin-bottom: 2rem;">System Statistics</h1>

    <div class="card" style="margin-bottom: 2rem;">
        <h3 style="margin-bottom: 1rem;">Storage Usage</h3>

        <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem; font-size: 0.875rem;">
            <span>Used: {{ $disk['used_human'] }}</span>
            <span>Total: {{ $disk['total_human'] }}</span>
        </div>

        <div
            style="background: rgba(255,255,255,0.1); border-radius: 999px; height: 1rem; overflow: hidden; position: relative;">
            <div
                style="background: var(--primary); width: {{ $disk['percent'] }}%; height: 100%; border-radius: 999px; transition: width 1s ease-out;">
            </div>
        </div>

        <div style="margin-top: 0.5rem; text-align: right; color: var(--text-muted); font-size: 0.875rem;">
            {{ $disk['percent'] }}% Full
            @if ($filesStats['total_size'] > 0 && $disk['used'] > 0)
                <span style="margin-left: 1rem;">(App Storage:
                    {{ number_format(($filesStats['total_size'] / $disk['used']) * 100, 1) }}% of Usage)</span>
            @endif
        </div>
    </div>

    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-value">{{ $filesStats['total'] }}</div>
            <div class="stat-label">Total Files Ever</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{{ $filesStats['active'] }}</div>
            <div class="stat-label">Currently Active</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{{ $filesStats['deleted'] }}</div>
            <div class="stat-label">Deleted Files</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{{ $filesStats['total_size_human'] }}</div>
            <div class="stat-label">Total Active Size</div>
        </div>
    </div>
@endsection
