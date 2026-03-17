"""
End-to-end integration tests for strands-spot complete system

Tests full workflow: credential setup → connection → operations → cleanup
Uses mocks to avoid requiring real robot hardware.
"""

import os
import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

from strands_spot import use_spot, SpotConnection, SPOT_SDK_AVAILABLE
from strands_spot.cli.setSpotcon import SpotCredentialManager
from strands_spot.cli.spotNetInfo import SpotNetworkDiagnostic


class TestEndToEndWorkflow:
    """Test complete workflow from credential setup to operations"""

    def setup_method(self):
        """Setup test environment"""
        self.test_hostname = "192.168.80.3"
        self.test_username = "testuser"
        self.test_password = "testpass"
        
        # Clear environment variables
        for var in ['SPOT_HOSTNAME', 'SPOT_USERNAME', 'SPOT_PASSWORD']:
            if var in os.environ:
                del os.environ[var]

    @patch("strands_spot.cli.setSpotcon.Path.home")
    def test_credential_profile_workflow(self, mock_home):
        """Test credential profile creation and usage"""
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_home.return_value = Path(temp_dir)
            
            # Create credential manager
            manager = SpotCredentialManager()
            
            # Test profile creation
            with patch('builtins.input', side_effect=[self.test_hostname, self.test_username]):
                with patch('getpass.getpass', return_value=self.test_password):
                    profile_name = manager.create_profile("test_profile")
            
            assert profile_name == "test_profile"
            
            # Verify profile file exists
            profile_path = manager.spot_dir / "test_profile.json"
            assert profile_path.exists()
            
            # Test profile loading
            credentials = manager.load_profile("test_profile")
            assert credentials["hostname"] == self.test_hostname
            assert credentials["username"] == self.test_username
            assert credentials["password"] == self.test_password

    @patch("strands_spot.use_spot.bosdyn.client.create_standard_sdk")
    def test_context_manager_cleanup(self, mock_sdk):
        """Test context manager ensures proper resource cleanup"""
        if not SPOT_SDK_AVAILABLE:
            pytest.skip("Spot SDK not available")
        
        # Setup mocks
        mock_robot = MagicMock()
        mock_sdk_instance = MagicMock()
        mock_sdk_instance.create_robot.return_value = mock_robot
        mock_sdk.return_value = mock_sdk_instance
        
        # Test context manager
        with SpotConnection(self.test_hostname, self.test_username, self.test_password) as conn:
            # Acquire lease
            conn.acquire_lease()
            assert conn._lease_active
        
        # Verify cleanup was called
        assert not conn._lease_active

    @patch("strands_spot.use_spot.SpotConnection")
    def test_network_diagnostic_integration(self, mock_conn_class):
        """Test network diagnostic utility integration"""
        if not SPOT_SDK_AVAILABLE:
            pytest.skip("Spot SDK not available")
        
        # Setup mocks
        mock_conn = MagicMock()
        mock_conn.hostname = self.test_hostname
        mock_conn._sdk_version = "5.0.0"
        mock_conn_class.return_value = mock_conn
        
        # Mock robot state client
        mock_robot_state_client = MagicMock()
        mock_robot_state = MagicMock()
        mock_robot_state.network_state = None  # Trigger fallback
        mock_robot_state_client.get_robot_state.return_value = mock_robot_state
        mock_conn.get_client.return_value = mock_robot_state_client
        
        # Test network diagnostic
        diagnostic = SpotNetworkDiagnostic(mock_conn)
        network_info = diagnostic.get_network_info()
        
        assert network_info["robot_hostname"] == self.test_hostname
        assert network_info["sdk_version"] == "5.0.0"
        assert network_info["connection_status"] == "connected"
        assert len(network_info["interfaces"]) > 0

    @patch("strands_spot.use_spot.SpotConnection")
    def test_error_scenarios_and_recovery(self, mock_conn_class):
        """Test error scenarios and recovery mechanisms"""
        if not SPOT_SDK_AVAILABLE:
            pytest.skip("Spot SDK not available")
        
        # Test connection failure
        mock_conn_class.side_effect = Exception("Connection failed")
        
        result = use_spot(
            hostname=self.test_hostname,
            username=self.test_username,
            password=self.test_password,
            service="robot_state",
            method="get_robot_state"
        )
        
        assert result["status"] == "error"
        assert "Connection failed" in result["content"][0]["text"]

    @patch("strands_spot.use_spot.SpotConnection")
    def test_resource_management_lease_lifecycle(self, mock_conn_class):
        """Test resource management and lease acquisition/release"""
        if not SPOT_SDK_AVAILABLE:
            pytest.skip("Spot SDK not available")
        
        mock_conn = MagicMock()
        mock_conn_class.return_value = mock_conn
        
        # Test lease-required service
        with patch("strands_spot.use_spot.execute_method") as mock_execute:
            result = use_spot(
                hostname=self.test_hostname,
                username=self.test_username,
                password=self.test_password,
                service="robot_command",
                method="stand",
                keep_lease=False
            )
        
        # Verify lease lifecycle
        mock_conn.acquire_lease.assert_called_once()
        mock_conn.release_lease.assert_called_once()
        mock_conn.close.assert_called_once()
        
        assert result["status"] == "success"

    @patch("strands_spot.use_spot.SpotConnection")
    def test_full_workflow_integration(self, mock_conn_class):
        """Test complete workflow: setup → connection → operations → cleanup"""
        if not SPOT_SDK_AVAILABLE:
            pytest.skip("Spot SDK not available")
        
        # Setup environment variables
        os.environ['SPOT_HOSTNAME'] = self.test_hostname
        os.environ['SPOT_USERNAME'] = self.test_username
        os.environ['SPOT_PASSWORD'] = self.test_password
        
        try:
            mock_conn = MagicMock()
            mock_conn.hostname = self.test_hostname
            mock_conn._sdk_version = "5.0.0"
            mock_conn_class.return_value = mock_conn
            
            # Test sequence of operations
            operations = [
                ("robot_state", "get_robot_state"),
                ("robot_command", "stand"),
                ("image", "list_image_sources"),
                ("robot_command", "sit")
            ]
            
            with patch("strands_spot.use_spot.execute_method") as mock_execute:
                for service, method in operations:
                    result = use_spot(service=service, method=method)
                    assert result["status"] == "success"
                    
        finally:
            # Cleanup environment
            for var in ['SPOT_HOSTNAME', 'SPOT_USERNAME', 'SPOT_PASSWORD']:
                if var in os.environ:
                    del os.environ[var]


