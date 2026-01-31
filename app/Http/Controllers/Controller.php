<?php

namespace App\Http\Controllers;

use OpenApi\Annotations as OA;

/**
 * @OA\Info(
 *      version="1.0.0",
 *      title="Simple Storage Server API",
 *      description="API for uploading, downloading, and managing files.",
 *      @OA\Contact(
 *          email="admin@example.com"
 *      )
 * )
 *
 * @OA\SecurityScheme(
 *     securityScheme="ApiKeyAuth",
 *     type="apiKey",
 *     in="header",
 *     name="X-API-Key"
 * )
 *
 * @OA\Get(
 *     path="/",
 *     description="Home Page",
 *     @OA\Response(response="default", description="Welcome page")
 * )
 */
abstract class Controller
{
    //
}
