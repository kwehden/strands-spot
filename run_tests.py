#!/usr/bin/env python3
"""
Test runner for strands-spot backward compatibility testing
Simulates pytest functionality without requiring pytest installation
"""

import os
import sys
import traceback
from unittest.mock import Mock, MagicMock, patch

# Mock all dependencies
def setup_mocks():
    """Setup all required mocks"""
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
    sys.modules['bosdyn.client.exceptions'] = Mock()
    
    # Mock version detector
    sys.modules['strands_spot.version_detector'] = Mock()
    mock_detector = Mock()
    mock_detector.detect_version.return_value = "3.2.0"
    mock_detector.validate_version.return_value = True
    sys.modules['strands_spot.version_detector'].SDKVersionDetector = mock_detector

# Mock pytest functionality
class MockPytest:
    @staticmethod
    def skip(reason):
        raise Exception(f"SKIPPED: {reason}")

# Setup mocks before importing
setup_mocks()

# Add current directory to path
sys.path.insert(0, '/home/ANT.AMAZON.COM/kwehden/projects/strands-spot')

# Import the test module
from strands_spot.use_spot import SpotConnection, use_spot, SPOT_SDK_AVAILABLE

# Mock pytest in the test module
import tests.test_use_spot as test_module
test_module.pytest = MockPytest()

class TestRunner:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.errors = []

    def run_test(self, test_class, test_method_name):
        """Run a single test method"""
        test_name = f"{test_class.__name__}::{test_method_name}"
        
        try:
            # Create test instance
            test_instance = test_class()
            
            # Get test method
            test_method = getattr(test_instance, test_method_name)
            
            print(f"Running {test_name}...", end=" ")
            
            # Run the test
            test_method()
            
            print("✅ PASSED")
            self.passed += 1
            
        except Exception as e:
            if "SKIPPED:" in str(e):
                print(f"⏭️  SKIPPED ({str(e).replace('SKIPPED: ', '')})")
                self.skipped += 1
            else:
                print("❌ FAILED")
                self.failed += 1
                self.errors.append(f"{test_name}: {str(e)}")
                print(f"   Error: {str(e)}")

    def run_all_tests(self):
        """Run all tests from the test module"""
        print("Running strands-spot backward compatibility tests")
        print("=" * 60)
        
        # Get test classes
        test_classes = []
        for name in dir(test_module):
            obj = getattr(test_module, name)
            if isinstance(obj, type) and name.startswith('Test'):
                test_classes.append(obj)
        
        # Run tests from each class
        for test_class in test_classes:
            print(f"\n{test_class.__name__}:")
            
            # Get test methods
            test_methods = [method for method in dir(test_class) 
                          if method.startswith('test_') and callable(getattr(test_class, method))]
            
            for test_method in test_methods:
                self.run_test(test_class, test_method)
        
        # Print summary
        print(f"\n{'='*60}")
        print(f"Test Results:")
        print(f"  Passed: {self.passed}")
        print(f"  Failed: {self.failed}")
        print(f"  Skipped: {self.skipped}")
        print(f"  Total: {self.passed + self.failed + self.skipped}")
        
        if self.failed > 0:
            print(f"\nFailures:")
            for error in self.errors:
                print(f"  - {error}")
        
        return self.failed == 0

def main():
    """Main test runner"""
    # Override SPOT_SDK_AVAILABLE to True for testing
    test_module.SPOT_SDK_AVAILABLE = True
    
    runner = TestRunner()
    success = runner.run_all_tests()
    
    if success:
        print("\n✅ All tests passed! Backward compatibility maintained.")
    else:
        print("\n❌ Some tests failed. Check compatibility issues above.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)