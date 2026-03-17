# Design: Multi-Version Spot SDK Support Retrofit

## 1. Overview

This design retrofits the existing strands-spot package to support multiple Boston Dynamics Spot SDK versions (4.0.0+ through 5.x+) while preserving the current SpotConnection API and use_spot function pattern. Based on research findings that SDK v4.x and v5.x have identical APIs, the implementation uses simple version detection for metadata/logging purposes only, with a single SpotConnection class that works unchanged across both SDK versions.

## 2. Architecture Components

### 2.1 Version Detection Module (`version_detector.py`)

```python
class SDKVersionDetector:
    _cached_version = None
    _detection_lock = threading.Lock()
    
    @classmethod
    def detect_version(cls) -> str:
        """Detect installed SDK version with global caching (<100ms, thread-safe)"""
        
    @classmethod  
    def validate_version(cls, version: str) -> bool:
        """Validate version format and support"""
```

**Responsibilities:**
- Auto-detect installed SDK version by importing and checking `bosdyn.__version__`
- Cache results globally with thread-safe singleton pattern
- Validate version format (X.Y.Z) and support range (4.0.0+)
- Complete detection within 100ms requirement
- Used for logging and metadata purposes only

### 2.2 Simplified SpotConnection (`use_spot.py`)

```python
class SpotConnection:
    def __init__(self, username: str = None, password: str = None, 
                 sdk_version: str = None):
        """Single implementation that works with both SDK 4.x and 5.x"""
        
        # Version detection for metadata/logging only
        self._sdk_version = sdk_version or self._detect_version()
        
        # Standard initialization works for both versions
        self.sdk = bosdyn.client.create_standard_sdk("strands_spot")
        self.robot = self.sdk.create_robot(self.hostname)
        self.robot.authenticate(self.username, self.password)
        self.robot.time_sync.wait_for_sync()
        
        # Log detected version for diagnostics
        logger.info(f"Connected using Spot SDK v{self._sdk_version}")
    
    def __enter__(self):
        """Context manager entry - establish connection and time sync"""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensure proper cleanup"""
        self.close()
```

**Responsibilities:**
- Environment-based credential loading (SPOT_USERNAME, SPOT_PASSWORD env vars)
- Context manager support for guaranteed resource cleanup
- Single implementation works unchanged across SDK 4.x and 5.x versions
- Version detection serves only informational/diagnostic purposes
- Preserve existing SpotConnection public API surface

### 2.4 SDK Version Differences

**CRITICAL FINDING: Minimal API Differences Between SDK v4.1.1 and v5.1.1**

After comprehensive research into Boston Dynamics Spot SDK versions v4.1.1 and v5.1.1, the analysis reveals **minimal to no breaking API changes** that would necessitate the complex version-aware architecture originally proposed.

#### 2.4.1 API Compatibility Analysis

**Import Structure (IDENTICAL):**
```python
# Both v4.1.1 and v5.1.1 use identical imports
import bosdyn.client
import bosdyn.api  
import bosdyn.core
from bosdyn.client.robot_command import RobotCommandClient
from bosdyn.client.robot_state import RobotStateClient
from bosdyn.client.power import PowerClient
from bosdyn.client.lease import LeaseClient, LeaseKeepAlive
# ... all other service clients identical
```

**SDK Initialization (NO CHANGES):**
```python
# Same pattern for both versions
sdk = bosdyn.client.create_standard_sdk("app_name")
robot = sdk.create_robot(hostname)
robot.authenticate(username, password)
robot.time_sync.wait_for_sync()
```

**Service Client Classes (NO CHANGES):**
- Class names: RobotCommandClient, RobotStateClient, PowerClient, etc. - identical
- Import locations: bosdyn.client.robot_command, bosdyn.client.robot_state, etc. - identical  
- Method signatures: All core operations maintain same signatures
- Default service names: All `.default_service_name` properties unchanged

**Authentication Flow (NO CHANGES):**
- `robot.authenticate(username, password)` - identical signature and behavior
- Credential handling patterns - no changes

