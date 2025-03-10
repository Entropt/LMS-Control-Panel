# api/lms_client.py - Main LMS Client that combines all specific clients
from typing import Dict, Any

from api.base_client import BaseLMSClient
from api.course_client import CourseClient
from api.assignment_client import AssignmentClient
from api.student_client import StudentClient
from api.auth_client import AuthClient

class LMSClient:
    """Main client for interacting with LMS API"""
    
    def __init__(self, base_url: str, api_key: str):
        """
        Initialize the LMS API client
        
        Args:
            base_url: Base URL for the LMS API
            api_key: API key for authentication
        """
        # Initialize base client
        self.base_client = BaseLMSClient(base_url, api_key)
        
        # Initialize specific clients
        self.courses = CourseClient(base_url, api_key)
        self.assignments = AssignmentClient(base_url, api_key)
        self.users = StudentClient(base_url, api_key)
        self.auth = AuthClient(base_url, api_key)
        
    # Legacy methods for backward compatibility
    def get_courses(self):
        """Get courses (legacy method)"""
        return self.courses.get_courses()
        
    def get_exercises(self, course_id):
        """Get exercises/assignments (legacy method)"""
        return self.assignments.get_assignments(course_id)