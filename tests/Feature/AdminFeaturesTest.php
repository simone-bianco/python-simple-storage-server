<?php

namespace Tests\Feature;

use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Foundation\Testing\WithFaker;
use Tests\TestCase;
use Illuminate\Support\Facades\Config;

class AdminFeaturesTest extends TestCase
{
    use RefreshDatabase;

    protected function setUp(): void
    {
        parent::setUp();
        // Simulate logged in admin for these tests
        $user = \App\Models\User::factory()->create();
        $this->actingAs($user);
    }

    public function test_statistics_page_loads()
    {
        $response = $this->get('/admin/statistics');
        $response->assertStatus(200)
                 ->assertSee('Statistics');
    }

    public function test_settings_page_loads()
    {
        $response = $this->get('/admin/settings');
        $response->assertStatus(200)
                 ->assertSee('Settings');
    }

    public function test_update_settings()
    {
        $response = $this->from('/admin/settings')->post('/admin/settings', [
            'auto_delete' => 'true',
            'retention_days' => 7
        ]);

        $response->assertRedirect('/admin/settings');
        $response->assertSessionHas('success', 'Impostazioni aggiornate con successo.');
    }
}
