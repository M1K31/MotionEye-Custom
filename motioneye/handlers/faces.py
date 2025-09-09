# Copyright (c) 2024 Jules
# This file is part of motionEye.
#
# This module handles the web UI for managing familiar faces.

import os
import json
import logging
from motioneye.handlers.base import BaseHandler, TemplateMixin
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
        for filename in os.listdir(FACES_DIR):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                name = os.path.splitext(filename)[0]
                faces.append({'name': name, 'filename': filename})

        return self.finish_json(faces)

    @BaseHandler.auth(admin=True)
    def post(self):
        """Upload a new face."""
        try:
            name = self.get_body_argument('name')
            file_info = self.request.files['file'][0]
            filename = file_info['filename']
            body = file_info['body']
        except Exception as e:
            logging.error(f"Failed to get face upload data: {e}")
            return self.finish_json({'error': 'Missing name or file.'}, status_code=400)

        if not name or not filename:
            return self.finish_json({'error': 'Name and filename are required.'}, status_code=400)

        # Sanitize the name to be used as a filename
        base_name = "".join(x for x in name if x.isalnum() or x in "._-").rstrip()
        extension = os.path.splitext(filename)[1]
        new_filename = f"{base_name}{extension}"

        if not os.path.exists(FACES_DIR):
            os.makedirs(FACES_DIR)

        file_path = os.path.join(FACES_DIR, new_filename)

        with open(file_path, 'wb') as f:
            f.write(body)

        self._clear_cache()
        logging.info(f"Added new face: {name} as {new_filename}")
        return self.finish_json({'name': name, 'filename': new_filename})

    @BaseHandler.auth(admin=True)
    def delete(self, filename):
        """Delete a known face."""
        if not filename:
            return self.finish_json({'error': 'Filename is required.'}, status_code=400)

        file_path = os.path.join(FACES_DIR, filename)

        if not os.path.exists(file_path):
            return self.finish_json({'error': 'File not found.'}, status_code=404)

        try:
            os.remove(file_path)
            self._clear_cache()
            logging.info(f"Deleted face: {filename}")
            return self.finish_json({'status': 'deleted'})
        except Exception as e:
            logging.error(f"Failed to delete face {filename}: {e}")
            return self.finish_json({'error': 'Failed to delete file.'}, status_code=500)

    def _clear_cache(self):
        """Deletes the encodings cache to force a refresh."""
        if os.path.exists(ENCODINGS_CACHE_PATH):
            try:
                os.remove(ENCODINGS_CACHE_PATH)
                logging.info("Cleared face encodings cache.")
            except Exception as e:
                logging.error(f"Failed to clear face encodings cache: {e}")


class FacesPageHandler(BaseHandler, TemplateMixin):
    @BaseHandler.auth(admin=True)
    def get(self):
        self.render('faces.html')