**Lease Management APIs (NO CHANGES):**
- LeaseClient class and methods - identical
- LeaseKeepAlive context manager - identical API
- Lease acquisition/release patterns - no changes

**Network Service APIs (NO CHANGES):**
- Network service client for spotNetInfo utility - identical
- Network interface querying methods - same signatures
- Response formats - consistent between versions

**Time Synchronization (NO CHANGES):**
- `robot.time_sync.wait_for_sync()` - identical pattern
- Time sync client APIs - no changes

#### 2.4.2 Architecture Impact Assessment

**Original Design Assumptions (INVALIDATED):**
- Need for version-specific SERVICE_CLIENTS mappings - **NOT REQUIRED**
- SpotConnectionV4 vs SpotConnectionV5 subclasses - **NOT NECESSARY**
- Complex version-aware service client routing - **UNNECESSARY COMPLEXITY**
- Factory pattern for version-specific implementations - **OVERENGINEERED**

**Actual Requirements:**
- Simple version detection for logging/metadata purposes
- Existing strands-spot implementation works with both versions unchanged
- No API compatibility layer needed

#### 2.4.3 Simplified Version Handling

Given the minimal differences, the version-aware architecture reduces to simple version detection:

```python
class SpotConnection:
    def __init__(self, username=None, password=None, sdk_version=None):
        # Version detection for metadata/logging only
        self._sdk_version = sdk_version or self._detect_version()
        
        # Standard initialization works for both versions
        self.sdk = bosdyn.client.create_standard_sdk("strands_spot")
        self.robot = self.sdk.create_robot(self.hostname)
        self.robot.authenticate(self.username, self.password)
        self.robot.time_sync.wait_for_sync()
        
        # Log detected version for diagnostics
        logger.info(f"Connected using Spot SDK v{self._sdk_version}")
    
    def _detect_version(self) -> str:
        """Simple version detection for metadata"""
        try:
            import bosdyn
            return bosdyn.__version__
        except (ImportError, AttributeError):
            return "unknown"
    
    def get_client(self, service: str):
        """Standard service client resolution - works for both versions"""
        client_class = SERVICE_CLIENTS.get(service)
        if not client_class:
            raise ValueError(f"Unknown service: {service}")
        return self.robot.ensure_client(client_class.default_service_name)
```

#### 2.4.4 Version-Specific Considerations

**SDK v4.1.1 Specific:**
- All current strands-spot functionality works without modification
- No special handling required for any service clients
- Standard authentication and lease management patterns apply

**SDK v5.1.1 Specific:**  
- Identical API surface to v4.1.1 for all core functionality
- No breaking changes in service client interfaces
- Same protobuf message formats and response structures

**Cross-Version Compatibility:**
- Single codebase supports both versions seamlessly
- No conditional logic required based on version
- Version detection serves only informational/diagnostic purposes

#### 2.4.5 Future Version Considerations

While v4.1.1 to v5.1.1 shows minimal changes, future major versions (e.g., SDK v6.x) may introduce breaking changes. The simplified approach allows for easy extension:

```python
def _validate_sdk_compatibility(self, version: str):
    """Future-proofing for potential breaking changes"""
    major_version = int(version.split('.')[0])
    
    if major_version < 4:
        raise ValueError(f"SDK v{version} not supported. Minimum: v4.0.0")
    elif major_version >= 6:
        logger.warning(f"SDK v{version} not tested. Compatibility not guaranteed.")
```

#### 2.4.6 Design Decision

**RECOMMENDATION: Adopt Simplified Version Detection**

Based on the research findings, the complex version-aware architecture should be **significantly simplified** to:

1. **Simple version detection** for logging and metadata
2. **Single SpotConnection implementation** that works with both SDK versions
3. **Standard service client mapping** without version-specific routing
4. **Preserve existing API** with minimal changes

This approach provides the requested version awareness while avoiding unnecessary complexity for API differences that don't actually exist between these specific SDK versions.

