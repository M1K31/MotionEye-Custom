# Copyright (c) 2024 Jules
# This file is part of motionEye.
#
# This module handles the web UI for managing familiar faces.

import os
import json
import logging
from motioneye.handlers.base import BaseHandler
from motioneye import settings

# Try to import face recognition manager, handle gracefully if dependencies are missing
try:
    from motioneye.face_recognition_manager import get_face_manager
    FACE_MANAGER_AVAILABLE = True
except ImportError:
    FACE_MANAGER_AVAILABLE = False
    get_face_manager = None
    logging.debug("face_recognition_manager not available (missing dependencies)")

# This should be consistent with face_recognition_manager.py
# Use the same faces folder as the manager
FACES_DIR = os.path.join(settings.CONF_PATH, 'faces')
# DEPRECATED: Use face_recognition_manager.py's JSON format instead
ENCODINGS_CACHE_PATH = os.path.join(FACES_DIR, 'known_faces.pkl')


class FacesHandler(BaseHandler):
    @BaseHandler.auth(admin=True)
    def get(self):
        """List the known faces and the last unfamiliar face event."""

        # Get last unfamiliar face timestamp
        last_unfamiliar_face = None
        timestamp_path = os.path.join(settings.CONF_PATH, 'last_unfamiliar_face.txt')
        if os.path.exists(timestamp_path):
            try:
                with open(timestamp_path, 'r') as f:
                    last_unfamiliar_face = f.read().strip()
            except Exception as e:
                logging.error(f"Failed to read unfamiliar face timestamp: {e}")

        # Get list of known faces
        faces = []
        if os.path.exists(FACES_DIR):
            try:
                for filename in os.listdir(FACES_DIR):
                    if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                        name = os.path.splitext(filename)[0]
                        faces.append({'name': name, 'filename': filename})
            except OSError as e:
                logging.error(f"Failed to list faces directory: {e}")
                self.set_status(500)
                return self.finish_json({'error': 'Failed to access faces directory.'})

        response = {
            'faces': faces,
            'last_unfamiliar_face': last_unfamiliar_face
        }
        return self.finish_json(response)

    @BaseHandler.auth(admin=True)
    def post(self):
        """Upload a new face."""
        try:
            # FIX: Use get_argument instead of get_body_argument
            name = self.get_argument('name')
            file_info = self.request.files['file'][0]
            filename = file_info['filename']
            body = file_info['body']
        except (KeyError, IndexError) as e:
            logging.error(f"Failed to get face upload data: {e}")
            self.set_status(400)  # FIX: Set status code separately
            return self.finish_json({'error': 'Missing name or file.'})

        if not name or not filename:
            self.set_status(400)  # FIX: Set status code separately
            return self.finish_json({'error': 'Name and filename are required.'})

        # FIX: Enhanced sanitization to prevent path traversal
        base_name = "".join(x for x in name if x.isalnum() or x in "._-").rstrip()
        if not base_name:  # Ensure we have a valid filename after sanitization
            self.set_status(400)
            return self.finish_json({'error': 'Invalid name provided.'})
        
        extension = os.path.splitext(filename)[1].lower()
        if extension not in ['.png', '.jpg', '.jpeg']:
            self.set_status(400)
            return self.finish_json({'error': 'Invalid file type. Only PNG, JPG, and JPEG are allowed.'})
        
        new_filename = f"{base_name}{extension}"

        # FIX: Ensure filename doesn't contain path separators
        if os.path.sep in new_filename or '..' in new_filename:
            self.set_status(400)
            return self.finish_json({'error': 'Invalid filename.'})

        try:
            if not os.path.exists(FACES_DIR):
                os.makedirs(FACES_DIR, mode=0o755)  # Secure permissions

            file_path = os.path.join(FACES_DIR, new_filename)
            
            # FIX: Additional security check
            if not file_path.startswith(FACES_DIR):
                self.set_status(400)
                return self.finish_json({'error': 'Invalid file path.'})

            # FIX: Add exception handling for file operations
            with open(file_path, 'wb') as f:
                f.write(body)

            self._clear_cache()
            logging.info(f"Added new face: {name} as {new_filename}")
            return self.finish_json({'name': name, 'filename': new_filename})
            
        except OSError as e:
            logging.error(f"Failed to save face file: {e}")
            self.set_status(500)
            return self.finish_json({'error': 'Failed to save file.'})

    @BaseHandler.auth(admin=True)
    def delete(self, filename):
        """Delete a known face."""
        if not filename:
            self.set_status(400)  # FIX: Set status code separately
            return self.finish_json({'error': 'Filename is required.'})

        # FIX: Additional security checks
        if os.path.sep in filename or '..' in filename:
            self.set_status(400)
            return self.finish_json({'error': 'Invalid filename.'})

        file_path = os.path.join(FACES_DIR, filename)
        
        # FIX: Ensure path is within FACES_DIR
        if not file_path.startswith(FACES_DIR):
            self.set_status(400)
            return self.finish_json({'error': 'Invalid file path.'})

        if not os.path.exists(file_path):
            self.set_status(404)  # FIX: Set status code separately
            return self.finish_json({'error': 'File not found.'})

        try:
            os.remove(file_path)
            self._clear_cache()
            logging.info(f"Deleted face: {filename}")
            return self.finish_json({'status': 'deleted'})
        except OSError as e:
            logging.error(f"Failed to delete face {filename}: {e}")
            self.set_status(500)  # FIX: Set status code separately
            return self.finish_json({'error': 'Failed to delete file.'})

    def _clear_cache(self):
        """
        Clears the encodings cache and triggers face recognition retraining.
        
        This ensures the face_recognition_manager stays in sync with
        the faces stored on disk.
        """
        # Clear legacy pickle cache if it exists
        if os.path.exists(ENCODINGS_CACHE_PATH):
            try:
                os.remove(ENCODINGS_CACHE_PATH)
                logging.info("Cleared legacy face encodings cache.")
            except OSError as e:
                logging.error(f"Failed to clear legacy face encodings cache: {e}")
        
        # Trigger retraining in the face recognition manager if available
        if not FACE_MANAGER_AVAILABLE or get_face_manager is None:
            return
        
        try:
            manager = get_face_manager()
            if manager and manager.is_available():
                # Update the manager's faces folder to match this handler
                manager.faces_folder = FACES_DIR
                manager.encodings_file = os.path.join(FACES_DIR, 'face_encodings.json')
                
                # Trigger retraining in background (non-blocking for web request)
                import threading
                def retrain():
                    try:
                        manager.train_face_recognition()
                    except Exception as e:
                        logging.error(f"Background face recognition training failed: {e}")
                
                thread = threading.Thread(target=retrain, daemon=True)
                thread.start()
                logging.info("Triggered face recognition retraining.")
        except Exception as e:
            logging.error(f"Failed to trigger face recognition retraining: {e}")


