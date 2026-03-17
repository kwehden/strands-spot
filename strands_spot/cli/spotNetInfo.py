#!/usr/bin/env python3
"""
spotNetInfo - Network diagnostic utility for Spot robots

Queries robot network interfaces and serves as connection/SDK compatibility test.
"""

import argparse
import json
import os
import sys
from typing import Dict, Any, List

try:
    from ..use_spot import SpotConnection
    from ..credential_manager import SpotCredentialManager
except ImportError:
    # For standalone execution
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from use_spot import SpotConnection
    from credential_manager import SpotCredentialManager


class SpotNetworkDiagnostic:
    """Network diagnostic utility using SpotConnection"""
    
    def __init__(self, connection: SpotConnection):
        self.connection = connection
    
    def get_network_info(self) -> Dict[str, Any]:
        """Query robot network interfaces using robot state client"""
        try:
            # Get robot state client (contains network information)
            robot_state_client = self.connection.get_client("robot_state")
            
            # Get robot state which includes network information
            robot_state = robot_state_client.get_robot_state()
            
            # Extract network interfaces from robot state
            interfaces = []
            
            # Try multiple approaches to get network information
            network_found = False
            
            # Approach 1: Check if network_state exists in robot state
            if hasattr(robot_state, 'network_state') and robot_state.network_state:
                for interface in robot_state.network_state.network_interfaces:
                    interface_info = {
                        "name": interface.name,
                        "type": self._determine_interface_type(interface.name),
                        "ip_addresses": [addr.address for addr in interface.ip_addresses] if hasattr(interface, 'ip_addresses') else [],
                        "mac_address": interface.mac_address if hasattr(interface, 'mac_address') else "unknown",
                        "status": "up" if (hasattr(interface, 'is_up') and interface.is_up) else "unknown"
                    }
                    interfaces.append(interface_info)
                    network_found = True
            
            # Approach 2: Try system_state for network info
            if not network_found and hasattr(robot_state, 'system_state') and robot_state.system_state:
                # Some SDK versions may have network info in system state
                if hasattr(robot_state.system_state, 'network_interfaces'):
                    for interface in robot_state.system_state.network_interfaces:
                        interface_info = {
                            "name": getattr(interface, 'name', 'unknown'),
                            "type": self._determine_interface_type(getattr(interface, 'name', '')),
                            "ip_addresses": [addr.address for addr in getattr(interface, 'ip_addresses', [])] if hasattr(interface, 'ip_addresses') else [],
                            "mac_address": getattr(interface, 'mac_address', 'unknown'),
                            "status": "up" if getattr(interface, 'is_up', False) else "unknown"
                        }
                        interfaces.append(interface_info)
                        network_found = True
            
            # Approach 3: Try directory client to get service endpoints (may reveal network info)
            if not network_found:
                try:
                    directory_client = self.connection.get_client("directory")
                    services = directory_client.list()
                    
                    # Extract unique hostnames from service endpoints
                    hostnames = set()
                    for service in services:
                        if hasattr(service, 'host_ip') and service.host_ip:
                            hostnames.add(service.host_ip)
                    
                    for i, hostname in enumerate(sorted(hostnames)):
                        interfaces.append({
                            "name": f"service_endpoint_{i}",
                            "type": "service_network",
                            "ip_addresses": [hostname],
                            "mac_address": "unknown",
                            "status": "up"
                        })
                        network_found = True
                        
                except Exception:
                    pass  # Directory approach failed, continue to fallback
            
            # Fallback: Create basic interface info from connection
            if not network_found:
                interfaces.append({
                    "name": "robot_connection",
                    "type": "connection",
                    "ip_addresses": [self.connection.hostname],
                    "mac_address": "unknown",
                    "status": "up"
                })
            
            return {
                "robot_hostname": self.connection.hostname,
                "sdk_version": getattr(self.connection, '_sdk_version', 'unknown'),
                "connection_status": "connected",
                "interfaces": interfaces,
                "detection_method": "robot_state" if network_found else "fallback"
            }
            
        except Exception as e:
            # Return basic connection info on error
            return {
                "robot_hostname": self.connection.hostname,
                "sdk_version": getattr(self.connection, '_sdk_version', 'unknown'),
                "connection_status": "connected",
                "error": str(e),
                "interfaces": [{
                    "name": "robot_connection",
                    "type": "connection", 
                    "ip_addresses": [self.connection.hostname],
                    "mac_address": "unknown",
                    "status": "up"
                }],
                "detection_method": "error_fallback"
            }
    
    def _determine_interface_type(self, interface_name: str) -> str:
        """Determine interface type based on name"""
        name_lower = interface_name.lower()
        if 'wlan0' in name_lower or 'onboard' in name_lower:
            return "wifi_onboard"
        elif 'wlan' in name_lower or 'wifi' in name_lower:
            return "wifi_client"
        elif 'eth' in name_lower or 'ethernet' in name_lower:
            return "ethernet"
        elif 'service' in name_lower:
            return "service"
        elif 'connection' in name_lower:
            return "connection"
        else:
            return "unknown"


