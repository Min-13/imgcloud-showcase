"""
Image Processing Frontend with Flask.
Provides web interface and forwards image processing requests to the C++ processor service via gRPC.

LAB04 Enhancement: When database services are available (MinIO, PostgreSQL, Redis),
enables user authentication, image storage, and job tracking.
Falls back to LAB03 functionality when services are unavailable.
"""
from flask import Flask, jsonify, request, send_file, send_from_directory, Response, make_response
import os
import requests
import grpc
import io
import json
import secrets
from datetime import datetime, timedelta
from functools import wraps

# Import generated gRPC code
import image_processor_pb2
import image_processor_pb2_grpc

# LAB04 imports - optional dependencies
try:
    from minio import Minio
    from minio.error import S3Error
    MINIO_AVAILABLE = True
except ImportError:
    MINIO_AVAILABLE = False
    print("MinIO not available - storage features disabled")

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    print("Redis not available - caching and session features disabled")

try:
    from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import sessionmaker, relationship
    from sqlalchemy.dialects.postgresql import JSONB
    from werkzeug.security import generate_password_hash, check_password_hash
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    print("SQLAlchemy not available - database features disabled")

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("PIL not available - thumbnail features disabled")

# Thumbnail cache configuration
THUMBNAIL_CACHE_TTL = 3600  # Cache thumbnails for 1 hour

app = Flask(__name__)

# Get configuration from environment variables
PROCESSOR_HOST = os.environ.get('PROCESSOR_HOST', 'localhost')
PROCESSOR_HTTP_PORT = os.environ.get('PROCESSOR_HTTP_PORT', '8080')
PROCESSOR_GRPC_PORT = os.environ.get('PROCESSOR_GRPC_PORT', '50051')
PROCESSOR_HTTP_URL = f'http://{PROCESSOR_HOST}:{PROCESSOR_HTTP_PORT}'
PROCESSOR_GRPC_ADDRESS = f'{PROCESSOR_HOST}:{PROCESSOR_GRPC_PORT}'

# LAB07: Per-instance identifier and unhealthy flag for load balancing demonstration
INSTANCE_ID = os.environ.get('INSTANCE_ID', 'frontend')
_force_unhealthy = False

# LAB04: Initialize optional services
minio_client = None
redis_client = None
redis_binary_client = None
SessionLocal = None

# MinIO configuration and initialization
if MINIO_AVAILABLE:
    MINIO_HOST = os.environ.get('MINIO_HOST')
    MINIO_PORT = os.environ.get('MINIO_PORT', '9000')
    MINIO_ACCESS_KEY = os.environ.get('MINIO_ACCESS_KEY', 'minioadmin')
    MINIO_SECRET_KEY = os.environ.get('MINIO_SECRET_KEY', 'minioadmin123')
    MINIO_BUCKET = os.environ.get('MINIO_BUCKET', 'images')
    MINIO_SECURE = os.environ.get('MINIO_SECURE', 'false').lower() == 'true'
    
    if MINIO_HOST:
        try:
            minio_client = Minio(
                f"{MINIO_HOST}:{MINIO_PORT}",
                access_key=MINIO_ACCESS_KEY,
                secret_key=MINIO_SECRET_KEY,
                secure=MINIO_SECURE
            )
            if not minio_client.bucket_exists(MINIO_BUCKET):
                minio_client.make_bucket(MINIO_BUCKET)
                print(f"Created MinIO bucket: {MINIO_BUCKET}")
            print(f"Connected to MinIO at {MINIO_HOST}:{MINIO_PORT}")
        except Exception as e:
            print(f"MinIO initialization error: {e}")
            minio_client = None
    else:
        print("MINIO_HOST not configured - storage features disabled")

# Session configuration (used by authentication/session management when Redis is available)
SESSION_TIMEOUT = int(os.environ.get('SESSION_TIMEOUT', 3600))
SECRET_KEY = os.environ.get('SECRET_KEY', secrets.token_hex(32))