class FacesTrainHandler(BaseHandler):
    """Handler for triggering face recognition training"""
    
    @BaseHandler.auth(admin=True)
    def post(self):
        """Trigger face recognition model training"""
        if not FACE_MANAGER_AVAILABLE or get_face_manager is None:
            self.set_status(503)
            return self.finish_json({
                'error': 'Face recognition dependencies not installed',
                'success': False
            })
        
        try:
            manager = get_face_manager()
            if not manager:
                self.set_status(503)
                return self.finish_json({
                    'error': 'Face recognition manager not available',
                    'success': False
                })
            
            if not manager.is_available():
                self.set_status(503)
                return self.finish_json({
                    'error': 'Face recognition library not installed or disabled',
                    'success': False
                })
            
            # Check if training is already in progress
            status = manager.get_status()
            if status.get('training_in_progress', False):
                self.set_status(409)
                return self.finish_json({
                    'error': 'Training already in progress',
                    'success': False
                })
            
            # Trigger training
            success = manager.train_face_recognition()
            
            if success:
                return self.finish_json({
                    'success': True,
                    'message': 'Face recognition training completed',
                    'total_encodings': manager.get_status()['total_encodings']
                })
            else:
                self.set_status(400)
                return self.finish_json({
                    'success': False,
                    'error': 'Training failed - check logs for details'
                })
                
        except Exception as e:
            logging.error(f"Error during face training: {e}")
            self.set_status(500)
            return self.finish_json({
                'error': str(e),
                'success': False
            })
    
    @BaseHandler.auth(admin=True)
    def get(self):
        """Get face recognition training status"""
        if not FACE_MANAGER_AVAILABLE or get_face_manager is None:
            return self.finish_json({
                'available': False,
                'error': 'Face recognition dependencies not installed'
            })
        
        try:
            manager = get_face_manager()
            if not manager:
                return self.finish_json({
                    'available': False,
                    'error': 'Face recognition manager not available'
                })
            
            return self.finish_json(manager.get_status())
            
        except Exception as e:
            logging.error(f"Error getting face recognition status: {e}")
            self.set_status(500)
            return self.finish_json({'error': str(e)})


class FacesPageHandler(BaseHandler):
    @BaseHandler.auth(admin=True)
    def get(self):
        self.render('faces.html')
