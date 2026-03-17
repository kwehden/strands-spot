"""
Unit tests for use_spot tool

Run with: pytest tests/test_use_spot.py
"""

import os
import pytest
from unittest.mock import Mock, MagicMock, patch

from strands_spot import use_spot, SpotConnection, SPOT_SDK_AVAILABLE


class TestSpotConnection:
    """Test SpotConnection class"""

    @patch("use_spot.bosdyn.client.create_standard_sdk")
    def test_init(self, mock_sdk):
        """Test connection initialization"""
        if not SPOT_SDK_AVAILABLE:
            pytest.skip("Spot SDK not available")

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

    @patch("use_spot.bosdyn.client.create_standard_sdk")
    def test_env_var_fallback(self, mock_sdk):
        """Test environment variable fallback"""
        if not SPOT_SDK_AVAILABLE:
            pytest.skip("Spot SDK not available")

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

    @patch("use_spot.bosdyn.client.create_standard_sdk")
    def test_mixed_params_env_vars(self, mock_sdk):
        """Test mixed parameters and environment variables"""
        if not SPOT_SDK_AVAILABLE:
            pytest.skip("Spot SDK not available")

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

        with pytest.raises(ValueError, match="Hostname required"):
            SpotConnection()

    def test_missing_credentials_error(self):
        """Test error when credentials not provided"""
        # Clear any existing env vars
        for var in ['SPOT_HOSTNAME', 'SPOT_USERNAME', 'SPOT_PASSWORD']:
            if var in os.environ:
                del os.environ[var]

        with pytest.raises(ValueError, match="Username and password required"):
            SpotConnection(hostname="192.168.80.3")

    def test_lease_management(self):
        """Test lease acquire/release"""
        if not SPOT_SDK_AVAILABLE:
            pytest.skip("Spot SDK not available")

        with patch("use_spot.bosdyn.client.create_standard_sdk"):
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
        result = use_spot(hostname="192.168.80.3", service="robot_state", method="get_robot_state")

        assert result["status"] == "error"
        assert "credentials" in result["content"][0]["text"].lower()

    def test_sdk_not_available(self):
        """Test graceful handling when SDK not installed"""
        with patch("use_spot.SPOT_SDK_AVAILABLE", False):
            result = use_spot(
                hostname="192.168.80.3",
                username="admin",
                password="pass",
                service="robot_state",
                method="get_robot_state",
            )

            assert result["status"] == "error"
            assert "not installed" in result["content"][0]["text"].lower()

    @patch("use_spot.SpotConnection")
    def test_successful_call(self, mock_conn_class):
        """Test successful operation"""
        if not SPOT_SDK_AVAILABLE:
            pytest.skip("Spot SDK not available")

        # Setup mocks
        mock_conn = MagicMock()
        mock_client = MagicMock()
        mock_response = MagicMock()

        mock_conn_class.return_value = mock_conn
        mock_conn.get_client.return_value = mock_client

        with patch("use_spot.execute_method", return_value=mock_response):
            result = use_spot(
                hostname="192.168.80.3",
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

    @patch("use_spot.SpotConnection")
    def test_lease_acquisition(self, mock_conn_class):
        """Test lease is acquired for robot_command"""
        if not SPOT_SDK_AVAILABLE:
            pytest.skip("Spot SDK not available")

        mock_conn = MagicMock()
        mock_conn_class.return_value = mock_conn

        with patch("use_spot.execute_method"):
            result = use_spot(
                hostname="192.168.80.3",
                username="admin",
                password="pass",
                service="robot_command",
                method="stand",
                params={},
            )

        # Verify lease was acquired
        mock_conn.acquire_lease.assert_called_once()
        mock_conn.release_lease.assert_called_once()

        # Check metadata in JSON block
        metadata = result["content"][2]["json"]["metadata"]
        assert metadata["lease_acquired"] == True

    @patch("use_spot.SpotConnection")
    def test_keep_lease(self, mock_conn_class):
        """Test keeping lease when requested"""
        if not SPOT_SDK_AVAILABLE:
            pytest.skip("Spot SDK not available")

        mock_conn = MagicMock()
        mock_conn_class.return_value = mock_conn

        with patch("use_spot.execute_method"):
            result = use_spot(
                hostname="192.168.80.3",
                username="admin",
                password="pass",
                service="robot_command",
                method="stand",
                params={},
                keep_lease=True,
            )

        # Verify lease was NOT released
        mock_conn.acquire_lease.assert_called_once()
        mock_conn.release_lease.assert_not_called()

        # Verify metadata reflects lease retention
        metadata = result["content"][2]["json"]["metadata"]
        assert metadata["lease_retained"] == True

    @patch("use_spot.SpotConnection")
    def test_error_handling(self, mock_conn_class):
        """Test error response format"""
        if not SPOT_SDK_AVAILABLE:
            pytest.skip("Spot SDK not available")

        mock_conn = MagicMock()
        mock_conn_class.return_value = mock_conn
        mock_conn.get_client.side_effect = Exception("Test error")

        result = use_spot(
            hostname="192.168.80.3",
            username="admin",
            password="pass",
            service="robot_command",
            method="stand",
            params={},
        )

        # Check error response structure
        assert result["status"] == "error"
        assert "❌" in result["content"][0]["text"]
        assert len(result["content"]) == 2  # text and metadata json
        assert "json" in result["content"][1]
        assert "metadata" in result["content"][1]["json"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
