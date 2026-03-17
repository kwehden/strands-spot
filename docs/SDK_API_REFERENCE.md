# Spot SDK API Reference

This document catalogs the Boston Dynamics Spot SDK APIs used by strands-spot and validates their signatures across SDK versions 4.x and 5.x.

## SDK Initialization Pattern

### Core Initialization Sequence
```python
# 1. Create SDK instance
sdk = bosdyn.client.create_standard_sdk("app_name")

# 2. Create robot connection
robot = sdk.create_robot(hostname)

# 3. Authenticate
robot.authenticate(username, password)

# 4. Time synchronization (required for commands)
robot.time_sync.wait_for_sync()
```

**API Signatures:**
- `create_standard_sdk(name: str) -> SDK`
- `SDK.create_robot(hostname: str) -> Robot`
- `Robot.authenticate(username: str, password: str) -> None`
- `Robot.time_sync.wait_for_sync(timeout_sec: float = 3.0) -> None`

## Service Client Resolution

### Pattern Used by strands-spot
```python
# Get service client by default service name
client = robot.ensure_client(service_name)
```

**API Signature:**
- `Robot.ensure_client(service_name: str) -> ServiceClient`

### Service Name Mappings
| strands-spot Service | SDK Service Name | Client Class |
|---------------------|------------------|--------------|
| robot_command | robot-command | RobotCommandClient |
| robot_state | robot-state | RobotStateClient |
| power | power | PowerClient |
| lease | lease | LeaseClient |
| image | image | ImageClient |
| estop | estop | EstopClient |
| time_sync | time-sync | TimeSyncClient |
| directory | directory | DirectoryClient |

## Service Client APIs

### RobotCommandClient
**Service Name:** `robot-command`  
**Import:** `from bosdyn.client.robot_command import RobotCommandClient`

**Methods Used:**
```python
# Execute robot command
robot_command(command, end_time_secs=None, timesync_endpoint=None) -> CommandResponse

# Async version
robot_command_async(command, end_time_secs=None, timesync_endpoint=None) -> Future
```

**Command Builders Used:**
```python
from bosdyn.client.robot_command import RobotCommandBuilder

# Stand command
RobotCommandBuilder.synchro_stand_command(footprint_R_body=None, body_height=None)

# Sit command  
RobotCommandBuilder.synchro_sit_command()

# Self-right command
RobotCommandBuilder.selfright_command()

# Velocity command
RobotCommandBuilder.synchro_velocity_command(v_x=0.0, v_y=0.0, v_rot=0.0)
```

### RobotStateClient
**Service Name:** `robot-state`  
**Import:** `from bosdyn.client.robot_state import RobotStateClient`

**Methods Used:**
```python
# Get current robot state
get_robot_state() -> RobotState

# Get robot metrics
get_robot_metrics() -> RobotMetrics
```

### PowerClient
**Service Name:** `power`  
**Import:** `from bosdyn.client.power import PowerClient`

**Methods Used:**
```python
# Power on robot
power_on(timeout_sec=20) -> PowerCommandResponse

# Power off robot
power_off(cut_immediately=False, timeout_sec=20) -> PowerCommandResponse
```

### LeaseClient
**Service Name:** `lease`  
**Import:** `from bosdyn.client.lease import LeaseClient, LeaseKeepAlive`

**Methods Used:**
```python
# Acquire lease
acquire(resource="body") -> LeaseUseResult

# Return lease
return_lease(lease) -> ReturnLeaseResponse

# List active leases
list_leases() -> ListLeasesResponse
```

**LeaseKeepAlive Context Manager:**
```python
LeaseKeepAlive(lease_client, must_acquire=True, return_at_exit=True)
```

### ImageClient
**Service Name:** `image`  
**Import:** `from bosdyn.client.image import ImageClient`

**Methods Used:**
```python
# List available image sources
list_image_sources() -> ListImageSourcesResponse

# Get images from sources
get_image_from_sources(image_sources: List[str]) -> List[ImageResponse]
```

### EstopClient
**Service Name:** `estop`  
**Import:** `from bosdyn.client.estop import EstopClient`

**Methods Used:**
```python
# Register estop endpoint
register_estop_endpoint(target_config_id, endpoint) -> RegisterEstopEndpointResponse

# Deregister estop endpoint
deregister_estop_endpoint() -> DeregisterEstopEndpointResponse
```

### TimeSyncClient
**Service Name:** `time-sync`  
**Import:** `from bosdyn.client.time_sync import TimeSyncClient`

