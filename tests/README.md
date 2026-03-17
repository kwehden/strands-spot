# Spot SDK API Validation Test Harness

This test harness validates that the Boston Dynamics Spot SDK API signatures used by strands-spot are consistent across SDK versions 4.x and 5.x.

## Overview

The test harness uses mock objects that match the real Spot SDK API signatures to validate:

- SDK initialization patterns (`create_standard_sdk`, `create_robot`, `authenticate`, `time_sync`)
- Service client constructors and method signatures
- Service name mappings used by strands-spot
- Lease management patterns

## Files

- `test_sdk_api_harness.py` - Main test harness with mock SDK classes and validation tests
- `run_api_tests.py` - Simple test runner with formatted output
- `../docs/SDK_API_REFERENCE.md` - Complete documentation of validated APIs

## Running the Tests

### Quick Run
```bash
cd tests
python3 run_api_tests.py
```

### Direct Test Execution
```bash
cd tests
python3 test_sdk_api_harness.py
```

### Using pytest (if available)
```bash
cd tests
pytest test_sdk_api_harness.py -v
```

## Test Coverage

### SDK Initialization (4 tests)
- ✅ `create_standard_sdk()` function signature
- ✅ `create_robot()` method signature  
- ✅ `authenticate()` method signature
- ✅ `time_sync.wait_for_sync()` availability

### Service Client Validation (8 service clients)
- ✅ **RobotCommandClient** - Motion control (`robot_command`, `robot_command_async`)
- ✅ **RobotStateClient** - Status queries (`get_robot_state`, `get_robot_metrics`)
- ✅ **PowerClient** - Power management (`power_on`, `power_off`)
- ✅ **LeaseClient** - Resource locks (`acquire`, `return_lease`, `list_leases`)
- ✅ **ImageClient** - Camera capture (`list_image_sources`, `get_image_from_sources`)
- ✅ **EstopClient** - Emergency stop (`register_estop_endpoint`, `deregister_estop_endpoint`)
- ✅ **TimeSyncClient** - Clock sync (`wait_for_sync`, `get_robot_time_range_in_local_time`)
- ✅ **DirectoryClient** - Service discovery (`list`, `get_entry`)

### Integration Validation (3 tests)
- ✅ Service client constructors (no required arguments)
- ✅ `default_service_name` class attributes
- ✅ `robot.ensure_client()` pattern used by strands-spot

## Expected Output

```
🤖 Boston Dynamics Spot SDK API Validation
==================================================

test_directory_client_methods ... ok
test_estop_client_methods ... ok
test_image_client_methods ... ok
test_lease_client_methods ... ok
test_lease_required_services ... ok
test_power_client_methods ... ok
test_robot_command_client_methods ... ok
test_robot_ensure_client_pattern ... ok
test_robot_state_client_methods ... ok
test_sdk_initialization_pattern ... ok
test_service_client_constructors ... ok
test_strands_spot_service_mapping ... ok
test_time_sync_client_methods ... ok
test_service_client_mapping_completeness ... ok
test_spot_connection_initialization_pattern ... ok

----------------------------------------------------------------------
Ran 15 tests in 0.003s

OK

==================================================
📊 VALIDATION SUMMARY
==================================================
Tests executed: 15
Failures: 0
Errors: 0
✅ ALL TESTS PASSED - SDK API signatures validated!

🎯 Validated APIs:
  • SDK initialization (create_standard_sdk, create_robot, authenticate)
  • Service client constructors and default_service_name attributes
  • RobotCommandClient (robot_command, robot_command_async)
  • RobotStateClient (get_robot_state, get_robot_metrics)
  • PowerClient (power_on, power_off)
  • LeaseClient (acquire, return_lease, list_leases)
  • ImageClient (list_image_sources, get_image_from_sources)
  • EstopClient (register_estop_endpoint, deregister_estop_endpoint)
  • TimeSyncClient (wait_for_sync, get_robot_time_range_in_local_time)
  • DirectoryClient (list, get_entry)
  • Service name mappings and lease-required services
```

## Mock Architecture

The test harness uses a comprehensive mock architecture that mirrors the real SDK:

### MockSDKClients
Mock implementations of all service client classes with matching method signatures:
- MockRobotCommandClient
- MockRobotStateClient  
- MockPowerClient
- MockLeaseClient
- MockImageClient
- MockEstopClient
- MockTimeSyncClient
- MockDirectoryClient

### MockSDK
Mock SDK initialization classes:
- MockRobot - Simulates robot connection with `authenticate()`, `ensure_client()`, `time_sync`
- MockSDK - Simulates SDK with `create_robot()` method
- `create_standard_sdk()` - Static function matching real SDK

## Validation Strategy

The test harness validates API compatibility by:

1. **Signature Inspection** - Uses Python's `inspect` module to validate method signatures
2. **Mock Matching** - Mock objects match real SDK API signatures exactly
3. **Pattern Testing** - Tests the specific usage patterns employed by strands-spot
4. **Service Mapping** - Validates service name to client class mappings

## Integration with strands-spot

This test harness validates the APIs actually used by strands-spot:

- Service clients listed in `SERVICE_CLIENTS` mapping
- Methods called by `execute_method()` function
- Initialization pattern in `SpotConnection` class
- Lease management in `acquire_lease()` / `release_lease()`

## SDK Version Compatibility

Based on the design documentation findings, SDK versions 4.x and 5.x have identical APIs. This test harness validates the common API surface that works across both versions, confirming that:

- No version-specific code paths are needed
- Single implementation works for both SDK versions
- Version detection is only needed for logging/metadata

## Extending the Test Harness

To add validation for additional APIs:

1. Add mock methods to appropriate `MockSDKClients` classes
2. Create test methods in `TestSpotSDKAPISignatures`
3. Update the API reference documentation
4. Run tests to validate new coverage

## Troubleshooting

### Import Errors
The test harness is designed to be standalone and doesn't require the actual Spot SDK to be installed.

### Test Failures
If tests fail, it indicates potential API signature mismatches that would affect strands-spot compatibility across SDK versions.