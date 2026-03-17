#!/usr/bin/env python3
"""
Credential Profile Usage Example

Demonstrates using credential profiles with setSpotcon and spotNetInfo utilities.
Shows profile creation, usage, and integration with main system.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from strands_spot.cli.setSpotcon import SpotCredentialManager
from strands_spot.cli.spotNetInfo import SpotNetworkDiagnostic
from strands_spot import SpotConnection

def create_example_profile():
    """Create an example credential profile"""
    print("\n📋 Creating Example Profile")
    print("-" * 30)
    
    manager = SpotCredentialManager()
    
    # Create profile with example credentials
    print("Creating profile 'example_robot'...")
    
    # Simulate user input for profile creation
    test_credentials = {
        "hostname": "192.168.80.3",
        "username": "admin", 
        "password": "password",
        "created": "2024-01-01T00:00:00",
        "last_used": None
    }
    
    # Save profile directly (simulating setSpotcon)
    manager._save_profile("example_robot", test_credentials)
    print("✅ Profile 'example_robot' created")
    
    return "example_robot"

def use_profile_with_connection(profile_name):
    """Use profile with SpotConnection"""
    print(f"\n📋 Using Profile '{profile_name}' with SpotConnection")
    print("-" * 50)
    
    try:
        manager = SpotCredentialManager()
        credentials = manager.load_profile(profile_name)
        
        # Set environment variables from profile
        os.environ["SPOT_HOSTNAME"] = credentials["hostname"]
        os.environ["SPOT_USERNAME"] = credentials["username"]
        os.environ["SPOT_PASSWORD"] = credentials["password"]
        
        print(f"✅ Loaded profile credentials:")
        print(f"   Hostname: {credentials['hostname']}")
        print(f"   Username: {credentials['username']}")
        print(f"   Created: {credentials['created']}")
        
        # Use with SpotConnection (would connect if robot available)
        print("\n🔗 Creating connection with profile credentials...")
        try:
            conn = SpotConnection()
            print(f"✅ Connection created for {conn.hostname}")
            conn.close()
        except Exception as e:
            print(f"ℹ️  Connection would work with real robot: {e}")
            
    except Exception as e:
        print(f"❌ Profile usage failed: {e}")

def use_profile_with_network_diagnostic(profile_name):
    """Use profile with network diagnostic utility"""
    print(f"\n📋 Using Profile '{profile_name}' with Network Diagnostics")
    print("-" * 55)
    
    try:
        manager = SpotCredentialManager()
        credentials = manager.load_profile(profile_name)
        
        # Set environment from profile (simulating spotNetInfo --profile)
        os.environ["SPOT_HOSTNAME"] = credentials["hostname"]
        os.environ["SPOT_USERNAME"] = credentials["username"]
        os.environ["SPOT_PASSWORD"] = credentials["password"]
        
        print(f"✅ Profile loaded for network diagnostics")
        print(f"   Would connect to: {credentials['hostname']}")
        
        # Simulate network diagnostic (would work with real robot)
        print("ℹ️  Network diagnostic would run: spotNetInfo --profile example_robot")
        
    except Exception as e:
        print(f"❌ Network diagnostic setup failed: {e}")

def list_available_profiles():
    """List all available credential profiles"""
    print("\n📋 Available Credential Profiles")
    print("-" * 35)
    
    try:
        manager = SpotCredentialManager()
        spot_dir = manager.spot_dir
        
        if not spot_dir.exists():
            print("   No profiles directory found")
            return
        
        profiles = list(spot_dir.glob("*.json"))
        
        if not profiles:
            print("   No profiles found")
            return
        
        for profile_path in profiles:
            profile_name = profile_path.stem
            try:
                credentials = manager.load_profile(profile_name)
                print(f"   📁 {profile_name}")
                print(f"      Hostname: {credentials['hostname']}")
                print(f"      Username: {credentials['username']}")
                print(f"      Created: {credentials.get('created', 'unknown')}")
                print(f"      Last used: {credentials.get('last_used', 'never')}")
            except Exception as e:
                print(f"   📁 {profile_name} (error loading: {e})")
                
    except Exception as e:
        print(f"❌ Failed to list profiles: {e}")

def demonstrate_cli_commands():
    """Demonstrate CLI command usage"""
    print("\n📋 CLI Command Examples")
    print("-" * 25)
    
    print("Create new profile:")
    print("   setSpotcon new myrobot")
    print("   setSpotcon new          # Auto-generates name")
    
    print("\nReplace existing profile:")
    print("   setSpotcon replace myrobot")
    
    print("\nUse profile with network diagnostics:")
    print("   spotNetInfo --profile myrobot")
    print("   spotNetInfo --profile myrobot --format json")
    
    print("\nUse profile with Python:")
    print("   # Load profile and set environment")
    print("   manager = SpotCredentialManager()")
    print("   creds = manager.load_profile('myrobot')")
    print("   os.environ['SPOT_HOSTNAME'] = creds['hostname']")
    print("   # Then use SpotConnection() or use_spot()")

def main():
    print("🦆 Credential Profile Usage Examples")
    print("=" * 40)
    
    # Show current profiles
    list_available_profiles()
    
    # Create example profile
    profile_name = create_example_profile()
    
    # Show updated profile list
    list_available_profiles()
    
    # Use profile with different components
    use_profile_with_connection(profile_name)
    use_profile_with_network_diagnostic(profile_name)
    
    # Show CLI examples
    demonstrate_cli_commands()
    
    print("\n✅ Credential profile examples completed!")
    print("\n💡 Profile Benefits:")
    print("   - Secure credential storage in ~/.spot/")
    print("   - Multiple robot configurations")
    print("   - Integration with CLI utilities")
    print("   - Auto-numbered naming (spotCredentials0, spotCredentials1, ...)")

if __name__ == "__main__":
    main()