#!/usr/bin/env python3
"""
Simple test runner for multi-version integration tests
Runs without pytest dependency
"""

import sys
import os
import traceback
from unittest.mock import Mock, patch, MagicMock

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from strands_spot.version_detector import SDKVersionDetector


class TestRunner:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []

    def run_test(self, test_func, test_name):
        """Run a single test function"""
        try:
            print(f"Running {test_name}...", end=" ")
            test_func()
            print("PASS")
            self.passed += 1
        except Exception as e:
            print("FAIL")
            self.failed += 1
            self.errors.append(f"{test_name}: {str(e)}")
            traceback.print_exc()

    def summary(self):
        """Print test summary"""
        total = self.passed + self.failed
        print(f"\n=== Test Summary ===")
        print(f"Total: {total}, Passed: {self.passed}, Failed: {self.failed}")
        
        if self.errors:
            print("\nFailures:")
            for error in self.errors:
                print(f"  - {error}")
        
        return self.failed == 0


def test_version_detection_with_sdk():
    """Test version detection when SDK is available"""
    # Reset cache
    SDKVersionDetector._cached_version = None
    
    with patch('bosdyn.__version__', '4.5.2'):
        with patch('strands_spot.version_detector.bosdyn'):
            version = SDKVersionDetector.detect_version()
            assert version == '4.5.2', f"Expected '4.5.2', got '{version}'"


def test_version_detection_missing_sdk():
    """Test version detection when SDK is missing"""
    # Reset cache
    SDKVersionDetector._cached_version = None
    
    with patch('strands_spot.version_detector.bosdyn', side_effect=ImportError):
        try:
            SDKVersionDetector.detect_version()
            assert False, "Expected ImportError"
        except ImportError as e:
            assert "Spot SDK not found" in str(e)


def test_version_caching():
    """Test that version is cached correctly"""
    # Reset cache
    SDKVersionDetector._cached_version = None
    
    with patch('bosdyn.__version__', '5.1.0'):
        with patch('strands_spot.version_detector.bosdyn'):
            # First call
            version1 = SDKVersionDetector.detect_version()
            # Second call should use cache
            version2 = SDKVersionDetector.detect_version()
            assert version1 == version2 == '5.1.0'


def test_valid_4x_versions():
    """Test validation of supported 4.x versions"""
    valid_versions = ['4.0.0', '4.5.2', '4.9.9']
    for version in valid_versions:
        result = SDKVersionDetector.validate_version(version)
        assert result is True, f"Version {version} should be valid"


def test_valid_5x_versions():
    """Test validation of supported 5.x versions"""
    valid_versions = ['5.0.0', '5.1.1', '5.9.9']
    for version in valid_versions:
        result = SDKVersionDetector.validate_version(version)
        assert result is True, f"Version {version} should be valid"


def test_unsupported_old_versions():
    """Test rejection of unsupported old versions"""
    old_versions = ['3.9.9', '2.1.0', '1.0.0']
    for version in old_versions:
        try:
            SDKVersionDetector.validate_version(version)
            assert False, f"Version {version} should be rejected"
        except ValueError as e:
            assert "Minimum supported: 4.0.0" in str(e)


def test_unsupported_future_versions():
    """Test rejection of unsupported future versions"""
    future_versions = ['6.0.0', '7.1.0', '10.0.0']
    for version in future_versions:
        try:
            SDKVersionDetector.validate_version(version)
            assert False, f"Version {version} should be rejected"
        except ValueError as e:
            assert "Supported: 4.0.0+ and 5.x series" in str(e)


def test_invalid_version_format():
    """Test rejection of invalid version formats"""
    invalid_formats = ['4.5', '4', 'v4.5.2', '4.5.2-beta', 'invalid']
    for version in invalid_formats:
        try:
            SDKVersionDetector.validate_version(version)
            assert False, f"Version {version} should be rejected for invalid format"
        except ValueError as e:
            assert "Invalid version format" in str(e)


def test_unknown_version():
    """Test rejection of unknown version"""
    try:
        SDKVersionDetector.validate_version('unknown')
        assert False, "Unknown version should be rejected"
    except ValueError as e:
        assert "Cannot validate unknown SDK version" in str(e)


def test_detect_current_sdk_version():
    """Test detection of currently installed SDK version"""
    # Reset cache
    SDKVersionDetector._cached_version = None
    
    try:
        version = SDKVersionDetector.detect_version()
        print(f"\nDetected SDK version: {version}")
        
        # If we get here, SDK is installed
        assert isinstance(version, str)
        if version != 'unknown':
            # Validate the detected version
            assert SDKVersionDetector.validate_version(version) is True
            print(f"SDK version {version} is valid and supported")
        else:
            print("SDK version is unknown")
            
    except ImportError:
        # SDK not installed - this is expected in test environment
        print("\nSDK not installed in test environment - this is expected")


def main():
    """Run all tests"""
    runner = TestRunner()
    
    print("=== Multi-Version Integration Tests ===\n")
    
    # Version detection tests
    runner.run_test(test_version_detection_with_sdk, "test_version_detection_with_sdk")
    runner.run_test(test_version_detection_missing_sdk, "test_version_detection_missing_sdk")
    runner.run_test(test_version_caching, "test_version_caching")
    
    # Version validation tests
    runner.run_test(test_valid_4x_versions, "test_valid_4x_versions")
    runner.run_test(test_valid_5x_versions, "test_valid_5x_versions")
    runner.run_test(test_unsupported_old_versions, "test_unsupported_old_versions")
    runner.run_test(test_unsupported_future_versions, "test_unsupported_future_versions")
    runner.run_test(test_invalid_version_format, "test_invalid_version_format")
    runner.run_test(test_unknown_version, "test_unknown_version")
    
    # Current environment test
    runner.run_test(test_detect_current_sdk_version, "test_detect_current_sdk_version")
    
    success = runner.summary()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())