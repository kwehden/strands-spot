# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Strands Spot is a Python tool for controlling Boston Dynamics Spot robots through the Strands Agents framework. It provides atomic-level access to Spot SDK operations following a service-method pattern, similar to use_aws and use_google.

**Core Design Philosophy:**
- Single `use_spot` tool function that maps to Spot SDK service methods
- Environment-based credentials (SPOT_HOSTNAME, SPOT_USERNAME, SPOT_PASSWORD)
- Automatic lease management for operations requiring robot control
- LLM-friendly response format with image support for vision models

## Development Commands

### Testing
```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_use_spot.py -v

# Run with coverage
pytest tests/ -v --cov=strands_spot --cov-report=term-missing

# Run single test function
pytest tests/test_use_spot.py::TestSpotConnection::test_init -v
```

### Code Quality
```bash
# Format code with black
black strands_spot/ tests/ --line-length 100

# Lint with ruff
ruff check strands_spot/ tests/

# Type checking (optional, not configured by default)
mypy strands_spot/
```

### Building and Installation
```bash
# Install in development mode
pip install -e .

# Install with dev dependencies
pip install -e ".[dev]"

# Build package
python -m build

# Install from local build
pip install dist/strands_spot-*.whl
```

### Testing Utilities
```bash
# Test connection to robot
spotNetInfo --format json

# Use credential profile
spotNetInfo --profile myrobot

# Create credential profile
setSpotcon new myrobot
```

## Architecture

### Core Components

**use_spot.py** - Main tool implementation
- `use_spot()` function: Strands @tool decorator for agent integration
- `SpotConnection` class: Connection manager with environment-based credentials
- `SERVICE_CLIENTS` mapping: Maps service names to SDK client classes
- `LEASE_REQUIRED_SERVICES`: Services that need lease acquisition

**Service-Method Pattern:**
```python
use_spot(
    service="robot_command",  # Maps to RobotCommandClient
    method="stand",           # Maps to stand command builder
    params={}                 # Method-specific parameters
)
```

**credential_manager.py** - Profile management
- Stores credentials in `~/.spot/*.json` with 600 permissions
- Auto-generates profile names (spotCredentials0, spotCredentials1, ...)
- Updates last_used timestamp on profile load

**version_detector.py** - SDK version detection
- Thread-safe singleton with global caching
- Detects version from `bosdyn.__version__`
- Used for metadata/logging only (SDK 4.x and 5.x have identical APIs)

**CLI tools:**
- `setSpotcon`: Credential profile management (new, replace, add commands)
- `spotNetInfo`: Network diagnostics and connection testing

### SDK Version Compatibility

**Critical Design Decision:** SDK versions 4.x and 5.x have identical APIs.
- No version-specific code paths required
- Single SpotConnection implementation works for both versions
- Version detection serves metadata/logging purposes only
- See `spec/design.md` Section 2.4 for detailed compatibility analysis

### Connection Lifecycle

**Environment Variables (Required):**
- `SPOT_HOSTNAME`: Robot IP address (e.g., "192.168.80.3")
- `SPOT_USERNAME`: Robot username (optional if using credential profile)
- `SPOT_PASSWORD`: Robot password (optional if using credential profile)

**SpotConnection Pattern:**
```python
# Context manager (recommended)
with SpotConnection() as conn:
    conn.acquire_lease()
    # Do operations
    # Automatic cleanup on exit

# Manual management
conn = SpotConnection()
try:
    conn.acquire_lease()
    # Operations
finally:
    conn.close()  # Always releases lease
```

**Lease Management:**
- Services in `LEASE_REQUIRED_SERVICES` automatically acquire lease
- Uses `LeaseKeepAlive` context manager for automatic renewal
- `keep_lease=True` parameter retains lease across multiple `use_spot` calls
- Always released in `finally` block or context manager exit

### Response Format

The `use_spot` function returns a standardized format:
```python
{
    "status": "success|error",
    "content": [
        {"text": "Human-readable message"},
        {"image": {...}},  # For image service only
        {"json": {"response_data": {...}}},
        {"json": {"metadata": {...}}}
    ]
}
```

**Image Service Special Handling:**
- Images automatically extracted from protobuf responses
- Formatted as LLM-readable content blocks with `{"image": {"format": "jpeg", "source": {"bytes": <binary>}}}`
- Enables vision models to analyze Spot camera captures directly

### Error Handling

**Exception Hierarchy:**
- `RpcError`: Spot SDK communication errors (from bosdyn.client.exceptions)
- `ValueError`: Configuration errors (missing credentials, invalid service/method)
- `ConnectionError`: Connection establishment failures

**Error Response Format:**
```python
{
    "status": "error",
    "content": [
        {"text": "❌ Error message"},
        {"json": {"metadata": {"error_type": "...", ...}}}
    ]
}
```