## 3. Implementation Strategy

### 3.1 Minimal Changes to Existing Code

**Modified Files:**
- `strands_spot/use_spot.py` - Add version parameter to SpotConnection constructor, add simple version detection
- `strands_spot/__init__.py` - Export new version detection utilities

**New Files:**
- `strands_spot/version_detector.py` - Simple version detection logic for metadata/logging

### 3.2 SpotConnection API Extension

```python
class SpotConnection:
    def __init__(self, username: str = None, password: str = None, 
                 sdk_version: str = None):
        """
        Initialize connection to Spot robot
        
        Args:
            username: Robot username (defaults to SPOT_USERNAME env var)
            password: Robot password (defaults to SPOT_PASSWORD env var)
            sdk_version: Optional SDK version (e.g., "4.5.2", "5.0.1")
                        If None, auto-detects installed version for logging only
        
        Environment Variables:
            SPOT_HOSTNAME: Robot IP or hostname (REQUIRED)
            SPOT_USERNAME: Robot username (optional if username provided)
            SPOT_PASSWORD: Robot password (optional if password provided)
        """
```

**Breaking Change:** hostname parameter removed - SPOT_HOSTNAME environment variable is now required.
**Environment Credentials:** All connection parameters now support environment variable fallback.

### 3.3 Simplified Version Detection Flow

```
SpotConnection.__init__()
├── sdk_version provided?
│   ├── Yes → SDKVersionDetector.validate_version()
│   └── No → SDKVersionDetector.detect_version()
├── Log detected version for diagnostics
└── Initialize with standard SDK imports (works for both 4.x and 5.x)
```

### 3.4 Service Client Resolution (Unchanged)

```python
def get_client(self, service: str):
    """Get service client by name - works unchanged across SDK versions"""
    client_class = SERVICE_CLIENTS.get(service)
    if not client_class:
        raise ValueError(f"Unknown service: {service}")
    
    # Standard client resolution works for both SDK versions
    return self.robot.ensure_client(client_class.default_service_name)
```

## 4. Credential Management Utility

### 4.1 setSpotcon CLI Tool

The `setSpotcon` utility manages credential profiles stored in the `~/.spot/` directory, providing secure storage and management of robot connection credentials.

```bash
# Create new profile (interactive prompts)
setSpotcon new [profile_name]

# Replace existing profile
setSpotcon replace <profile_name>

# Add additional profile
setSpotcon add [profile_name]
```

**Profile Naming:**
- User-provided: `setSpotcon new myrobot` → `~/.spot/myrobot.json`
- Auto-generated: `setSpotcon new` → `~/.spot/spotCredentials0.json`, `~/.spot/spotCredentials1.json`, etc.

### 4.2 Credential File Format

Each profile is stored as a JSON file in `~/.spot/`:

```json
{
  "hostname": "192.168.80.3",
  "username": "admin",
  "password": "encrypted_password_hash",
  "created": "2024-01-15T10:30:00Z",
  "last_used": "2024-01-15T14:22:00Z"
}
```

**Security Features:**
- Passwords stored using bcrypt hashing
- File permissions set to 600 (owner read/write only)
- Directory permissions set to 700 (owner access only)

### 4.3 Profile Management

```python
class SpotCredentialManager:
    def __init__(self):
        self.credentials_dir = Path.home() / ".spot"
        self.credentials_dir.mkdir(mode=0o700, exist_ok=True)
    
    def create_profile(self, name: str = None) -> str:
        """Create new credential profile"""
        if name is None:
            name = self._generate_auto_name()
        
        profile_path = self.credentials_dir / f"{name}.json"
        if profile_path.exists():
            raise ValueError(f"Profile '{name}' already exists")
        
        return self._save_profile(name, self._prompt_credentials())
    
    def replace_profile(self, name: str) -> str:
        """Replace existing credential profile"""
        profile_path = self.credentials_dir / f"{name}.json"
        if not profile_path.exists():
            raise ValueError(f"Profile '{name}' not found")
        
        return self._save_profile(name, self._prompt_credentials())
    
    def _generate_auto_name(self) -> str:
        """Generate auto-incremented profile name"""
        existing = [f.stem for f in self.credentials_dir.glob("spotCredentials*.json")]
        numbers = [int(name.replace("spotCredentials", "")) for name in existing 
                  if name.startswith("spotCredentials") and name[15:].isdigit()]
        next_num = max(numbers, default=-1) + 1
        return f"spotCredentials{next_num}"
```

