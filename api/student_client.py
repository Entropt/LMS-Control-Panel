# api/student_client.py - Student API Client
from typing import List, Dict, Any
import requests

from api.base_client import BaseLMSClient

class StudentClient(BaseLMSClient):
    """Client for student-related API endpoints"""
    
    def get_self(self) -> Dict[str, Any]:
        """
        Get information about the current student
        
        Returns:
            Student object
        """
        try:
            return self.get("/students/self")
        except requests.exceptions.RequestException as e:
            print(f"Error fetching student info: {e}")
            return {}
    
    def get_student(self, student_id: str) -> Dict[str, Any]:
        """
        Get information about a specific student
        
        Args:
            student_id: ID of the student
            
        Returns:
            Student object
        """
        try:
            return self.get(f"/students/{student_id}")
        except requests.exceptions.RequestException as e:
            print(f"Error fetching student {student_id}: {e}")
            return {}
    
    def get_course_students(self, course_id: str, enrollment_type: str = None) -> List[Dict[str, Any]]:
        """
        Get students enrolled in a specific course
        
        Args:
            course_id: ID of the course
            enrollment_type: Filter by enrollment type (student, teacher, ta, etc.)
            
        Returns:
            List of student objects
        """
        try:
            params = {}
            if enrollment_type:
                params["enrollment_type"] = enrollment_type
                
            return self.get(f"/courses/{course_id}/students", params)
        except requests.exceptions.RequestException as e:
            print(f"Error fetching students for course {course_id}: {e}")
            return []
    
    def get_student_enrollments(self, student_id: str) -> List[Dict[str, Any]]:
        """
        Get enrollments for a specific student
        
        Args:
            student_id: ID of the student
            
        Returns:
            List of enrollment objects
        """
        try:
            return self.get(f"/students/{student_id}/enrollments")
        except requests.exceptions.RequestException as e:
            print(f"Error fetching enrollments for student {student_id}: {e}")
            return []