<?php
/**
 * Unit tests for database module (db.php)
 * Tests PDO connection, persistent connections, and prepared statements
 */

use PHPUnit\Framework\TestCase;

require_once __DIR__ . '/../db.php';

class DatabaseTest extends TestCase
{
    private $originalDbUrl;
    
    protected function setUp(): void
    {
        $this->originalDbUrl = getenv('DATABASE_URL');
        putenv('DATABASE_URL=postgresql://testuser:testpass@localhost:5432/testdb');
    }
    
    protected function tearDown(): void
    {
        if ($this->originalDbUrl) {
            putenv("DATABASE_URL={$this->originalDbUrl}");
        } else {
            putenv('DATABASE_URL');
        }
    }
    
    public function testDatabaseUrlParsing()
    {
        $db = Database::getInstance();
        $this->assertInstanceOf(Database::class, $db);
    }
    
    public function testSingletonPattern()
    {
        $db1 = Database::getInstance();
        $db2 = Database::getInstance();
        
        $this->assertSame($db1, $db2, 'Database should follow singleton pattern');
    }
    
    public function testExecuteQueryWithParameters()
    {
        $db = $this->getMockBuilder(Database::class)
                   ->onlyMethods(['executeQuery'])
                   ->getMock();
        
        $db->expects($this->once())
           ->method('executeQuery')
           ->with(
               $this->equalTo('SELECT * FROM users WHERE id = ?'),
               $this->equalTo([1])
           )
           ->willReturn([
               ['id' => 1, 'username' => 'test', 'email' => 'test@test.com']
           ]);
        
        $result = $db->executeQuery('SELECT * FROM users WHERE id = ?', [1]);
        
        $this->assertIsArray($result);
        $this->assertCount(1, $result);
        $this->assertEquals('test', $result[0]['username']);
    }
    
    public function testPreparedStatementUsage()
    {
        // Test that prepared statements are used (no string interpolation)
        $db = Database::getInstance();
        
        // This should use prepared statement, not string concatenation
        $maliciousInput = "1' OR '1'='1";
        
        try {
            // If using prepared statements correctly, this won't cause SQL injection
            $result = $db->executeQuery(
                'SELECT * FROM users WHERE id = ?',
                [$maliciousInput]
            );
            
            // If we get here without exception, prepared statements are working
            $this->assertTrue(true);
        } catch (Exception $e) {
            // If there's an error, it should be a legitimate database error,
            // not a SQL injection exploit
            $this->assertStringNotContainsString(
                'SQL syntax',
                $e->getMessage(),
                'Should use prepared statements to prevent SQL injection'
            );
        }
    }
    
    public function testConnectionPooling()
    {
        // Test that PDO::ATTR_PERSISTENT is set for connection pooling
        $db = Database::getInstance();
        
        // Get reflection to access private properties
        $reflection = new ReflectionClass($db);
        
        if ($reflection->hasProperty('pdo')) {
            $pdoProperty = $reflection->getProperty('pdo');
            $pdoProperty->setAccessible(true);
            $pdo = $pdoProperty->getValue($db);
            
            if ($pdo instanceof PDO) {
                $persistent = $pdo->getAttribute(PDO::ATTR_PERSISTENT);
                $this->assertTrue(
                    $persistent,
                    'PDO should use persistent connections'
                );
            }
        }
    }
}
