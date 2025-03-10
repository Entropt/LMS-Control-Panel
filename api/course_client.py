# api/course_client.py - Course API Client
from typing import List, Dict, Any
import requests

from api.base_client import BaseLMSClient

class CourseClient(BaseLMSClient):
    """Client for course-related API endpoints"""
    
    def get_courses(self) -> List[Dict[str, Any]]:
        """
        Get list of courses where the user is enrolled as a teacher
        
        Returns:
            List of course objects
        """
        try:
            # Canvas LMS API endpoint for courses where the user is a teacher
            courses = self.get("/users/self/favorites/courses")
            
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
    
    def get_course(self, course_id: str) -> Dict[str, Any]:
        """
        Get details for a specific course
        
        Args:
            course_id: ID of the course
            
        Returns:
            Course object
        """
        try:
            return self.get(f"/courses/{course_id}")
        except requests.exceptions.RequestException as e:
            print(f"Error fetching course {course_id}: {e}")
            return {}
    
    def get_course_modules(self, course_id: str) -> List[Dict[str, Any]]:
        """
        Get modules for a specific course
        
        Args:
            course_id: ID of the course
            
        Returns:
            List of module objects
        """
        try:
            return self.get(f"/courses/{course_id}/modules")
        except requests.exceptions.RequestException as e:
            print(f"Error fetching modules for course {course_id}: {e}")
            return []
    
    def get_course_sections(self, course_id: str) -> List[Dict[str, Any]]:
        """
        Get sections for a specific course
        
        Args:
            course_id: ID of the course
            
        Returns:
            List of section objects
        """
        try:
            return self.get(f"/courses/{course_id}/sections")
        except requests.exceptions.RequestException as e:
            print(f"Error fetching sections for course {course_id}: {e}")
            return []