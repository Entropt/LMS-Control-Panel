# models/exercise.py - Exercise tracking model
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from models.user import db

class ExerciseAttempt(db.Model):
    """Model to track student exercise attempts"""
    __tablename__ = 'exercise_attempts'
    
    id = db.Column(db.Integer, primary_key=True)
    student_email = db.Column(db.String(120), nullable=False)
    course_id = db.Column(db.String(50), nullable=False)
    exercise_id = db.Column(db.String(50), nullable=False)
    started_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    score = db.Column(db.Float, nullable=True)
    attempts = db.Column(db.Integer, default=1)
    is_completed = db.Column(db.Boolean, default=False)
    
    def __init__(self, student_email, course_id, exercise_id):
        self.student_email = student_email
        self.course_id = course_id
        self.exercise_id = exercise_id
        
    def to_dict(self):
        """Convert attempt to dictionary"""
        return {
            'id': self.id,
            'student_email': self.student_email,
            'course_id': self.course_id,
            'exercise_id': self.exercise_id,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'score': self.score,
            'attempts': self.attempts,
            'is_completed': self.is_completed
        }
        
def log_exercise_attempt(student_email, course_id, exercise_id):
    """
    Log a student's attempt at an exercise
    
    Args:
        student_email: Email of the student
        course_id: ID of the course
        exercise_id: ID of the exercise
        
    Returns:
        ExerciseAttempt: The created or updated attempt record
    """
    # Check if there's an existing attempt
    attempt = ExerciseAttempt.query.filter_by(
        student_email=student_email,
        course_id=course_id,
        exercise_id=exercise_id,
        is_completed=False
    ).first()
    
    if attempt:
        # Update existing attempt
        attempt.attempts += 1
        db.session.commit()
        return attempt
    else:
        # Create new attempt
        new_attempt = ExerciseAttempt(
            student_email=student_email,
            course_id=course_id,
            exercise_id=exercise_id
        )
        db.session.add(new_attempt)
        db.session.commit()
        return new_attempt
        
def complete_exercise_attempt(student_email, course_id, exercise_id, score):
    """
    Mark an exercise attempt as completed with a score
    
    Args:
        student_email: Email of the student
        course_id: ID of the course
        exercise_id: ID of the exercise
        score: Score achieved
        
    Returns:
        ExerciseAttempt: The updated attempt record
    """
    # Find the most recent attempt
    attempt = ExerciseAttempt.query.filter_by(
        student_email=student_email,
        course_id=course_id,
        exercise_id=exercise_id
    ).order_by(ExerciseAttempt.started_at.desc()).first()
    
    if attempt:
        attempt.completed_at = datetime.utcnow()
        attempt.score = score
        attempt.is_completed = True
        db.session.commit()
        
    return attempt
    
def get_student_exercise_attempts(student_email, course_id=None):
    """
    Get all exercise attempts for a student
    
    Args:
        student_email: Email of the student
        course_id: Optional course ID to filter by
        
    Returns:
        List[ExerciseAttempt]: List of attempt records
    """
    query = ExerciseAttempt.query.filter_by(student_email=student_email)
    
    if course_id:
        query = query.filter_by(course_id=course_id)
        
    return query.order_by(ExerciseAttempt.started_at.desc()).all()