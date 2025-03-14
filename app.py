# app.py - Flask application entry point
import base64
from urllib.parse import urljoin
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash, Response, make_response
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import os
from datetime import timedelta
from dotenv import load_dotenv
from functools import wraps
import requests

# Import our modules
from api.lms_client import LMSClient
from models.user import db, User, initialize_db
from config.settings import load_config
from api.course_client import CourseClient

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI', 'sqlite:///lms_control.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)
app.config['JUICE_SHOP_URL'] = os.getenv('JUICE_SHOP_URL', 'http://localhost:3000')

# Initialize database
db.init_app(app)

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Load configuration
config = load_config()

# Initialize API client with default empty token (will be set per user)
lms_client = LMSClient(
    base_url=config.get('api', {}).get('base_url'),
    api_key=config.get('api', {}).get('api_key')  # Will be set on a per-request basis from the user's token
)

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Admin-only access decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Access denied. Administrator privileges required.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Request hook to set API token for current user
@app.before_request
def set_api_token():
    if current_user.is_authenticated and current_user.canvas_api_token:
        # Create a new client instance with user's token
        app.config['lms_client'] = LMSClient(
            base_url=config.get('api', {}).get('base_url', ''),
            api_key=current_user.canvas_api_token
        )
    else:
        app.config['lms_client'] = lms_client

# Routes
@app.route('/')
def index():
    """Main dashboard page (redirect based on user role)"""
    if current_user.is_authenticated and current_user.is_admin:
        return redirect(url_for('dashboard'))
    
    return redirect(url_for('assignment_login'))

# Add these routes to app.py for the JavaScript approach

@app.route('/assignment-login', methods=['GET', 'POST'])
def assignment_login():
    """Assignment login page using JavaScript approach"""
    if request.method == 'POST':
        email = request.form.get('email')
        
        for course_id in CourseClient.get_courses:
            if CourseClient.is_student_in_course_by_id(course_id=course_id, student_email=email):
                # Add course_id to cookie and break
                url_for('reverse_proxy')
                break
    else:
        # Get the Juice Shop URL from config
        juice_shop_url = app.config.get('JUICE_SHOP_URL')
        return render_template('assignment_login.html', juice_shop_url=juice_shop_url)

@app.route('/log-assignment-access', methods=['POST'])
def log_assignment_access_route():
    """API endpoint to log assignment access"""
    if not request.is_json:
        return jsonify({"error": "Invalid request"}), 400
        
    data = request.json
    username = data.get('username')
    
    if not username:
        return jsonify({"error": "Username is required"}), 400
    
    # Log the access (if using tracking)
    # log_assignment_access(username, request)
    
    return jsonify({"success": True})

@app.route('/favicon.ico')
def favicon():
    """Serve the favicon"""
    return app.send_static_file('favicon.ico')