# Redis configuration and initialization
if REDIS_AVAILABLE:
    REDIS_HOST = os.environ.get('REDIS_HOST')
    REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
    
    if REDIS_HOST:
        try:
            redis_client = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                db=0,
                decode_responses=True
            )
            redis_client.ping()
            print(f"Connected to Redis at {REDIS_HOST}:{REDIS_PORT}")
        except Exception as e:
            print(f"Redis initialization error: {e}")
            redis_client = None
        
        try:
            redis_binary_client = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                db=1,
                decode_responses=False
            )
            redis_binary_client.ping()
            print("Connected to Redis (binary)")
        except Exception as e:
            print(f"Redis binary client initialization error: {e}")
            redis_binary_client = None
    else:
        print("REDIS_HOST not configured - caching and session features disabled")

# PostgreSQL configuration and initialization
if SQLALCHEMY_AVAILABLE:
    DATABASE_URL = os.environ.get('DATABASE_URL')
    DB_SCHEMA = os.environ.get('DB_SCHEMA', 'public')
    
    Base = declarative_base()
    
    class User(Base):
        __tablename__ = 'users'
        
        id = Column(Integer, primary_key=True)
        username = Column(String(255), unique=True, nullable=False)
        password_hash = Column(String(255), nullable=False)
        created_at = Column(DateTime, default=datetime.utcnow)
        
        images = relationship("ImageRecord", back_populates="user", cascade="all, delete-orphan")
        jobs = relationship("Job", back_populates="user", cascade="all, delete-orphan")
    
    class ImageRecord(Base):
        __tablename__ = 'images'
        
        id = Column(Integer, primary_key=True)
        user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
        original_filename = Column(String(255), nullable=False)
        minio_key = Column(String(255), nullable=False)
        file_size = Column(Integer)
        content_type = Column(String(50))
        upload_date = Column(DateTime, default=datetime.utcnow)
        
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
        
        user = relationship("User", back_populates="jobs")
        image = relationship("ImageRecord", back_populates="jobs")
    
    if DATABASE_URL:
        try:
            engine = create_engine(
                DATABASE_URL,
                connect_args={'options': f'-csearch_path={DB_SCHEMA}'},
                pool_size=5,
                max_overflow=10
            )
            Base.metadata.create_all(engine)
            SessionLocal = sessionmaker(bind=engine)
            print(f"Connected to PostgreSQL (schema: {DB_SCHEMA})")
        except Exception as e:
            print(f"Database initialization error: {e}")
            SessionLocal = None
    else:
        print("DATABASE_URL not configured - authentication and storage features disabled")

# Authentication decorator (LAB04)
def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not redis_client:
            return jsonify({'error': 'Session service unavailable'}), 503
        
        session_id = request.cookies.get('session_id')
        if not session_id:
            return jsonify({'error': 'Not authenticated'}), 401
        
        session_data = redis_client.get(f"session:{session_id}")
        if not session_data:
            return jsonify({'error': 'Session expired'}), 401
        
        # Extend session on activity
        redis_client.expire(f"session:{session_id}", SESSION_TIMEOUT)
        
        # Parse session data
        session = json.loads(session_data)
        request.user_id = session['user_id']
        request.username = session['username']
        
        return f(*args, **kwargs)
    return decorated_function

@app.before_request
def check_forced_unhealthy():
    """When forced unhealthy, return 503 for all endpoints except the toggle itself (Lab07).

    This causes nginx's passive health checker to detect failures on real proxied
    requests (not just /health), so students can see traffic drain from this instance
    when any endpoint is exercised through the load balancer.
    """
    if _force_unhealthy and request.path != '/api/toggle-unhealthy':
        return jsonify({
            'status': 'unhealthy',
            'message': f'Instance {INSTANCE_ID} forced unhealthy (Lab07 demonstration)',
            'instance_id': INSTANCE_ID
        }), 503

