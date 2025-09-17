#!/usr/bin/env python3

# This script is called by motion's on_picture_save event.
# It uses OpenCV and face_recognition to detect unfamiliar faces.

import cv2
import face_recognition
import sys
import os
import pickle
import urllib.request
import numpy as np

# --- Model Configuration ---
YOLO_CONFIG_URL = 'https://raw.githubusercontent.com/pjreddie/darknet/master/cfg/yolov3-tiny.cfg'
YOLO_WEIGHTS_URL = 'https://pjreddie.com/media/files/yolov3-tiny.weights'
COCO_NAMES_URL = 'https://raw.githubusercontent.com/pjreddie/darknet/master/data/coco.names'

MODEL_DIR = None  # Will be set to os.path.join(conf_path, 'dnn_models')
YOLO_CONFIG_PATH = None
YOLO_WEIGHTS_PATH = None
COCO_NAMES_PATH = None

# List of animal classes from COCO dataset
ANIMAL_CLASSES = [
    'bird', 'cat', 'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe'
]

# Global cache for models
_known_faces_cache = None
_animal_net_cache = None
_coco_classes_cache = None


def _setup_paths(conf_path):
    """Sets up the global path variables."""
    global MODEL_DIR, YOLO_CONFIG_PATH, YOLO_WEIGHTS_PATH, COCO_NAMES_PATH
    if MODEL_DIR is None:
        MODEL_DIR = os.path.join(conf_path, 'dnn_models')
        YOLO_CONFIG_PATH = os.path.join(MODEL_DIR, 'yolov3-tiny.cfg')
        YOLO_WEIGHTS_PATH = os.path.join(MODEL_DIR, 'yolov3-tiny.weights')
        COCO_NAMES_PATH = os.path.join(MODEL_DIR, 'coco.names')


def _download_file(url, path):
    """Downloads a file from a URL to a given path."""
    print(f"INFO: Downloading {url} to {path}...")
    try:
        urllib.request.urlretrieve(url, path)
        print("INFO: Download complete.")
    except Exception as e:
        print(f"ERROR: Failed to download {url}: {e}", file=sys.stderr)
        # Clean up partial file if download failed
        if os.path.exists(path):
            os.remove(path)
        raise


def prepare_animal_detector(conf_path):
    """
    Downloads the YOLO model if not present, loads it, and returns the
    network and class names.
    """
    global _animal_net_cache, _coco_classes_cache
    _setup_paths(conf_path)

    if _animal_net_cache is not None and _coco_classes_cache is not None:
        return _animal_net_cache, _coco_classes_cache

    if not os.path.exists(MODEL_DIR):
        print(f"INFO: Model directory '{MODEL_DIR}' not found. Creating it.")
        os.makedirs(MODEL_DIR)

    # Download model files if they don't exist
    if not os.path.exists(YOLO_CONFIG_PATH):
        _download_file(YOLO_CONFIG_URL, YOLO_CONFIG_PATH)
    if not os.path.exists(YOLO_WEIGHTS_PATH):
        _download_file(YOLO_WEIGHTS_URL, YOLO_WEIGHTS_PATH)
    if not os.path.exists(COCO_NAMES_PATH):
        _download_file(COCO_NAMES_URL, COCO_NAMES_PATH)

    # Load YOLO model
    try:
        print("INFO: Loading YOLO model from disk...")
        net = cv2.dnn.readNet(YOLO_WEIGHTS_PATH, YOLO_CONFIG_PATH)
        with open(COCO_NAMES_PATH, 'r') as f:
            classes = [line.strip() for line in f.readlines()]

        _animal_net_cache = net
        _coco_classes_cache = classes
        print("INFO: YOLO model loaded successfully.")
        return net, classes
    except Exception as e:
        print(f"ERROR: Failed to load YOLO model: {e}", file=sys.stderr)
        return None, None


def load_known_faces(conf_path):
    """
    Scans the FACES_DIR for images, creates face encodings,
    and caches them to a pickle file.
    """
    global _known_faces_cache
    if _known_faces_cache is not None:
        return _known_faces_cache

    faces_dir = os.path.join(conf_path, 'faces')
    encodings_cache_path = os.path.join(faces_dir, 'known_faces.pkl')

    # Load from cache if it exists
    if os.path.exists(encodings_cache_path):
        try:
            with open(encodings_cache_path, 'rb') as f:
                _known_faces_cache = pickle.load(f)
                print("INFO: Loaded known face encodings from cache.")
                return _known_faces_cache
        except Exception as e:
            print(f"WARNING: Could not load encodings cache: {e}. Re-generating.")

    known_encodings = []
    known_names = []

    if not os.path.exists(faces_dir):
        print(f"INFO: Faces directory '{faces_dir}' not found. Creating it.")
        os.makedirs(faces_dir)

    print(f"INFO: Scanning '{faces_dir}' for known faces...")
    for filename in os.listdir(faces_dir):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            name = os.path.splitext(filename)[0]
            image_path = os.path.join(faces_dir, filename)
            try:
                image = face_recognition.load_image_file(image_path)
                # Assuming one face per image for known faces
                encodings = face_recognition.face_encodings(image)
                if encodings:
                    known_encodings.append(encodings[0])
                    known_names.append(name)
                    print(f"INFO: Encoded face for '{name}' from {filename}")
            except Exception as e:
                print(f"ERROR: Failed to process known face {image_path}: {e}", file=sys.stderr)

    _known_faces_cache = {"encodings": known_encodings, "names": known_names}

    # Save to cache for next time
    try:
        with open(encodings_cache_path, 'wb') as f:
            pickle.dump(_known_faces_cache, f)
    except Exception as e:
        print(f"WARNING: Could not save encodings cache: {e}")

    return _known_faces_cache


