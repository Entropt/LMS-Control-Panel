# models/user.py - User model and authentication functions
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import os
from typing import Optional, List, Dict

# Initialize SQLAlchemy
db = SQLAlchemy()

class User(UserMixin, db.Model):
    """User model for authentication and authorization"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    canvas_api_token = db.Column(db.String(255), nullable=True)
    
    def __init__(self, username: str, email: str, password: str, is_admin: bool = False, canvas_api_token: str = None):
        self.username = username
        self.email = email
        self.set_password(password)
        self.is_admin = is_admin
        self.canvas_api_token = canvas_api_token
    
    def set_password(self, password: str) -> None:
        """Set hashed password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password: str) -> bool:
        """Check password against stored hash"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self) -> Dict:
        """Convert user to dictionary (for API responses)"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'is_admin': self.is_admin
        }

# Function to initialize the database with default admin user
def initialize_db(app) -> None:
    """
    Initialize database with default admin user if no users exist
    
    Args:
        app: Flask application
    """
    with app.app_context():
        db.create_all()
        
        # Check if any user exists
        if User.query.count() == 0:
            # Create default admin user
            admin_username = os.getenv('ADMIN_USERNAME')
            admin_email = os.getenv('ADMIN_EMAIL')
            admin_password = os.getenv('ADMIN_PASSWORD')
            
            admin = User(
                username=admin_username,
                email=admin_email,
                password=admin_password,
                is_admin=True
            )
            
            db.session.add(admin)
            db.session.commit()
            print(f"Created default admin user: {admin_username}")