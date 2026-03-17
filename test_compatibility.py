#!/usr/bin/env python3
"""
Minimal backward compatibility test for SpotConnection
Tests the updated signature without requiring full SDK installation
"""

import os
import sys
import inspect
from unittest.mock import Mock, patch

# Mock strands.tool decorator
def tool(func):
    return func

# Mock bosdyn imports to avoid SDK dependency
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
sys.modules['bosdyn.client.exceptions'] = Mock()
sys.modules['strands'] = Mock()
sys.modules['strands'].tool = tool

# Mock version detector
sys.modules['strands_spot.version_detector'] = Mock()
mock_detector = Mock()
mock_detector.detect_version.return_value = "3.2.0"
mock_detector.validate_version.return_value = True
sys.modules['strands_spot.version_detector'].SDKVersionDetector = mock_detector

# Now import the actual module
from strands_spot.use_spot import SpotConnection

def test_signature_compatibility():
    """Test that SpotConnection has the expected backward-compatible signature"""
    print("=== Testing SpotConnection Signature Compatibility ===")
    
    # Check signature
    sig = inspect.signature(SpotConnection.__init__)
    params = list(sig.parameters.keys())
    
    print(f"SpotConnection.__init__ parameters: {params}")
    
    # Verify expected signature: (self, hostname=None, username=None, password=None)
    expected_params = ['self', 'hostname', 'username', 'password']
    
    if params == expected_params:
        print("✅ Signature matches expected backward-compatible format")
    else:
        print(f"❌ Signature mismatch. Expected: {expected_params}, Got: {params}")
        return False
        
    # Test parameter defaults
    for param_name in ['hostname', 'username', 'password']:
        param = sig.parameters[param_name]
        if param.default is None:
            print(f"✅ {param_name} has default None")
        else:
            print(f"❌ {param_name} default is {param.default}, expected None")
            return False
            
    return True

def test_environment_variable_fallback():
    """Test environment variable fallback behavior"""
    print("\n=== Testing Environment Variable Fallback ===")
    
    # Clear any existing env vars
    for var in ['SPOT_HOSTNAME', 'SPOT_USERNAME', 'SPOT_PASSWORD']:
        if var in os.environ:
            del os.environ[var]
    
    # Test 1: No parameters, no env vars - should raise ValueError
    try:
        conn = SpotConnection()
        print("❌ Should have raised ValueError for missing hostname")
        return False
    except ValueError as e:
        if "hostname" in str(e).lower():
            print("✅ Correctly raises ValueError when hostname missing")
        else:
            print(f"❌ Wrong error message: {e}")
            return False
    except Exception as e:
        print(f"❌ Unexpected exception: {e}")
        return False
    
    # Test 2: Only hostname parameter, no credentials - should raise ValueError
    try:
        conn = SpotConnection(hostname="192.168.80.3")
        print("❌ Should have raised ValueError for missing credentials")
        return False
    except ValueError as e:
        if "username" in str(e).lower() and "password" in str(e).lower():
            print("✅ Correctly raises ValueError when credentials missing")
        else:
            print(f"❌ Wrong error message: {e}")
            return False
    except Exception as e:
        print(f"❌ Unexpected exception: {e}")
        return False
    
    # Test 3: Environment variables only
    os.environ['SPOT_HOSTNAME'] = '192.168.80.3'
    os.environ['SPOT_USERNAME'] = 'admin'
    os.environ['SPOT_PASSWORD'] = 'password'
    
    with patch('bosdyn.client.create_standard_sdk') as mock_sdk:
        mock_robot = Mock()
        mock_sdk_instance = Mock()
        mock_sdk_instance.create_robot.return_value = mock_robot
        mock_sdk.return_value = mock_sdk_instance
        
        try:
            conn = SpotConnection()  # No parameters, should use env vars
            print("✅ Successfully created connection using environment variables")
            
            # Verify it used env vars
            if conn.hostname == '192.168.80.3' and conn.username == 'admin':
                print("✅ Environment variables correctly used")
            else:
                print(f"❌ Wrong values: hostname={conn.hostname}, username={conn.username}")
                return False
                
        except Exception as e:
            print(f"❌ Failed to create connection with env vars: {e}")
            return False
    
    # Test 4: Mixed parameters and env vars (parameters should take precedence)
    with patch('bosdyn.client.create_standard_sdk') as mock_sdk:
        mock_robot = Mock()
        mock_sdk_instance = Mock()
        mock_sdk_instance.create_robot.return_value = mock_robot
        mock_sdk.return_value = mock_sdk_instance
        
        try:
            conn = SpotConnection(hostname="192.168.80.4", username="user2")
            # password should come from env var
            print("✅ Successfully created connection with mixed parameters/env vars")
            
            if conn.hostname == '192.168.80.4' and conn.username == 'user2' and conn.password == 'password':
                print("✅ Parameters override env vars correctly")
            else:
                print(f"❌ Wrong precedence: hostname={conn.hostname}, username={conn.username}, password={conn.password}")
                return False
                
        except Exception as e:
            print(f"❌ Failed with mixed params: {e}")
            return False
    
    return True

def test_backward_compatibility_with_existing_tests():
    """Test that existing test patterns still work"""
    print("\n=== Testing Backward Compatibility with Existing Tests ===")
    
    with patch('bosdyn.client.create_standard_sdk') as mock_sdk:
        mock_robot = Mock()
        mock_sdk_instance = Mock()
        mock_sdk_instance.create_robot.return_value = mock_robot
        mock_sdk.return_value = mock_sdk_instance
        
        try:
            # This is the pattern used in existing tests
            conn = SpotConnection("192.168.80.3", "admin", "pass")
            print("✅ Existing test pattern works (positional args)")
            
            if conn.hostname == "192.168.80.3" and conn.username == "admin":
                print("✅ Positional arguments correctly assigned")
            else:
                print(f"❌ Wrong assignment: hostname={conn.hostname}, username={conn.username}")
                return False
                
        except Exception as e:
            print(f"❌ Existing test pattern failed: {e}")
            return False
    
    return True

def main():
    """Run all compatibility tests"""
    print("Boston Dynamics Spot SDK - SpotConnection Backward Compatibility Test")
    print("=" * 70)
    
    tests = [
        test_signature_compatibility,
        test_environment_variable_fallback,
        test_backward_compatibility_with_existing_tests
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                print(f"❌ {test.__name__} FAILED")
        except Exception as e:
            print(f"❌ {test.__name__} FAILED with exception: {e}")
    
    print(f"\n=== Test Results ===")
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("✅ ALL TESTS PASSED - Backward compatibility maintained")
        return True
    else:
        print("❌ SOME TESTS FAILED - Backward compatibility issues detected")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)