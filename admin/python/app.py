"""
Admin Interface Flask Application.
This file sets up the Flask app and routes. Students implement endpoints in endpoints.py.
"""
from flask import Flask, send_from_directory
import os

# Import endpoint classes
from endpoints import (
    UsersEndpoint,
    ImagesEndpoint,
    OperationsEndpoint,
    JobsEndpoint,
    HealthEndpoint
)

app = Flask(__name__)

# Configuration
ADMIN_PORT = int(os.environ.get('ADMIN_PORT', 8090))


@app.route('/')
def index():
    """Serve the admin UI."""
    static_dir = os.path.join(os.path.dirname(__file__), 'static')
    return send_from_directory(static_dir, 'admin.html')


# Register endpoint routes with unique endpoint names
app.add_url_rule('/api/users', 'api_users', UsersEndpoint.get)
app.add_url_rule('/api/images', 'api_images', ImagesEndpoint.get)
app.add_url_rule('/api/operations', 'api_operations', OperationsEndpoint.get)
app.add_url_rule('/api/jobs', 'api_jobs', JobsEndpoint.get)
app.add_url_rule('/health', 'health', HealthEndpoint.get)


if __name__ == '__main__':
    print(f"Starting admin interface on port {ADMIN_PORT}")
    app.run(host='0.0.0.0', port=ADMIN_PORT, debug=False)