@app.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Admin dashboard page"""
    return render_template('dashboard.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    error_message = None
    status_code = 200
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user, remember=True)
            next_page = request.args.get('next')
            
            # Redirect based on role
            if user.is_admin:
                return redirect(next_page or url_for('dashboard'))
            else:
                return redirect(app.config['JUICE_SHOP_URL'])
        else:
            error_message = 'Invalid email or password'
            status_code = 401
            
    response = make_response(render_template('login.html', error_message=error_message))
    response.status_code = status_code
    return response

@app.route('/logout')
@login_required
def logout():
    """Logout user"""
    logout_user()
    return redirect(url_for('login'))

@app.route('/users')
@login_required
@admin_required
def user_management():
    """User management page"""
    users = User.query.all()
    return render_template('users.html', users=users)

@app.route('/api/courses')
@login_required
@admin_required
def get_courses():
    """API endpoint to get courses"""
    lms_client = app.config['lms_client']
    
    print(lms_client)
    courses = lms_client.courses.get_courses()
    return jsonify(courses)

@app.route('/api/courses/<course_id>/exercises')
@login_required
@admin_required
def get_exercises(course_id):
    """API endpoint to get exercises for a course"""
    lms_client = app.config['lms_client']
    exercises = lms_client.assignments.get_assignments(course_id)
    return jsonify(exercises)

@app.route('/api/users')
@login_required
@admin_required
def get_users():
    """API endpoint to get all users"""
    users = [user.to_dict() for user in User.query.all()]
    return jsonify(users)

@app.route('/api/users', methods=['POST'])
@login_required
@admin_required
def create_user():
    """API endpoint to create a new user"""
    data = request.json
    
    if not data or not all(k in data for k in ('username', 'email', 'password')):
        return jsonify({'error': 'Missing required fields'}), 400
        
    # Check if user already exists
    if User.query.filter_by(username=data['username']).first() or User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Username or email already exists'}), 400
        
    # Create new user
    new_user = User(
        username=data['username'],
        email=data['email'],
        password=data['password'],
        is_admin=data.get('is_admin', False),
        canvas_api_token=data.get('canvas_api_token', '')
    )
    
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify(new_user.to_dict()), 201

@app.route('/api/users/<int:user_id>', methods=['PUT'])
@login_required
@admin_required
def update_user(user_id):
    """API endpoint to update a user"""
    user = User.query.get_or_404(user_id)
    data = request.json
    
    if 'username' in data:
        # Check if username is already taken by another user
        existing = User.query.filter_by(username=data['username']).first()
        if existing and existing.id != user_id:
            return jsonify({'error': 'Username already taken'}), 400
        user.username = data['username']
        
    if 'email' in data:
        # Check if email is already taken by another user
        existing = User.query.filter_by(email=data['email']).first()
        if existing and existing.id != user_id:
            return jsonify({'error': 'Email already taken'}), 400
        user.email = data['email']
        
    if 'password' in data:
        user.set_password(data['password'])
        
    if 'is_admin' in data:
        user.is_admin = data['is_admin']
        
    if 'canvas_api_token' in data:
        user.canvas_api_token = data['canvas_api_token']
        
    db.session.commit()
    
    return jsonify(user.to_dict())

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_user(user_id):
    """API endpoint to delete a user"""
    user = User.query.get_or_404(user_id)
    
    # Prevent deleting self
    if user.id == current_user.id:
        return jsonify({'error': 'Cannot delete yourself'}), 400
        
    db.session.delete(user)
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/assignment', defaults={'path': ''})
@app.route('/assignment/<path:path>')
def reverse_proxy(path):
    """
    Reverse proxy route that forwards requests to Juice Shop
    """
    # Target Juice Shop URL
    target_url = os.getenv('JUICE_SHOP_URL')
    
    # Construct the full URL by joining the target URL with the requested path
    url = urljoin(target_url, path)
    
    # Get the request method (GET, POST, etc.)
    method = request.method
    
    # Get the headers from the original request, but exclude some
    # that would cause issues with the proxied request
    excluded_headers = ['host', 'content-length', 'connection']
    headers = {key: value for key, value in request.headers.items()
               if key.lower() not in excluded_headers}
    
    # Forward the request to the target URL
    try:
        if method == 'GET':
            resp = requests.get(url, params=request.args, headers=headers, 
                               cookies=request.cookies, stream=True)
        elif method == 'POST':
            resp = requests.post(url, data=request.get_data(), headers=headers, 
                                cookies=request.cookies, stream=True)
        elif method == 'PUT':
            resp = requests.put(url, data=request.get_data(), headers=headers, 
                               cookies=request.cookies, stream=True)
        elif method == 'DELETE':
            resp = requests.delete(url, headers=headers, cookies=request.cookies, 
                                  stream=True)
        elif method == 'OPTIONS':
            resp = requests.options(url, headers=headers, cookies=request.cookies, 
                                   stream=True)
        else:
            # For other methods, just return a method not allowed response
            return Response(f"Method {method} not allowed", status=405)
        
        # Create a Flask Response object from the requests response
        response = Response(resp.iter_content(chunk_size=10*1024), 
                           status=resp.status_code)
        
        # Copy headers from the requests response to the Flask response
        for key, value in resp.headers.items():
            if key.lower() not in ['content-encoding', 'transfer-encoding', 'content-length']:
                response.headers[key] = value
                
        return response
        
    except requests.exceptions.RequestException as e:
        # Handle any errors when connecting to the Juice Shop
        return Response(f"Error connecting to Juice Shop: {str(e)}", status=500)

if __name__ == '__main__':
    initialize_db(app)  # Initialize database with default admin user
    app.run(debug=True)