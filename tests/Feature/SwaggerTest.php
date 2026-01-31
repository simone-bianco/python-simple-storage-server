<?php

namespace Tests\Feature;

use Tests\TestCase;
use Illuminate\Support\Facades\Config;

class SwaggerTest extends TestCase
{
    public function test_swagger_ui_is_protected()
    {
        // Set password
        Config::set('app.swagger_password', 'secret');
        // Or env, but config is what middleware uses if I changed it to config.
        // Wait, my middleware used config('app.swagger_password') OR env.
        // Let's set env in phpunit.xml logic or just config since env helper reads config in runtime often if cached, but here testing.
        // Actually, my middleware code: $password = config('app.swagger_password'); then check env if null.
        // Laravel's config('app.swagger_password') is null by default unless I add it to config/app.php.
        // So it likely falls back to env().
        
        // Let's rely on the middleware logic I wrote:
        // $password = env('SWAGGER_PASSWORD');
        
        // Verify 401 without auth
        $this->get('/api/documentation')
             ->assertStatus(401);

        // Verify 200 with auth
        $this->withBasicAuth('admin', 'secret')
             ->get('/api/documentation')
             ->assertStatus(200);
    }
}
