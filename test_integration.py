#!/usr/bin/env python3
"""
Test Face Recognition Integration
"""
import sys
import os

# Add the motioneye directory to path
sys.path.insert(0, '/home/mikel/Documents/VSProjects/MotionEye-Custom')

from motioneye.face_recognition_manager import FaceRecognitionManager

def test_integration():
    print("Testing Face Recognition Integration...")
    
    # Initialize manager
    manager = FaceRecognitionManager()
    
    # Test basic functionality
    success = manager.test_functionality()
    
    if success:
        print("✓ Integration test passed!")
        return True
    else:
        print("✗ Integration test failed!")
        return False

if __name__ == "__main__":
    test_integration()