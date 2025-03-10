# api/assignment_client.py - Assignment API Client
from typing import List, Dict, Any
import requests

from api.base_client import BaseLMSClient

class AssignmentClient(BaseLMSClient):
    """Client for assignment-related API endpoints"""
    
    def get_assignments(self, course_id: str) -> List[Dict[str, Any]]:
        """
        Get list of assignments for a specific course
        
        Args:
            course_id: ID of the course to get assignments for
            
        Returns:
            List of assignment objects in a standardized format
        """
        try:
            assignments = self.get(f"/courses/{course_id}/assignments")
            
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
            print(f"Error fetching assignments for course {course_id}: {e}")
            return []
    
    def get_assignment(self, course_id: str, assignment_id: str) -> Dict[str, Any]:
        """
        Get details for a specific assignment
        
        Args:
            course_id: ID of the course
            assignment_id: ID of the assignment
            
        Returns:
            Assignment object
        """
        try:
            assignment = self.get(f"/courses/{course_id}/assignments/{assignment_id}")
            
            # Process assignment to match our expected format
            return {
                'id': assignment.get('id'),
                'title': assignment.get('name'),
                'type': 'Assignment',
                'due_date': assignment.get('due_at'),
                'status': 'Active' if assignment.get('published') else 'Draft',
                'description': assignment.get('description'),
                'points_possible': assignment.get('points_possible'),
                'submission_types': assignment.get('submission_types'),
                'html_url': assignment.get('html_url'),
                'grading_type': assignment.get('grading_type'),
                'allowed_attempts': assignment.get('allowed_attempts')
            }
        except requests.exceptions.RequestException as e:
            print(f"Error fetching assignment {assignment_id} for course {course_id}: {e}")
            return {}
    
    def get_assignment_submissions(self, course_id: str, assignment_id: str) -> List[Dict[str, Any]]:
        """
        Get submissions for a specific assignment
        
        Args:
            course_id: ID of the course
            assignment_id: ID of the assignment
            
        Returns:
            List of submission objects
        """
        try:
            return self.get(f"/courses/{course_id}/assignments/{assignment_id}/submissions")
        except requests.exceptions.RequestException as e:
            print(f"Error fetching submissions for assignment {assignment_id} in course {course_id}: {e}")
            return []
            
    def create_assignment(self, course_id: str, assignment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new assignment
        
        Args:
            course_id: ID of the course
            assignment_data: Assignment data
            
        Returns:
            Created assignment object
        """
        try:
            return self.post(f"/courses/{course_id}/assignments", {"assignment": assignment_data})
        except requests.exceptions.RequestException as e:
            print(f"Error creating assignment in course {course_id}: {e}")
            return {}
            
    def update_assignment(self, course_id: str, assignment_id: str, assignment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing assignment
        
        Args:
            course_id: ID of the course
            assignment_id: ID of the assignment
            assignment_data: Updated assignment data
            
        Returns:
            Updated assignment object
        """
        try:
            return self.put(f"/courses/{course_id}/assignments/{assignment_id}", {"assignment": assignment_data})
        except requests.exceptions.RequestException as e:
            print(f"Error updating assignment {assignment_id} in course {course_id}: {e}")
            return {}