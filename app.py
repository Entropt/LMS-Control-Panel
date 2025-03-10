# app.py - Flask application entry point
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import os
from dotenv import load_dotenv

# Import our modules
from api.lms_client import LMSClient
from config.settings import load_config

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

# Load configuration
config = load_config()

# Initialize API client
lms_client = LMSClient(
    base_url=config.get('api', {}).get('base_url') or os.getenv('LMS_API_URL'),
    api_key=config.get('api', {}).get('api_key') or os.getenv('LMS_API_TOKEN')
)

@app.route('/')
def index():
    """Main dashboard page"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        # Handle login (you can implement your authentication logic here)
        session['user_id'] = 1  # Placeholder for actual user ID
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    return redirect(url_for('login'))

@app.route('/api/courses')
def get_courses():
    """API endpoint to get courses"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    courses = lms_client.get_courses()
    return jsonify(courses)

@app.route('/api/courses/<course_id>/exercises')
def get_exercises(course_id):
    """API endpoint to get exercises for a course"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    exercises = lms_client.get_exercises(course_id)
    return jsonify(exercises)

if __name__ == '__main__':
    app.run(debug=True)