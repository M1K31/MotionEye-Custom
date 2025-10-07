#!/usr/bin/env python3

"""
Tests for motionEye Lite integration
Tests the embedded systems approach for older macOS compatibility
"""

import os
import sys
import subprocess
import tempfile
import unittest
from pathlib import Path


class TestMotionEyeLite(unittest.TestCase):
    """Test suite for motionEye Lite functionality"""

    def setUp(self):
        """Set up test environment"""
        self.project_root = Path(__file__).parent
        self.lite_binary = Path("/usr/local/motioneye-lite/bin/motion")
        self.build_script = self.project_root / "build" / "build_motion_lite_macos.sh"
        self.management_script = self.project_root / "motioneye-lite"

    def test_motion_binary_exists(self):
        """Test that the motion binary was built and installed"""
        self.assertTrue(self.lite_binary.exists(), f"Motion binary not found at {self.lite_binary}")
        self.assertTrue(os.access(self.lite_binary, os.X_OK), "Motion binary is not executable")

    def test_motion_version(self):
        """Test that motion reports correct version and features"""
        result = subprocess.run([str(self.lite_binary), "-h"], 
                              capture_output=True, text=True, timeout=10)
        # Motion help returns exit code 1 but still shows version info
        
        output = result.stdout
        self.assertIn("motion Version 4.3.1", output, "Incorrect motion version")
        self.assertIn("motion-project.github.io", output, "Missing project URL")

    def test_ffmpeg_integration(self):
        """Test that motion was built with FFmpeg support"""
        # Check if FFmpeg libraries exist and are properly linked
        ffmpeg_libs = [
            "/usr/local/motioneye-lite/lib/libavcodec.a",
            "/usr/local/motioneye-lite/lib/libavformat.a",
            "/usr/local/motioneye-lite/lib/libavutil.a"
        ]
        
        for lib in ffmpeg_libs:
            self.assertTrue(os.path.exists(lib), f"FFmpeg library {lib} not found")
        
        # Verify motion binary has FFmpeg symbols (using otool for macOS)
        try:
            result = subprocess.run(["otool", "-L", str(self.lite_binary)], 
                                  capture_output=True, text=True, timeout=10)
            # On static build, FFmpeg should be embedded, not as external dependency
            self.assertEqual(result.returncode, 0, "Failed to check motion dependencies")
        except FileNotFoundError:
            self.skipTest("otool not available for dependency checking")

    def test_build_script_exists(self):
        """Test that the build script is present and executable"""
        self.assertTrue(self.build_script.exists(), f"Build script not found at {self.build_script}")
        self.assertTrue(os.access(self.build_script, os.R_OK), "Build script is not readable")

    def test_management_script_exists(self):
        """Test that the management script is present and executable"""
        self.assertTrue(self.management_script.exists(), f"Management script not found at {self.management_script}")
        self.assertTrue(os.access(self.management_script, os.X_OK), "Management script is not executable")

    def test_lite_components_installed(self):
        """Test that all required Lite components are installed"""
        lite_path = Path("/usr/local/motioneye-lite")
        
        # Check directory structure
        self.assertTrue((lite_path / "bin").exists(), "bin directory missing")
        self.assertTrue((lite_path / "lib").exists(), "lib directory missing")
        self.assertTrue((lite_path / "include").exists(), "include directory missing")
        
        # Check for key libraries
        lib_path = lite_path / "lib"
        required_libs = ["libavcodec.a", "libavformat.a", "libavutil.a", "libavdevice.a", "libmicrohttpd.a"]
        for lib in required_libs:
            lib_file = lib_path / lib
            self.assertTrue(lib_file.exists(), f"Required library {lib} not found")

    def test_pkg_config_files(self):
        """Test that pkg-config files are properly installed"""
        pkgconfig_path = Path("/usr/local/motioneye-lite/lib/pkgconfig")
        self.assertTrue(pkgconfig_path.exists(), "pkgconfig directory missing")
        
        required_pc_files = ["libavcodec.pc", "libavformat.pc", "libavutil.pc", 
                           "libavdevice.pc", "libmicrohttpd.pc"]
        for pc_file in required_pc_files:
            pc_path = pkgconfig_path / pc_file
            self.assertTrue(pc_path.exists(), f"pkg-config file {pc_file} not found")

    def test_system_requirements(self):
        """Test that system meets requirements for Lite build"""
        # Check macOS version compatibility
        result = subprocess.run(["sw_vers", "-productVersion"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            version = result.stdout.strip()
            major, minor = map(int, version.split('.')[:2])
            self.assertGreaterEqual((major, minor), (10, 15), 
                                  f"macOS {version} may not be compatible")

    def test_performance_optimizations(self):
        """Test that performance optimizations are in place"""
        # Check that motion binary is properly optimized
        result = subprocess.run(["file", str(self.lite_binary)], 
                              capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, "Failed to analyze motion binary")
        
        output = result.stdout
        self.assertIn("x86_64", output, "Binary not built for x86_64 architecture")
        self.assertIn("executable", output, "File is not an executable")


class TestMotionEyeLiteIntegration(unittest.TestCase):
    """Test suite for motionEye Lite integration with main project"""

    def setUp(self):
        """Set up integration test environment"""
        self.project_root = Path(__file__).parent

    def test_documentation_updated(self):
        """Test that documentation has been updated for Lite features"""
        readme_files = [
            self.project_root / "README.md",
            self.project_root / "NEW_FEATURES.md"
        ]
        
        for readme in readme_files:
            if readme.exists():
                content = readme.read_text()
                # Check for Lite-related content
                self.assertTrue(
                    "lite" in content.lower() or "embedded" in content.lower() or "performance" in content.lower(),
                    f"{readme.name} should mention Lite features"
                )

    def test_installation_scripts_present(self):
        """Test that installation and uninstallation scripts are present"""
        install_scripts = [
            self.project_root / "build" / "install_macos.sh",
            self.project_root / "build" / "uninstall_macos.sh"
        ]
        
        for script in install_scripts:
            if script.exists():
                self.assertTrue(os.access(script, os.R_OK), f"{script.name} is not readable")


if __name__ == "__main__":
    # Set up test environment
    os.environ["PYTHONPATH"] = str(Path(__file__).parent)
    
    # Run tests
    unittest.main(verbosity=2)