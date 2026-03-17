# Migration Guide

## Overview

This guide covers migrating from earlier versions of strands-spot to the latest version with multi-version SDK support and new features.

## Breaking Changes

### None - Fully Backward Compatible

The latest version maintains full backward compatibility. All existing code will continue to work without modification.

## New Features Available

### 1. Environment Variable Support

**Before:**
```python
use_spot(
    hostname="192.168.80.3",
    username="admin", 
    password="password",
    service="robot_command",
    method="stand"
)
```

**After (optional improvement):**
```bash
# Set once
export SPOT_HOSTNAME="192.168.80.3"
export SPOT_USERNAME="admin"
export SPOT_PASSWORD="password"
```

```python
# Use anywhere without parameters
use_spot(service="robot_command", method="stand")
```

### 2. Context Manager Support

**New capability:**
```python
from strands_spot import SpotConnection

with SpotConnection() as conn:
    conn.acquire_lease()
    # Robot operations
    # Automatic cleanup on exit
```

### 3. Credential Profiles

**New CLI utilities:**
```bash
# Create profiles
setSpotcon new production
setSpotcon new development

# Use profiles
spotNetInfo --profile production
```

### 4. Network Diagnostics

**New utility:**
```bash
spotNetInfo                    # Basic network info
spotNetInfo --format json      # JSON output
spotNetInfo --profile myrobot  # Use profile
```

## Recommended Migration Steps

### Step 1: Update Environment (Optional)

Set environment variables for convenience:
```bash
export SPOT_HOSTNAME="192.168.80.3"
export SPOT_USERNAME="admin"
export SPOT_PASSWORD="password"
```

### Step 2: Simplify Code (Optional)

Remove redundant hostname/username/password parameters:

```python
# Before
use_spot(hostname="192.168.80.3", username="admin", password="pass", 
         service="robot_command", method="stand")

# After (if env vars set)
use_spot(service="robot_command", method="stand")
```

### Step 3: Use Context Manager (Optional)

For direct SDK access, consider using context manager:

```python
# New pattern for advanced usage
with SpotConnection() as conn:
    robot_state_client = conn.get_client("robot_state")
    robot_command_client = conn.get_client("robot_command")
    # Direct SDK calls
```

### Step 4: Create Profiles (Optional)

For multiple robots:
```bash
setSpotcon new robot1
setSpotcon new robot2
```

## No Action Required

- **Existing code continues to work unchanged**
- **All parameters still accepted**
- **No functionality removed**
- **Same API surface**

## Benefits of Migration

1. **Cleaner code** - Fewer parameters needed
2. **Better security** - Credentials in environment/profiles
3. **Multiple robots** - Easy switching with profiles
4. **Resource management** - Context manager ensures cleanup
5. **Diagnostics** - Built-in network testing tools

## Support

All versions of the Spot SDK (4.0.0+) are supported with the same API. No code changes needed for SDK version differences.