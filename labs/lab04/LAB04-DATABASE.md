# LAB04 - PostgreSQL Database

This document provides detailed information about using PostgreSQL for structured data storage in LAB04.

## What is PostgreSQL?

PostgreSQL is a powerful, open-source relational database management system (RDBMS) with over 30 years of active development.

**Key Features:**
- **ACID Compliant**: Reliable transactions with rollback support
- **Relational**: Complex queries with joins across multiple tables
- **Extensible**: Custom functions, data types, and operators
- **Standards Compliant**: Follows SQL standards closely
- **Rich Data Types**: JSON, arrays, geospatial, and more
- **Performance**: Advanced indexing and query optimization

## Database Schema

Your application uses three main tables in your personal schema:

### Users Table

```sql
CREATE TABLE STUDENTNAME.users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_username ON STUDENTNAME.users(username);
```

**Purpose**: Store user account information

**Fields**:
- `id`: Auto-incrementing primary key
- `username`: Unique username for login
- `password_hash`: Hashed password (never store plaintext!)
- `created_at`: Account creation timestamp

### Images Table

```sql
CREATE TABLE STUDENTNAME.images (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES STUDENTNAME.users(id) ON DELETE CASCADE,
    original_filename VARCHAR(255) NOT NULL,
    minio_key VARCHAR(255) NOT NULL,
    file_size INTEGER,
    content_type VARCHAR(50),
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_images_user_id ON STUDENTNAME.images(user_id);
CREATE INDEX idx_images_minio_key ON STUDENTNAME.images(minio_key);
```

**Purpose**: Store metadata about uploaded images

**Fields**:
- `id`: Auto-incrementing primary key
- `user_id`: Foreign key to users table
- `original_filename`: Name of uploaded file
- `minio_key`: Location in MinIO object storage
- `file_size`: Size in bytes
- `content_type`: MIME type (e.g., image/jpeg)
- `upload_date`: Upload timestamp

### Jobs Table

```sql
CREATE TABLE STUDENTNAME.jobs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES STUDENTNAME.users(id) ON DELETE CASCADE,
    image_id INTEGER REFERENCES STUDENTNAME.images(id) ON DELETE CASCADE,
    operation VARCHAR(50) NOT NULL,
    parameters JSONB,
    status VARCHAR(20) DEFAULT 'pending',
    result_minio_key VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE INDEX idx_jobs_user_id ON STUDENTNAME.jobs(user_id);
CREATE INDEX idx_jobs_status ON STUDENTNAME.jobs(status);
CREATE INDEX idx_jobs_image_id ON STUDENTNAME.jobs(image_id);
```

**Purpose**: Track image processing jobs

**Fields**:
- `id`: Auto-incrementing primary key
- `user_id`: Foreign key to users table
- `image_id`: Foreign key to images table
- `operation`: Type of processing (resize, grayscale, etc.)
- `parameters`: JSON object with operation parameters
- `status`: pending, processing, completed, failed
- `result_minio_key`: Location of processed image in MinIO
- `created_at`: Job creation timestamp
- `completed_at`: Job completion timestamp

## Schema Isolation

Each student gets their own schema to isolate their data:

```sql
-- Create schema for student
CREATE SCHEMA alice;

-- Grant permissions
GRANT ALL PRIVILEGES ON SCHEMA alice TO alice;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA alice TO alice;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA alice TO alice;

-- Create tables in student schema
CREATE TABLE alice.users (...);
CREATE TABLE alice.images (...);
CREATE TABLE alice.jobs (...);
```

**Benefits**:
- Students can't see each other's data
- Same table names across schemas
- Simple permissions management
- One database for all students

## Python Integration with SQLAlchemy

### Installation

Already included in `requirements.txt`:
```
SQLAlchemy==2.0.23
psycopg2-binary==2.9.9
```

### Configuration

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# Get database URL from environment
DATABASE_URL = os.environ.get('DATABASE_URL')
DB_SCHEMA = os.environ.get('DB_SCHEMA')

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={'options': f'-csearch_path={DB_SCHEMA}'},
    pool_size=5,
    max_overflow=10
)

