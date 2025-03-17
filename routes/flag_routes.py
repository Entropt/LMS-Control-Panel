# routes/flag_routes.py - Flag submission and verification routes
from flask import Blueprint, request, jsonify, session
from utils.flag_generator import verify_flag, register_completion

flag_blueprint = Blueprint('flags', __name__)

@flag_blueprint.route('/api/flags/verify', methods=['POST'])
def verify_flag_route():
    """
    Verify a submitted flag
    
    Expected JSON body:
    {
        "flag": "flag{...}",
        "challenge": "challenge_name"
    }
    """
    if not request.is_json:
        return jsonify({"error": "Expected JSON request"}), 400
        
    data = request.json
    flag = data.get('flag')
    challenge = data.get('challenge')
    
    if not flag or not challenge:
        return jsonify({"error": "Flag and challenge name are required"}), 400
        
    # Get session ID from cookie
    session_id = session.get('lti_session_id')
    
    # Verify the flag
    if verify_flag(flag, challenge, session_id=session_id):
        # Register completion if flag is correct
        success, message = register_completion(challenge, session_id)
        
        if success:
            return jsonify({
                "success": True,
                "message": "Congratulations! Flag is correct.",
                "completion": {
                    "challenge": challenge,
                    "status": "complete"
                }
            })
        else:
            return jsonify({
                "success": True,
                "message": "Flag is correct, but there was an error registering completion: " + message
            })
    else:
        return jsonify({
            "success": False,
            "message": "Incorrect flag. Try again!"
        }), 400
        
def init_flag_routes(app):
    """Register flag routes with the app"""
    # Blueprint registration is now done in app.py
    pass