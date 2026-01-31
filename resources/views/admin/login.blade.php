<!DOCTYPE html>
<html>

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Simple Storage - Login</title>
    <link rel="stylesheet" href="{{ asset('css/admin.css') }}">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
</head>

<body class="auth-container">
    <div class="card auth-card animate-fade-in">
        <h2
            style="text-align: center; margin-bottom: 2rem; display: flex; align-items: center; justify-content: center; gap: 0.5rem; color: var(--primary);">
            <svg width="32" height="32" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
            </svg>
            Simple Storage
        </h2>
        @if (session('error'))
            <div
                style="background: rgba(239, 68, 68, 0.2); border: 1px solid var(--danger); color: #fca5a5; padding: 0.75rem; border-radius: 0.5rem; margin-bottom: 1.5rem; text-align: center;">
                {{ session('error') }}
            </div>
        @endif
        @if (session('success'))
            <div
                style="background: rgba(34, 197, 94, 0.2); border: 1px solid var(--success); color: #86efac; padding: 0.75rem; border-radius: 0.5rem; margin-bottom: 1.5rem; text-align: center;">
                {{ session('success') }}
            </div>
        @endif
        <form method="POST" action="{{ route('login') }}">
            @csrf
            <div style="margin-bottom: 1rem;">
                <label
                    style="display: block; margin-bottom: 0.5rem; color: var(--text-muted); font-size: 0.875rem;">Username</label>
                <input type="text" name="username" required autofocus placeholder="Enter admin username">
            </div>
            <div style="margin-bottom: 2rem;">
                <label
                    style="display: block; margin-bottom: 0.5rem; color: var(--text-muted); font-size: 0.875rem;">Password</label>
                <input type="password" name="password" required placeholder="Enter password">
            </div>
            <button type="submit" class="btn btn-primary"
                style="width: 100%; padding: 0.75rem; font-size: 1rem;">Login</button>
        </form>
    </div>
</body>

</html>