@app.after_request
def add_instance_header(response):
    """Add instance ID to all responses so clients can identify which instance served them (Lab07)"""
    response.headers['X-Instance-ID'] = INSTANCE_ID
    return response

@app.route('/')
def root():
    """Root endpoint - serve the appropriate web UI based on available features"""
    static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static')
    # Serve LAB04 UI if database features are available, otherwise serve basic LAB03 UI
    if SessionLocal is not None and minio_client is not None and redis_client is not None:
        return send_from_directory(static_dir, 'lab04.html')
    return send_from_directory(static_dir, 'index.html')

@app.route('/health')
def health():
    """Health check endpoint - checks all available services"""
    services = {}
    
    # Check processor (always required)
    try:
        processor_response = requests.get(f'{PROCESSOR_HTTP_URL}/health', timeout=2)
        services['processor'] = 'healthy' if processor_response.status_code == 200 else 'unhealthy'
    except Exception:
        services['processor'] = 'unavailable'
    
    # Check LAB04 services if configured
    if MINIO_AVAILABLE and minio_client:
        try:
            if minio_client.bucket_exists(MINIO_BUCKET):
                services['minio'] = 'healthy'
            else:
                services['minio'] = 'unhealthy'
        except Exception:
            services['minio'] = 'unavailable'
    else:
        services['minio'] = 'unavailable'
    
    if REDIS_AVAILABLE and redis_client:
        try:
            redis_client.ping()
            services['redis'] = 'healthy'
        except Exception:
            services['redis'] = 'unavailable'
    else:
        services['redis'] = 'unavailable'
    
    if SQLALCHEMY_AVAILABLE and SessionLocal:
        try:
            from sqlalchemy import text
            session = SessionLocal()
            # Test database connection with text() wrapper for SQLAlchemy 2.0+
            session.execute(text("SELECT 1"))
            session.close()
            services['database'] = 'healthy'
        except Exception as e:
            print(f"Database health check failed: {e}")
            services['database'] = 'unavailable'
    else:
        services['database'] = 'unavailable'
    
    # Determine overall status (processor must be healthy, other services are optional)
    return jsonify({
        'status': 'healthy' if services.get('processor') == 'healthy' else 'degraded',
        'message': 'Frontend is running',
        'services': services,
        'lab04_features': SessionLocal is not None and minio_client is not None and redis_client is not None,
        'instance_id': INSTANCE_ID
    })

# LAB07: Toggle unhealthy state for this instance to demonstrate load balancing
@app.route('/api/toggle-unhealthy', methods=['POST'])
def toggle_unhealthy():
    """Toggle the forced-unhealthy flag for this frontend instance.

    When set, the /health endpoint returns HTTP 503.  A reverse proxy (e.g. nginx)
    performing passive health checking will stop routing traffic to this instance,
    letting students observe how traffic is redistributed across healthy instances.
    """
    global _force_unhealthy
    _force_unhealthy = not _force_unhealthy
    return jsonify({
        'unhealthy': _force_unhealthy,
        'instance_id': INSTANCE_ID,
        'message': f'Instance {INSTANCE_ID} is now {"unhealthy" if _force_unhealthy else "healthy"}'
    })

# LAB04: User registration endpoint
@app.route('/api/register', methods=['POST'])
def register():
    """Register a new user (LAB04 feature)"""
    if not SessionLocal:
        return jsonify({'error': 'Database not configured'}), 503
    
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    
    if len(password) < 8:
        return jsonify({'error': 'Password must be at least 8 characters'}), 400
    
    session = SessionLocal()
    try:
        existing = session.query(User).filter_by(username=username).first()
        if existing:
            return jsonify({'error': 'Username already exists'}), 409
        
        user = User(
            username=username,
            password_hash=generate_password_hash(password)
        )
        session.add(user)
        session.commit()
        
        return jsonify({
            'success': True,
            'message': 'User registered successfully',
            'user_id': user.id
        }), 201
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

