# LAB04: Environment Variables Reference

This document provides a complete reference for all environment variables required to configure your LAB04 services.

## Frontend Service Environment Variables

Your frontend service needs environment variables to connect to all storage and processing services. These should be added to your frontend service configuration in `docker-compose.yml`.

### Processor Connection (Required - from LAB03)

**Required Variables:**
- `PORT` - Port the frontend listens on (inside container)
- `PROCESSOR_HOST` - Service name of your image processor container
- `PROCESSOR_HTTP_PORT` - HTTP port for processor health checks
- `PROCESSOR_GRPC_PORT` - gRPC port for image processing requests

**Example values:**
- `PORT=8080`
- `PROCESSOR_HOST=STUDENTNAME-imgprocessor`
- `PROCESSOR_HTTP_PORT=8080`
- `PROCESSOR_GRPC_PORT=50051`

### MinIO Configuration (LAB04 - Required)

**Required Variables:**
- `MINIO_HOST` - Service name of your MinIO container
- `MINIO_PORT` - MinIO API port (default: 9000)
- `MINIO_ACCESS_KEY` - MinIO root username
- `MINIO_SECRET_KEY` - MinIO root password
- `MINIO_BUCKET` - Bucket name for storing images
- `MINIO_SECURE` - Use HTTPS for MinIO connection (false for local Docker)

**Example values:**
- `MINIO_HOST=STUDENTNAME-minio`
- `MINIO_PORT=9000`
- `MINIO_ACCESS_KEY=minioadmin`
- `MINIO_SECRET_KEY=minioadmin123`
- `MINIO_BUCKET=images`
- `MINIO_SECURE=false`

### Redis Configuration (LAB04 - Required)

**Required Variables:**
- `REDIS_HOST` - Service name of your Redis container
- `REDIS_PORT` - Redis port (default: 6379)

**Example values:**
- `REDIS_HOST=STUDENTNAME-redis`
- `REDIS_PORT=6379`

### PostgreSQL Configuration (LAB04 - Required)

**Required Variables:**
- `DATABASE_URL` - Full PostgreSQL connection string
- `DB_SCHEMA` - Schema name within your database

**Connection String Format:**
```
postgresql://username:password@host:port/database
```

**Your connection details:**
- `username`: Your STUDENTNAME
- `password`: Password provided by instructor
- `host`: `420s26-postgres` (shared PostgreSQL service name)
- `port`: `5432` (PostgreSQL default port)
- `database`: Your database name (same as STUDENTNAME)

**Example value:**
- `DATABASE_URL=postgresql://STUDENTNAME:YOUR_PASSWORD@420s26-postgres:5432/STUDENTNAME`
- `DB_SCHEMA=STUDENTNAME`

### Session Configuration (LAB04 - Optional)

**Optional Variables:**
- `SECRET_KEY` - Secret key for session encryption (auto-generated if not provided)
- `SESSION_TIMEOUT` - Session expiration time in seconds (default: 3600 = 1 hour)

**Example values:**
- `SECRET_KEY=your-secret-key-here`
- `SESSION_TIMEOUT=3600`

## How to Configure Environment Variables

Environment variables should be added to your frontend service in `docker-compose.yml`. Refer to Docker Compose documentation for the correct syntax to add environment variables to a service.

**Remember to replace:**
- `STUDENTNAME` with your actual username
- `YOUR_PASSWORD` with the password provided by your instructor
- `YOUR_PORT` with your assigned port number from PORTS.md

## Important Notes

### Service Names vs. Host Names

When services communicate within Docker Compose, they use **service names** as hostnames:
- Use `STUDENTNAME-minio` not `localhost` or an IP address
- Docker's internal DNS resolves service names automatically
- This only works when services are on the same Docker network

### Security Considerations

**Development (Your Environment):**
- Simple passwords are acceptable (e.g., `minioadmin123`)
- `MINIO_SECURE=false` is fine for local testing

**Production (Future Deployments):**
- Use strong, randomly generated passwords
- Enable TLS/SSL (`MINIO_SECURE=true`)
- Never commit credentials to version control
- Use environment variable files (`.env`) that are gitignored

### Connection String Format

PostgreSQL connection strings follow this format:
```
postgresql://[user[:password]@][netloc][:port][/dbname]
```

Example breakdown for student `alice`:
- Protocol: `postgresql://`
- Username: `alice`
- Password: `SecurePass123` (provided by instructor)
- Host: `420s26-postgres` (Docker service name)
- Port: `5432` (PostgreSQL default)
- Database: `alice` (your database name)

Full string: `postgresql://alice:SecurePass123@420s26-postgres:5432/alice`

### Graceful Degradation

The frontend application is designed to work with partial configuration:
- **LAB03 mode**: Only processor variables needed
- **LAB04 mode**: All variables needed for full functionality

If LAB04 services are not configured, the app logs warnings and operates in LAB03 mode:
```
MinIO not available - storage features disabled
Redis not available - caching and session features disabled
DATABASE_URL not configured - authentication and storage features disabled
```

This allows you to:
1. Start with LAB03 configuration
2. Add services incrementally
3. Test each service as you add it
4. Debug connection issues one service at a time

## Troubleshooting

### "Service not available" errors

Check these in order:
1. Is the service running? (`docker compose ps`)
2. Is the environment variable set correctly? (`docker compose config`)
3. Is the service name spelled correctly?
4. Are both services on the same network?

### Connection refused errors

- Verify service names match in `docker-compose.yml` and environment variables
- Check that ports are correct (9000 for MinIO, 6379 for Redis, 5432 for PostgreSQL)
- Ensure all services are on the same Docker network

### Database connection errors

- Verify your DATABASE_URL is correct (check username, password, host, database name)
- Confirm your database exists: `docker exec -it 420s26-postgres psql -U STUDENTNAME -d STUDENTNAME -c "\dt"`
- Check that your schema exists: `docker exec -it 420s26-postgres psql -U STUDENTNAME -d STUDENTNAME -c "SELECT schema_name FROM information_schema.schemata;"`

## Testing Environment Variables

You can verify environment variables are set correctly:

```bash
# View all environment variables in running frontend container
docker exec STUDENTNAME-frontend env | grep -E "MINIO|REDIS|DATABASE|PROCESSOR"

# Test specific variable
docker exec STUDENTNAME-frontend printenv DATABASE_URL
```

This helps confirm:
- Variables are set in the container
- Values are correct
- No typos in variable names