### 4.4 Integration with SpotConnection

The credential manager integrates seamlessly with SpotConnection through environment variables:

```python
class SpotConnection:
    def __init__(self, username: str = None, password: str = None, 
                 sdk_version: str = None, profile: str = None):
        """Initialize with credential profile support"""
        
        # Load from profile if specified
        if profile:
            credentials = SpotCredentialManager().load_profile(profile)
            os.environ["SPOT_HOSTNAME"] = credentials["hostname"]
            os.environ["SPOT_USERNAME"] = credentials["username"] 
            os.environ["SPOT_PASSWORD"] = credentials["password"]
        
        # Environment variables take precedence
        self.hostname = os.getenv("SPOT_HOSTNAME")
        self.username = username or os.getenv("SPOT_USERNAME")
        self.password = password or os.getenv("SPOT_PASSWORD")
        
        if not self.hostname:
            raise ValueError("SPOT_HOSTNAME environment variable required")
        if not self.username or not self.password:
            raise ValueError("Credentials required via parameters, environment vars, or profile")
```

### 4.5 Environment Variable Workflow

```bash
# Set credentials using setSpotcon
setSpotcon new production
# Prompts for: hostname, username, password
# Saves to ~/.spot/production.json

# Load profile into environment
export SPOT_PROFILE=production
# OR manually set environment variables
export SPOT_HOSTNAME=192.168.80.3
export SPOT_USERNAME=admin  
export SPOT_PASSWORD=secret

# SpotConnection automatically uses environment variables
python -c "from strands_spot import SpotConnection; conn = SpotConnection()"
```

### 4.6 Network Diagnostic Utility

The `spotNetInfo` utility provides network diagnostics for connected Spot robots, serving dual purposes as a network information tool and connection/SDK version compatibility tester.

```bash
# Basic network information
spotNetInfo

# Specify profile for connection
spotNetInfo --profile production

# JSON output format
spotNetInfo --format json
```

**Implementation Approach:**

```python
class SpotNetworkDiagnostic:
    def __init__(self, connection: SpotConnection):
        self.connection = connection
        self.network_client = connection.get_client("network")
    
    def get_network_info(self) -> Dict[str, Any]:
        """Query robot network interfaces using standard client resolution"""
        interfaces = self.network_client.get_network_interfaces()
        
        return {
            "robot_hostname": self.connection.hostname,
            "sdk_version": self.connection._sdk_version,
            "interfaces": [
                {
                    "name": iface.name,
                    "type": "wifi_onboard" if "wlan0" in iface.name else "wifi_client",
                    "ip_addresses": [addr.address for addr in iface.ip_addresses],
                    "mac_address": iface.mac_address,
                    "status": "up" if iface.is_up else "down"
                }
                for iface in interfaces.network_interfaces
            ]
        }
```

**CLI Implementation:**

```python
def main():
    parser = argparse.ArgumentParser(description="Spot robot network diagnostics")
    parser.add_argument("--profile", help="Credential profile name")
    parser.add_argument("--format", choices=["table", "json"], default="table")
    args = parser.parse_args()
    
    try:
        # Use SpotConnection with profile support
        if args.profile:
            os.environ["SPOT_PROFILE"] = args.profile
        
        with SpotConnection() as conn:
            diagnostic = SpotNetworkDiagnostic(conn)
            network_info = diagnostic.get_network_info()
            
            if args.format == "json":
                print(json.dumps(network_info, indent=2))
            else:
                print_table_format(network_info)
                
    except Exception as e:
        print(f"Connection failed: {e}")
        sys.exit(1)
```