def detect_animals(net, image, classes, confidence_threshold=0.5, nms_threshold=0.4):
    """Detects animals in an image using the YOLO model."""
    h, w, _ = image.shape
    blob = cv2.dnn.blobFromImage(image, 1/255.0, (416, 416), swapRB=True, crop=False)
    net.setInput(blob)

    output_layer_names = net.getUnconnectedOutLayersNames()
    layer_outputs = net.forward(output_layer_names)

    boxes = []
    confidences = []
    class_ids = []

    for output in layer_outputs:
        for detection in output:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            if confidence > confidence_threshold:
                label = classes[class_id]
                if label in ANIMAL_CLASSES:
                    box = detection[0:4] * np.array([w, h, w, h])
                    (center_x, center_y, width, height) = box.astype("int")
                    x = int(center_x - (width / 2))
                    y = int(center_y - (height / 2))
                    boxes.append([x, y, int(width), int(height)])
                    confidences.append(float(confidence))
                    class_ids.append(class_id)

    # Apply non-maxima suppression
    indices = cv2.dnn.NMSBoxes(boxes, confidences, confidence_threshold, nms_threshold)

    detected_animals = []
    if len(indices) > 0:
        for i in indices.flatten():
            box = boxes[i]
            label = classes[class_ids[i]]
            detected_animals.append({'type': 'animal', 'label': label, 'box': box})

    return detected_animals


def analyze_image(image_path, conf_path, animal_detection_enabled=False, person_detection_enabled=False):
    """
    Analyzes an image for animals and faces, returning a structured list of detected subjects.
    """
    if not os.path.exists(image_path):
        print(f"ERROR: Image path does not exist: {image_path}", file=sys.stderr)
        return []

    try:
        image = cv2.imread(image_path)
        if image is None:
            print(f"ERROR: Could not read image from {image_path}", file=sys.stderr)
            return []
    except Exception as e:
        print(f"ERROR: Failed to load image {image_path} with OpenCV: {e}", file=sys.stderr)
        return []

    all_subjects = []

    # --- Animal Detection ---
    if animal_detection_enabled:
        net, classes = prepare_animal_detector(conf_path)
        if net and classes:
            animals = detect_animals(net, image, classes)
            all_subjects.extend(animals)
            if animals:
                animal_labels = [a['label'] for a in animals]
                print(f"EVENT: Animal(s) detected: {', '.join(animal_labels)}")

    # --- Person Detection / Face Recognition ---
    if person_detection_enabled:
        known_faces = load_known_faces(conf_path)
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB) # face_recognition uses RGB

        try:
            face_locations = face_recognition.face_locations(rgb_image)
            face_encodings = face_recognition.face_encodings(rgb_image, face_locations)
        except Exception as e:
            print(f"ERROR: Failed during face detection: {e}", file=sys.stderr)
            face_encodings = []

        if not face_encodings:
            print("INFO: No faces found in the image.")
        else:
            known_encodings = known_faces.get("encodings", [])
            known_names = known_faces.get("names", [])

            for i, face_encoding in enumerate(face_encodings):
                matches = face_recognition.compare_faces(known_encodings, face_encoding)
                name = "unknown_person"

                if True in matches:
                    first_match_index = matches.index(True)
                    name = known_names[first_match_index]
                    print(f"INFO: Detected familiar person: {name}")
                else:
                    print(f"EVENT: Detected UNFAMILIAR person in {image_path}")
                    # Store the timestamp for the unfamiliar face event
                    try:
                        timestamp_path = os.path.join(conf_path, 'last_unfamiliar_face.txt')
                        with open(timestamp_path, 'w') as f:
                            from datetime import datetime
                            f.write(datetime.now().isoformat())
                    except Exception as e:
                        print(f"ERROR: Could not write unfamiliar face timestamp: {e}", file=sys.stderr)

                # Get bounding box from face_locations
                top, right, bottom, left = face_locations[i]
                box = [left, top, right - left, bottom - top]
                all_subjects.append({'type': 'person', 'label': name, 'box': box})

    return all_subjects