# LAB04: Login endpoint
@app.route('/api/login', methods=['POST'])
def login():
    """Authenticate user and create session (LAB04 feature)"""
    if not SessionLocal or not redis_client:
        return jsonify({'error': 'Authentication services unavailable'}), 503
    
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    
    session = SessionLocal()
    try:
        user = session.query(User).filter_by(username=username).first()
        if not user or not check_password_hash(user.password_hash, password):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        session_id = secrets.token_urlsafe(32)
        session_data = {
            'user_id': user.id,
            'username': user.username,
            'created_at': datetime.utcnow().isoformat()
        }
        
        redis_client.setex(
            f"session:{session_id}",
            SESSION_TIMEOUT,
            json.dumps(session_data)
        )
        
        response = make_response(jsonify({
            'success': True,
            'message': 'Logged in successfully',
            'user': {'id': user.id, 'username': user.username}
        }))
        # Set secure=False for local development (HTTP), True for production (HTTPS)
        # In production, set SECURE_COOKIES=true environment variable
        secure_cookies = os.environ.get('SECURE_COOKIES', 'false').lower() == 'true'
        response.set_cookie(
            'session_id',
            session_id,
            httponly=True,
            secure=secure_cookies,
            samesite='Lax',
            max_age=SESSION_TIMEOUT
        )
        
        return response
    finally:
        session.close()

# LAB04: Logout endpoint
@app.route('/api/logout', methods=['POST'])
@require_auth
def logout():
    """Logout user and destroy session (LAB04 feature)"""
    session_id = request.cookies.get('session_id')
    if session_id and redis_client:
        redis_client.delete(f"session:{session_id}")
    
    # Match the secure setting from login
    secure_cookies = os.environ.get('SECURE_COOKIES', 'false').lower() == 'true'
    response = make_response(jsonify({'success': True, 'message': 'Logged out'}))
    response.set_cookie('session_id', '', expires=0, httponly=True, secure=secure_cookies, samesite='Lax')
    return response

# LAB04: Get current user endpoint
@app.route('/api/user')
@require_auth
def get_user():
    """Get current user info (LAB04 feature)"""
    return jsonify({
        'user_id': request.user_id,
        'username': request.username
    })

# LAB04: Upload image endpoint
@app.route('/api/upload', methods=['POST'])
@require_auth
def upload_image():
    """Upload image to MinIO and store metadata in database (LAB04 feature)"""
    if not minio_client or not SessionLocal:
        return jsonify({'error': 'Storage services unavailable'}), 503
    
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400
    
    image_file = request.files['image']
    if image_file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    image_data = image_file.read()
    content_type = image_file.content_type or 'image/jpeg'
    
    minio_key = f"users/{request.user_id}/originals/{secrets.token_hex(16)}.jpg"
    
    try:
        minio_client.put_object(
            bucket_name=MINIO_BUCKET,
            object_name=minio_key,
            data=io.BytesIO(image_data),
            length=len(image_data),
            content_type=content_type
        )
    except Exception as e:
        return jsonify({'error': f'Storage error: {str(e)}'}), 500
    
    session = SessionLocal()
    try:
        image_record = ImageRecord(
            user_id=request.user_id,
            original_filename=image_file.filename,
            minio_key=minio_key,
            file_size=len(image_data),
            content_type=content_type
        )
        session.add(image_record)
        session.commit()
        
        return jsonify({
            'success': True,
            'image_id': image_record.id,
            'filename': image_file.filename,
            'size': len(image_data)
        }), 201
    except Exception as e:
        session.rollback()
        try:
            minio_client.remove_object(MINIO_BUCKET, minio_key)
        except:
            pass
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

