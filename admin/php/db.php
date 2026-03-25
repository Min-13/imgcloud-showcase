<?php
/**
 * Database connection module for LAB05
 * Provides PDO connection with persistent connections
 */

class Database {
    private static $instance = null;
    private $pdo;
    
    /**
     * Private constructor - singleton pattern
     */
    private function __construct() {
        $db_url = getenv('DATABASE_URL');
        if (!$db_url) {
            throw new Exception("DATABASE_URL environment variable not set");
        }
        
        $config = $this->parseDatabaseUrl($db_url);
        
        $dsn = sprintf(
            "pgsql:host=%s;port=%d;dbname=%s",
            $config['host'],
            $config['port'],
            $config['database']
        );
        
        $options = [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            PDO::ATTR_PERSISTENT => true,
            PDO::ATTR_EMULATE_PREPARES => false
        ];
        
        $this->pdo = new PDO(
            $dsn,
            $config['username'],
            $config['password'],
            $options
        );
        
        // TODO: Pre-create some connections to warm up the pool
        // Test the connection by executing a simple query like "SELECT 1"
    }
    
    /**
     * Get singleton instance
     */
    public static function getInstance() {
        if (self::$instance === null) {
            self::$instance = new self();
        }
        return self::$instance;
    }
    
    /**
     * Get PDO connection
     */
    public function getConnection() {
        return $this->pdo;
    }
    
    /**
     * Parse DATABASE_URL into components
     */
    private function parseDatabaseUrl($url) {
        $parsed = parse_url($url);
        
        if (!$parsed) {
            throw new Exception("Invalid DATABASE_URL format");
        }
        
        return [
            'host' => $parsed['host'],
            'port' => $parsed['port'] ?? 5432,
            'database' => ltrim($parsed['path'], '/'),
            'username' => $parsed['user'],
            'password' => $parsed['pass']
        ];
    }
    
    /**
     * Execute a query and return all results
     */
    public function query($sql, $params = []) {
        $stmt = $this->pdo->prepare($sql);
        $stmt->execute($params);
        return $stmt->fetchAll(PDO::FETCH_ASSOC);
    }
    
    /**
     * Alias for query() - used by endpoints
     */
    public function executeQuery($sql, $params = []) {
        return $this->query($sql, $params);
    }
    
    /**
     * Execute a query and return one result
     */
    public function queryOne($sql, $params = []) {
        $stmt = $this->pdo->prepare($sql);
        $stmt->execute($params);
        return $stmt->fetch(PDO::FETCH_ASSOC);
    }
}

// Create global instance for use in endpoints
$db = Database::getInstance();
