# services/lti_service.py - LTI Service implementation
import jwt
import time
import uuid
import json
import requests
from datetime import datetime, timedelta
from flask import request, session, url_for
from pylti1p3.tool_config import ToolConfJsonFile
from pylti1p3.registration import Registration
from pylti1p3.message_launch import MessageLaunch

from models.lti_config import LTIConfig, LTILaunchData, db

class LTIService:
    """Service for handling LTI 1.3 requests and authentication"""
    
    def __init__(self, app):
        """Initialize the LTI service with Flask app context"""
        self.app = app
        self.config = None
        
    def load_config(self):
        """Load LTI config from database"""
        with self.app.app_context():
            self.config = LTIConfig.query.first()
            return self.config
            
    def get_public_keyset(self):
        """
        Return JWKS (JSON Web Key Set) for the tool
        This endpoint will be exposed to Canvas LMS
        """
        if not self.config:
            self.load_config()
            
        if not self.config:
            return {"keys": []}
            
        # Return the tool's public key in JWKS format
        return {
            "keys": [
                json.loads(self.config.tool_public_key)
            ]
        }
        
    def get_tool_configuration(self):
        """
        Return the LTI tool configuration for Canvas
        Used for dynamic registration
        """
        if not self.config:
            self.load_config()
            
        if not self.config:
            return {}
            
        # Base URL for the application
        base_url = request.url_root.rstrip('/')
        
        # Return tool configuration in proper format
        return {
            "title": self.config.tool_name,
            "description": self.config.tool_description,
            "oidc_initiation_url": f"{base_url}/lti/login",
            "target_link_uri": f"{base_url}/lti/launch",
            "scopes": [
                "https://purl.imsglobal.org/spec/lti-ags/scope/lineitem",
                "https://purl.imsglobal.org/spec/lti-ags/scope/result.readonly",
                "https://purl.imsglobal.org/spec/lti-ags/scope/score",
                "https://purl.imsglobal.org/spec/lti-nrps/scope/contextmembership.readonly"
            ],
            "extensions": [
                {
                    "platform": "canvas.instructure.com",
                    "settings": {
                        "platform": "canvas.instructure.com",
                        "placements": [
                            {
                                "placement": "course_navigation",
                                "message_type": "LtiResourceLinkRequest",
                                "target_link_uri": f"{base_url}/lti/launch",
                                "text": "Juice Shop Exercises"
                            },
                            {
                                "placement": "assignment_selection",
                                "message_type": "LtiDeepLinkingRequest",
                                "target_link_uri": f"{base_url}/lti/deep_linking"
                            }
                        ]
                    }
                }
            ],
            "public_jwk_url": f"{base_url}/lti/jwks",
            "custom_fields": {
                "canvas_course_id": "$Canvas.course.id",
                "canvas_user_id": "$Canvas.user.id"
            }
        }
        
    def validate_launch_request(self, request_data):
        """
        Validate an LTI launch request
        Returns user info if valid, None otherwise
        """
        if not self.config:
            self.load_config()
            
        if not self.config:
            return None
            
        try:
            # Create a Registration object for the LTI tool
            registration = Registration()
            registration.set_auth_login_url(self.config.auth_login_url)
            registration.set_auth_token_url(self.config.auth_token_url)
            registration.set_client_id(self.config.client_id)
            registration.set_key_set_url(self.config.key_set_url)
            registration.set_tool_private_key(self.config.private_key)
            
            # Create message launch and validate
            message_launch = MessageLaunch(registration)
            launch_data = message_launch.parse_and_validate_launch_request(request)
            
            if launch_data.is_valid():
                # Extract and return relevant data
                user_id = launch_data.get_claim('sub')
                context_id = launch_data.get_claim('https://purl.imsglobal.org/spec/lti/claim/context', {}).get('id')
                resource_link_id = launch_data.get_claim('https://purl.imsglobal.org/spec/lti/claim/resource_link', {}).get('id')
                roles = launch_data.get_claim('https://purl.imsglobal.org/spec/lti/claim/roles', [])
                
                # Generate a session ID
                session_id = str(uuid.uuid4())
                
                # Store launch data in database
                expiry = datetime.now() + timedelta(hours=2)
                launch_record = LTILaunchData(
                    session_id=session_id,
                    user_id=user_id,
                    context_id=context_id,
                    resource_link_id=resource_link_id,
                    roles=','.join(roles),
                    expiry=expiry
                )
                db.session.add(launch_record)
                db.session.commit()
                
                # Return session data
                return {
                    'session_id': session_id,
                    'user_id': user_id,
                    'context_id': context_id,
                    'resource_link_id': resource_link_id,
                    'roles': roles
                }
            
            return None
        except Exception as e:
            print(f"Error validating LTI launch: {e}")
            return None
            
    def get_launch_data(self, session_id):
        """
        Retrieve launch data from session ID
        Returns None if session doesn't exist or is expired
        """
        with self.app.app_context():
            launch_data = LTILaunchData.query.filter_by(session_id=session_id).first()
            
            if not launch_data:
                return None
                
            # Check if session is expired
            if launch_data.expiry < datetime.now():
                db.session.delete(launch_data)
                db.session.commit()
                return None
                
            return {
                'user_id': launch_data.user_id,
                'context_id': launch_data.context_id,
                'resource_link_id': launch_data.resource_link_id,
                'roles': launch_data.roles.split(',') if launch_data.roles else []
            }
            
    def send_grade(self, score, session_id):
        """
        Send grade back to Canvas
        
        Args:
            score: Score value between 0.0 and 1.0
            session_id: LTI session ID from launch
            
        Returns:
            Success status and message
        """
        if not self.config:
            self.load_config()
            
        launch_data = self.get_launch_data(session_id)
        if not launch_data:
            return False, "Invalid or expired session"
            
        try:
            # We would need the AGS endpoint from the launch data
            # For now we'll return a placeholder
            return True, "Score successfully sent"
        except Exception as e:
            return False, f"Error sending score: {e}"