## Testing Strategy

### Test Files Organization
- `test_use_spot.py`: Core functionality, connection, lease management
- `test_sdk_api_harness.py`: Validates SDK API signatures across versions
- `test_multi_version.py`: Multi-version compatibility tests
- `test_e2e.py`: End-to-end integration tests (requires real robot)

### Mocking Pattern
Tests use `unittest.mock` to avoid requiring real robot connections:
```python
@patch("strands_spot.use_spot.bosdyn.client.create_standard_sdk")
def test_something(mock_sdk):
    mock_robot = MagicMock()
    mock_sdk_instance = MagicMock()
    mock_sdk_instance.create_robot.return_value = mock_robot
    mock_sdk.return_value = mock_sdk_instance
    # Test code
```

### Environment Variable Management in Tests
Always clean up environment variables in teardown:
```python
def setup():
    os.environ['SPOT_HOSTNAME'] = 'test'

def teardown():
    for var in ['SPOT_HOSTNAME', 'SPOT_USERNAME', 'SPOT_PASSWORD']:
        if var in os.environ:
            del os.environ[var]
```

## Service Client Mappings

**Common Services:**
- `robot_command`: Motion control (stand, sit, velocity_command, self_right)
- `robot_state`: Status queries (get_robot_state, get_robot_metrics)
- `power`: Power management (power_on, power_off)
- `image`: Camera capture (list_image_sources, get_image_from_sources)
- `lease`: Resource management (acquire, release, list_leases)

**Lease Required:** robot_command, power, graph_nav, spot_check, manipulation, docking, choreography

See README.md for complete service list and method examples.

## Common Patterns

### Adding New Service Support
1. Add client class to `SERVICE_CLIENTS` mapping in use_spot.py
2. Add service name to `LEASE_REQUIRED_SERVICES` if it requires lease
3. Add tests in test_use_spot.py
4. Update README.md service table

### Adding Special Method Handling
Some methods (e.g., robot_command service) need special handling:
```python
def execute_robot_command_method(client, method, params):
    if method == "stand":
        cmd = RobotCommandBuilder.synchro_stand_command(**params)
        return client.robot_command(cmd)
    # ... other special cases
```

Add new special cases to `execute_robot_command_method()` or create new service-specific handlers.

### Protobuf Response Conversion
Responses are converted to dicts using `MessageToDict`:
```python
from google.protobuf.json_format import MessageToDict
response_data = MessageToDict(response, preserving_proto_field_name=True)
```

## Security Considerations

**Credential Storage:**
- Profiles stored in `~/.spot/` with directory permissions 700
- Individual profile files have permissions 600
- Passwords stored in plaintext (consider encryption for production use)

**Lease Management:**
- Always release leases to prevent robot lockout
- Use context managers for guaranteed cleanup
- Check `_lease_active` flag before operations

## Key Design Decisions

1. **Hostname moved to environment variable** - SpotConnection no longer accepts hostname parameter. Must use SPOT_HOSTNAME env var.

2. **Single SDK implementation** - No version-specific code paths. SDK 4.x and 5.x APIs are identical.

3. **Automatic lease management** - use_spot automatically acquires/releases leases based on service type.

4. **Strands agents integration** - @tool decorator makes use_spot directly usable by Strands agents for natural language robot control.

5. **LLM-friendly image format** - Images from camera captures are formatted as content blocks that vision models can consume directly.

## Bedrock LLM Configuration

This project uses AWS Bedrock for LLM integration with Strands agents.

**Verified Configuration:**
```python
from strands.models.bedrock import BedrockModel

model = BedrockModel(
    model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",  # On-demand model
    temperature=1.0,
    max_tokens=10000
)
```

**Available Models:**
- **On-demand (ready to use):** Claude 3.5 Sonnet v2, Claude 3.5 Haiku, Claude 3.5 Sonnet, Claude 3 Sonnet/Haiku
- **Requires inference profile:** Claude 4.6, Claude 4.5, Claude Opus 4.6, Claude Haiku 4.5

**Important:** Newer Claude 4.x models require an inference profile ARN configured in AWS Bedrock Console. Use Claude 3.5 Sonnet v2 for simplest setup.

**Testing:**
```bash
source .venv/bin/activate
python test_bedrock_access.py      # List available models
python test_strands_bedrock.py     # Test agent integration
```

## Documentation References

- `spec/design.md`: Detailed architecture and multi-version support design
- `docs/SDK_API_REFERENCE.md`: Complete API signatures and compatibility validation
- `README.md`: User-facing documentation and examples
- `test_bedrock_access.py`: Bedrock configuration test script
- `test_strands_bedrock.py`: Strands + Bedrock integration test
- `MIGRATION.md`: Migration guide for breaking changes (if exists)