# LAB04: List images endpoint
@app.route('/api/images')
@require_auth
def list_images():
    """List user's images (LAB04 feature)"""
    if not SessionLocal:
        return jsonify({'error': 'Database unavailable'}), 503
    
    session = SessionLocal()
    try:
        images = session.query(ImageRecord)\
            .filter_by(user_id=request.user_id)\
            .order_by(ImageRecord.upload_date.desc())\
            .limit(50)\
            .all()
        
        result_images = []
        for img in images:
            # Check if thumbnail is cached in Redis
            thumbnail_cached = False
            if redis_binary_client:
                try:
                    cache_key = f"thumbnail:{img.id}"
                    thumbnail_cached = redis_binary_client.exists(cache_key) > 0
                except Exception:
                    pass
            
            # Generate presigned URLs for accessing images
            image_url = f"/api/images/{img.id}"
            thumbnail_url = f"/api/images/{img.id}/thumbnail"
            
            result_images.append({
                'id': img.id,
                'filename': img.original_filename,
                'size': img.file_size,
                'uploaded_at': img.upload_date.isoformat(),
                'url': image_url,
                'thumbnail_url': thumbnail_url,
                'thumbnail_cached': thumbnail_cached
            })
        
        return jsonify({'images': result_images})
    finally:
        session.close()

# LAB04: Get specific image endpoint
@app.route('/api/images/<int:image_id>')
@require_auth
def get_image(image_id):
    """Retrieve a specific image by ID (LAB04 feature)"""
    if not SessionLocal or not minio_client:
        return jsonify({'error': 'Service unavailable'}), 503
    
    session = SessionLocal()
    try:
        image = session.query(ImageRecord).filter_by(id=image_id, user_id=request.user_id).first()
        if not image:
            return jsonify({'error': 'Image not found'}), 404
        
        # Retrieve from MinIO
        try:
            response = minio_client.get_object(MINIO_BUCKET, image.minio_key)
            image_data = response.read()
            response.close()
            response.release_conn()
            
            return Response(image_data, mimetype=image.content_type or 'image/jpeg')
        except S3Error as e:
            return jsonify({'error': 'Failed to retrieve image'}), 500
    finally:
        session.close()

# LAB04: Get image thumbnail endpoint
@app.route('/api/images/<int:image_id>/thumbnail')
@require_auth
def get_thumbnail(image_id):
    """Retrieve thumbnail for an image, using Redis cache (LAB04 feature)"""
    if not SessionLocal or not minio_client:
        return jsonify({'error': 'Service unavailable'}), 503
    
    session = SessionLocal()
    try:
        image = session.query(ImageRecord).filter_by(id=image_id, user_id=request.user_id).first()
        if not image:
            return jsonify({'error': 'Image not found'}), 404
        
        cache_key = f"thumbnail:{image_id}"
        
        # Try to get from Redis cache first
        if redis_binary_client:
            try:
                cached_thumbnail = redis_binary_client.get(cache_key)
                if cached_thumbnail:
                    return Response(cached_thumbnail, mimetype='image/jpeg')
            except Exception as e:
                print(f"Redis cache read error: {e}")
        
        # Not in cache - generate thumbnail
        try:
            # Retrieve original image from MinIO
            response = minio_client.get_object(MINIO_BUCKET, image.minio_key)
            image_data = response.read()
            response.close()
            response.release_conn()
            
            # Generate thumbnail using PIL
            if PIL_AVAILABLE:
                from PIL import Image as PILImage
                import io as python_io
                
                img = PILImage.open(python_io.BytesIO(image_data))
                img.thumbnail((300, 300), PILImage.Resampling.LANCZOS)
                
                thumbnail_io = python_io.BytesIO()
                img.save(thumbnail_io, format='JPEG', quality=85)
                thumbnail_data = thumbnail_io.getvalue()
                
                # Cache in Redis for future requests
                if redis_binary_client:
                    try:
                        redis_binary_client.setex(cache_key, THUMBNAIL_CACHE_TTL, thumbnail_data)
                    except Exception as e:
                        print(f"Redis cache write error: {e}")
                
                return Response(thumbnail_data, mimetype='image/jpeg')
            else:
                # If PIL not available, just return the original image
                return Response(image_data, mimetype='image/jpeg')
                
        except S3Error as e:
            return jsonify({'error': 'Failed to retrieve image'}), 500
    finally:
        session.close()