**Output Format (Table):**
```
Spot Network Information
Robot: 192.168.80.3 (SDK v4.5.2)

Interface    Type          IP Address      MAC Address        Status
---------    ----          ----------      -----------        ------
wlan0        wifi_onboard  192.168.80.3    aa:bb:cc:dd:ee:ff  up
wlan1        wifi_client   10.0.1.150      ff:ee:dd:cc:bb:aa  up
```

**Output Format (JSON):**
```json
{
  "robot_hostname": "192.168.80.3",
  "sdk_version": "4.5.2",
  "interfaces": [
    {
      "name": "wlan0",
      "type": "wifi_onboard",
      "ip_addresses": ["192.168.80.3"],
      "mac_address": "aa:bb:cc:dd:ee:ff",
      "status": "up"
    },
    {
      "name": "wlan1", 
      "type": "wifi_client",
      "ip_addresses": ["10.0.1.150"],
      "mac_address": "ff:ee:dd:cc:bb:aa",
      "status": "up"
    }
  ]
}
```

**Integration Benefits:**
- Uses simplified SpotConnection that works across SDK 4.x/5.x versions
- Leverages environment-based credentials or credential profiles
- Serves as test utility for verifying connection establishment and SDK version detection
- Standard service client resolution works automatically across versions

**Error Handling:**
- Connection failures indicate credential or network issues
- Service client errors reveal SDK version compatibility problems
- Network service unavailability suggests robot firmware issues

## 5. Error Handling

### 4.1 Global Version Cache

```python
class SDKVersionDetector:
    _cached_version = None
    _detection_lock = threading.Lock()
    
    @classmethod
    def detect_version(cls) -> str:
        if cls._cached_version is not None:
            return cls._cached_version
            
        with cls._detection_lock:
            if cls._cached_version is not None:  # Double-check
                return cls._cached_version
                
            # Perform detection
            cls._cached_version = cls._detect_version_impl()
            return cls._cached_version
```

**Benefits:**
- First detection: <100ms
- Subsequent calls: <1ms (cached)
- Thread-safe for multi-threaded environments
- Global caching across all SpotConnection instances

### 4.2 Simple Version Cache

```python
class SDKVersionDetector:
    _cached_version = None
    _detection_lock = threading.Lock()
    
    @classmethod
    def detect_version(cls) -> str:
        if cls._cached_version is not None:
            return cls._cached_version
            
        with cls._detection_lock:
            if cls._cached_version is not None:  # Double-check
                return cls._cached_version
                
            # Perform detection
            cls._cached_version = cls._detect_version_impl()
            return cls._cached_version
```

**Benefits:**
- First detection: <100ms
- Subsequent calls: <1ms (cached)
- Thread-safe for multi-threaded environments
- Global caching across all SpotConnection instances

### 4.3 Connection Lifecycle Management

```python
class SpotConnection:
    def __init__(self, username: str = None, password: str = None, sdk_version: str = None):
        """Initialize with environment-based credentials and proper error handling"""
        self.hostname = os.getenv("SPOT_HOSTNAME")
        self.username = username or os.getenv("SPOT_USERNAME")
        self.password = password or os.getenv("SPOT_PASSWORD")
        self._lease_active = False
        self._connection_established = False
        self.lease_keepalive = None
        
        # Version detection for metadata/logging only
        self._sdk_version = sdk_version or self._detect_version()
        
        if not self.hostname:
            raise ValueError("SPOT_HOSTNAME environment variable required")
        if not self.username or not self.password:
            raise ValueError("Credentials required via parameters or SPOT_USERNAME/SPOT_PASSWORD env vars")
        
        self._establish_connection()
    
    def _establish_connection(self):
        """Establish SDK connection with proper error handling"""
        try:
            self.sdk = bosdyn.client.create_standard_sdk("strands_spot")
            self.robot = self.sdk.create_robot(self.hostname)
            self.robot.authenticate(self.username, self.password)
            self.robot.time_sync.wait_for_sync()
            self._connection_established = True
            logger.info(f"Connected using Spot SDK v{self._sdk_version}")
        except Exception as e:
            self.close()
            raise ConnectionError(f"Failed to establish connection: {e}")
    
    def close(self):
        """Guaranteed cleanup of all resources"""
        if self._lease_active:
            self.release_lease()
        self._connection_established = False
```

