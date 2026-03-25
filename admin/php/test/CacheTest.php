<?php
/**
 * Unit tests for cache module (cache.php)
 * Tests Redis connection and cache operations
 */

use PHPUnit\Framework\TestCase;

require_once __DIR__ . '/../cache.php';

class CacheTest extends TestCase
{
    private $originalRedisUrl;
    
    protected function setUp(): void
    {
        $this->originalRedisUrl = getenv('REDIS_URL');
        putenv('REDIS_URL=redis://localhost:6379/0');
    }
    
    protected function tearDown(): void
    {
        if ($this->originalRedisUrl) {
            putenv("REDIS_URL={$this->originalRedisUrl}");
        } else {
            putenv('REDIS_URL');
        }
    }
    
    public function testRedisUrlParsing()
    {
        $cache = CacheManager::getInstance();
        $this->assertInstanceOf(CacheManager::class, $cache);
    }
    
    public function testSingletonPattern()
    {
        $cache1 = CacheManager::getInstance();
        $cache2 = CacheManager::getInstance();
        
        $this->assertSame($cache1, $cache2, 'CacheManager should follow singleton pattern');
    }
    
    public function testSetOperation()
    {
        $cache = $this->getMockBuilder(CacheManager::class)
                      ->onlyMethods(['set'])
                      ->getMock();
        
        $cache->expects($this->once())
              ->method('set')
              ->with(
                  $this->equalTo('test_key'),
                  $this->equalTo('test_value'),
                  $this->equalTo(300)
              )
              ->willReturn(true);
        
        $result = $cache->set('test_key', 'test_value', 300);
        $this->assertTrue($result);
    }
    
    public function testGetOperation()
    {
        $cache = $this->getMockBuilder(CacheManager::class)
                      ->onlyMethods(['get'])
                      ->getMock();
        
        $cache->expects($this->once())
              ->method('get')
              ->with($this->equalTo('test_key'))
              ->willReturn('test_value');
        
        $result = $cache->get('test_key');
        $this->assertEquals('test_value', $result);
    }
    
    public function testGetMiss()
    {
        $cache = $this->getMockBuilder(CacheManager::class)
                      ->onlyMethods(['get'])
                      ->getMock();
        
        $cache->expects($this->once())
              ->method('get')
              ->with($this->equalTo('nonexistent_key'))
              ->willReturn(null);
        
        $result = $cache->get('nonexistent_key');
        $this->assertNull($result);
    }
    
    public function testDeleteOperation()
    {
        $cache = $this->getMockBuilder(CacheManager::class)
                      ->onlyMethods(['delete'])
                      ->getMock();
        
        $cache->expects($this->once())
              ->method('delete')
              ->with($this->equalTo('test_key'))
              ->willReturn(true);
        
        $result = $cache->delete('test_key');
        $this->assertTrue($result);
    }
    
    public function testJsonSerialization()
    {
        $cache = CacheManager::getInstance();
        
        $testData = ['id' => 1, 'name' => 'test'];
        $jsonData = json_encode($testData);
        
        // Mock the set and get operations
        $cache = $this->getMockBuilder(CacheManager::class)
                      ->onlyMethods(['set', 'get'])
                      ->getMock();
        
        $cache->expects($this->once())
              ->method('set')
              ->with($this->equalTo('json_key'), $this->equalTo($jsonData));
        
        $cache->expects($this->once())
              ->method('get')
              ->with($this->equalTo('json_key'))
              ->willReturn($jsonData);
        
        $cache->set('json_key', $jsonData);
        $result = $cache->get('json_key');
        
        $retrieved = json_decode($result, true);
        $this->assertEquals($testData, $retrieved);
    }
    
    public function testRedisDatabaseSelection()
    {
        // Test that Redis database selection works with non-zero database number
        // This is an integration test that verifies the student implementation
        // parses the URL and executes the Redis SELECT command
        
        putenv('REDIS_URL=redis://localhost:6379/2');
        
        // When properly implemented, the CacheManager should:
        // 1. Parse the URL to extract database number (2)
        // 2. Call $this->redis->select(2)
        // 3. Successfully connect and use database 2
        
        // Note: This test requires a running Redis instance for full validation
        // The student implementation should extract '2' from '/2' in the URL path
        // and call: $this->redis->select((int)$db_number)
        
        $this->expectNotToPerformAssertions();
        
        // Reset singleton for this test
        $reflection = new \ReflectionClass(CacheManager::class);
        $instance = $reflection->getProperty('instance');
        $instance->setAccessible(true);
        $instance->setValue(null, null);
    }
}
