#!/usr/bin/env python3
"""
Context Manager Usage Example

Demonstrates using SpotConnection as a context manager for guaranteed cleanup.
Shows proper resource management patterns.
"""

import os
from strands_spot import SpotConnection

def main():
    # Check environment variables
    if not all([os.getenv("SPOT_HOSTNAME"), os.getenv("SPOT_USERNAME"), os.getenv("SPOT_PASSWORD")]):
        print("❌ Missing environment variables. Set:")
        print("   export SPOT_HOSTNAME=192.168.80.3")
        print("   export SPOT_USERNAME=admin")
        print("   export SPOT_PASSWORD=password")
        return
    
    print("🦆 Context Manager Example")
    print("=" * 30)
    
    # Using context manager ensures proper cleanup
    try:
        with SpotConnection() as conn:
            print(f"✅ Connected to robot at {conn.hostname}")
            
            # Acquire lease for robot control
            conn.acquire_lease()
            print("✅ Lease acquired")
            
            # Get robot state client
            robot_state_client = conn.get_client("robot_state")
            robot_state = robot_state_client.get_robot_state()
            
            power_state = robot_state.power_state
            print(f"   Motor power: {power_state.motor_power_state}")
            print(f"   Battery: {robot_state.battery_states[0].charge_percentage.value:.1f}%")
            
            # Get robot command client
            robot_command_client = conn.get_client("robot_command")
            
            # Stand command
            from bosdyn.client.robot_command import RobotCommandBuilder
            stand_command = RobotCommandBuilder.synchro_stand_command()
            robot_command_client.robot_command(stand_command)
            print("✅ Stand command sent")
            
            # Context manager will automatically:
            # 1. Release lease
            # 2. Clean up connection
            print("✅ Operations completed, cleaning up...")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("✅ Context manager example completed!")
    print("   (Lease automatically released and connection cleaned up)")

if __name__ == "__main__":
    main()