## 5. Caching Strategy & Connection Lifecycle

### 5.1 Global Version Cache

```python
class SDKVersionDetector:
    _cached_version = None
    _detection_lock = threading.Lock()
    
    @classmethod
    def detect_version(cls) -> str:
        if cls._cached_version is not None:
            return cls._cached_version
            
        with cls._detection_lock:
            if cls._cached_version is not None:  # Double-check
                return cls._cached_version
                
            # Perform detection
            cls._cached_version = cls._detect_version_impl()
            return cls._cached_version
```

**Benefits:**
- First detection: <100ms
- Subsequent calls: <1ms (cached)
- Thread-safe for multi-threaded environments
- Global caching across all SpotConnection instances

### 5.2 Service Client Mapping Cache

```python
_SERVICE_MAPPING_CACHE = {}

def get_service_clients(version: str) -> Dict[str, str]:
    if version not in _SERVICE_MAPPING_CACHE:
        _SERVICE_MAPPING_CACHE[version] = _load_service_mapping(version)
    return _SERVICE_MAPPING_CACHE[version]
```

### 5.3 Connection Lifecycle Management

```python

## 6. Error Handling

### 6.1 Version Validation Errors

```python
# Invalid version format
raise ValueError("Invalid version format. Expected 'X.Y.Z' (e.g., '4.5.2')")

# Unsupported version
raise ValueError("Unsupported SDK version. Supported: 4.0.0+ and 5.x series")

# Missing SDK installation  
raise ImportError("Spot SDK version 4.5.2 not found. Install with: pip install bosdyn-client==4.5.2")
```

### 6.2 Import Error Handling

```python
try:
    import bosdyn.client
    SPOT_SDK_AVAILABLE = True
    SDK_VERSION = bosdyn.__version__
except ImportError:
    SPOT_SDK_AVAILABLE = False
    SDK_VERSION = None
```

## 7. Logging Strategy

```python
# INFO level - Version detection results
logger.info(f"Detected Spot SDK version: {version}")
logger.info(f"Using explicit SDK version: {version}")

# DEBUG level - Service client selection
logger.debug(f"Selected {service} client for SDK v{version}: {client_class}")

# WARNING level - Deprecated versions
logger.warning(f"SDK version {version} is deprecated. Consider upgrading to 5.x")
```

## 8. Testing Strategy

### 8.1 Backward Compatibility Tests

- All existing tests in `tests/test_use_spot.py` must pass unchanged
- No modifications to existing test cases
- Tests validate that default behavior (no version specified) works

### 8.2 Version-Specific Tests

```python
def test_explicit_version_selection():
    """Test SpotConnection with explicit SDK version"""
    
def test_version_detection():
    """Test automatic version detection"""
    
def test_unsupported_version_error():
    """Test error handling for unsupported versions"""
