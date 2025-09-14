# Copyright (c) 2024 Jules
# This file is part of motionEye.
#
# This module handles the web UI for managing familiar faces.

import os
import json
import logging
from motioneye.handlers.base import BaseHandler
from motioneye import settings

# This should be consistent with opencv_processor.py
FACES_DIR = os.path.join(settings.CONF_PATH, 'faces')
ENCODINGS_CACHE_PATH = os.path.join(FACES_DIR, 'known_faces.pkl')


class FacesHandler(BaseHandler):
    @BaseHandler.auth(admin=True)
    def get(self):
        """List the known faces."""
        if not os.path.exists(FACES_DIR):
            return self.finish_json([])

        faces = []
        try:
            for filename in os.listdir(FACES_DIR):
                if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                    name = os.path.splitext(filename)[0]
                    faces.append({'name': name, 'filename': filename})
        except OSError as e:
            logging.error(f"Failed to list faces directory: {e}")
            self.set_status(500)
            return self.finish_json({'error': 'Failed to access faces directory.'})

        return self.finish_json(faces)

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
        """Deletes the encodings cache to force a refresh."""
        if os.path.exists(ENCODINGS_CACHE_PATH):
            try:
                os.remove(ENCODINGS_CACHE_PATH)
                logging.info("Cleared face encodings cache.")
            except OSError as e:
                logging.error(f"Failed to clear face encodings cache: {e}")


class FacesPageHandler(BaseHandler):
    @BaseHandler.auth(admin=True)
    def get(self):
        self.render('faces.html')
