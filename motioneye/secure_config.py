# Copyright (c) 2025 Mikel Smart
# This file is part of motionEye.
# SPDX-License-Identifier: MIT  # Replace with the project's license identifier
# See LICENSE at the repository root for full license text.

import json
import hmac
import hashlib
import secrets
import logging
import os
from datetime import datetime

class SecureConfigManager:
    """Secure configuration backup/restore without pickle vulnerabilities"""
    
    def __init__(self):
        self.secret_key_file = os.path.expanduser('~/.motioneye_secret_key')
        self.secret_key = self._get_or_generate_secret_key()
    
    def _get_or_generate_secret_key(self):
        """Get or generate secret key for HMAC signing"""
        try:
            # Try to read existing key
            with open(self.secret_key_file, 'rb') as f:
                return f.read()
        except FileNotFoundError:
            # Generate new key
            key = secrets.token_bytes(32)
            try:
                # Ensure directory exists
                os.makedirs(os.path.dirname(self.secret_key_file), mode=0o700, exist_ok=True)
                
                with open(self.secret_key_file, 'wb') as f:
                    f.write(key)
                os.chmod(self.secret_key_file, 0o600)
                logging.info("Generated new secret key for configuration security")
            except Exception as e:
                logging.warning(f"Could not save secret key: {e}")
            return key
    
    def create_secure_backup(self, config_data):
        """Create secure configuration backup using JSON + HMAC"""
        try:
            # Sanitize sensitive data
            sanitized_config = self._sanitize_config(config_data)
            
            # Convert to JSON
            json_data = json.dumps(sanitized_config, default=str, indent=2)
            
            # Create HMAC signature
            signature = hmac.new(
                self.secret_key,
                json_data.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # Create signed backup
            backup = {
                'data': json_data,
                'signature': signature,
                'timestamp': datetime.now().isoformat(),
                'version': '2.0',
                'format': 'secure_json'
            }
            
            return json.dumps(backup, indent=2)
            
        except Exception as e:
            logging.error(f"Failed to create secure backup: {e}")
            raise ValueError("Backup creation failed")
    
    def restore_secure_backup(self, backup_content):
        """Safely restore configuration from secure backup"""
        try:
            backup_data = json.loads(backup_content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid backup format: {e}")
        
        # Verify structure
        required_fields = ['data', 'signature', 'timestamp', 'version']
        if not all(field in backup_data for field in required_fields):
            raise ValueError("Missing required backup fields")
        
        # Verify signature
        expected_signature = hmac.new(
            self.secret_key,
            backup_data['data'].encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(backup_data['signature'], expected_signature):
            raise ValueError("Backup signature verification failed - backup may be corrupted or tampered with")
        
        # Parse and return config data
        try:
            config_data = json.loads(backup_data['data'])
            logging.info("Configuration backup restored successfully")
            return config_data
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid backup data: {e}")
    
    def _sanitize_config(self, config_data):
        """Remove sensitive information from config before backup"""
        if not isinstance(config_data, dict):
            return config_data
        
        sensitive_keys = [
            'password', 'passwd', 'secret', 'key', 'token',
            'smtp_password', 'ftp_password', 'admin_password',
            'surveillance_password', 'email_password'
        ]
        
        sanitized = {}
        for key, value in config_data.items():
            if any(sensitive_key in key.lower() for sensitive_key in sensitive_keys):
                sanitized[key] = '[REDACTED]'
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_config(value)
            else:
                sanitized[key] = value
        
        return sanitized

# Global secure config manager
secure_config_manager = SecureConfigManager()

# Legacy compatibility functions
def create_backup(config_data):
    """Create secure backup - replaces pickle-based backup"""
    global secure_config_manager
    return secure_config_manager.create_secure_backup(config_data)

def restore_backup(backup_content):
    """Restore secure backup - replaces pickle-based restore"""
    global secure_config_manager
    return secure_config_manager.restore_secure_backup(backup_content)