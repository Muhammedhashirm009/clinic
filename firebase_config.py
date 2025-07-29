import os
import json
import firebase_admin
from firebase_admin import credentials, firestore

class FirebaseConfig:
    def __init__(self):
        self.firebase_app = None
        self.db = None
        
    def initialize_firebase(self, config_dict=None):
        """Initialize Firebase with provided configuration"""
        try:
            # Check if already initialized
            if self.firebase_app:
                return True
                
            if config_dict:
                # Use provided config
                firebase_config = config_dict
            else:
                # Try to get from environment or stored config
                firebase_config = self.get_stored_config()
                
            if not firebase_config:
                return False
                
            # Initialize Firebase Admin SDK
            if not firebase_admin._apps:
                cred = credentials.Certificate(firebase_config.get('service_account'))
                self.firebase_app = firebase_admin.initialize_app(cred)
            else:
                self.firebase_app = firebase_admin.get_app()
                
            # Initialize Firestore
            self.db = firestore.client()
            
            return True
            
        except Exception as e:
            print(f"Firebase initialization error: {e}")
            return False
    
    def get_stored_config(self):
        """Get Firebase config from environment or file"""
        try:
            # Try environment variables first
            config = {
                'project_id': os.environ.get('FIREBASE_PROJECT_ID'),
                'service_account': json.loads(os.environ.get('FIREBASE_SERVICE_ACCOUNT', '{}'))
            }
            
            if all(config.values()):
                return config
                
            # Try local config file
            if os.path.exists('firebase_credentials.json'):
                with open('firebase_credentials.json', 'r') as f:
                    return json.load(f)
                    
        except Exception as e:
            print(f"Error loading Firebase config: {e}")
            
        return None
    
    def save_config(self, config_dict):
        """Save Firebase configuration"""
        try:
            with open('firebase_credentials.json', 'w') as f:
                json.dump(config_dict, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving Firebase config: {e}")
            return False
    
    def is_configured(self):
        """Check if Firebase is properly configured"""
        return self.firebase_app is not None and self.db is not None

# Global Firebase instance
firebase_config = FirebaseConfig()