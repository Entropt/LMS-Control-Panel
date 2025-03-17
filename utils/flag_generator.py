# utils/flag_generator.py - Generate dynamic flags for CTF challenges
import hmac
import hashlib
import base64
import json
import os
from datetime import datetime, timedelta
from models.lti_config import LTILaunchData, db
from flask import current_app

def hmac_generator(key, value):
    """
    Generate an HMAC of a value using the provided key
    Replicates the "hmac" function from juice-shop-ctf/lib/generators/fbctf.js
    
    Args:
        key: Secret key for HMAC
        value: Value to generate HMAC for
        
    Returns:
        HMAC digest as string
    """
    h = hmac.new(key.encode('utf-8'), value.encode('utf-8'), hashlib.sha256)
    return h.hexdigest()

def generate_flag(challenge_name, user_id=None, context_id=None, session_id=None):
    """
    Generate a dynamic flag for a specific challenge and user
    
    Args:
        challenge_name: Name of the challenge
        user_id: Canvas user ID (optional)
        context_id: Canvas course ID (optional)
        session_id: LTI session ID (optional)
        
    Returns:
        Flag string
    """
    # Get CTF secret key from environment or generate one if not set
    ctf_key = os.getenv('CTF_KEY')
    if not ctf_key:
        # Use app secret key as fallback
        ctf_key = current_app.secret_key
    
    # Create flag components
    flag_components = {
        'challenge': challenge_name
    }
    
    # Add user context if available
    if user_id:
        flag_components['user'] = user_id
    
    if context_id:
        flag_components['course'] = context_id
    
    if session_id:
        # Get session data if session_id is provided
        launch_data = LTILaunchData.query.filter_by(session_id=session_id).first()
        if launch_data:
            flag_components['user'] = launch_data.user_id
            flag_components['course'] = launch_data.context_id
    
    # Generate the flag
    serialized = json.dumps(flag_components, sort_keys=True)
    flag_hmac = hmac_generator(ctf_key, serialized)
    
    # Format the flag
    flag = f"flag{{{flag_hmac}}}"
    return flag

def verify_flag(submitted_flag, challenge_name, user_id=None, context_id=None, session_id=None):
    """
    Verify a submitted flag against the expected flag
    
    Args:
        submitted_flag: Flag submitted by the user
        challenge_name: Name of the challenge
        user_id: Canvas user ID (optional)
        context_id: Canvas course ID (optional)
        session_id: LTI session ID (optional)
        
    Returns:
        Boolean indicating whether the flag is correct
    """
    expected_flag = generate_flag(challenge_name, user_id, context_id, session_id)
    return submitted_flag == expected_flag

def register_completion(challenge_name, session_id):
    """
    Register challenge completion for a user
    
    Args:
        challenge_name: Name of the completed challenge
        session_id: LTI session ID
        
    Returns:
        Success status and message
    """
    # Implementation would depend on how you want to track completions
    # This is a placeholder
    # You might want to:
    # 1. Store completion in database
    # 2. Update Canvas grade using the assignment service
    
    return True, "Challenge completion registered"