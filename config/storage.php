<?php

return [
    'api_key' => env('STORAGE_API_KEY', 'change-me-in-production'),
    'path' => env('STORAGE_PATH', 'storage'), // Not directly used by filesystems usually, but good for ref
    'auto_delete' => env('AUTO_DELETE', true),
    'admin_username' => env('ADMIN_USERNAME', 'admin'),
    'admin_password' => env('ADMIN_PASSWORD', '@Password1234.'),
    'rate_limit_ui' => env('RATE_LIMIT_UI', 60),
    'rate_limit_login' => env('RATE_LIMIT_LOGIN', 10),
];