# LAB03: Process image endpoint (always available)
@app.route('/process', methods=['POST'])
def process_image():
    """
    Process image endpoint - forwards request to C++ processor service via gRPC.
    
    This endpoint works with or without LAB04 features (no authentication required).
    """
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
        
        image_file = request.files['image']
        if image_file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        
        image_data = image_file.read()
        
        # Get operation parameters
        operation = request.form.get('operation', '')
        width = int(request.form.get('width') or 0)
        height = int(request.form.get('height') or 0)
        kernel_size = int(request.form.get('kernel_size') or 5)
        angle = int(request.form.get('angle') or 0)
        direction = request.form.get('direction', '')
        
        # Create gRPC request
        grpc_request = image_processor_pb2.ProcessRequest(
            image_data=image_data,
            operation=operation,
            width=width,
            height=height,
            kernel_size=kernel_size,
            angle=angle,
            direction=direction
        )
        
        # Connect to gRPC server and make request
        with grpc.insecure_channel(PROCESSOR_GRPC_ADDRESS) as channel:
            stub = image_processor_pb2_grpc.ImageProcessorStub(channel)
            grpc_response = stub.ProcessImage(grpc_request, timeout=30)
        
        if grpc_response.error:
            return jsonify({'error': grpc_response.error}), 400
        
        return Response(grpc_response.image_data, mimetype='image/png')
    
    except grpc.RpcError as e:
        if e.code() == grpc.StatusCode.UNAVAILABLE:
            return jsonify({'error': 'Cannot connect to image processor service'}), 503
        elif e.code() == grpc.StatusCode.DEADLINE_EXCEEDED:
            return jsonify({'error': 'Image processing timeout'}), 504
        else:
            return jsonify({'error': f'gRPC error: {e.details()}'}), 500
    except ValueError as e:
        return jsonify({'error': f'Invalid parameter: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# LAB04: Process image from gallery
@app.route('/api/images/<int:image_id>/process', methods=['POST'])
@require_auth
def process_gallery_image(image_id):
    """Process an image from the gallery and save result (LAB04 feature)"""
    if not SessionLocal or not minio_client:
        return jsonify({'error': 'Services unavailable'}), 503
    
    session = SessionLocal()
    try:
        # Get the original image
        image = session.query(ImageRecord).filter_by(id=image_id, user_id=request.user_id).first()
        if not image:
            return jsonify({'error': 'Image not found'}), 404
        
        # Get operation parameters from JSON body
        data = request.get_json()
        operation = data.get('operation', '')
        
        # Retrieve original image from MinIO
        try:
            response = minio_client.get_object(MINIO_BUCKET, image.minio_key)
            image_data = response.read()
            response.close()
            response.release_conn()
        except S3Error as e:
            return jsonify({'error': 'Failed to retrieve original image'}), 500
        
        # Process image via gRPC
        width = int(data.get('width') or 0)
        height = int(data.get('height') or 0)
        kernel_size = int(data.get('kernel_size') or 5)
        angle = int(data.get('angle') or 0)
        direction = data.get('direction', '')
        
        grpc_request = image_processor_pb2.ProcessRequest(
            image_data=image_data,
            operation=operation,
            width=width,
            height=height,
            kernel_size=kernel_size,
            angle=angle,
            direction=direction
        )
        
        try:
            with grpc.insecure_channel(PROCESSOR_GRPC_ADDRESS) as channel:
                stub = image_processor_pb2_grpc.ImageProcessorStub(channel)
                grpc_response = stub.ProcessImage(grpc_request, timeout=30)
            
            if grpc_response.error:
                return jsonify({'error': grpc_response.error}), 400
                
            processed_data = grpc_response.image_data
            
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.UNAVAILABLE:
                return jsonify({'error': 'Cannot connect to image processor service'}), 503
            elif e.code() == grpc.StatusCode.DEADLINE_EXCEEDED:
                return jsonify({'error': 'Image processing timeout'}), 504
            else:
                return jsonify({'error': f'gRPC error: {e.details()}'}), 500
        
        # Save processed image to MinIO
        result_key = f"users/{request.user_id}/processed/{secrets.token_hex(16)}_{operation}.jpg"
        try:
            minio_client.put_object(
                bucket_name=MINIO_BUCKET,
                object_name=result_key,
                data=io.BytesIO(processed_data),
                length=len(processed_data),
                content_type='image/jpeg'
            )
        except Exception as e:
            return jsonify({'error': f'Failed to save processed image: {str(e)}'}), 500
        
        # Create new image record for processed image
        processed_filename = f"{operation}_{image.original_filename}"
        new_image = ImageRecord(
            user_id=request.user_id,
            original_filename=processed_filename,
            minio_key=result_key,
            file_size=len(processed_data),
            content_type='image/jpeg'
        )
        session.add(new_image)
        
        # Create job record
        job = Job(
            user_id=request.user_id,
            image_id=image_id,
            operation=operation,
            parameters={'width': width, 'height': height, 'kernel_size': kernel_size, 'angle': angle, 'direction': direction},
            status='completed',
            result_minio_key=result_key,
            completed_at=datetime.utcnow()
        )
        session.add(job)
        session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Image processed with {operation}',
            'new_image_id': new_image.id,
            'result_image': {
                'id': new_image.id,
                'filename': processed_filename,
                'url': f'/api/images/{new_image.id}',
                'thumbnail_url': f'/api/images/{new_image.id}/thumbnail'
            }
        }), 201
        
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

