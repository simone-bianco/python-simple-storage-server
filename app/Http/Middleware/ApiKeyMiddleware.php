<?php

namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;
use Symfony\Component\HttpFoundation\Response;

class ApiKeyMiddleware
{
    /**
     * Handle an incoming request.
     *
     * @param  \Closure(\Illuminate\Http\Request): (\Symfony\Component\HttpFoundation\Response)  $next
     */
    public function handle(Request $request, Closure $next): Response
    {
        $apiKey = config('storage.api_key');
        
        // Support Authorization Bearer or X-API-Key
        $token = $request->bearerToken() ?? $request->header('X-API-Key');

        if (!$token || $token !== $apiKey) {
            return response()->json(['error' => 'Invalid or missing API key'], 401);
        }

        return $next($request);
    }
}
