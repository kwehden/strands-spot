"""
Unit tests for use_spot tool - Modified for direct execution

Run with: python3 test_runner_standalone.py
"""

import os
import sys
from unittest.mock import Mock, MagicMock, patch

# Setup mocks before any imports
def setup_mocks():
    # Mock strands
    sys.modules['strands'] = Mock()
    sys.modules['strands'].tool = lambda func: func
    
    # Mock bosdyn
    sys.modules['bosdyn'] = Mock()
    sys.modules['bosdyn.client'] = Mock()
    sys.modules['bosdyn.client.util'] = Mock()
    sys.modules['bosdyn.client.robot_command'] = Mock()
    sys.modules['bosdyn.client.robot_state'] = Mock()
    sys.modules['bosdyn.client.power'] = Mock()
    sys.modules['bosdyn.client.lease'] = Mock()
    sys.modules['bosdyn.client.image'] = Mock()
    sys.modules['bosdyn.client.estop'] = Mock()
    sys.modules['bosdyn.client.time_sync'] = Mock()
    sys.modules['bosdyn.client.directory'] = Mock()
    
    # Mock exceptions properly
    class MockRpcError(Exception):
        pass
    
    mock_exceptions = Mock()
    mock_exceptions.RpcError = MockRpcError
    sys.modules['bosdyn.client.exceptions'] = mock_exceptions
    
    # Mock version detector
    sys.modules['strands_spot.version_detector'] = Mock()
    mock_detector = Mock()
    mock_detector.detect_version.return_value = "3.2.0"
    mock_detector.validate_version.return_value = True
    sys.modules['strands_spot.version_detector'].SDKVersionDetector = mock_detector

setup_mocks()

# Add project root to path
sys.path.insert(0, '/home/ANT.AMAZON.COM/kwehden/projects/strands-spot')

from strands_spot import use_spot
from strands_spot.use_spot import SpotConnection

# Mock SPOT_SDK_AVAILABLE as True for testing
SPOT_SDK_AVAILABLE = True

class TestSpotConnection:
    """Test SpotConnection class"""

    def test_init(self):
        """Test connection initialization"""
        with patch("strands_spot.use_spot.bosdyn.client.create_standard_sdk") as mock_sdk:
            # Setup mocks
            mock_robot = MagicMock()
            mock_sdk_instance = MagicMock()
            mock_sdk_instance.create_robot.return_value = mock_robot
            mock_sdk.return_value = mock_sdk_instance

            # Create connection
            conn = SpotConnection("192.168.80.3", "admin", "pass")

            # Verify
            assert conn.hostname == "192.168.80.3"
            assert conn.username == "admin"
            mock_sdk.assert_called_once()
            mock_robot.authenticate.assert_called_once()

    def test_env_var_fallback(self):
        """Test environment variable fallback"""
        with patch("strands_spot.use_spot.bosdyn.client.create_standard_sdk") as mock_sdk:
            # Setup mocks
            mock_robot = MagicMock()
            mock_sdk_instance = MagicMock()
            mock_sdk_instance.create_robot.return_value = mock_robot
            mock_sdk.return_value = mock_sdk_instance

            # Set environment variables
            os.environ['SPOT_HOSTNAME'] = '192.168.80.5'
            os.environ['SPOT_USERNAME'] = 'testuser'
            os.environ['SPOT_PASSWORD'] = 'testpass'

            try:
                # Create connection without parameters
                conn = SpotConnection()

                # Verify env vars were used
                assert conn.hostname == "192.168.80.5"
                assert conn.username == "testuser"
                assert conn.password == "testpass"
            finally:
                # Clean up env vars
                for var in ['SPOT_HOSTNAME', 'SPOT_USERNAME', 'SPOT_PASSWORD']:
                    if var in os.environ:
                        del os.environ[var]

    def test_mixed_params_env_vars(self):
        """Test mixed parameters and environment variables"""
        with patch("strands_spot.use_spot.bosdyn.client.create_standard_sdk") as mock_sdk:
            # Setup mocks
            mock_robot = MagicMock()
            mock_sdk_instance = MagicMock()
            mock_sdk_instance.create_robot.return_value = mock_robot
            mock_sdk.return_value = mock_sdk_instance

            # Set environment variables
            os.environ['SPOT_HOSTNAME'] = '192.168.80.5'
            os.environ['SPOT_USERNAME'] = 'envuser'
            os.environ['SPOT_PASSWORD'] = 'envpass'

            try:
                # Create connection with some parameters (should override env vars)
                conn = SpotConnection(hostname="192.168.80.6", username="paramuser")

                # Verify parameters take precedence
                assert conn.hostname == "192.168.80.6"
                assert conn.username == "paramuser"
                assert conn.password == "envpass"  # From env var
            finally:
                # Clean up env vars
                for var in ['SPOT_HOSTNAME', 'SPOT_USERNAME', 'SPOT_PASSWORD']:
                    if var in os.environ:
                        del os.environ[var]

    def test_missing_hostname_error(self):
        """Test error when hostname not provided"""
        # Clear any existing env vars
        for var in ['SPOT_HOSTNAME', 'SPOT_USERNAME', 'SPOT_PASSWORD']:
            if var in os.environ:
                del os.environ[var]

        try:
            SpotConnection()
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "hostname" in str(e).lower()

    def test_missing_credentials_error(self):
        """Test error when credentials not provided"""
        # Clear any existing env vars
        for var in ['SPOT_HOSTNAME', 'SPOT_USERNAME', 'SPOT_PASSWORD']:
            if var in os.environ:
                del os.environ[var]

        try:
            SpotConnection(hostname="192.168.80.3")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "username" in str(e).lower() and "password" in str(e).lower()

    def test_lease_management(self):
        """Test lease acquire/release"""
        with patch("strands_spot.use_spot.bosdyn.client.create_standard_sdk") as mock_sdk:
            mock_robot = MagicMock()
            mock_sdk_instance = MagicMock()
            mock_sdk_instance.create_robot.return_value = mock_robot
            mock_sdk.return_value = mock_sdk_instance
            
            # Mock LeaseKeepAlive
            with patch("strands_spot.use_spot.LeaseKeepAlive") as mock_lease_keepalive:
                mock_lease_instance = MagicMock()
                mock_lease_keepalive.return_value = mock_lease_instance
                
                conn = SpotConnection("192.168.80.3", "admin", "pass")

                # Initially no lease
                assert not conn._lease_active

                # Acquire lease
                conn.acquire_lease()
                assert conn._lease_active

                # Release lease
                conn.release_lease()
                assert not conn._lease_active


