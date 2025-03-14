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
        
    def is_student_in_course_by_id(self, course_id: str, student_email: str) -> bool:
        """
        Check if a student with the given email is enrolled in the specified course
        
        Args:
            course_id: ID of the course to check
            student_email: Email address to check against enrolled students
            api_token: Canvas API token for authentication
            
        Returns:
            bool: True if the student is enrolled, False otherwise
        """
        try:
            response = self.get(f"/courses/{course_id}/users?include[]=enrollments&per_page=200")
            response.raise_for_status()
            
            users = response.json()
            for user in users:
                # Check the email field
                if user.get("email") and user["email"].lower() == student_email.lower():
                    # Verify they have a StudentEnrollment
                    for enrollment in user.get("enrollments", []):
                        if enrollment.get("type") == "StudentEnrollment" and enrollment.get("enrollment_state") == "active":
                            return True
                        
            # If we get here, the student wasn't found or isn't actively enrolled
            return False
        except requests.exceptions.RequestException as e:
            print(f"Error fetching students for course {course_id}: {e}")
            return []
            