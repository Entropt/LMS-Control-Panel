# api/lms_client.py - API Client for LMS
import requests
import json
from typing import List, Dict, Any, Optional

class LMSClient:
    """Client for interacting with LMS API"""
    
    def __init__(self, base_url: str, api_key: str):
        """
        Initialize the LMS API client
        
        Args:
            base_url: Base URL for the LMS API
            api_key: API key for authentication
        """
        self.base_url = base_url
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def get_courses(self) -> List[Dict[str, Any]]:
        """
        Get list of courses where the user is enrolled as a teacher
        
        Returns:
            List of course objects
        """
        # Canvas LMS API endpoint for courses where the user is a teacher
        endpoint = f"{self.base_url}/users/self/favorites/courses"
        
        try:
            response = requests.get(endpoint, headers=self.headers)
            response.raise_for_status()
            courses = response.json()
            
            # Filter courses where the user is enrolled as a teacher
            teacher_courses = []
            for course in courses:
                enrollments = course.get('enrollments', [])
                for enrollment in enrollments:
                    if enrollment.get('type') == 'teacher':
                        teacher_courses.append(course)
                        break
            
            return teacher_courses
        except requests.exceptions.RequestException as e:
            print(f"Error fetching courses: {e}")
            return []
            
    def get_exercises(self, course_id: str) -> List[Dict[str, Any]]:
        """
        Get list of exercises (assignments) for a specific course
        
        Args:
            course_id: ID of the course to get exercises for
            
        Returns:
            List of exercise objects
        """
        # Canvas LMS API endpoint for course assignments
        endpoint = f"{self.base_url}/courses/{course_id}/assignments"
        
        try:
            response = requests.get(endpoint, headers=self.headers)
            response.raise_for_status()
            assignments = response.json()
            
            # Process assignments to match our expected format
            exercises = []
            for assignment in assignments:
                exercises.append({
                    'id': assignment.get('id'),
                    'title': assignment.get('name'),
                    'type': 'Assignment',
                    'due_date': assignment.get('due_at'),
                    'status': 'Active' if assignment.get('published') else 'Draft',
                    'description': assignment.get('description'),
                    'points_possible': assignment.get('points_possible'),
                    'submission_types': assignment.get('submission_types')
                })
            
            return exercises
        except requests.exceptions.RequestException as e:
            print(f"Error fetching exercises: {e}")
            return []
    
    # Add more API methods here as needed