# LAB04: Delete image endpoint
@app.route('/api/images/<int:image_id>', methods=['DELETE'])
@require_auth
def delete_image(image_id):
    """Delete an image and its associated data (LAB04 feature)"""
    if not SessionLocal or not minio_client:
        return jsonify({'error': 'Services unavailable'}), 503
    
    session = SessionLocal()
    try:
        # Get the image
        image = session.query(ImageRecord).filter_by(id=image_id, user_id=request.user_id).first()
        if not image:
            return jsonify({'error': 'Image not found'}), 404
        
        minio_key = image.minio_key
        
        # Delete from database (cascade will delete jobs)
        session.delete(image)
        session.commit()
        
        # Delete from MinIO
        try:
            minio_client.remove_object(MINIO_BUCKET, minio_key)
        except Exception as e:
            print(f"Warning: Failed to delete from MinIO: {e}")
        
        # Delete thumbnail from Redis cache
        if redis_binary_client:
            try:
                cache_key = f"thumbnail:{image_id}"
                redis_binary_client.delete(cache_key)
            except Exception as e:
                print(f"Warning: Failed to delete from cache: {e}")
        
        return jsonify({'success': True, 'message': 'Image deleted'}), 200
        
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@app.route('/operations')
def list_operations():
    """List available image processing operations"""
    return jsonify({
        'operations': [
            {
                'name': 'resize',
                'description': 'Resize image to specified dimensions',
                'parameters': ['width', 'height'],
                'processor': 'C++ Service'
            },
            {
                'name': 'grayscale',
                'description': 'Convert image to grayscale',
                'parameters': [],
                'processor': 'C++ Service'
            },
            {
                'name': 'blur',
                'description': 'Apply Gaussian blur to image',
                'parameters': ['kernel_size (optional, default: 5)'],
                'processor': 'C++ Service'
            },
            {
                'name': 'edge_detection',
                'description': 'Apply Canny edge detection',
                'parameters': [],
                'processor': 'C++ Service'
            },
            {
                'name': 'rotate',
                'description': 'Rotate image by specified angle',
                'parameters': ['angle (degrees)'],
                'processor': 'C++ Service'
            },
            {
                'name': 'mirror',
                'description': 'Mirror image horizontally or vertically',
                'parameters': ['direction (horizontal/vertical)'],
                'processor': 'C++ Service'
            }
        ]
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
