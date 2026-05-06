import json
import os
import tempfile
import unittest

import numpy as np

from motioneye import face_recognition_manager


class FaceEncodingPersistenceTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def test_save_and_load_uses_json(self):
        path = os.path.join(self.tmpdir, 'faces.json')
        encodings = {
            'alice': [np.zeros(128).tolist()],
            'bob': [np.ones(128).tolist()],
        }
        face_recognition_manager.save_encodings(path, encodings)

        with open(path, 'r') as f:
            data = json.load(f)
        self.assertIn('alice', data)

        loaded = face_recognition_manager.load_encodings(path)
        self.assertIn('alice', loaded)
        self.assertEqual(len(loaded['alice']), 1)

    def test_load_missing_file_returns_empty(self):
        loaded = face_recognition_manager.load_encodings('/nonexistent/path.json')
        self.assertEqual(loaded, {})

    def test_legacy_binary_file_is_rejected(self):
        path = os.path.join(self.tmpdir, 'legacy.bin')
        with open(path, 'wb') as f:
            f.write(b'\x80\x04stuff')
        loaded = face_recognition_manager.load_encodings(path)
        self.assertEqual(loaded, {}, 'legacy binary files must be ignored, not loaded')


if __name__ == '__main__':
    unittest.main()
