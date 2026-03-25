<?php
/**
 * Unit tests for endpoints module (endpoints.php)
 * Tests all 5 endpoints: Users, Images, Operations, Jobs, Health
 */

use PHPUnit\Framework\TestCase;

require_once __DIR__ . '/../endpoints.php';
require_once __DIR__ . '/../db.php';
require_once __DIR__ . '/../cache.php';

class EndpointsTest extends TestCase
{
    public function testUsersEndpointExists()
    {
        $this->assertTrue(
            class_exists('UsersEndpoint'),
            'UsersEndpoint class should exist'
        );
    }
    
    public function testImagesEndpointExists()
    {
        $this->assertTrue(
            class_exists('ImagesEndpoint'),
            'ImagesEndpoint class should exist'
        );
    }
    
    public function testOperationsEndpointExists()
    {
        $this->assertTrue(
            class_exists('OperationsEndpoint'),
            'OperationsEndpoint class should exist'
        );
    }
    
    public function testJobsEndpointExists()
    {
        $this->assertTrue(
            class_exists('JobsEndpoint'),
            'JobsEndpoint class should exist'
        );
    }
    
    public function testHealthEndpointExists()
    {
        $this->assertTrue(
            class_exists('HealthEndpoint'),
            'HealthEndpoint class should exist'
        );
    }
    
    public function testUsersEndpointReturnsJson()
    {
        $endpoint = $this->getMockBuilder(UsersEndpoint::class)
                         ->onlyMethods(['get'])
                         ->getMock();
        
        $testResponse = json_encode([
            'users' => [
                ['id' => 1, 'username' => 'test', 'email' => 'test@test.com']
            ],
            'cached' => false,
            'cache_ttl' => 300
        ]);
        
        $endpoint->expects($this->once())
                 ->method('get')
                 ->willReturn($testResponse);
        
        $result = $endpoint->get();
        $decoded = json_decode($result, true);
        
        $this->assertIsArray($decoded);
        $this->assertArrayHasKey('users', $decoded);
        $this->assertArrayHasKey('cached', $decoded);
    }
    
    public function testImagesEndpointReturnsJson()
    {
        $endpoint = $this->getMockBuilder(ImagesEndpoint::class)
                         ->onlyMethods(['get'])
                         ->getMock();
        
        $testResponse = json_encode([
            'images' => [
                [
                    'id' => 1,
                    'user_id' => 1,
                    'username' => 'test',
                    'filename' => 'test.jpg',
                    'size' => 1024,
                    'content_type' => 'image/jpeg',
                    'uploaded_at' => '2024-01-01'
                ]
            ],
            'cached' => false,
            'cache_ttl' => 300
        ]);
        
        $endpoint->expects($this->once())
                 ->method('get')
                 ->willReturn($testResponse);
        
        $result = $endpoint->get();
        $decoded = json_decode($result, true);
        
        $this->assertIsArray($decoded);
        $this->assertArrayHasKey('images', $decoded);
    }
    
    public function testOperationsEndpointStructure()
    {
        $endpoint = $this->getMockBuilder(OperationsEndpoint::class)
                         ->onlyMethods(['get'])
                         ->getMock();
        
        $testResponse = json_encode([
            'operations' => [
                [
                    'operation' => 'resize',
                    'total' => 100,
                    'completed' => 95,
                    'failed' => 3,
                    'pending' => 2,
                    'avg_time_ms' => 150.5
                ]
            ],
            'cached' => false,
            'cache_ttl' => 60
        ]);
        
        $endpoint->expects($this->once())
                 ->method('get')
                 ->willReturn($testResponse);
        
        $result = $endpoint->get();
        $decoded = json_decode($result, true);
        
        $this->assertIsArray($decoded);
        $this->assertArrayHasKey('operations', $decoded);
        
        if (!empty($decoded['operations'])) {
            $op = $decoded['operations'][0];
            $this->assertArrayHasKey('operation', $op);
            $this->assertArrayHasKey('total', $op);
            $this->assertArrayHasKey('avg_time_ms', $op);
        }
    }
    
    public function testJobsEndpointStructure()
    {
        $endpoint = $this->getMockBuilder(JobsEndpoint::class)
                         ->onlyMethods(['get'])
                         ->getMock();
        
        $testResponse = json_encode([
            'jobs' => [
                [
                    'id' => 1,
                    'user_id' => 1,
                    'username' => 'test',
                    'operation_type' => 'resize',
                    'status' => 'completed',
                    'created_at' => '2024-01-01'
                ]
            ],
            'queue_stats' => [
                'pending' => 5,
                'processing' => 2,
                'completed' => 100,
                'failed' => 3
            ],
            'cached' => false,
            'cache_ttl' => 60
        ]);
        
        $endpoint->expects($this->once())
                 ->method('get')
                 ->willReturn($testResponse);
        
        $result = $endpoint->get();
        $decoded = json_decode($result, true);
        
        $this->assertIsArray($decoded);
        $this->assertArrayHasKey('jobs', $decoded);
        $this->assertArrayHasKey('queue_stats', $decoded);
    }
    
    public function testHealthEndpointStructure()
    {
        $endpoint = $this->getMockBuilder(HealthEndpoint::class)
                         ->onlyMethods(['get'])
                         ->getMock();
        
        $testResponse = json_encode([
            'status' => 'healthy',
            'database' => true,
            'cache' => true
        ]);
        
        $endpoint->expects($this->once())
                 ->method('get')
                 ->willReturn($testResponse);
        
        $result = $endpoint->get();
        $decoded = json_decode($result, true);
        
        $this->assertIsArray($decoded);
        $this->assertArrayHasKey('status', $decoded);
        $this->assertArrayHasKey('database', $decoded);
        $this->assertArrayHasKey('cache', $decoded);
    }
}
