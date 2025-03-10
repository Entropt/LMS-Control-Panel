# api/auth_client.py - Authentication API Client
from typing import Dict, Any, Optional
import requests

from api.base_client import BaseLMSClient

class AuthClient(BaseLMSClient):
    """Client for authentication-related API endpoints"""
    
    def authenticate(self, username: str, password: str) -> Dict[str, Any]:
        """
        Authenticate user with username and password
        
        Args:
            username: User's username or email
            password: User's password
            
        Returns:
            Authentication response with user info and token if successful
        """
        try:
            # For Canvas LMS, we typically use token-based auth rather than
            # username/password. This is a placeholder for your authentication logic.
            auth_data = {
                "username": username,
                "password": password
            }
            
            # This would be the endpoint for authentication
            # Note: Canvas typically doesn't have a direct API endpoint for this
            return self.post("/login", auth_data)
        except requests.exceptions.RequestException as e:
            print(f"Error authenticating user: {e}")
            return {"success": False, "error": str(e)}
            
    def validate_token(self, token: str) -> Dict[str, Any]:
        """
        Validate an authentication token
        
        Args:
            token: Authentication token
            
        Returns:
            Validation result with user info if valid
        """
        try:
            # Use the token to get user info as validation
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(f"{self.base_url}/users/self", headers=headers)
            response.raise_for_status()
            
            user_data = response.json()
            return {
                "success": True,
                "user": user_data
            }
        except requests.exceptions.RequestException as e:
            print(f"Error validating token: {e}")
            return {"success": False, "error": str(e)}
    
    def logout(self, token: str) -> Dict[str, Any]:
        """
        Invalidate an authentication token (logout)
        
        Args:
            token: Authentication token
            
        Returns:
            Logout result
        """
        # Canvas doesn't have a direct logout API endpoint for tokens
        # This is a placeholder for custom logout logic
        return {"success": True}