# Create session factory
SessionLocal = sessionmaker(bind=engine)
```

### Model Definitions

```python
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    images = relationship("Image", back_populates="user", cascade="all, delete-orphan")
    jobs = relationship("Job", back_populates="user", cascade="all, delete-orphan")

class Image(Base):
    __tablename__ = 'images'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    original_filename = Column(String(255), nullable=False)
    minio_key = Column(String(255), nullable=False)
    file_size = Column(Integer)
    content_type = Column(String(50))
    upload_date = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="images")
    jobs = relationship("Job", back_populates="image", cascade="all, delete-orphan")

class Job(Base):
    __tablename__ = 'jobs'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    image_id = Column(Integer, ForeignKey('images.id'), nullable=False)
    operation = Column(String(50), nullable=False)
    parameters = Column(JSONB)
    status = Column(String(20), default='pending')
    result_minio_key = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    # Relationships
    user = relationship("User", back_populates="jobs")
    image = relationship("Image", back_populates="jobs")
```

### Database Operations

#### Create Tables

```python
def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
```

#### Create User

```python
from werkzeug.security import generate_password_hash

def create_user(username, password):
    """Create a new user"""
    session = SessionLocal()
    try:
        user = User(
            username=username,
            password_hash=generate_password_hash(password)
        )
        session.add(user)
        session.commit()
        return user.id
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()
```

#### Authenticate User

```python
from werkzeug.security import check_password_hash

def authenticate_user(username, password):
    """Authenticate a user"""
    session = SessionLocal()
    try:
        user = session.query(User).filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            return user.id
        return None
    finally:
        session.close()
```

#### Create Image Record

```python
def create_image(user_id, filename, minio_key, file_size, content_type):
    """Create an image record"""
    session = SessionLocal()
    try:
        image = Image(
            user_id=user_id,
            original_filename=filename,
            minio_key=minio_key,
            file_size=file_size,
            content_type=content_type
        )
        session.add(image)
        session.commit()
        return image.id
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()
```

#### Create Job

```python
import json

def create_job(user_id, image_id, operation, parameters):
    """Create a processing job"""
    session = SessionLocal()
    try:
        job = Job(
            user_id=user_id,
            image_id=image_id,
            operation=operation,
            parameters=json.dumps(parameters)
        )
        session.add(job)
        session.commit()
        return job.id
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()
```

#### Update Job Status

```python
def update_job_status(job_id, status, result_key=None):
    """Update job status"""
    session = SessionLocal()
    try:
        job = session.query(Job).filter_by(id=job_id).first()
        if job:
            job.status = status
            if result_key:
                job.result_minio_key = result_key
            if status == 'completed':
                job.completed_at = datetime.utcnow()
            session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()
```

#### Query User's Images

```python
def get_user_images(user_id, limit=50, offset=0):
    """Get all images for a user"""
    session = SessionLocal()
    try:
        images = session.query(Image)\
            .filter_by(user_id=user_id)\
            .order_by(Image.upload_date.desc())\
            .limit(limit)\
            .offset(offset)\
            .all()
        
        return [{
            'id': img.id,
            'filename': img.original_filename,
            'minio_key': img.minio_key,
            'file_size': img.file_size,
            'upload_date': img.upload_date.isoformat()
        } for img in images]
    finally:
        session.close()
```

#### Query User's Jobs

```python
def get_user_jobs(user_id, status=None):
    """Get jobs for a user, optionally filtered by status"""
    session = SessionLocal()
    try:
        query = session.query(Job).filter_by(user_id=user_id)
        if status:
            query = query.filter_by(status=status)
        
        jobs = query.order_by(Job.created_at.desc()).all()
        
        return [{
            'id': job.id,
            'image_id': job.image_id,
            'operation': job.operation,
            'status': job.status,
            'created_at': job.created_at.isoformat(),
            'completed_at': job.completed_at.isoformat() if job.completed_at else None
        } for job in jobs]
    finally:
        session.close()
