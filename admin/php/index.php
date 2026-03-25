<?php
/**
 * Admin Interface PHP Application.
 * This file sets up routing. Students implement endpoints in endpoints.php.
 */

require_once 'endpoints.php';

// Helper function to send JSON response
function sendJson($data, $status = 200) {
    http_response_code($status);
    header('Content-Type: application/json');
    echo json_encode($data);
    exit;
}

// Get request path
$request_uri = $_SERVER['REQUEST_URI'];
$path = parse_url($request_uri, PHP_URL_PATH);

// Route requests
if ($path === '/' || $path === '/index.php') {
    // Serve the admin UI
    $static_dir = dirname(__FILE__) . '/static';
    readfile($static_dir . '/admin.html');
    exit;
}

// API routes
if ($path === '/api/users') {
    sendJson(UsersEndpoint::get());
}

if ($path === '/api/images') {
    sendJson(ImagesEndpoint::get());
}

if ($path === '/api/operations') {
    sendJson(OperationsEndpoint::get());
}

if ($path === '/api/jobs') {
    sendJson(JobsEndpoint::get());
}

if ($path === '/health') {
    sendJson(HealthEndpoint::get());
}

// 404 for unknown routes
http_response_code(404);
echo "Not Found";
?>
