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
from models.exercise import log_exercise_attempt, complete_exercise_attempt, get_student_exercise_attempts

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)
app.config['JUICE_SHOP_URL'] = os.getenv('JUICE_SHOP_URL')

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

# Add these imports at the top of app.py if not already there

# Add this function to check if a user is a student
def is_student(email, course_id=None):
    """
    Check if the given email belongs to a student, optionally in a specific course
    
    Args:
        email: The email to check
        course_id: Optional course ID to check enrollment for
        
    Returns:
        bool: True if the user is a student, False otherwise
    """
    client = app.config['lms_client']
    if course_id:
        return client.courses.is_student_in_course_by_id(course_id, email)
    
    # Check if they're a student in any course
    courses = client.courses.get_courses()
    for course in courses:
        if client.courses.is_student_in_course_by_id(course['id'], email):
            return True
    return False

# Update the student_portal route to ensure proper authorization
@app.route('/student')
def student_portal():
    """Student portal page"""
    if 'student_email' not in session:
        return redirect(url_for('assignment_login'))
    
    return render_template('student_exercise.html')

# Update the API endpoint to get student courses with proper validation
@app.route('/api/student/courses')
def get_student_courses():
    """API endpoint to get courses for the logged-in student"""
    if 'student_email' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    email = session['student_email']
    lms_client = app.config['lms_client']
    
    # Get all courses
    all_courses = lms_client.courses.get_courses()
    enrolled_courses = []
    
    # Filter courses where the student is enrolled
    for course in all_courses:
        if lms_client.courses.is_student_in_course_by_id(course['id'], email):
            enrolled_courses.append(course)
    
    # Update the enrolled courses in session
    session['enrolled_courses'] = [course['id'] for course in enrolled_courses]
    
    return jsonify(enrolled_courses)

@app.route('/api/student/courses/<course_id>/exercises')
def get_student_exercises(course_id):
    """API endpoint to get exercises for a student in a specific course"""
    if 'student_email' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    # Verify the student is enrolled in this course
    lms_client = app.config['lms_client']
    if not lms_client.courses.is_student_in_course_by_id(course_id, session['student_email']):
        return jsonify({'error': 'Not enrolled in this course'}), 403
    
    exercises = lms_client.assignments.get_student_exercises(course_id)
    return jsonify(exercises)

# Replace the log_student_exercise_access function in app.py
@app.route('/api/student/log-exercise-access', methods=['POST'])
def log_student_exercise_access():
    """API endpoint to log student exercise access with validation"""
    if 'student_email' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    if not request.is_json:
        return jsonify({"error": "Invalid request"}), 400
        
    data = request.json
    course_id = data.get('course_id')
    exercise_id = data.get('exercise_id')
    
    if not course_id or not exercise_id:
        return jsonify({"error": "Missing required fields"}), 400
    
    # Ensure the student is enrolled in this course
    lms_client = app.config['lms_client']
    if not lms_client.courses.is_student_in_course_by_id(
        course_id, 
        session['student_email']
    ):
        return jsonify({'error': 'Not enrolled in this course'}), 403
    
    # Verify this exercise exists in the course
    course_exercises = lms_client.assignments.get_student_exercises(course_id)
    exercise_exists = False
    
    for exercise in course_exercises:
        if str(exercise['id']) == str(exercise_id):
            exercise_exists = True
            break
    
    if not exercise_exists:
        return jsonify({'error': 'Exercise not found or not available'}), 404
    
    # All validation passed - log the exercise attempt
    from models.exercise import log_exercise_attempt
    log_exercise_attempt(
        student_email=session['student_email'],
        course_id=course_id,
        exercise_id=exercise_id
    )
    
    # Set the current exercise in the session
    session['current_exercise'] = exercise_id
    session['current_course'] = course_id
    
    return jsonify({"success": True, "redirectUrl": f"/assignment/{exercise_id}"})

@app.route('/api/student/exercise-history')
def get_exercise_history():
    """API endpoint to get exercise history for a student"""
    if 'student_email' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    course_id = request.args.get('course_id')
    attempts = get_student_exercise_attempts(
        student_email=session['student_email'],
        course_id=course_id
    )
    
    return jsonify([attempt.to_dict() for attempt in attempts])

@app.route('/student-progress')
@login_required
@admin_required
def student_progress():
    """Student progress page for teachers/admins"""
    return render_template('student_progress.html')

@app.route('/api/courses/<course_id>/students')
@login_required
@admin_required
def get_course_students(course_id):
    """API endpoint to get students for a course"""
    lms_client = app.config['lms_client']
    students = lms_client.users.get_course_students(course_id, "student")
    return jsonify(students)

@app.route('/api/courses/<course_id>/progress')
@login_required
@admin_required
def get_course_progress(course_id):
    """API endpoint to get progress data for all students in a course"""
    from models.exercise import ExerciseAttempt
    
    # Get all attempts for the given course
    attempts = ExerciseAttempt.query.filter_by(course_id=course_id).all()
    
    return jsonify([attempt.to_dict() for attempt in attempts])

