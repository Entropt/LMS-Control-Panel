# routes/lti_routes.py - LTI route implementations
from flask import Blueprint, request, redirect, url_for, session, jsonify, render_template, current_app
from models.lti_config import LTIConfig, db
from utils.key_generator import generate_rsa_keys, create_jwk_from_public_key
import os
import json

lti_blueprint = Blueprint('lti', __name__)

def get_lti_service():
    """Helper to get LTI service from app config"""
    return current_app.config.get('lti_service')

def init_lti_routes(app):
    """Initialize LTI routes with app context"""
    # Make lti_service available in templates
    @app.context_processor
    def inject_lti_service():
        return {'lti_service': app.config.get('lti_service')}

@lti_blueprint.route('/config', methods=['GET'])
def lti_config():
    """Return LTI tool configuration for Canvas"""
    lti_service = get_lti_service()
    return jsonify(lti_service.get_tool_configuration())

@lti_blueprint.route('/jwks', methods=['GET'])
def lti_jwks():
    """Return JWKS (JSON Web Key Set) for the tool"""
    lti_service = get_lti_service()
    return jsonify(lti_service.get_public_keyset())

@lti_blueprint.route('/setup', methods=['GET', 'POST'])
def lti_setup():
    """Setup LTI configuration page"""
    if request.method == 'POST':
        # Generate new RSA keys
        keys = generate_rsa_keys()
        private_key = keys['private_key']
        public_key = keys['public_key']
        
        # Generate JWK from public key
        jwk = create_jwk_from_public_key(public_key)
        
        # Save configuration
        config = LTIConfig.query.first()
        if not config:
            # Create new config
            config = LTIConfig(
                client_id=request.form.get('client_id'),
                deployment_id=request.form.get('deployment_id'),
                auth_login_url=request.form.get('auth_login_url'),
                auth_token_url=request.form.get('auth_token_url'),
                key_set_url=request.form.get('key_set_url'),
                private_key=private_key,
                public_key=public_key,
                tool_public_key=jwk,
                tool_name=request.form.get('tool_name'),
                tool_description=request.form.get('tool_description')
            )
            db.session.add(config)
        else:
            # Update existing config
            config.client_id = request.form.get('client_id')
            config.deployment_id = request.form.get('deployment_id')
            config.auth_login_url = request.form.get('auth_login_url')
            config.auth_token_url = request.form.get('auth_token_url')
            config.key_set_url = request.form.get('key_set_url')
            config.private_key = private_key
            config.public_key = public_key
            config.tool_public_key = jwk
            config.tool_name = request.form.get('tool_name')
            config.tool_description = request.form.get('tool_description')
            
        db.session.commit()
        return redirect(url_for('lti.lti_setup', success=True))
    
    # Get current config
    config = LTIConfig.query.first()
    
    # For new setup, suggest default Canvas URLs
    default_auth_login_url = "https://canvas.instructure.com/api/lti/authorize_redirect"
    default_auth_token_url = "https://canvas.instructure.com/login/oauth2/token"
    default_key_set_url = "https://canvas.instructure.com/api/lti/security/jwks"
    
    return render_template(
        'lti_setup.html', 
        config=config,
        default_auth_login_url=default_auth_login_url,
        default_auth_token_url=default_auth_token_url,
        default_key_set_url=default_key_set_url,
        success=request.args.get('success', False)
    )

@lti_blueprint.route('/login', methods=['GET', 'POST'])
def lti_login():
    """
    OIDC Login initiation endpoint
    This is called by Canvas during the LTI launch flow
    """
    # Just redirect back to the authorization URL with the same parameters
    if request.method == 'POST':
        # Forward all POST parameters to the redirect
        params = {}
        for key, value in request.form.items():
            params[key] = value
            
        # Get redirect URL from iss parameter (platform identifier)
        iss = request.form.get('iss')
        if iss and 'canvas.instructure.com' in iss:
            # Use Canvas authorization URL
            redirect_url = f"{request.form.get('login_hint')}&{request.url_encode(params)}"
            return redirect(redirect_url)
    
    # If we get here, something went wrong
    return jsonify({"error": "Invalid LTI login request"}), 400

@lti_blueprint.route('/launch', methods=['POST'])
def lti_launch():
    """
    Main LTI launch endpoint
    This is called by Canvas after successful authentication
    """
    # Validate the launch request
    lti_service = get_lti_service()
    launch_data = lti_service.validate_launch_request(request)
    
    if not launch_data:
        return jsonify({"error": "Invalid LTI launch request"}), 400
        
    # Store session ID in cookie
    session['lti_session_id'] = launch_data['session_id']
    
    # Check if the user is student or teacher
    is_instructor = any(role.endswith('/Instructor') for role in launch_data['roles'])
    
    if is_instructor:
        # Redirect to admin dashboard
        return redirect(url_for('dashboard'))
    else:
        # Redirect to student view (Juice Shop assignment)
        juice_shop_url = os.getenv('JUICE_SHOP_URL', 'http://localhost:3000')
        return redirect(juice_shop_url)

@lti_blueprint.route('/deep_linking', methods=['POST'])
def lti_deep_linking():
    """
    Deep Linking endpoint
    This is called by Canvas when selecting the tool from the assignment creation interface
    """
    # Validate the launch request
    lti_service = get_lti_service()
    launch_data = lti_service.validate_launch_request(request)
    
    if not launch_data:
        return jsonify({"error": "Invalid LTI launch request"}), 400
        
    # Store session ID in cookie
    session['lti_session_id'] = launch_data['session_id']
    
    # Render the deep linking selection page
    return render_template('lti_deep_linking.html', launch_data=launch_data)

@lti_blueprint.route('/submit_score', methods=['POST'])
def submit_score():
    """
    Submit a score back to Canvas
    Expected JSON body: {"score": 0.95}
    """
    if not request.is_json:
        return jsonify({"error": "Expected JSON request"}), 400
        
    data = request.json
    score = data.get('score')
    
    if score is None or not isinstance(score, (int, float)) or score < 0 or score > 1:
        return jsonify({"error": "Score must be a number between 0 and 1"}), 400
        
    # Get session ID from cookie
    session_id = session.get('lti_session_id')
    if not session_id:
        return jsonify({"error": "No active LTI session"}), 400
        
    # Send grade back to Canvas
    lti_service = get_lti_service()
    success, message = lti_service.send_grade(score, session_id)
    
    if success:
        return jsonify({"message": message})
    else:
        return jsonify({"error": message}), 400