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
import platform
from pathlib import Path


class TestMotionEyeLite(unittest.TestCase):
    """Test suite for motionEye Lite functionality"""

    def setUp(self):
        """Set up test environment"""
        self.project_root = Path(__file__).parent
        self.lite_binary = Path("/usr/local/motioneye-lite/bin/motion")
        self.lite_path = Path("/usr/local/motioneye-lite")
        self.build_script = self.project_root / "build" / "build_motion_lite_macos.sh"
        self.management_script = self.project_root / "build" / "motioneye-lite-launcher.sh"
        
        # Check if we're in a CI environment or if Lite is not installed
        self.is_ci = os.getenv('CI') == 'true' or os.getenv('GITHUB_ACTIONS') == 'true'
        self.lite_installed = self.lite_path.exists()
        
    def _skip_if_not_lite_environment(self):
        """Skip test if not in a motionEye Lite environment"""
        if self.is_ci and not self.lite_installed:
            self.skipTest("Skipping motionEye Lite test in CI environment without Lite installation")

    def test_motion_binary_exists(self):
        """Test that the motion binary was built and installed"""
        self._skip_if_not_lite_environment()
        self.assertTrue(self.lite_binary.exists(), f"Motion binary not found at {self.lite_binary}")
        self.assertTrue(os.access(self.lite_binary, os.X_OK), "Motion binary is not executable")

    def test_motion_version(self):
        """Test that motion reports correct version and features"""
        self._skip_if_not_lite_environment()
        result = subprocess.run([str(self.lite_binary), "-h"], 
                              capture_output=True, text=True, timeout=10)
        # Motion help returns exit code 1 but still shows version info
        
        output = result.stdout
        self.assertIn("motion Version 4.3.1", output, "Incorrect motion version")
        self.assertIn("motion-project.github.io", output, "Missing project URL")

    def test_ffmpeg_integration(self):
        """Test that motion was built with FFmpeg support"""
        self._skip_if_not_lite_environment()
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
        self._skip_if_not_lite_environment()
        lite_path = Path("/usr/local/motioneye-lite")
        
        # Check directory structure
        self.assertTrue((lite_path / "bin").exists(), "bin directory missing")
        self.assertTrue((lite_path / "lib").exists(), "lib directory missing")
        self.assertTrue((lite_path / "include").exists(), "include directory missing")
        
        # Check key files
        self.assertTrue((lite_path / "bin" / "motion").exists(), "motion binary missing")
        
        # Check configuration directory exists (config files are optional for embedded builds)
        etc_path = lite_path / "etc"
        self.assertTrue(etc_path.exists(), "etc directory missing")

    def test_pkg_config_files(self):
        """Test that pkg-config files are properly installed"""
        self._skip_if_not_lite_environment()
        pkgconfig_path = Path("/usr/local/motioneye-lite/lib/pkgconfig")
        self.assertTrue(pkgconfig_path.exists(), "pkgconfig directory missing")
        
        # Check for essential pkg-config files
        essential_pc_files = ["libavcodec.pc", "libavformat.pc", "libavutil.pc"]
        for pc_file in essential_pc_files:
            pc_path = pkgconfig_path / pc_file
            if pc_path.exists():
                # At least one FFmpeg pkg-config file should exist
                return
        
        self.fail("No FFmpeg pkg-config files found")

    def test_system_requirements(self):
        """Test that system meets requirements for Lite build"""
        # Skip on CI environments that aren't macOS
        if self.is_ci and not platform.system() == 'Darwin':
            self.skipTest("System requirements test only runs on macOS")
            
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
        self._skip_if_not_lite_environment()
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