class TestCredentialProfileIntegration:
    """Test credential profile integration with main system"""

    @patch("strands_spot.cli.setSpotcon.Path.home")
    def test_profile_environment_integration(self, mock_home):
        """Test credential profiles work with environment variable system"""
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_home.return_value = Path(temp_dir)
            
            # Create profile
            manager = SpotCredentialManager()
            with patch('builtins.input', side_effect=["192.168.80.5", "admin"]):
                with patch('getpass.getpass', return_value="secret"):
                    profile_name = manager.create_profile()
            
            # Load profile and set environment
            credentials = manager.load_profile(profile_name)
            os.environ["SPOT_HOSTNAME"] = credentials["hostname"]
            os.environ["SPOT_USERNAME"] = credentials["username"]
            os.environ["SPOT_PASSWORD"] = credentials["password"]
            
            try:
                # Test that SpotConnection uses profile credentials
                with patch("strands_spot.use_spot.bosdyn.client.create_standard_sdk"):
                    conn = SpotConnection()
                    assert conn.hostname == "192.168.80.5"
                    assert conn.username == "admin"
                    assert conn.password == "secret"
            finally:
                # Cleanup
                for var in ['SPOT_HOSTNAME', 'SPOT_USERNAME', 'SPOT_PASSWORD']:
                    if var in os.environ:
                        del os.environ[var]


