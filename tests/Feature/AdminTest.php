<?php

namespace Tests\Feature;

use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Foundation\Testing\WithFaker;
use Tests\TestCase;
use App\Models\User;
use Illuminate\Support\Facades\Hash;

class AdminTest extends TestCase
{
    use RefreshDatabase;

    protected function setUp(): void
    {
        parent::setUp();
        // Create an admin user for testing
        // We don't need to Config::set anymore for auth, but maybe for seeder if we ran it.
        // But here we create user directly.
    }

    public function test_login_page_loads()
    {
        $response = $this->get('/admin/login');
        $response->assertStatus(200);
    }

    public function test_admin_login_success()
    {
        $user = User::factory()->create([
            'email' => 'admin@test.com',
            'password' => Hash::make('password'),
        ]);

        $response = $this->post('/admin/login', [
            'username' => 'admin@test.com', // Controller expects 'username' input mapped to email
            'password' => 'password'
        ]);

        $response->assertStatus(302);
        // assertRedirectToRoute is better if named route exists, otherwise check path
        // $response->assertRedirect(route('admin.dashboard')); 
        // Logic check:
        $location = $response->headers->get('Location');
        $this->assertTrue(str_contains($location, '/admin'), "Redirected to $location instead of /admin");
        
        $this->assertAuthenticatedAs($user);
    }

    public function test_admin_login_failure()
    {
        $user = User::factory()->create([
            'email' => 'admin@test.com',
            'password' => Hash::make('password'),
        ]);

        $response = $this->post('/admin/login', [
            'username' => 'admin@test.com',
            'password' => 'wrong'
        ]);

        $response->assertSessionHas('error');
        $this->assertGuest();
    }

    public function test_dashboard_protected()
    {
        $response = $this->get('/admin/dashboard');
        $response->assertRedirect('/admin/login');
    }

    public function test_dashboard_accessible_when_logged_in()
    {
        $user = User::factory()->create();

        $this->actingAs($user)
             ->get('/admin/dashboard')
             ->assertStatus(200)
             ->assertSee('Dashboard');
    }
}
