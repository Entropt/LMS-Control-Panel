# config/settings.py - Configuration settings
import os
import json
from pathlib import Path

def get_config_path():
    """Get the path to the config file"""
    # Check for config in environment variable
    config_path_env = os.getenv('LMS_CONFIG_PATH')
    if config_path_env:
        return Path(config_path_env)
        
    # Check for config in current directory
    local_config = Path("config.json")
    if local_config.exists():
        return local_config
        
    # Default to app directory
    app_dir = Path(__file__).parent.parent
    return app_dir / "config" / "config.json"

def load_config():
    """Load configuration from file"""
    config_path = get_config_path()
    
    # Create default config if it doesn't exist
    if not config_path.exists():
        default_config = {
            "api": {
                "base_url": "https://lms.example.com/api/v1",
                "api_key": ""
            }
        }
        
        # Ensure directory exists
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write default config
        with open(config_path, "w") as f:
            json.dump(default_config, f, indent=2)
            
        return default_config
    
    # Load existing config
    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config: {e}")
        return {}

def save_config(config):
    """Save configuration to file"""
    config_path = get_config_path()
    
    # Ensure directory exists
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write config
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)