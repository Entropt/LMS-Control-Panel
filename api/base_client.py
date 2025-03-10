# api/base_client.py - Base API Client
import requests
from typing import Dict, Any, Optional

class BaseLMSClient:
    """Base client for interacting with LMS API"""
    
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
    
    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make a GET request to the API
        
        Args:
            endpoint: API endpoint (without base URL)
            params: Query parameters
            
        Returns:
            Response data as dictionary
        
        Raises:
            requests.exceptions.RequestException: If the request fails
        """
        url = f"{self.base_url}{endpoint}"
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()
        
    def post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a POST request to the API
        
        Args:
            endpoint: API endpoint (without base URL)
            data: Request body data
            
        Returns:
            Response data as dictionary
            
        Raises:
            requests.exceptions.RequestException: If the request fails
        """
        url = f"{self.base_url}{endpoint}"
        response = requests.post(url, headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()
        
    def put(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a PUT request to the API
        
        Args:
            endpoint: API endpoint (without base URL)
            data: Request body data
            
        Returns:
            Response data as dictionary
            
        Raises:
            requests.exceptions.RequestException: If the request fails
        """
        url = f"{self.base_url}{endpoint}"
        response = requests.put(url, headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()
        
    def delete(self, endpoint: str) -> Dict[str, Any]:
        """
        Make a DELETE request to the API
        
        Args:
            endpoint: API endpoint (without base URL)
            
        Returns:
            Response data as dictionary
            
        Raises:
            requests.exceptions.RequestException: If the request fails
        """
        url = f"{self.base_url}{endpoint}"
        response = requests.delete(url, headers=self.headers)
        response.raise_for_status()
        return response.json()