```

## Connection Pooling

SQLAlchemy automatically manages a connection pool:

```python
engine = create_engine(
    DATABASE_URL,
    pool_size=5,        # Number of connections to keep open
    max_overflow=10,    # Additional connections when pool is full
    pool_timeout=30,    # Wait time before timeout
    pool_recycle=3600   # Recycle connections after 1 hour
)
```

**Benefits**:
- Reuses connections instead of creating new ones
- Reduces database load
- Improves performance
- Handles connection failures gracefully

## Transactions

Always use transactions for data consistency:

```python
def transfer_image(image_id, from_user_id, to_user_id):
    """Transfer image ownership with transaction"""
    session = SessionLocal()
    try:
        # Start transaction
        image = session.query(Image).filter_by(id=image_id).first()
        if image and image.user_id == from_user_id:
            image.user_id = to_user_id
            session.commit()  # Commit transaction
        else:
            session.rollback()  # Rollback if conditions not met
    except Exception as e:
        session.rollback()  # Rollback on error
        raise e
    finally:
        session.close()
```

## Best Practices

### 1. Always Close Sessions

Use try/finally to ensure sessions are closed:

```python
session = SessionLocal()
try:
    # Database operations
    pass
finally:
    session.close()
```

### 2. Use Context Managers

```python
from contextlib import contextmanager

@contextmanager
def get_session():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

# Usage
with get_session() as session:
    user = session.query(User).first()
```

### 3. Use Parameterized Queries

SQLAlchemy does this automatically, but never use string formatting:

```python
# Good - parameterized
user = session.query(User).filter_by(username=username).first()

# Bad - SQL injection risk
user = session.execute(f"SELECT * FROM users WHERE username='{username}'")
```

### 4. Index Frequently Queried Columns

```sql
-- Speed up queries by user_id
CREATE INDEX idx_images_user_id ON images(user_id);

-- Speed up status lookups
CREATE INDEX idx_jobs_status ON jobs(status);
```

### 5. Use Appropriate Data Types

```python
# Use DateTime for timestamps
created_at = Column(DateTime, default=datetime.utcnow)

# Use JSONB for flexible parameters (with indexing support)
parameters = Column(JSONB)

# Use specific sizes for strings
username = Column(String(255))
```

## Testing

### Unit Tests with SQLite

Use SQLite in-memory database for fast tests:

```python
import pytest
from sqlalchemy import create_engine

@pytest.fixture
def test_db():
    """Create a test database"""
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    return engine

def test_create_user(test_db):
    session = SessionLocal(bind=test_db)
    user = User(username="test", password_hash="hash")
    session.add(user)
    session.commit()
    
    assert user.id is not None
    assert user.username == "test"
```

### Integration Tests with PostgreSQL

Use a test schema for integration tests:

```python
@pytest.fixture
def test_schema():
    """Create a test schema"""
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        conn.execute("CREATE SCHEMA IF NOT EXISTS test")
        conn.commit()
    
    # Use test schema
    test_engine = create_engine(
        DATABASE_URL,
        connect_args={'options': '-csearch_path=test'}
    )
    Base.metadata.create_all(test_engine)
    
    yield test_engine
    
    # Cleanup
    with engine.connect() as conn:
        conn.execute("DROP SCHEMA test CASCADE")
        conn.commit()
```

## Common Issues

### Issue: "relation does not exist"

**Solution**: Check that:
- Schema is specified correctly
- Tables are created in correct schema
- Connection uses correct search_path

### Issue: "duplicate key value violates unique constraint"

**Solution**: This means you're trying to insert a duplicate value:
```python
# Check if user exists before creating
existing = session.query(User).filter_by(username=username).first()
if existing:
    raise ValueError("Username already exists")
```

### Issue: "connection pool exhausted"

**Solution**: Increase pool size or fix connection leaks:
```python
# Make sure sessions are always closed
try:
    # operations
finally:
    session.close()  # Always close!
```

### Issue: "password authentication failed"

**Solution**: Check:
- DATABASE_URL has correct credentials
- User has permissions on schema
- PostgreSQL is accepting connections

## Summary

PostgreSQL provides:
- ✅ ACID transactions for data integrity
- ✅ Complex queries with joins
- ✅ Schema isolation for multi-tenancy
- ✅ Rich data types (JSON, arrays, etc.)
- ✅ Connection pooling for performance

For more details, see the [SQLAlchemy documentation](https://docs.sqlalchemy.org/).
