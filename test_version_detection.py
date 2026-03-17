#!/usr/bin/env python3
"""
Standalone test for SDKVersionDetector
Tests version detection logic without full module dependencies
"""

import sys
import os
import re
import threading
from typing import Optional
from unittest.mock import patch


# Inline version of SDKVersionDetector for testing
class SDKVersionDetector:
    """Simple SDK version detector for metadata/logging purposes."""
    
    _cached_version: Optional[str] = None
    _detection_lock = threading.Lock()
    
    @classmethod
    def detect_version(cls) -> str:
        """Detect installed SDK version with caching."""
        if cls._cached_version is not None:
            return cls._cached_version
            
        with cls._detection_lock:
            if cls._cached_version is not None:  # Double-check
                return cls._cached_version
                
            try:
                import bosdyn
                version = getattr(bosdyn, '__version__', 'unknown')
                cls._cached_version = version
                return version
            except ImportError:
                raise ImportError("Spot SDK not found. Install with: pip install bosdyn-client")
    
    @classmethod
    def validate_version(cls, version: str) -> bool:
        """Validate version format and support range."""
        if version == "unknown":
            raise ValueError("Cannot validate unknown SDK version")
            
        # Validate X.Y.Z format (strict - no additional characters)
        if not re.match(r'^\d+\.\d+\.\d+$', version):
            raise ValueError("Invalid version format. Expected 'X.Y.Z' (e.g., '4.5.2')")
        
        # Extract major version
        try:
            major_version = int(version.split('.')[0])
        except (ValueError, IndexError):
            raise ValueError("Invalid version format. Expected 'X.Y.Z' (e.g., '4.5.2')")
        
        # Check support range (4.0.0+ and 5.x series)
        if major_version < 4:
            raise ValueError("Unsupported SDK version. Minimum supported: 4.0.0")
        elif major_version > 5:
            raise ValueError("Unsupported SDK version. Supported: 4.0.0+ and 5.x series")
            
        return True


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
    SDKVersionDetector._cached_version = None
    
    # Mock bosdyn module with version
    mock_bosdyn = type('MockBosdyn', (), {'__version__': '4.5.2'})
    
    with patch.dict('sys.modules', {'bosdyn': mock_bosdyn}):
        version = SDKVersionDetector.detect_version()
        assert version == '4.5.2', f"Expected '4.5.2', got '{version}'"


def test_version_detection_missing_sdk():
    """Test version detection when SDK is missing"""
    SDKVersionDetector._cached_version = None
    
    # Ensure bosdyn is not in sys.modules
    if 'bosdyn' in sys.modules:
        del sys.modules['bosdyn']
    
    try:
        SDKVersionDetector.detect_version()
        assert False, "Expected ImportError"
    except ImportError as e:
        assert "Spot SDK not found" in str(e)


def test_version_caching():
    """Test that version is cached correctly"""
    SDKVersionDetector._cached_version = None
    
    mock_bosdyn = type('MockBosdyn', (), {'__version__': '5.1.0'})
    
    with patch.dict('sys.modules', {'bosdyn': mock_bosdyn}):
        version1 = SDKVersionDetector.detect_version()
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


def test_thread_safety():
    """Test thread-safe version detection"""
    SDKVersionDetector._cached_version = None
    results = []
    
    mock_bosdyn = type('MockBosdyn', (), {'__version__': '4.8.1'})
    
    def detect_version():
        with patch.dict('sys.modules', {'bosdyn': mock_bosdyn}):
            results.append(SDKVersionDetector.detect_version())

    threads = [threading.Thread(target=detect_version) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # All threads should get same result
    assert all(r == '4.8.1' for r in results), f"Results not consistent: {results}"
    assert len(results) == 5


def test_detect_current_sdk_version():
    """Test detection of currently installed SDK version"""
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
    
    print("=== Multi-Version Integration Tests ===")
    print("Testing SDK version detection and validation logic\n")
    
    # Version detection tests
    runner.run_test(test_version_detection_with_sdk, "version_detection_with_sdk")
    runner.run_test(test_version_detection_missing_sdk, "version_detection_missing_sdk")
    runner.run_test(test_version_caching, "version_caching")
    runner.run_test(test_thread_safety, "thread_safety")
    
    # Version validation tests
    runner.run_test(test_valid_4x_versions, "valid_4x_versions")
    runner.run_test(test_valid_5x_versions, "valid_5x_versions")
    runner.run_test(test_unsupported_old_versions, "unsupported_old_versions")
    runner.run_test(test_unsupported_future_versions, "unsupported_future_versions")
    runner.run_test(test_invalid_version_format, "invalid_version_format")
    runner.run_test(test_unknown_version, "unknown_version")
    
    # Current environment test
    runner.run_test(test_detect_current_sdk_version, "detect_current_sdk_version")
    
    success = runner.summary()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())