```

## 9. Performance Requirements

- **Version Detection:** <100ms for first SpotConnection instantiation
- **Cached Access:** <1ms for subsequent instantiations  
- **Memory Overhead:** Minimal - single cached version string + service mappings
- **Thread Safety:** Lock-based synchronization for detection, lock-free for cached access

## 10. Extension Path for Future Versions

### 10.1 Adding SDK 6.x Support

If future SDK versions introduce breaking changes, the simplified approach allows easy extension:

1. Add version-specific logic in SpotConnection constructor
2. Implement conditional service client resolution if needed
3. Update version validation in `version_detector.py`
4. Minimal changes to public API required

### 10.2 Version-Specific Feature Support

```python
class SpotConnection:
    def new_v6_feature(self):
        """SDK 6.x specific feature with version check"""
        if self._sdk_version.startswith('6.'):
            # Implementation
        else:
            raise NotImplementedError("Feature requires SDK 6.x+")
    
    def _validate_sdk_compatibility(self, version: str):
        """Future-proofing for potential breaking changes"""
        major_version = int(version.split('.')[0])
        
        if major_version < 4:
            raise ValueError(f"SDK v{version} not supported. Minimum: v4.0.0")
        elif major_version >= 6:
            logger.warning(f"SDK v{version} not tested. Compatibility not guaranteed.")
```

## 11. Migration Path

### 11.1 Phase 1: Core Infrastructure
- Implement simple version detection module
- Add version parameter to SpotConnection constructor
- Add environment-based credential loading

### 11.2 Phase 2: Utilities
- Implement setSpotcon credential management utility
- Implement spotNetInfo network diagnostic utility
- Add context manager support

### 11.3 Phase 3: Testing & Validation
- Validate backward compatibility
- Performance testing for <100ms requirement
- Integration testing across SDK versions

## 12. Risk Mitigation

### 12.1 SDK API Breaking Changes
**Risk:** Minor version differences cause import failures
**Mitigation:** Version-specific service client mappings with fallback handling

### 12.2 Performance Degradation
**Risk:** Version detection adds latency
**Mitigation:** Global caching with <1ms cached access

### 12.3 Thread Safety Issues
**Risk:** Race conditions in multi-threaded environments
**Mitigation:** Thread-safe singleton pattern with double-checked locking

### 12.4 Connection Resource Leaks
**Risk:** Unclosed connections and unreleased leases in factory pattern
**Mitigation:** 
- Context manager support (`__enter__`/`__exit__`) for guaranteed cleanup
- Automatic lease release in `close()` method
- Exception handling in connection establishment

### 12.5 Lease Management Failures
**Risk:** Lease not properly acquired/released across version-specific implementations
**Mitigation:**
- Consistent lease lifecycle in base SpotConnection class
- LeaseKeepAlive context manager for automatic lease management
- Lease state tracking (`_lease_active`) across all subclasses

### 12.6 Authentication Failures in Non-Interactive Environments
**Risk:** Missing credentials in automated/CI environments
**Mitigation:**
- Environment variable fallback (SPOT_HOSTNAME, SPOT_USERNAME, SPOT_PASSWORD)
- Credential profile support via setSpotcon utility
- Clear error messages for missing credentials
- Validation at connection initialization

## 13. Resource Management

### 13.1 Connection Lifecycle Pattern

Following Boston Dynamics wasd example patterns for robust resource management:

```python
class SpotConnection:
    def __init__(self, username: str = None, password: str = None):
        """Initialize with graceful error handling and environment credentials"""
        self._lease_active = False
        self._connection_established = False
        self.lease_keepalive = None
        
        # Load from environment variables
        self.hostname = os.getenv("SPOT_HOSTNAME")
        self.username = username or os.getenv("SPOT_USERNAME")
        self.password = password or os.getenv("SPOT_PASSWORD")
        
        if not self.hostname:
            raise ValueError("SPOT_HOSTNAME environment variable required")
        if not self.username or not self.password:
            raise ValueError("Credentials required via parameters or SPOT_USERNAME/SPOT_PASSWORD env vars")
        
        self._establish_connection()
    
    def _establish_connection(self):
        """Establish connection with proper error handling"""
        try:
            self.sdk = bosdyn.client.create_standard_sdk("strands_spot")
            self.robot = self.sdk.create_robot(self.hostname)
            self.robot.authenticate(self.username, self.password)
            self.robot.time_sync.wait_for_sync()
            self._connection_established = True
        except Exception as e:
            self.close()
            raise ConnectionError(f"Connection failed: {e}")
    
    def acquire_lease(self):
        """Acquire lease with LeaseKeepAlive context manager"""
        if self._lease_active:
            return
        
        self.lease_client = self.robot.ensure_client(LeaseClient.default_service_name)
        self.lease_keepalive = LeaseKeepAlive(
            self.lease_client, 
            must_acquire=True, 
            return_at_exit=True
        )
        self.lease_keepalive.__enter__()
        self._lease_active = True
    
    def release_lease(self):
        """Release lease with proper cleanup"""
        if not self._lease_active or not self.lease_keepalive:
            return
        
        try:
            self.lease_keepalive.__exit__(None, None, None)
        finally:
            self._lease_active = False
            self.lease_keepalive = None
    
    def close(self):
        """Guaranteed resource cleanup"""
        if self._lease_active:
            self.release_lease()
        self._connection_established = False
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
```

### 13.2 Simplified Connection Management

```python
class SpotConnection:
    def __init__(self, username: str = None, password: str = None, sdk_version: str = None):
        """Create connection with version detection and environment credentials"""
        
        # Detect version if not specified (for logging/metadata only)
        self._sdk_version = sdk_version or self._detect_version()
        
        # Validate version
        if not SDKVersionDetector.validate_version(self._sdk_version):
            raise ValueError(f"Unsupported SDK version: {self._sdk_version}")
        
        # Standard initialization works for both SDK 4.x and 5.x
        self._establish_connection()
    
    def _detect_version(self) -> str:
        """Simple version detection for metadata"""
        try:
            import bosdyn
            return bosdyn.__version__
        except (ImportError, AttributeError):
            return "unknown"