class TestUseSpot:
    """Test use_spot main function"""

    def test_missing_credentials(self):
        """Test error when credentials missing"""
        # Clear env vars
        for var in ['SPOT_HOSTNAME', 'SPOT_USERNAME', 'SPOT_PASSWORD']:
            if var in os.environ:
                del os.environ[var]
        
        # Set only hostname to test missing credentials
        os.environ['SPOT_HOSTNAME'] = '192.168.80.3'
        
        try:        
            result = use_spot(service="robot_state", method="get_robot_state")

            assert result["status"] == "error"
            assert "credentials" in result["content"][0]["text"].lower() or "username" in result["content"][0]["text"].lower() or "hostname" in result["content"][0]["text"].lower()
        finally:
            if 'SPOT_HOSTNAME' in os.environ:
                del os.environ['SPOT_HOSTNAME']

    def test_sdk_not_available(self):
        """Test graceful handling when SDK not installed"""
        with patch("strands_spot.use_spot.SPOT_SDK_AVAILABLE", False):
            result = use_spot(
                username="admin",
                password="pass",
                service="robot_state",
                method="get_robot_state",
            )

            assert result["status"] == "error"
            assert "not installed" in result["content"][0]["text"].lower()

    def test_successful_call(self):
        """Test successful operation"""
        # Set environment variables for hostname
        os.environ['SPOT_HOSTNAME'] = '192.168.80.3'
        
        try:
            with patch("strands_spot.use_spot.SpotConnection") as mock_conn_class:
                # Setup mocks
                mock_conn = MagicMock()
                mock_client = MagicMock()
                mock_response = MagicMock()

                mock_conn_class.return_value = mock_conn
                mock_conn.get_client.return_value = mock_client
                mock_conn.hostname = "192.168.80.3"
                mock_conn._sdk_version = "3.2.0"

                with patch("strands_spot.use_spot.execute_method", return_value=mock_response):
                    result = use_spot(
                        username="admin",
                        password="pass",
                        service="robot_state",
                        method="get_robot_state",
                        params={},
                    )

                assert result["status"] == "success"
                assert "✅" in result["content"][0]["text"]

                # Check content structure
                assert len(result["content"]) == 3  # text, response_data json, metadata json
                assert "json" in result["content"][1]
                assert "json" in result["content"][2]
                assert "response_data" in result["content"][1]["json"]
                assert "metadata" in result["content"][2]["json"]
        finally:
            if 'SPOT_HOSTNAME' in os.environ:
                del os.environ['SPOT_HOSTNAME']


def run_tests():
    """Run all tests"""
    print("Running strands-spot backward compatibility tests")
    print("=" * 60)
    
    test_classes = [TestSpotConnection, TestUseSpot]
    
    passed = 0
    failed = 0
    total = 0
    
    for test_class in test_classes:
        print(f"\n{test_class.__name__}:")
        
        # Get test methods
        test_methods = [method for method in dir(test_class) 
                      if method.startswith('test_') and callable(getattr(test_class, method))]
        
        for test_method_name in test_methods:
            total += 1
            test_name = f"{test_class.__name__}::{test_method_name}"
            
            try:
                # Create test instance and run test
                test_instance = test_class()
                test_method = getattr(test_instance, test_method_name)
                
                print(f"  Running {test_method_name}...", end=" ")
                test_method()
                print("✅ PASSED")
                passed += 1
                
            except Exception as e:
                print("❌ FAILED")
                print(f"    Error: {str(e)}")
                failed += 1
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"Test Results:")
    print(f"  Passed: {passed}")
    print(f"  Failed: {failed}")
    print(f"  Total: {total}")
    
    if failed == 0:
        print("\n✅ All tests passed! Backward compatibility maintained.")
        return True
    else:
        print(f"\n❌ {failed} test(s) failed. Check compatibility issues above.")
        return False

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)