# Copyright (c) 2020 Vlsarro
# Copyright (c) 2013 Calin Crisan
# This file is part of motionEye.
#
# motionEye is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging
import os

from motioneye import config, mediafiles, motionctl, tasks, uploadservices, utils
from motioneye.handlers.base import BaseHandler

try:
    from motioneye.face_recognition_manager import get_face_manager
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False
    logging.warning("Face recognition not available - face_recognition_manager import failed")

__all__ = ('RelayEventHandler',)


class RelayEventHandler(BaseHandler):
    @BaseHandler.auth(admin=True)
    def post(self):
        event = self.get_argument('event')
        motion_camera_id = int(self.get_argument('motion_camera_id'))

        camera_id = motionctl.motion_camera_id_to_camera_id(motion_camera_id)
        if camera_id is None:
            logging.debug(
                'ignoring event for unknown motion camera id %s' % motion_camera_id
            )
            return self.finish_json()

        else:
            logging.debug(
                'received relayed event {event} for motion camera id {id} (camera id {cid})'.format(
                    event=event, id=motion_camera_id, cid=camera_id
                )
            )

        camera_config = config.get_camera(camera_id)
        if not utils.is_local_motion_camera(camera_config):
            logging.warning(
                'ignoring event for non-local camera with id %s' % camera_id
            )
            return self.finish_json()

        if event == 'start':
            if not camera_config['@motion_detection']:
                logging.debug(
                    'ignoring start event for camera with id %s and motion detection disabled'
                    % camera_id
                )
                return self.finish_json()

            motionctl.set_motion_detected(camera_id, True)

        elif event == 'stop':
            motionctl.set_motion_detected(camera_id, False)

        elif event == 'movie_end':
            filename = self.get_argument('filename')

            # Process face recognition
            self.process_face_recognition(camera_id, filename, camera_config)

            # generate preview (thumbnail)
            tasks.add(
                5,
                mediafiles.make_movie_preview,
                tag='make_movie_preview(%s)' % filename,
                camera_config=camera_config,
                full_path=filename,
            )

            # upload to external service
            if camera_config['@upload_enabled'] and camera_config['@upload_movie']:
                self.upload_media_file(filename, camera_id, camera_config)

        elif event == 'picture_save':
            filename = self.get_argument('filename')

            # Process face recognition
            self.process_face_recognition(camera_id, filename, camera_config)

            # upload to external service
            if camera_config['@upload_enabled'] and camera_config['@upload_picture']:
                self.upload_media_file(filename, camera_id, camera_config)

        else:
            logging.warning('unknown event %s' % event)

        self.finish_json()

    def process_face_recognition(self, camera_id, filename, camera_config):
        """Process face recognition for motion events"""
        logging.info(f"process_face_recognition called for camera {camera_id}, file: {filename}")

        if not FACE_RECOGNITION_AVAILABLE:
            logging.warning("Face recognition not available - skipping")
            return

        try:
            logging.info("Getting face manager...")
            face_manager = get_face_manager()
            if face_manager and face_manager.is_available():
                logging.info("Face manager available, processing motion event...")
                
                # Debug logging
                cwd = os.getcwd()
                logging.info(f"Current working directory: {cwd}")
                logging.info(f"Received filename: {filename}")

                # Handle relative paths - check conf/media and media directories
                actual_file = None
                if not os.path.isabs(filename):
                    possible_paths = [
                        os.path.join(cwd, 'conf', filename),  # Files are in conf/media
                        os.path.join(cwd, filename),  # Also try direct path
                        os.path.join(cwd, filename.lstrip('/')),
                        filename
                    ]
                    
                    # Wait up to 3 seconds for file to appear
                    import time
                    for attempt in range(6):
                        for path in possible_paths:
                            if os.path.exists(path):
                                actual_file = path
                                logging.info(f"Found image file at: {actual_file} (attempt {attempt + 1})")
                                break

                        if actual_file:
                            break

                        if attempt < 5:
                            time.sleep(0.5)
                            logging.info(f"File not found yet, waiting... (attempt {attempt + 1})")
                    
                    if actual_file:
                        filename = actual_file
                    else:
                        logging.error(f"Could not find image file after waiting. CWD: {cwd}, Original: {filename}")
                        logging.error(f"Final check - tried paths: {possible_paths}")
                        return

                # Process face recognition
                faces = face_manager.process_motion_event(camera_id, filename)

                if faces:
                    recognized_names = [
                        face['name'] for face in faces
                        if face['name'] != 'Unknown' and face['confidence'] >= 0.6
                    ]

                    if recognized_names:
                        logging.info(f"Camera {camera_id}: Face recognition detected - {', '.join(recognized_names)}")
                    else:
                        logging.info(f"Camera {camera_id}: Faces detected but none recognized")
                else:
                    logging.info(f"Camera {camera_id}: No faces detected")
            else:
                logging.warning("Face manager not available or disabled")

        except Exception as e:
            logging.error(f"Face recognition error for camera {camera_id}: {e}")
            import traceback
            logging.error(traceback.format_exc())

    def upload_media_file(self, filename, camera_id, camera_config):
        service_name = camera_config['@upload_service']

        tasks.add(
            5,
            uploadservices.upload_media_file,
            tag='upload_media_file(%s)' % filename,
            camera_id=camera_id,
            service_name=service_name,
            camera_name=camera_config['camera_name'],
            target_dir=camera_config['@upload_subfolders']
            and camera_config['target_dir'],
            filename=filename,
        )