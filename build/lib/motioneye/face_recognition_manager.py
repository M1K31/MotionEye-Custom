#!/usr/bin/env python3
"""
Face Recognition Manager for MotionEye-Custom
Integrates face recognition with motion detection events
"""

import os
import cv2
import pickle
import numpy as np
import logging
from typing import Dict, List, Optional
import json
from pathlib import Path

# Try to import face_recognition, handle gracefully if not available
try:
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False
    logging.warning("face_recognition library not available")


class FaceRecognitionManager:
    """
    Manages face recognition functionality for MotionEye
    """
    
    def __init__(self, config_path: str = "/etc/motioneye/faces_config.json"):
        self.config_path = config_path
        self.known_face_encodings = []
        self.known_face_names = []
        self.config = self.load_config()
        self.faces_folder = self.config.get('faces_folder', '/var/lib/motioneye/faces')
        self.encodings_file = os.path.join(self.faces_folder, 'face_encodings.pkl')
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Initialize if face recognition is available
        if FACE_RECOGNITION_AVAILABLE:
            # Ensure faces folder exists
            os.makedirs(self.faces_folder, exist_ok=True)
            
            # Load existing encodings
            self.load_face_encodings()
            
            self.logger.info(f"Face Recognition Manager initialized - {len(self.known_face_encodings)} encodings loaded")
        else:
            self.logger.warning("Face Recognition Manager initialized but face_recognition library not available")
    
    def load_config(self) -> Dict:
        """Load face recognition configuration"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading config: {e}")
        
        # Default configuration
        return {
            'faces_folder': '/var/lib/motioneye/faces',
            'recognition_threshold': 0.6,
            'detection_method': 'hog',  # 'hog' for CPU, 'cnn' for GPU
            'max_face_distance': 0.6,
            'enable_recognition': True,
            'min_confidence': 0.6,
            'process_every_n_frames': 1,  # Process every frame by default
            'resize_frame_width': 640  # Resize frames for faster processing
        }
    
    def save_config(self):
        """Save configuration to file"""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving config: {e}")
    
    def scan_faces_folder(self) -> Dict[str, List[str]]:
        """
        Scan the faces folder for person directories and images
        
        Expected structure:
        faces_folder/
        ├── person1/
        │   ├── image1.jpg
        │   └── image2.jpg
        └── person2/
            └── image1.jpg
        """
        faces_data = {}
        
        if not os.path.exists(self.faces_folder):
            return faces_data
        
        try:
            for person_dir in os.listdir(self.faces_folder):
                person_path = os.path.join(self.faces_folder, person_dir)
                
                # Skip files, only process directories
                if not os.path.isdir(person_path):
                    continue
                
                image_files = []
                for file_name in os.listdir(person_path):
                    if file_name.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')):
                        image_files.append(os.path.join(person_path, file_name))
                
                if image_files:
                    faces_data[person_dir] = image_files
                    
        except Exception as e:
            self.logger.error(f"Error scanning faces folder: {e}")
        
        return faces_data
    
    def train_face_recognition(self) -> bool:
        """Train face recognition model with images from faces folder"""
        if not FACE_RECOGNITION_AVAILABLE:
            self.logger.error("Cannot train: face_recognition library not available")
            return False
        
        try:
            self.known_face_encodings = []
            self.known_face_names = []
            
            faces_data = self.scan_faces_folder()
            
            if not faces_data:
                self.logger.warning("No face data found in faces folder")
                return False
            
            total_processed = 0
            
            for person_name, image_paths in faces_data.items():
                self.logger.info(f"Processing faces for: {person_name}")
                
                for image_path in image_paths:
                    try:
                        # Load and process image
                        image = face_recognition.load_image_file(image_path)
                        
                        # Get face encodings
                        encodings = face_recognition.face_encodings(
                            image,
                            model=self.config.get('detection_method', 'hog')
                        )
                        
                        if encodings:
                            for encoding in encodings:
                                self.known_face_encodings.append(encoding)
                                self.known_face_names.append(person_name)
                                total_processed += 1
                            
                            self.logger.info(f"Found {len(encodings)} face(s) in {os.path.basename(image_path)}")
                        else:
                            self.logger.warning(f"No faces found in {os.path.basename(image_path)}")
                            
                    except Exception as e:
                        self.logger.error(f"Error processing {image_path}: {e}")
            
            # Save encodings to file
            if total_processed > 0:
                self.save_face_encodings()
                self.logger.info(f"Training completed: {total_processed} face encodings from {len(faces_data)} people")
                return True
            else:
                self.logger.warning("Training failed: no face encodings generated")
                return False
            
        except Exception as e:
            self.logger.error(f"Error during training: {e}")
            return False
    
    def save_face_encodings(self):
        """Save face encodings to pickle file"""
        try:
            data = {
                'encodings': self.known_face_encodings,
                'names': self.known_face_names,
                'config': self.config,
                'version': '1.0'
            }
            
            with open(self.encodings_file, 'wb') as f:
                pickle.dump(data, f)
                
            self.logger.info(f"Face encodings saved to {self.encodings_file}")
            
        except Exception as e:
            self.logger.error(f"Error saving encodings: {e}")
    
    def load_face_encodings(self):
        """Load face encodings from pickle file"""
        try:
            if os.path.exists(self.encodings_file):
                with open(self.encodings_file, 'rb') as f:
                    data = pickle.load(f)
                    
                self.known_face_encodings = data.get('encodings', [])
                self.known_face_names = data.get('names', [])
                
                self.logger.info(f"Loaded {len(self.known_face_encodings)} face encodings")
            else:
                self.logger.info("No existing face encodings found")
                
        except Exception as e:
            self.logger.error(f"Error loading encodings: {e}")
            self.known_face_encodings = []
            self.known_face_names = []
    
    def recognize_faces_in_image(self, image_path: str) -> List[Dict]:
        """
        Recognize faces in an image file
        
        Args:
            image_path: Path to image file
            
        Returns:
            List of recognition results
        """
        if not FACE_RECOGNITION_AVAILABLE:
            return []
        
        if not self.config.get('enable_recognition', True):
            return []
        
        if not self.known_face_encodings:
            return []
        
        try:
            # Load image
            if not os.path.exists(image_path):
                self.logger.error(f"Image file not found: {image_path}")
                return []
            
            # Use OpenCV to load image (more reliable than face_recognition.load_image_file)
            frame = cv2.imread(image_path)
            if frame is None:
                self.logger.error(f"Could not load image: {image_path}")
                return []
            
            return self.recognize_faces_in_frame(frame)
            
        except Exception as e:
            self.logger.error(f"Error recognizing faces in {image_path}: {e}")
            return []
    
    def recognize_faces_in_frame(self, frame: np.ndarray) -> List[Dict]:
        """
        Recognize faces in a video frame
        
        Args:
            frame: OpenCV image frame (BGR format)
            
        Returns:
            List of dictionaries with recognition results
        """
        if not FACE_RECOGNITION_AVAILABLE:
            return []
        
        if not self.config.get('enable_recognition', True):
            return []
        
        if not self.known_face_encodings:
            return []
        
        try:
            # Resize frame for faster processing
            height, width = frame.shape[:2]
            resize_width = self.config.get('resize_frame_width', 640)
            
            if width > resize_width:
                scale = resize_width / width
                new_width = int(width * scale)
                new_height = int(height * scale)
                frame = cv2.resize(frame, (new_width, new_height))
            
            # Convert BGR to RGB (face_recognition expects RGB)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Find face locations
            face_locations = face_recognition.face_locations(
                rgb_frame,
                model=self.config.get('detection_method', 'hog')
            )
            
            if not face_locations:
                return []
            
            # Get face encodings
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
            
            results = []
            min_confidence = self.config.get('min_confidence', 0.6)
            
            for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                # Compare with known faces
                matches = face_recognition.compare_faces(
                    self.known_face_encodings,
                    face_encoding,
                    tolerance=self.config.get('max_face_distance', 0.6)
                )
                
                name = "Unknown"
                confidence = 0.0
                
                # Find best match
                if self.known_face_encodings:
                    face_distances = face_recognition.face_distance(
                        self.known_face_encodings,
                        face_encoding
                    )
                    
                    best_match_index = np.argmin(face_distances)
                    
                    if matches[best_match_index]:
                        confidence = 1.0 - face_distances[best_match_index]
                        
                        # Only accept if confidence is above threshold
                        if confidence >= min_confidence:
                            name = self.known_face_names[best_match_index]
                
                # Scale coordinates back to original frame size if resized
                if width > resize_width:
                    scale_back = width / resize_width
                    top = int(top * scale_back)
                    right = int(right * scale_back)
                    bottom = int(bottom * scale_back)
                    left = int(left * scale_back)
                
                results.append({
                    'name': name,
                    'confidence': confidence,
                    'location': (top, right, bottom, left),
                    'bbox': {
                        'x': left, 
                        'y': top, 
                        'width': right - left, 
                        'height': bottom - top
                    }
                })
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error recognizing faces in frame: {e}")
            return []
    
    def process_motion_event(self, camera_id: str, image_path: str) -> Optional[List[Dict]]:
        """
        Process a motion detection event for face recognition
        
        Args:
            camera_id: Camera identifier
            image_path: Path to motion detection image
            
        Returns:
            List of face recognition results or None if disabled/error
        """
        if not FACE_RECOGNITION_AVAILABLE or not self.config.get('enable_recognition', True):
            return None
        
        try:
            # Recognize faces in the motion detection image
            faces = self.recognize_faces_in_image(image_path)
            
            if faces:
                recognized_names = [
                    f"{face['name']} ({face['confidence']:.2f})"
                    for face in faces 
                    if face['name'] != 'Unknown' and face['confidence'] >= self.config.get('min_confidence', 0.6)
                ]
                
                if recognized_names:
                    self.logger.info(f"Camera {camera_id}: Face recognition - {', '.join(recognized_names)}")
                    
                    # You can add additional actions here:
                    # - Send notifications
                    # - Save to database
                    # - Trigger webhooks
                    # - Update statistics
                    
                else:
                    self.logger.debug(f"Camera {camera_id}: Unknown faces detected")
            
            return faces
            
        except Exception as e:
            self.logger.error(f"Error processing motion event for camera {camera_id}: {e}")
            return None
    
    def get_status(self) -> Dict:
        """Get current face recognition status"""
        faces_data = self.scan_faces_folder()
        
        return {
            'available': FACE_RECOGNITION_AVAILABLE,
            'enabled': self.config.get('enable_recognition', True),
            'faces_folder': self.faces_folder,
            'known_people': list(faces_data.keys()),
            'total_encodings': len(self.known_face_encodings),
            'detection_method': self.config.get('detection_method', 'hog'),
            'recognition_threshold': self.config.get('max_face_distance', 0.6),
            'min_confidence': self.config.get('min_confidence', 0.6),
            'config_path': self.config_path
        }
    
    def is_available(self) -> bool:
        """Check if face recognition is available and enabled"""
        return FACE_RECOGNITION_AVAILABLE and self.config.get('enable_recognition', True)


# Global instance for MotionEye integration
_face_manager_instance = None

def get_face_manager() -> Optional[FaceRecognitionManager]:
    """Get or create the global face recognition manager instance"""
    global _face_manager_instance
    
    if _face_manager_instance is None:
        try:
            _face_manager_instance = FaceRecognitionManager()
        except Exception as e:
            logging.error(f"Failed to initialize face recognition manager: {e}")
            return None
    
    return _face_manager_instance


# Test functionality
if __name__ == "__main__":
    # Test the face recognition manager
    logging.basicConfig(level=logging.INFO)
    
    print("Testing Face Recognition Manager...")
    
    manager = FaceRecognitionManager()
    
    # Test status
    status = manager.get_status()
    print(f"Status: {status}")
    
    # Test training if faces exist
    faces_data = manager.scan_faces_folder()
    if faces_data:
        print(f"Found {len(faces_data)} people with face data")
        success = manager.train_face_recognition()
        print(f"Training {'successful' if success else 'failed'}")
    else:
        print("No face data found. Add some faces to /var/lib/motioneye/faces/person_name/")
    
    print("Face Recognition Manager test completed!")