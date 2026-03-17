#!/usr/bin/env python3
"""
Simple end-to-end validation runner (no pytest required)

Tests key functionality without requiring external dependencies.
"""

import os
import sys
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_imports():
    """Test that all modules can be imported"""
    print("🧪 Testing imports...")
    
    try:
        from strands_spot import use_spot, SpotConnection
        from strands_spot.cli.setSpotcon import SpotCredentialManager
        from strands_spot.cli.spotNetInfo import SpotNetworkDiagnostic
        from strands_spot.version_detector import SDKVersionDetector
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_credential_manager():
    """Test credential profile functionality"""
    print("🧪 Testing credential manager...")
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock home directory
            with patch("strands_spot.cli.setSpotcon.Path.home", return_value=Path(temp_dir)):
                manager = SpotCredentialManager()
                
                # Test profile creation
                test_creds = {
                    "hostname": "192.168.80.3",
                    "username": "admin",
                    "password": "password",
                    "created": "2024-01-01T00:00:00",
                    "last_used": None
                }
                
                manager._save_profile("test_profile", test_creds)
                
                # Test profile loading
                loaded_creds = manager.load_profile("test_profile")
                assert loaded_creds["hostname"] == "192.168.80.3"
                assert loaded_creds["username"] == "admin"
                
                print("✅ Credential manager working")
                return True
                
    except Exception as e:
        print(f"❌ Credential manager failed: {e}")
        return False

def test_environment_variables():
    """Test environment variable handling"""
    print("🧪 Testing environment variables...")
    
    try:
        # Clear existing env vars
        for var in ['SPOT_HOSTNAME', 'SPOT_USERNAME', 'SPOT_PASSWORD']:
            if var in os.environ:
                del os.environ[var]
        
        # Test missing hostname error
        try:
            from strands_spot import SpotConnection
            SpotConnection()
            print("❌ Should have failed with missing hostname")
            return False
        except ValueError as e:
            if "Hostname required" in str(e):
                print("✅ Environment variable validation working")
            else:
                print(f"❌ Wrong error message: {e}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Environment variable test failed: {e}")
        return False

def test_context_manager():
    """Test context manager functionality"""
    print("🧪 Testing context manager...")
    
    try:
        with patch("strands_spot.use_spot.bosdyn.client.create_standard_sdk"):
            from strands_spot import SpotConnection
            
            # Test context manager protocol
            conn = SpotConnection("192.168.80.3", "admin", "pass")
            
            # Check context manager methods exist
            assert hasattr(conn, '__enter__')
            assert hasattr(conn, '__exit__')
            assert callable(conn.__enter__)
            assert callable(conn.__exit__)
            
            # Test context manager returns self
            assert conn.__enter__() is conn
            
            print("✅ Context manager working")
            return True
            
    except Exception as e:
        print(f"❌ Context manager test failed: {e}")
        return False

def test_network_diagnostic():
    """Test network diagnostic functionality"""
    print("🧪 Testing network diagnostic...")
    
    try:
        from strands_spot.cli.spotNetInfo import SpotNetworkDiagnostic
        
        # Mock connection
        mock_conn = MagicMock()
        mock_conn.hostname = "192.168.80.3"
        mock_conn._sdk_version = "5.0.0"
        
        # Mock robot state client with fallback scenario
        mock_robot_state_client = MagicMock()
        mock_robot_state_client.get_robot_state.side_effect = Exception("Network unavailable")
        mock_conn.get_client.return_value = mock_robot_state_client
        
        # Test diagnostic
        diagnostic = SpotNetworkDiagnostic(mock_conn)
        network_info = diagnostic.get_network_info()
        
        # Verify fallback behavior
        assert network_info["robot_hostname"] == "192.168.80.3"
        assert network_info["connection_status"] == "connected"
        assert network_info["detection_method"] == "error_fallback"
        assert len(network_info["interfaces"]) == 1
        
        print("✅ Network diagnostic working")
        return True
        
    except Exception as e:
        print(f"❌ Network diagnostic test failed: {e}")
        return False

def test_use_spot_function():
    """Test use_spot function basic functionality"""
    print("🧪 Testing use_spot function...")
    
    try:
        from strands_spot import use_spot
        
        # Test SDK not available scenario
        with patch("strands_spot.use_spot.SPOT_SDK_AVAILABLE", False):
            result = use_spot(
                hostname="192.168.80.3",
                username="admin",
                password="pass",
                service="robot_state",
                method="get_robot_state"
            )
            
            assert result["status"] == "error"
            assert "not installed" in result["content"][0]["text"].lower()
        
        print("✅ use_spot function working")
        return True
        
    except Exception as e:
        print(f"❌ use_spot function test failed: {e}")
        return False

def test_examples_syntax():
    """Test that example files have valid syntax"""
    print("🧪 Testing example file syntax...")
    
    try:
        examples_dir = Path(__file__).parent.parent / "examples"
        example_files = list(examples_dir.glob("*.py"))
        
        for example_file in example_files:
            try:
                with open(example_file, 'r') as f:
                    compile(f.read(), example_file, 'exec')
            except SyntaxError as e:
                print(f"❌ Syntax error in {example_file}: {e}")
                return False
        
        print(f"✅ All {len(example_files)} example files have valid syntax")
        return True
        
    except Exception as e:
        print(f"❌ Example syntax test failed: {e}")
        return False

def main():
    """Run all validation tests"""
    print("🦆 Strands-Spot End-to-End Validation")
    print("=" * 40)
    
    tests = [
        test_imports,
        test_credential_manager,
        test_environment_variables,
        test_context_manager,
        test_network_diagnostic,
        test_use_spot_function,
        test_examples_syntax
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 40)
    print(f"📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All tests passed - System ready for deployment!")
        return True
    else:
        print("❌ Some tests failed - Review issues above")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)