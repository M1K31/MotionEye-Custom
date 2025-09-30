import pytest
import sys
import os
import json
import tempfile
from unittest.mock import patch

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from motioneye.face_recognition_manager import FaceRecognitionManager

@pytest.fixture
def manager_with_temp_config():
    """A pytest fixture to create a FaceRecognitionManager with a temporary config."""
    with tempfile.TemporaryDirectory() as temp_dir:
        faces_folder = os.path.join(temp_dir, "faces")
        config_file_path = os.path.join(temp_dir, "faces_config.json")

        # Create the config file
        config_data = {"faces_folder": faces_folder}
        with open(config_file_path, 'w') as f:
            json.dump(config_data, f)

        manager_instance = FaceRecognitionManager(config_path=config_file_path)
        yield manager_instance

def test_integration(manager_with_temp_config):
    """
    Tests that the FaceRecognitionManager can be initialized and its status checked.
    """
    print("Testing Face Recognition Integration...")
    
    # Get the manager from the fixture
    manager = manager_with_temp_config

    # Test that the manager's status can be retrieved successfully
    status = manager.get_status()
    
    assert isinstance(status, dict), "get_status() should return a dictionary."
    assert "available" in status, "'available' key is missing from status."
    assert "enabled" in status, "'enabled' key is missing from status."
    assert status['faces_folder'].startswith(tempfile.gettempdir()), "faces_folder is not using the temporary directory."
    
    print("✓ Integration test passed!")

if __name__ == "__main__":
    pytest.main()