class TestNetworkDiagnosticUtility:
    """Test network diagnostic utility functionality"""

    @patch("strands_spot.use_spot.SpotConnection")
    def test_network_info_extraction(self, mock_conn_class):
        """Test network information extraction from robot state"""
        if not SPOT_SDK_AVAILABLE:
            pytest.skip("Spot SDK not available")
        
        mock_conn = MagicMock()
        mock_conn.hostname = "192.168.80.3"
        mock_conn._sdk_version = "5.0.0"
        
        # Mock network interface data
        mock_interface = MagicMock()
        mock_interface.name = "wlan0"
        mock_interface.ip_addresses = [MagicMock(address="192.168.80.3")]
        mock_interface.mac_address = "aa:bb:cc:dd:ee:ff"
        mock_interface.is_up = True
        
        mock_robot_state = MagicMock()
        mock_robot_state.network_state.network_interfaces = [mock_interface]
        
        mock_robot_state_client = MagicMock()
        mock_robot_state_client.get_robot_state.return_value = mock_robot_state
        mock_conn.get_client.return_value = mock_robot_state_client
        
        # Test diagnostic
        diagnostic = SpotNetworkDiagnostic(mock_conn)
        network_info = diagnostic.get_network_info()
        
        assert len(network_info["interfaces"]) == 1
        interface = network_info["interfaces"][0]
        assert interface["name"] == "wlan0"
        assert interface["type"] == "wifi_onboard"
        assert "192.168.80.3" in interface["ip_addresses"]
        assert interface["mac_address"] == "aa:bb:cc:dd:ee:ff"
        assert interface["status"] == "up"

    @patch("strands_spot.use_spot.SpotConnection")
    def test_network_diagnostic_fallback(self, mock_conn_class):
        """Test network diagnostic fallback when robot state unavailable"""
        if not SPOT_SDK_AVAILABLE:
            pytest.skip("Spot SDK not available")
        
        mock_conn = MagicMock()
        mock_conn.hostname = "192.168.80.3"
        mock_conn._sdk_version = "5.0.0"
        
        # Mock robot state client that fails
        mock_robot_state_client = MagicMock()
        mock_robot_state_client.get_robot_state.side_effect = Exception("Network state unavailable")
        mock_conn.get_client.return_value = mock_robot_state_client
        
        # Test diagnostic fallback
        diagnostic = SpotNetworkDiagnostic(mock_conn)
        network_info = diagnostic.get_network_info()
        
        assert network_info["connection_status"] == "connected"
        assert network_info["detection_method"] == "error_fallback"
        assert len(network_info["interfaces"]) == 1
        assert network_info["interfaces"][0]["name"] == "robot_connection"


class TestSystemIntegration:
    """Test complete system integration"""

    def test_backward_compatibility(self):
        """Test that existing functionality remains compatible"""
        # Test that use_spot still accepts hostname parameter
        with patch("strands_spot.use_spot.SpotConnection") as mock_conn_class:
            mock_conn = MagicMock()
            mock_conn_class.return_value = mock_conn
            
            with patch("strands_spot.use_spot.execute_method"):
                result = use_spot(
                    hostname="192.168.80.3",
                    username="admin", 
                    password="pass",
                    service="robot_state",
                    method="get_robot_state"
                )
            
            # Verify connection was created with hostname
            mock_conn_class.assert_called_once()
            args = mock_conn_class.call_args[1] if mock_conn_class.call_args[1] else mock_conn_class.call_args[0]
            assert "192.168.80.3" in str(args)

    def test_environment_variable_priority(self):
        """Test environment variable vs parameter priority"""
        os.environ['SPOT_HOSTNAME'] = 'env.hostname'
        os.environ['SPOT_USERNAME'] = 'envuser'
        os.environ['SPOT_PASSWORD'] = 'envpass'
        
        try:
            with patch("strands_spot.use_spot.bosdyn.client.create_standard_sdk"):
                # Parameters should override environment
                conn = SpotConnection(hostname="param.hostname", username="paramuser")
                assert conn.hostname == "param.hostname"
                assert conn.username == "paramuser"
                assert conn.password == "envpass"  # From environment
        finally:
            for var in ['SPOT_HOSTNAME', 'SPOT_USERNAME', 'SPOT_PASSWORD']:
                if var in os.environ:
                    del os.environ[var]

    def test_deployment_readiness_check(self):
        """Test that all components are ready for deployment"""
        # Check that all required modules can be imported
        try:
            from strands_spot import use_spot, SpotConnection
            from strands_spot.cli.setSpotcon import SpotCredentialManager
            from strands_spot.cli.spotNetInfo import SpotNetworkDiagnostic
            from strands_spot.version_detector import SDKVersionDetector
            from strands_spot.credential_manager import SpotCredentialManager as CredManager
        except ImportError as e:
            pytest.fail(f"Import error indicates deployment issue: {e}")
        
        # Check that key functions are callable
        assert callable(use_spot)
        assert callable(SpotConnection)
        assert callable(SpotCredentialManager)
        assert callable(SpotNetworkDiagnostic)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])