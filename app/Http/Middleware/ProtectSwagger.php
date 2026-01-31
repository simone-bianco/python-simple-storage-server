<?php

namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;
use Symfony\Component\HttpFoundation\Response;

class ProtectSwagger
{
    /**
     * Handle an incoming request.
     *
     * @param  \Closure(\Illuminate\Http\Request): (\Symfony\Component\HttpFoundation\Response)  $next
     */
    public function handle(Request $request, Closure $next): Response
    {
        $password = config('app.swagger_password');

        if (!$password) {
             // If no password set, open access (or maybe deny? User said *definable* in env)
             // Let's assume if env is Set, we protect. If not, open?
             // Or maybe strictly protect. Let's use env('SWAGGER_PASSWORD').
             // Better to access via config if I add it to config/app.php or services.php
             // For now I'll access env directly or config.
             $password = env('SWAGGER_PASSWORD');
        }

        if (!$password) {
            return $next($request);
        }

        $user = $request->getUser();
        $pass = $request->getPassword();

        if ($user !== 'admin' || $pass !== $password) {
            return response('Unauthorized', 401, ['WWW-Authenticate' => 'Basic']);
        }

        return $next($request);
    }
}
