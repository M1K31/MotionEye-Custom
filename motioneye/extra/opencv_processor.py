#!/usr/bin/env python3

# This script is called by motion's on_picture_save event.
# It uses OpenCV and face_recognition to detect unfamiliar faces.

import cv2
import face_recognition
import sys
import os
import pickle

# Global cache for known face encodings
_known_faces_cache = None


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


def analyze_image(image_path, known_faces):
    """Detects and identifies faces in an image."""
    if not os.path.exists(image_path):
        print(f"ERROR: Image path does not exist: {image_path}", file=sys.stderr)
        return

    try:
        unknown_image = face_recognition.load_image_file(image_path)
        unknown_face_locations = face_recognition.face_locations(unknown_image)
        unknown_face_encodings = face_recognition.face_encodings(unknown_image, unknown_face_locations)
    except Exception as e:
        print(f"ERROR: Failed to process image {image_path}: {e}", file=sys.stderr)
        return

    if not unknown_face_encodings:
        print("INFO: No faces found in the image.")
        return

    known_encodings = known_faces.get("encodings", [])
    known_names = known_faces.get("names", [])

    unfamiliar_faces_count = 0
    familiar_faces_found = set()

    for face_encoding in unknown_face_encodings:
        # See if the face is a match for the known face(s)
        matches = face_recognition.compare_faces(known_encodings, face_encoding)
        name = "Unfamiliar Person"

        # If a match was found in known_face_encodings, just use the first one.
        if True in matches:
            first_match_index = matches.index(True)
            name = known_names[first_match_index]
            familiar_faces_found.add(name)
        else:
            unfamiliar_faces_count += 1

    if unfamiliar_faces_count > 0:
        print(f"EVENT: Detected {unfamiliar_faces_count} UNFAMILIAR person(s) in {image_path}")

    if familiar_faces_found:
        print(f"INFO: Detected familiar person(s): {', '.join(familiar_faces_found)}")


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python3 opencv_processor.py <image_path> <config_path>", file=sys.stderr)
        sys.exit(1)

    image_path_arg = sys.argv[1]
    config_path_arg = sys.argv[2]

    # Load known faces once
    known_faces_data = load_known_faces(config_path_arg)

    analyze_image(image_path_arg, known_faces_data)
