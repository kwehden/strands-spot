#!/usr/bin/env python3
"""
Simple test runner for Spot SDK API validation harness.

Usage:
    python3 run_api_tests.py
    ./run_api_tests.py
"""

import sys
import os

# Add the tests directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_sdk_api_harness import run_api_validation

def main():
    """Run API validation tests and report results"""
    print("🤖 Boston Dynamics Spot SDK API Validation")
    print("=" * 50)
    
    results = run_api_validation()
    
    print("\n" + "=" * 50)
    print("📊 VALIDATION SUMMARY")
    print("=" * 50)
    print(f"Tests executed: {results['tests_run']}")
    print(f"Failures: {results['failures']}")
    print(f"Errors: {results['errors']}")
    
    if results['success']:
        print("✅ ALL TESTS PASSED - SDK API signatures validated!")
        print("\n🎯 Validated APIs:")
        print("  • SDK initialization (create_standard_sdk, create_robot, authenticate)")
        print("  • Service client constructors and default_service_name attributes")
        print("  • RobotCommandClient (robot_command, robot_command_async)")
        print("  • RobotStateClient (get_robot_state, get_robot_metrics)")
        print("  • PowerClient (power_on, power_off)")
        print("  • LeaseClient (acquire, return_lease, list_leases)")
        print("  • ImageClient (list_image_sources, get_image_from_sources)")
        print("  • EstopClient (register_estop_endpoint, deregister_estop_endpoint)")
        print("  • TimeSyncClient (wait_for_sync, get_robot_time_range_in_local_time)")
        print("  • DirectoryClient (list, get_entry)")
        print("  • Service name mappings and lease-required services")
        return 0
    else:
        print("❌ TESTS FAILED - API validation issues detected!")
        return 1

if __name__ == "__main__":
    sys.exit(main())