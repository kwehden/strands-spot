#!/usr/bin/env python3
"""
Environment Variable Configuration Example

Shows different ways to configure credentials using environment variables.
Demonstrates precedence and fallback behavior.
"""

import os
from strands_spot import SpotConnection, use_spot

def example_1_env_vars_only():
    """Example 1: Using only environment variables"""
    print("\n📋 Example 1: Environment Variables Only")
    print("-" * 40)
    
    # Set environment variables
    os.environ["SPOT_HOSTNAME"] = "192.168.80.3"
    os.environ["SPOT_USERNAME"] = "admin"
    os.environ["SPOT_PASSWORD"] = "password"
    
    try:
        # No parameters needed - uses environment variables
        conn = SpotConnection()
        print(f"✅ Connected using env vars: {conn.hostname}")
        conn.close()
    except Exception as e:
        print(f"❌ Connection failed: {e}")

def example_2_mixed_params_env():
    """Example 2: Mixed parameters and environment variables"""
    print("\n📋 Example 2: Mixed Parameters and Environment")
    print("-" * 50)
    
    # Set some environment variables
    os.environ["SPOT_USERNAME"] = "admin"
    os.environ["SPOT_PASSWORD"] = "password"
    
    try:
        # Hostname as parameter, credentials from environment
        conn = SpotConnection(hostname="192.168.80.4")
        print(f"✅ Connected with mixed config: {conn.hostname}")
        print(f"   Username from env: {conn.username}")
        conn.close()
    except Exception as e:
        print(f"❌ Connection failed: {e}")

def example_3_parameter_override():
    """Example 3: Parameters override environment variables"""
    print("\n📋 Example 3: Parameter Override")
    print("-" * 35)
    
    # Set environment variables
    os.environ["SPOT_HOSTNAME"] = "192.168.80.3"
    os.environ["SPOT_USERNAME"] = "env_user"
    os.environ["SPOT_PASSWORD"] = "env_pass"
    
    try:
        # Parameters override environment variables
        conn = SpotConnection(
            hostname="192.168.80.5",
            username="param_user"
            # password still from environment
        )
        print(f"✅ Connected with overrides:")
        print(f"   Hostname (param): {conn.hostname}")
        print(f"   Username (param): {conn.username}")
        print(f"   Password (env): {conn.password}")
        conn.close()
    except Exception as e:
        print(f"❌ Connection failed: {e}")

def example_4_use_spot_env():
    """Example 4: Using use_spot with environment variables"""
    print("\n📋 Example 4: use_spot with Environment Variables")
    print("-" * 50)
    
    # Ensure environment is set
    os.environ["SPOT_HOSTNAME"] = "192.168.80.3"
    os.environ["SPOT_USERNAME"] = "admin"
    os.environ["SPOT_PASSWORD"] = "password"
    
    # No hostname/username/password parameters needed
    result = use_spot(
        service="robot_state",
        method="get_robot_state"
    )
    
    if result["status"] == "success":
        print("✅ use_spot worked with environment variables!")
        metadata = result["content"][2]["json"]["metadata"]
        print(f"   Robot: {metadata['robot']['hostname']}")
    else:
        print(f"❌ use_spot failed: {result['content'][0]['text']}")

def show_current_env():
    """Show current environment variable configuration"""
    print("\n🔍 Current Environment Configuration:")
    print("-" * 40)
    
    env_vars = ["SPOT_HOSTNAME", "SPOT_USERNAME", "SPOT_PASSWORD"]
    for var in env_vars:
        value = os.getenv(var, "Not set")
        # Mask password for security
        if var == "SPOT_PASSWORD" and value != "Not set":
            value = "*" * len(value)
        print(f"   {var}: {value}")

def main():
    print("🦆 Environment Variable Configuration Examples")
    print("=" * 50)
    
    show_current_env()
    
    # Run examples
    example_1_env_vars_only()
    example_2_mixed_params_env()
    example_3_parameter_override()
    example_4_use_spot_env()
    
    print("\n✅ Environment configuration examples completed!")
    print("\n💡 Best Practices:")
    print("   - Use environment variables for security")
    print("   - Set SPOT_HOSTNAME, SPOT_USERNAME, SPOT_PASSWORD")
    print("   - Parameters override environment variables")
    print("   - use_spot() works without any parameters when env vars are set")

if __name__ == "__main__":
    main()