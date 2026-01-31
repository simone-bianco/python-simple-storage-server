<?php

namespace App\Console\Commands;

use App\Services\CleanupService;
use Illuminate\Console\Command;

class CleanupStorage extends Command
{
    /**
     * The name and signature of the console command.
     *
     * @var string
     */
    protected $signature = 'storage:cleanup';

    /**
     * The console command description.
     *
     * @var string
     */
    protected $description = 'Cleanup old downloaded files based on settings';

    /**
     * Execute the console command.
     */
    public function handle(CleanupService $service)
    {
        $this->info('Starting cleanup...');
        
        $result = $service->run();
        
        if ($result['status'] === 'skipped') {
            $this->warn($result['message']);
        } else {
            $this->info("Cleanup completed. Deleted {$result['deleted_count']} files.");
        }
    }
}