**Methods Used:**
```python
# Get robot time range
get_robot_time_range_in_local_time() -> TimeRange

# Wait for time sync
wait_for_sync(timeout_sec=3.0) -> None
```

### DirectoryClient
**Service Name:** `directory`  
**Import:** `from bosdyn.client.directory import DirectoryClient`

**Methods Used:**
```python
# List available services
list() -> ListServiceEntriesResponse

# Get service entry
get_entry(service_name: str) -> ServiceEntry
```

## Lease Management Pattern

### Services Requiring Lease
The following services require an active lease for operation:
- `robot_command` - Motion control
- `power` - Power management
- `graph_nav` - Navigation
- `spot_check` - Diagnostics
- `manipulation` - Arm control
- `docking` - Charging operations
- `choreography` - Dance moves

### Lease Lifecycle Pattern
```python
# Acquire lease
lease_client = robot.ensure_client(LeaseClient.default_service_name)
lease_keepalive = LeaseKeepAlive(lease_client, must_acquire=True, return_at_exit=True)
lease_keepalive.__enter__()

try:
    # Perform operations requiring lease
    pass
finally:
    # Release lease
    lease_keepalive.__exit__(None, None, None)
```

## Error Handling

### Exception Types
```python
from bosdyn.client.exceptions import RpcError

# All SDK operations can raise RpcError
try:
    client.some_operation()
except RpcError as e:
    # Handle RPC communication errors
    pass
```

## Version Compatibility

### SDK 4.x vs 5.x Compatibility
Based on analysis of SDK versions 4.1.1 and 5.1.1:

**✅ IDENTICAL APIs:**
- All import paths unchanged
- All class names unchanged  
- All method signatures unchanged
- All service names unchanged
- All default service names unchanged
- Authentication flow unchanged
- Lease management unchanged
- Time synchronization unchanged

**📋 VALIDATION STATUS:**
- Import structure: ✅ Validated identical
- SDK initialization: ✅ Validated identical
- Service client classes: ✅ Validated identical
- Method signatures: ✅ Validated identical
- Authentication flow: ✅ Validated identical
- Lease management: ✅ Validated identical

### Version Detection
```python
# Simple version detection for metadata/logging
import bosdyn
sdk_version = bosdyn.__version__  # e.g., "4.5.2" or "5.1.1"
```

## Test Coverage

### APIs Validated by Test Harness
The test harness in `tests/test_sdk_api_harness.py` validates:

1. **SDK Initialization Pattern**
   - `create_standard_sdk()` function signature
   - `create_robot()` method signature  
   - `authenticate()` method signature
   - `time_sync.wait_for_sync()` method availability

2. **Service Client Constructors**
   - All service clients accept no required constructor arguments
   - All service clients have `default_service_name` class attribute

3. **Method Signatures**
   - RobotCommandClient: `robot_command()`, `robot_command_async()`
   - RobotStateClient: `get_robot_state()`, `get_robot_metrics()`
   - PowerClient: `power_on()`, `power_off()`
   - LeaseClient: `acquire()`, `return_lease()`, `list_leases()`
   - ImageClient: `list_image_sources()`, `get_image_from_sources()`
   - EstopClient: `register_estop_endpoint()`, `deregister_estop_endpoint()`
   - TimeSyncClient: `get_robot_time_range_in_local_time()`, `wait_for_sync()`
   - DirectoryClient: `list()`, `get_entry()`

4. **Service Resolution Pattern**
   - `robot.ensure_client()` method availability
   - Service name mapping correctness

5. **strands-spot Integration**
   - SERVICE_CLIENTS mapping completeness
   - Lease-required services identification

### Test Execution
```bash
# Run API validation tests
python tests/test_sdk_api_harness.py

# Run as part of test suite
python -m pytest tests/test_sdk_api_harness.py -v
```

## Implementation Notes

### Single Implementation Strategy
Since SDK 4.x and 5.x have identical APIs, strands-spot uses:
- Single `SpotConnection` class that works with both versions
- Version detection for logging/metadata only
- No version-specific code paths required
- Standard service client resolution works unchanged

### Future Version Considerations
For potential future SDK versions (6.x+) that may introduce breaking changes:
- Version validation can be extended in `version_detector.py`
- Conditional logic can be added if API differences emerge
- Current architecture supports easy extension without breaking changes

## References

- [Boston Dynamics Spot SDK Documentation](https://github.com/boston-dynamics/spot-sdk)
- [Spot SDK Python Examples](https://github.com/boston-dynamics/spot-sdk/tree/master/python/examples)
- [API Reference Documentation](https://dev.bostondynamics.com/python/bosdyn-client/src/bosdyn/client)