```

### 13.3 Usage Patterns

**Context Manager Pattern (Recommended):**
```python
# Set environment variables first
os.environ["SPOT_HOSTNAME"] = "192.168.80.3"
os.environ["SPOT_USERNAME"] = "admin"
os.environ["SPOT_PASSWORD"] = "password"

with SpotConnection() as conn:
    conn.acquire_lease()
    client = conn.get_client("robot_command")
    # Operations...
    # Automatic cleanup on exit
```

**Manual Management:**
```python
# Environment variables already set
conn = SpotConnection()
try:
    conn.acquire_lease()
    # Operations...
finally:
    conn.close()  # Ensures lease release
```

### 13.4 Error Recovery

```python
def robust_connection_pattern():
    """Robust connection with retry and cleanup"""
    conn = None
    try:
        conn = SpotConnection()
        conn.acquire_lease()
        return conn
    except Exception as e:
        if conn:
            conn.close()
        raise ConnectionError(f"Failed to establish robust connection: {e}")
```

## 14. Success Criteria

- ✅ SpotConnection requires SPOT_HOSTNAME environment variable (hostname parameter removed)
- ✅ SpotConnection accepts optional `sdk_version` parameter for metadata/logging only
- ✅ Simple version detection when no version specified (used for logging/diagnostics)
- ✅ Single SpotConnection implementation works unchanged across SDK 4.x and 5.x versions
- ✅ Environment-based credential loading (SPOT_HOSTNAME, SPOT_USERNAME, SPOT_PASSWORD)
- ✅ setSpotcon utility for credential profile management
- ✅ Credential profiles stored in ~/.spot/ directory with proper security
- ✅ Profile naming: user-provided or auto-numbered spotCredentials[x]
- ✅ spotNetInfo utility for network diagnostics and connection testing
- ✅ Network utility reports IPs and MACs for onboard and client WiFi
- ✅ Context manager support for guaranteed resource cleanup
- ✅ Proper lease acquisition/release lifecycle
- ✅ All existing tests pass with minimal modification (environment variable setup)
- ✅ Version detection completes within 100ms
- ✅ Standard service client resolution works across SDK versions
- ✅ Clear error messages for unsupported versions
- ✅ Thread-safe operation in multi-threaded environments
- ✅ Simplified connection lifecycle without factory pattern complexity
- ✅ Robust error handling and recovery patterns
- ✅ No resource leaks in connection or lease management