# Replace the assignment_login route with this corrected version
@app.route('/assignment-login', methods=['GET', 'POST'])
def assignment_login():
    """Assignment login page using server-side validation"""
    # If already logged in as a student, redirect to student portal
    if 'student_email' in session:
        return redirect(url_for('student_portal'))
        
    error_message = None
    
    if request.method == 'POST':
        email = request.form.get('email')
        
        if not email:
            error_message = "Email is required"
            return render_template('assignment_login.html', 
                                  error_message=error_message,
                                  juice_shop_url=app.config.get('JUICE_SHOP_URL'))
        
        # Initialize LMS client with default token
        lms_client = app.config['lms_client']
        
        # Check if the email belongs to a student in any course
        student_enrolled = False
        enrolled_courses = []
        courses = lms_client.courses.get_courses()
        
        for course in courses:
            if lms_client.courses.is_student_in_course_by_id(course['id'], email):
                student_enrolled = True
                enrolled_courses.append(course)
        
        if student_enrolled:
            # Store the student email in session
            session['student_email'] = email
            session['enrolled_courses'] = [course['id'] for course in enrolled_courses]
            return redirect(url_for('student_portal'))
        else:
            # Not a valid student email
            error_message = "Email not found or not enrolled as a student in any course"
            return render_template('assignment_login.html', 
                                  error_message=error_message,
                                  juice_shop_url=app.config.get('JUICE_SHOP_URL'))
    else:
        # Get the Juice Shop URL from config
        juice_shop_url = app.config.get('JUICE_SHOP_URL')
        return render_template('assignment_login.html', juice_shop_url=juice_shop_url)

# Update the proxy_exercise route with strong validation
@app.route('/assignment/<exercise_id>')
def proxy_exercise(exercise_id):
    """
    Proxy route that forwards requests to Juice Shop for a specific exercise
    """
    if 'student_email' not in session:
        return redirect(url_for('assignment_login'))
    
    # Check if user has a current course and exercise
    if 'current_course' not in session or 'current_exercise' not in session:
        return redirect(url_for('student_portal'))
    
    # Verify that current_exercise matches the requested exercise
    if session['current_exercise'] != exercise_id:
        return redirect(url_for('student_portal'))
    
    # Verify the student is enrolled in the current course
    lms_client = app.config['lms_client']
    if not lms_client.courses.is_student_in_course_by_id(
        session['current_course'], 
        session['student_email']
    ):
        # If not enrolled, clear session and redirect to login
        session.pop('current_course', None)
        session.pop('current_exercise', None)
        return redirect(url_for('assignment_login'))
    
    # Verify this exercise exists in the course
    course_exercises = lms_client.assignments.get_student_exercises(session['current_course'])
    exercise_exists = False
    
    for exercise in course_exercises:
        if str(exercise['id']) == str(exercise_id):
            exercise_exists = True
            break
    
    if not exercise_exists:
        return jsonify({'error': 'Exercise not found or not available'}), 404
    
    # Target Juice Shop URL
    target_url = os.getenv('JUICE_SHOP_URL')
    
    # Log the access attempt
    from models.exercise import log_exercise_attempt
    log_exercise_attempt(
        student_email=session['student_email'],
        course_id=session['current_course'],
        exercise_id=exercise_id
    )
    
    # Forward to Juice Shop with tracking cookies
    response = make_response(redirect(target_url))
    response.set_cookie('ctf_exercise_id', exercise_id)
    response.set_cookie('ctf_student_email', session['student_email'])
    response.set_cookie('ctf_course_id', session['current_course'])
    
    return response

@app.route('/api/webhook/flag-submission', methods=['POST'])
def flag_submission_webhook():
    """
    Webhook endpoint for receiving flag submissions from Juice Shop
    This can be called by Juice Shop when a flag is submitted
    """
    if not request.is_json:
        return jsonify({"error": "Invalid request"}), 400
        
    data = request.json
    
    # Expected format:
    # {
    #   "student_email": "student@example.com",
    #   "exercise_id": "123",
    #   "course_id": "456", 
    #   "flag": "submitted flag",
    #   "is_correct": true/false,
    #   "score": 100
    # }
    
    required_fields = ['student_email', 'exercise_id', 'course_id', 'is_correct']
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400
    
    # If the flag is correct, mark the exercise as completed
    if data.get('is_correct', False):
        complete_exercise_attempt(
            student_email=data['student_email'],
            course_id=data['course_id'],
            exercise_id=data['exercise_id'],
            score=data.get('score', 100)
        )
    
    return jsonify({"success": True})

# @app.route('/assignment-login', methods=['GET', 'POST'])
# def assignment_login():
#     """Assignment login page using JavaScript approach"""
#     if request.method == 'POST':
#         email = request.form.get('email')
        
#         for course_id in CourseClient.get_courses:
#             if CourseClient.is_student_in_course_by_id(course_id=course_id, student_email=email):
#                 # Add course_id to cookie and break
#                 url_for('reverse_proxy')
#                 break
#     else:
#         # Get the Juice Shop URL from config
#         juice_shop_url = app.config.get('JUICE_SHOP_URL')
#         return render_template('assignment_login.html', juice_shop_url=juice_shop_url)

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