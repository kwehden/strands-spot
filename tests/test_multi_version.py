"""
Multi-Version Integration Tests for strands-spot SDK 4.x and 5.x support

Tests version detection and basic operations across supported SDK versions.
Works with whatever SDK version is currently installed (4.x or 5.x).
"""

import pytest
import threading
import time
from unittest.mock import Mock, patch, MagicMock

from strands_spot.version_detector import SDKVersionDetector
from strands_spot.use_spot import SpotConnection, use_spot


class TestVersionDetection:
    """Test SDK version detection functionality"""

    def setup_method(self):
        """Reset cached version before each test"""
        SDKVersionDetector._cached_version = None

    def test_version_detection_with_sdk(self):
        """Test version detection when SDK is available"""
        with patch('bosdyn.__version__', '4.5.2'):
            with patch('strands_spot.version_detector.bosdyn'):
                version = SDKVersionDetector.detect_version()
                assert version == '4.5.2'

    def test_version_detection_missing_sdk(self):
        """Test version detection when SDK is missing"""
        with patch('strands_spot.version_detector.bosdyn', side_effect=ImportError):
            with pytest.raises(ImportError, match="Spot SDK not found"):
                SDKVersionDetector.detect_version()

    def test_version_caching(self):
        """Test that version is cached correctly"""
        with patch('bosdyn.__version__', '5.1.0'):
            with patch('strands_spot.version_detector.bosdyn'):
                # First call
                version1 = SDKVersionDetector.detect_version()
                # Second call should use cache
                version2 = SDKVersionDetector.detect_version()
                assert version1 == version2 == '5.1.0'

    def test_thread_safe_detection(self):
        """Test thread-safe version detection"""
        results = []
        
        def detect_version():
            with patch('bosdyn.__version__', '4.8.1'):
                with patch('strands_spot.version_detector.bosdyn'):
                    results.append(SDKVersionDetector.detect_version())

        threads = [threading.Thread(target=detect_version) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All threads should get same result
        assert all(r == '4.8.1' for r in results)
        assert len(results) == 5


class TestVersionValidation:
    """Test version validation logic"""

    def test_valid_4x_versions(self):
        """Test validation of supported 4.x versions"""
        valid_versions = ['4.0.0', '4.5.2', '4.9.9']
        for version in valid_versions:
            assert SDKVersionDetector.validate_version(version) is True

    def test_valid_5x_versions(self):
        """Test validation of supported 5.x versions"""
        valid_versions = ['5.0.0', '5.1.1', '5.9.9']
        for version in valid_versions:
            assert SDKVersionDetector.validate_version(version) is True

    def test_unsupported_old_versions(self):
        """Test rejection of unsupported old versions"""
        old_versions = ['3.9.9', '2.1.0', '1.0.0']
        for version in old_versions:
            with pytest.raises(ValueError, match="Unsupported SDK version.*Minimum supported: 4.0.0"):
                SDKVersionDetector.validate_version(version)

    def test_unsupported_future_versions(self):
        """Test rejection of unsupported future versions"""
        future_versions = ['6.0.0', '7.1.0', '10.0.0']
        for version in future_versions:
            with pytest.raises(ValueError, match="Unsupported SDK version.*Supported: 4.0.0\\+ and 5.x series"):
                SDKVersionDetector.validate_version(version)

    def test_invalid_version_format(self):
        """Test rejection of invalid version formats"""
        invalid_formats = ['4.5', '4', 'v4.5.2', '4.5.2-beta', 'invalid']
        for version in invalid_formats:
            with pytest.raises(ValueError, match="Invalid version format"):
                SDKVersionDetector.validate_version(version)

    def test_unknown_version(self):
        """Test rejection of unknown version"""
        with pytest.raises(ValueError, match="Cannot validate unknown SDK version"):
            SDKVersionDetector.validate_version('unknown')


class TestSpotConnectionVersionLogging:
    """Test that SpotConnection logs detected SDK version"""

    @patch('strands_spot.use_spot.bosdyn.client.create_standard_sdk')
    @patch('strands_spot.use_spot.logger')
    def test_version_logging_success(self, mock_logger, mock_sdk):
        """Test successful version detection and logging"""
        # Setup mocks
        mock_robot = MagicMock()
        mock_sdk_instance = MagicMock()
        mock_sdk_instance.create_robot.return_value = mock_robot
        mock_sdk.return_value = mock_sdk_instance

        with patch.object(SDKVersionDetector, 'detect_version', return_value='4.5.2'):
            with patch.object(SDKVersionDetector, 'validate_version', return_value=True):
                conn = SpotConnection('192.168.80.3', 'admin', 'pass')
                
                # Verify version was logged
                mock_logger.info.assert_any_call('Using Boston Dynamics SDK version 4.5.2')
                assert conn._sdk_version == '4.5.2'

    @patch('strands_spot.use_spot.bosdyn.client.create_standard_sdk')
    @patch('strands_spot.use_spot.logger')
    def test_version_detection_failure(self, mock_logger, mock_sdk):
        """Test handling of version detection failure"""
        # Setup mocks
        mock_robot = MagicMock()
        mock_sdk_instance = MagicMock()
        mock_sdk_instance.create_robot.return_value = mock_robot
        mock_sdk.return_value = mock_sdk_instance

        with patch.object(SDKVersionDetector, 'detect_version', side_effect=ImportError("SDK not found")):
            conn = SpotConnection('192.168.80.3', 'admin', 'pass')
            
            # Verify warning was logged
            mock_logger.warning.assert_any_call('Could not detect SDK version: SDK not found')
            assert conn._sdk_version == 'unknown'


class TestBasicConnectionFunctionality:
    """Test basic connection functionality with version detection"""

    @patch('strands_spot.use_spot.SPOT_SDK_AVAILABLE', True)
    @patch('strands_spot.use_spot.SpotConnection')
    def test_use_spot_includes_version_metadata(self, mock_conn_class):
        """Test that use_spot includes SDK version in metadata"""
        # Setup mocks
        mock_conn = MagicMock()
        mock_conn._sdk_version = '5.1.1'
        mock_conn.hostname = '192.168.80.3'
        mock_conn_class.return_value = mock_conn

        with patch('strands_spot.use_spot.execute_method', return_value=Mock()):
            result = use_spot(
                service='robot_state',
                method='get_robot_state',
                username='admin',
                password='pass'
            )

        # Verify version is in metadata
        assert result['status'] == 'success'
        metadata = result['content'][2]['json']['metadata']
        assert metadata['sdk_version'] == '5.1.1'

    @patch('strands_spot.use_spot.SPOT_SDK_AVAILABLE', False)
    def test_use_spot_sdk_not_available(self):
        """Test use_spot when SDK is not available"""
        result = use_spot(
            service='robot_state',
            method='get_robot_state',
            username='admin',
            password='pass'
        )

        assert result['status'] == 'error'
        assert 'not installed' in result['content'][0]['text']


class TestErrorHandling:
    """Test error handling for missing SDK scenarios"""

    def test_version_detector_import_error(self):
        """Test version detector handles missing SDK gracefully"""
        with patch('strands_spot.version_detector.bosdyn', side_effect=ImportError):
            with pytest.raises(ImportError, match="Spot SDK not found"):
                SDKVersionDetector.detect_version()

    @patch('strands_spot.use_spot.bosdyn.client.create_standard_sdk')
    def test_spot_connection_version_detection_error(self, mock_sdk):
        """Test SpotConnection handles version detection errors"""
        # Setup mocks
        mock_robot = MagicMock()
        mock_sdk_instance = MagicMock()
        mock_sdk_instance.create_robot.return_value = mock_robot
        mock_sdk.return_value = mock_sdk_instance

        with patch.object(SDKVersionDetector, 'detect_version', side_effect=Exception("Detection failed")):
            conn = SpotConnection('192.168.80.3', 'admin', 'pass')
            
            # Should handle error gracefully
            assert conn._sdk_version == 'unknown'


class TestCurrentEnvironment:
    """Test with current environment SDK version"""

    def test_detect_current_sdk_version(self):
        """Test detection of currently installed SDK version"""
        try:
            version = SDKVersionDetector.detect_version()
            print(f"Detected SDK version: {version}")
            
            # If we get here, SDK is installed
            assert isinstance(version, str)
            if version != 'unknown':
                # Validate the detected version
                assert SDKVersionDetector.validate_version(version) is True
                
        except ImportError:
            # SDK not installed - this is expected in test environment
            print("SDK not installed in test environment")
            pytest.skip("Spot SDK not available in test environment")

    def test_version_format_compliance(self):
        """Test that any detected version follows expected format"""
        try:
            version = SDKVersionDetector.detect_version()
            if version != 'unknown':
                # Should be X.Y.Z format
                parts = version.split('.')
                assert len(parts) >= 3
                assert all(part.isdigit() for part in parts[:3])
                
        except ImportError:
            pytest.skip("Spot SDK not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])