def draw_annotations(image_path, subjects):
    """Draws bounding boxes and labels on an image."""
    try:
        image = cv2.imread(image_path)
        if image is None:
            print(f"ERROR: Could not read image for annotation: {image_path}", file=sys.stderr)
            return

        for subject in subjects:
            box = subject['box']
            label = subject['label']
            x, y, w, h = box

            # Draw the bounding box
            cv2.rectangle(image, (x, y), (x + w, y + h), (0, 0, 255), 2)

            # Draw the label
            cv2.putText(image, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)

        cv2.imwrite(image_path, image)
        print(f"INFO: Annotated image saved to {image_path}")

    except Exception as e:
        print(f"ERROR: Failed to annotate image {image_path}: {e}", file=sys.stderr)


import argparse
import subprocess

def trigger_notifications(camera_id, conf_path):
    """Reads the camera config and triggers the notification commands."""
    camera_conf_path = os.path.join(conf_path, f'camera-{camera_id}.conf')
    if not os.path.exists(camera_conf_path):
        print(f"ERROR: Camera config not found at {camera_conf_path}", file=sys.stderr)
        return

    on_event_start_cmd = ''
    try:
        with open(camera_conf_path, 'r') as f:
            for line in f:
                if line.strip().startswith('on_event_start'):
                    on_event_start_cmd = line.strip().split(' ', 1)[1]
                    break
    except Exception as e:
        print(f"ERROR: Failed to read camera config: {e}", file=sys.stderr)
        return

    if not on_event_start_cmd:
        print("INFO: No on_event_start command found for this camera.")
        return

    # Extract only notification-related commands
    commands = on_event_start_cmd.split(';')
    for cmd in commands:
        cmd = cmd.strip()
        if 'sendmail' in cmd or 'sendtelegram' in cmd:
            print(f"INFO: Triggering notification command: {cmd}")
            try:
                # We need to replace motion conversion specifiers like %t
                # For animal notifications, we don't have a motion event id, so we can use a placeholder.
                cmd_to_run = cmd.replace('%t', '0')
                subprocess.run(cmd_to_run, shell=True, check=True)
            except Exception as e:
                print(f"ERROR: Failed to run notification command '{cmd}': {e}", file=sys.stderr)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="motionEye OpenCV Processor")
    parser.add_argument("image_path", help="Path to the image to analyze")
    parser.add_argument("config_path", help="Path to the motionEye configuration directory")
    parser.add_argument("--camera-id", required=True, type=int, help="The ID of the camera")
    parser.add_argument("--animal-detection", type=lambda x: x.lower() == 'true', default=False, help="Enable animal detection")
    parser.add_argument("--person-detection", type=lambda x: x.lower() == 'true', default=False, help="Enable person detection")
    parser.add_argument("--notify-on-animal", type=lambda x: x.lower() == 'true', default=False, help="Enable notifications for animal detection")
    parser.add_argument("--known-path", default="", help="Path to save images of known persons")
    parser.add_argument("--unknown-path", default="", help="Path to save images of unknown persons")
    parser.add_argument("--animal-path", default="", help="Path to save images of animals")
    args = parser.parse_args()

    subjects = analyze_image(
        args.image_path,
        args.config_path,
        animal_detection_enabled=args.animal_detection,
        person_detection_enabled=args.person_detection
    )

    if not subjects:
        print("No subjects detected. No action taken.")
        sys.exit(0)

    # --- Notification Logic ---
    animal_detected = any(s['type'] == 'animal' for s in subjects)
    if animal_detected and args.notify_on_animal:
        print("INFO: Animal detected and notifications are enabled. Triggering notifications.")
        trigger_notifications(args.camera_id, args.config_path)

    # --- File Sorting and Annotation Logic ---
    subject_types = {s['type'] for s in subjects}
    is_mixed = len(subject_types) > 1

    if not is_mixed and 'person' in subject_types:
        person_labels = {s['label'] for s in subjects if s['type'] == 'person'}
        if len({'known' if label != 'unknown_person' else 'unknown' for label in person_labels}) > 1:
            is_mixed = True

    if is_mixed:
        print("INFO: Mixed content detected. Annotating image.")
        draw_annotations(args.image_path, subjects)
        sys.exit(0)

    final_path = None
    category = list(subject_types)[0]

    if category == 'animal' and args.animal_path:
        final_path = args.animal_path
    elif category == 'person':
        person_label = list({s['label'] for s in subjects if s['type'] == 'person'})[0]
        if person_label == 'unknown_person' and args.unknown_path:
            final_path = args.unknown_path
        elif person_label != 'unknown_person' and args.known_path:
            final_path = args.known_path

    if final_path:
        try:
            if not os.path.exists(final_path):
                os.makedirs(final_path)

            base_filename = os.path.basename(args.image_path)
            new_path = os.path.join(final_path, base_filename)

            counter = 1
            while os.path.exists(new_path):
                name, ext = os.path.splitext(base_filename)
                new_path = os.path.join(final_path, f"{name}_{counter}{ext}")
                counter += 1

            os.rename(args.image_path, new_path)
            print(f"INFO: Moved '{args.image_path}' to '{new_path}'")
        except Exception as e:
            print(f"ERROR: Failed to move file: {e}", file=sys.stderr)
            draw_annotations(args.image_path, subjects)
    else:
        print("INFO: No specific path configured. Annotating original file.")
        draw_annotations(args.image_path, subjects)
