<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('files', function (Blueprint $table) {
            $table->string('job_id')->primary();
            $table->string('file_path');
            $table->bigInteger('file_size')->nullable();
            $table->timestamp('uploaded_at')->useCurrent();
            $table->timestamp('downloaded_at')->nullable();
            $table->boolean('deleted')->default(false);
            $table->index('deleted');
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('files');
    }
};
