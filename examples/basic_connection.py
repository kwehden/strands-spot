#!/usr/bin/env python3
"""
Basic Spot Connection Example

Demonstrates the simplest way to connect to and control a Spot robot.
Uses environment variables for credentials.
"""

import os
from strands_spot import use_spot

def main():
    # Check environment variables
    if not all([os.getenv("SPOT_HOSTNAME"), os.getenv("SPOT_USERNAME"), os.getenv("SPOT_PASSWORD")]):
        print("❌ Missing environment variables. Set:")
        print("   export SPOT_HOSTNAME=192.168.80.3")
        print("   export SPOT_USERNAME=admin")
        print("   export SPOT_PASSWORD=password")
        return
    
    print("🦆 Basic Spot Connection Example")
    print("=" * 40)
    
    # Get robot state (no lease required)
    print("\n1. Getting robot state...")
    result = use_spot(
        service="robot_state",
        method="get_robot_state"
    )
    
    if result["status"] == "success":
        print("✅ Connected successfully!")
        # Extract power state from response
        response_data = result["content"][1]["json"]["response_data"]
        power_state = response_data.get("power_state", {})
        print(f"   Motor power: {power_state.get('motor_power_state', 'unknown')}")
    else:
        print(f"❌ Connection failed: {result['content'][0]['text']}")
        return
    
    # Stand the robot
    print("\n2. Standing up...")
    result = use_spot(
        service="robot_command",
        method="stand"
    )
    
    if result["status"] == "success":
        print("✅ Robot is standing!")
    else:
        print(f"❌ Stand failed: {result['content'][0]['text']}")
    
    print("\n✅ Basic example completed!")

if __name__ == "__main__":
    main()