# models/lti_config.py - LTI Configuration Model
from flask_sqlalchemy import SQLAlchemy
from models.user import db

class LTIConfig(db.Model):
    """LTI Configuration for Canvas Integration"""
    __tablename__ = 'lti_configs'
    
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.String(255), unique=True, nullable=False)
    deployment_id = db.Column(db.String(255), nullable=False)
    auth_login_url = db.Column(db.String(255), nullable=False)
    auth_token_url = db.Column(db.String(255), nullable=False)
    key_set_url = db.Column(db.String(255), nullable=False)
    private_key = db.Column(db.Text, nullable=False)  # Store PEM format private key
    public_key = db.Column(db.Text, nullable=False)   # Store PEM format public key
    tool_public_key = db.Column(db.Text, nullable=False)  # Public key exposed to Canvas
    
    # Additional details for the tool
    tool_name = db.Column(db.String(255), default="Juice Shop Integration")
    tool_description = db.Column(db.Text, default="Security training platform integration")
    
    def __init__(self, client_id, deployment_id, auth_login_url, auth_token_url, 
                 key_set_url, private_key, public_key, tool_public_key, 
                 tool_name="Juice Shop Integration", 
                 tool_description="Security training platform integration"):
        self.client_id = client_id
        self.deployment_id = deployment_id
        self.auth_login_url = auth_login_url
        self.auth_token_url = auth_token_url
        self.key_set_url = key_set_url
        self.private_key = private_key
        self.public_key = public_key
        self.tool_public_key = tool_public_key
        self.tool_name = tool_name
        self.tool_description = tool_description
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'client_id': self.client_id,
            'deployment_id': self.deployment_id,
            'auth_login_url': self.auth_login_url,
            'auth_token_url': self.auth_token_url,
            'key_set_url': self.key_set_url,
            'tool_name': self.tool_name,
            'tool_description': self.tool_description
        }

# Table for storing launch data
class LTILaunchData(db.Model):
    """Store LTI launch data for session management"""
    __tablename__ = 'lti_launch_data'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(255), unique=True, nullable=False)
    user_id = db.Column(db.String(255), nullable=False)
    context_id = db.Column(db.String(255), nullable=False)  # Course ID
    resource_link_id = db.Column(db.String(255))
    roles = db.Column(db.String(255))
    expiry = db.Column(db.DateTime, nullable=False)
    
    def __init__(self, session_id, user_id, context_id, resource_link_id, roles, expiry):
        self.session_id = session_id
        self.user_id = user_id
        self.context_id = context_id
        self.resource_link_id = resource_link_id
        self.roles = roles
        self.expiry = expiry