def print_table_format(network_info: Dict[str, Any]):
    """Print network information in table format"""
    print("Spot Network Information")
    print(f"Robot: {network_info['robot_hostname']} (SDK v{network_info['sdk_version']})")
    print(f"Status: {network_info['connection_status']}")
    
    if 'detection_method' in network_info:
        method = network_info['detection_method']
        if method == "robot_state":
            print("Detection: Robot state network interfaces")
        elif method == "fallback":
            print("Detection: Connection fallback (limited info)")
        elif method == "error_fallback":
            print("Detection: Error fallback (basic info only)")
    
    if 'error' in network_info:
        print(f"Warning: {network_info['error']}")
    
    print()
    print("Interface    Type          IP Address      MAC Address        Status")
    print("---------    ----          ----------      -----------        ------")
    
    for interface in network_info['interfaces']:
        name = interface['name'][:12]  # Truncate long names
        itype = interface['type'][:12]
        ip_addrs = ', '.join(interface['ip_addresses'][:2])  # Show first 2 IPs
        if len(interface['ip_addresses']) > 2:
            ip_addrs += "..."
        mac = interface['mac_address'][:17]  # Standard MAC length
        status = interface['status']
        
        print(f"{name:<12} {itype:<12} {ip_addrs:<15} {mac:<18} {status}")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Spot robot network diagnostics and connection test",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  spotNetInfo                    # Basic network info using env vars
  spotNetInfo --profile prod     # Use credential profile
  spotNetInfo --format json      # JSON output format

Environment Variables:
  SPOT_HOSTNAME - Robot IP address (required if no profile)
  SPOT_USERNAME - Robot username (required if no profile)  
  SPOT_PASSWORD - Robot password (required if no profile)
        """
    )
    
    parser.add_argument(
        "--profile", 
        help="Credential profile name from ~/.spot/"
    )
    parser.add_argument(
        "--format", 
        choices=["table", "json"], 
        default="table",
        help="Output format (default: table)"
    )
    
    args = parser.parse_args()
    
    try:
        # Load profile if specified
        if args.profile:
            try:
                manager = SpotCredentialManager()
                credentials = manager.load_profile(args.profile)
                
                # Set environment variables from profile
                os.environ["SPOT_HOSTNAME"] = credentials["hostname"]
                os.environ["SPOT_USERNAME"] = credentials["username"]
                os.environ["SPOT_PASSWORD"] = credentials["password"]
                
            except FileNotFoundError:
                print(f"Error: Profile '{args.profile}' not found", file=sys.stderr)
                print("Available profiles:", file=sys.stderr)
                try:
                    spot_dir = SpotCredentialManager().spot_dir
                    profiles = [f.stem for f in spot_dir.glob("*.json")]
                    for profile in sorted(profiles):
                        print(f"  {profile}", file=sys.stderr)
                except Exception as e:
                    print(f"  (Could not list profiles: {e})", file=sys.stderr)
                sys.exit(1)
            except Exception as e:
                print(f"Error loading profile: {e}", file=sys.stderr)
                sys.exit(1)
        
        # Create connection and run diagnostics
        with SpotConnection() as conn:
            diagnostic = SpotNetworkDiagnostic(conn)
            network_info = diagnostic.get_network_info()
            
            if args.format == "json":
                print(json.dumps(network_info, indent=2))
            else:
                print_table_format(network_info)
                
    except ValueError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        print("\nEither set environment variables or use --profile:", file=sys.stderr)
        print("  export SPOT_HOSTNAME=192.168.80.3", file=sys.stderr)
        print("  export SPOT_USERNAME=admin", file=sys.stderr)
        print("  export SPOT_PASSWORD=password", file=sys.stderr)
        print("  spotNetInfo", file=sys.stderr)
        print("\nOr create a profile:", file=sys.stderr)
        print("  setSpotcon new myrobot", file=sys.stderr)
        print("  spotNetInfo --profile myrobot", file=sys.stderr)
        sys.exit(1)
        
    except Exception as e:
        print(f"Connection failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()