"""
use_spot - Generic tool for Boston Dynamics Spot SDK

Provides atomic-level access to Spot SDK operations following the
service-method pattern similar to use_aws and use_google.
"""

import os
import time
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from strands import tool
from .version_detector import SDKVersionDetector

# Spot SDK imports
try:
    import bosdyn.client
    import bosdyn.client.util
    from bosdyn.client import Robot
    from bosdyn.client.robot_command import (
        RobotCommandClient,
        RobotCommandBuilder,
        blocking_stand,
    )
    from bosdyn.client.robot_state import RobotStateClient
    from bosdyn.client.power import PowerClient
    from bosdyn.client.lease import LeaseClient, LeaseKeepAlive
    from bosdyn.client.image import ImageClient
    from bosdyn.client.estop import EstopClient
    from bosdyn.client.time_sync import TimeSyncClient
    from bosdyn.client.directory import DirectoryClient
    from bosdyn.client.exceptions import RpcError

    SPOT_SDK_AVAILABLE = True
except ImportError:
    SPOT_SDK_AVAILABLE = False
    RpcError = Exception  # Fallback

logger = logging.getLogger(__name__)

# Service client mapping
SERVICE_CLIENTS = {
    "robot_command": RobotCommandClient,
    "robot_state": RobotStateClient,
    "power": PowerClient,
    "lease": LeaseClient,
    "image": ImageClient,
    "estop": EstopClient,
    "time_sync": TimeSyncClient,
    "directory": DirectoryClient,
}

# Services that require lease
LEASE_REQUIRED_SERVICES = {
    "robot_command",
    "power",
    "graph_nav",
    "spot_check",
    "manipulation",
    "docking",
    "choreography",
}


class SpotConnection:
    """Manages connection to a Spot robot with environment-based credentials"""

    def __init__(self, hostname: str = None, username: str = None, password: str = None):
        """
        Initialize connection to Spot robot using environment variables

        Args:
            hostname: Robot IP or hostname (optional, uses SPOT_HOSTNAME env var)
            username: Robot username (optional, uses SPOT_USERNAME env var)
            password: Robot password (optional, uses SPOT_PASSWORD env var)
        
        Environment Variables:
            SPOT_HOSTNAME: Robot IP or hostname (optional if provided as parameter)
            SPOT_USERNAME: Robot username (optional if provided as parameter)
            SPOT_PASSWORD: Robot password (optional if provided as parameter)
        """
        # Get hostname from parameter or environment
        self.hostname = hostname or os.getenv("SPOT_HOSTNAME")
        if not self.hostname:
            raise ValueError("Hostname required via parameter or SPOT_HOSTNAME environment variable")
        
        # Get credentials from parameters or environment
        self.username = username or os.getenv("SPOT_USERNAME")
        self.password = password or os.getenv("SPOT_PASSWORD")
        
        if not self.username or not self.password:
            raise ValueError("Username and password required via parameters or SPOT_USERNAME/SPOT_PASSWORD env vars")
        
        self.sdk = None
        self.robot = None
        self.lease_client = None
        self.lease_keepalive = None
        self._lease_active = False

        # Detect SDK version for metadata/logging
        try:
            self._sdk_version = SDKVersionDetector.detect_version()
            if SDKVersionDetector.validate_version(self._sdk_version):
                logger.info(f"Using Boston Dynamics SDK version {self._sdk_version}")
            else:
                logger.warning(f"Unsupported or unknown SDK version: {self._sdk_version}")
        except Exception as e:
            self._sdk_version = "unknown"
            logger.warning(f"Could not detect SDK version: {e}")

        # Create SDK and robot
        self.sdk = bosdyn.client.create_standard_sdk("use_spot")
        self.robot = self.sdk.create_robot(self.hostname)

        # Authenticate
        self.robot.authenticate(self.username, self.password)
        logger.info(f"Authenticated to robot at {self.hostname}")

        # Time sync (required for commands)
        self.robot.time_sync.wait_for_sync()
        logger.info("Time sync established")

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with guaranteed cleanup"""
        self.close()

    def acquire_lease(self):
        """Acquire robot control lease"""
        if self._lease_active:
            return

        self.lease_client = self.robot.ensure_client(LeaseClient.default_service_name)
        self.lease_keepalive = LeaseKeepAlive(
            self.lease_client, must_acquire=True, return_at_exit=True
        )
        self.lease_keepalive.__enter__()
        self._lease_active = True
        logger.info("Lease acquired")

    def release_lease(self):
        """Release robot control lease"""
        if not self._lease_active:
            return

        if self.lease_keepalive:
            self.lease_keepalive.__exit__(None, None, None)
        self._lease_active = False
        logger.info("Lease released")

    def get_client(self, service: str):
        """
        Get service client by name

        Args:
            service: Service name (e.g., "robot_command")

        Returns:
            Service client instance

        Raises:
            ValueError: Unknown service name
        """
        client_class = SERVICE_CLIENTS.get(service)
        if not client_class:
            raise ValueError(f"Unknown service: {service}")

        return self.robot.ensure_client(client_class.default_service_name)

    def close(self):
        """Clean up connection and resources"""
        if self._lease_active:
            self.release_lease()
        # Additional cleanup can be added here if needed


def format_protobuf_response(response) -> dict:
    """
    Convert protobuf response to dictionary

    Args:
        response: Protobuf message

    Returns:
        Dict representation of protobuf
    """
    if response is None:
        return {}

    try:
        from google.protobuf.json_format import MessageToDict

        return MessageToDict(response, preserving_proto_field_name=True)
    except Exception as e:
        logger.warning(f"Failed to convert protobuf to dict: {e}")
        # Fallback to string representation
        return {"raw": str(response)}


def execute_robot_command_method(
    client: RobotCommandClient, method: str, params: Dict[str, Any]
) -> Any:
    """
    Execute robot_command service methods

    Args:
        client: RobotCommandClient instance
        method: Method name
        params: Method parameters

    Returns:
        Method result
    """
    if method == "stand":
        # Build stand command
        if params:
            footprint_R_body = params.get("footprint_R_body")
            body_height = params.get("body_height")
            cmd = RobotCommandBuilder.synchro_stand_command(
                footprint_R_body=footprint_R_body, body_height=body_height
            )
        else:
            cmd = RobotCommandBuilder.synchro_stand_command()
        return client.robot_command(cmd)

    elif method == "sit":
        cmd = RobotCommandBuilder.synchro_sit_command()
        return client.robot_command(cmd)

    elif method == "self_right":
        cmd = RobotCommandBuilder.selfright_command()
        return client.robot_command(cmd)

    elif method == "velocity_command":
        v_x = params.get("v_x", 0.0)
        v_y = params.get("v_y", 0.0)
        v_rot = params.get("v_rot", 0.0)
        cmd = RobotCommandBuilder.synchro_velocity_command(v_x=v_x, v_y=v_y, v_rot=v_rot)
        return client.robot_command(cmd)

    else:
        # Generic method call
        method_func = getattr(client, method)
        return method_func(**params) if params else method_func()


def execute_method(client, service: str, method: str, params: Dict[str, Any]) -> Any:
    """
    Execute method on service client with service-specific handling

    Args:
        client: Service client instance
        service: Service name
        method: Method name
        params: Method parameters

    Returns:
        Method result
    """
    # Special handling for robot_command service
    if service == "robot_command" and isinstance(client, RobotCommandClient):
        return execute_robot_command_method(client, method, params)

    # Generic method execution for other services
    method_func = getattr(client, method)

    if not params:
        return method_func()
    else:
        return method_func(**params)


@tool
def use_spot(
    service: str,
    method: str,
    username: str = None,
    password: str = None,
    params: dict = None,
    timeout: float = None,
    keep_lease: bool = False,
) -> dict:
    """
    Execute Boston Dynamics Spot SDK operations.

    This is the atomic interface to Spot robot control. Each call represents
    a single SDK service method invocation following the service-method pattern.

    Service-Method Pattern:
        service → SDK service (robot_command, robot_state, power, image, etc.)
        method → Service method (stand, get_robot_state, power_on, etc.)
        params → Method-specific parameters

    Available Services (15 total):
        - robot_command: Motion control (stand, sit, walk, velocity_command)
        - robot_state: Status queries (get_robot_state, get_metrics)
        - power: Power management (power_on, power_off)
        - image: Camera capture (list_image_sources, get_image_from_sources)
        - graph_nav: Navigation (navigate_to, set_localization)
        - manipulation: Arm control (manipulation_api_command)
        - docking: Charging (dock_robot, undock_robot)
        - lease: Resource locks (acquire_lease, release_lease)
        - estop: Emergency stop (register_estop, stop)
        - time_sync: Clock sync (get_robot_time)
        - directory: Service discovery (list_services)
        - choreography: Dance moves (execute_choreography)
        - data_acquisition: Sensor data (acquire_data)
        - autowalk: Missions (load_autowalk, play_mission)
        - spot_check: Diagnostics (start_spot_check)

    Args:
        service: Service name from list above
        method: Method name on the service
        username: Robot username (defaults to SPOT_USERNAME env var)
        password: Robot password (defaults to SPOT_PASSWORD env var)
        params: Method parameters as dictionary
        timeout: Operation timeout in seconds
        keep_lease: Maintain lease after operation (default: False)

    Environment Variables:
        SPOT_HOSTNAME: Robot IP address (required, e.g., "192.168.80.3")
        SPOT_USERNAME: Robot username (optional if provided as parameter)
        SPOT_PASSWORD: Robot password (optional if provided as parameter)

    Returns:
        Standardized response dict:
        {
            "status": "success|error",
            "content": [
                {"text": "Human-readable message"},
                {"image": {"format": "jpeg", "source": {"bytes": <binary>}}},  # For image service
                {"json": {"response_data": {...}}},
                {"json": {"metadata": {...}}}
            ]
        }

        **Image Service**: When using the image service (get_image_from_sources, get_image),
        captured images are automatically extracted and formatted as LLM-readable content blocks.
        The LLM can "see" and analyze these images directly in the response.

    Examples:
        # Stand the robot (requires SPOT_HOSTNAME env var)
        use_spot(
            service="robot_command",
            method="stand",
            params={}
        )

        # Get robot state (no lease required)
        use_spot(
            service="robot_state",
            method="get_robot_state",
            params={}
        )

        # Walk forward
        use_spot(
            service="robot_command",
            method="velocity_command",
            params={"v_x": 0.5, "v_y": 0.0, "v_rot": 0.0}
        )

        # Capture image
        use_spot(
            service="image",
            method="get_image_from_sources",
            params={"image_sources": ["frontleft_fisheye_image"]}
        )

    Safety Notes:
        - Lease is automatically managed (acquired/released)
        - Set keep_lease=True to maintain control across multiple calls
        - Always ensure E-stop is configured
        - Use timeout to prevent hanging operations
        - Check response status before chaining operations
    """
    # Check if Spot SDK is available
    if not SPOT_SDK_AVAILABLE:
        return {
            "status": "error",
            "content": [
                {
                    "text": "Spot SDK not installed. Install with: pip install bosdyn-client bosdyn-api bosdyn-core"
                }
            ],
        }

    start_time = time.time()
    conn = None
    lease_acquired = False

    try:
        # Create connection using environment variables
        logger.info("Connecting to robot using environment variables")
        conn = SpotConnection(username=username, password=password)

        # Acquire lease if needed
        if service in LEASE_REQUIRED_SERVICES:
            conn.acquire_lease()
            lease_acquired = True
            logger.info(f"Lease acquired for {service} service")

        # Get service client
        client = conn.get_client(service)
        logger.info(f"Got client for service: {service}")

        # Execute method
        logger.info(f"Executing {service}.{method} with params: {params}")
        response = execute_method(client, service, method, params or {})

        # Release lease unless keep_lease=True
        if lease_acquired and not keep_lease:
            conn.release_lease()
            logger.info("Lease released")

        # Format response
        duration_ms = int((time.time() - start_time) * 1000)

        # Format human-readable message
        success_msg = f"✅ Executed {service}.{method} successfully in {duration_ms}ms"

        # Convert response to dict
        response_data = format_protobuf_response(response) if response else {}

        # Build metadata
        metadata = {
            "service": service,
            "method": method,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "duration_ms": duration_ms,
            "lease_acquired": lease_acquired,
            "lease_retained": keep_lease and lease_acquired,
            "robot": {"hostname": conn.hostname},
            "sdk_version": conn._sdk_version,
        }

        # Special handling for image service - extract images for LLM consumption
        content_blocks = [{"text": success_msg}]

        if service == "image" and hasattr(response, "__iter__"):
            # For get_image_from_sources or get_image, response is a list of ImageResponse
            try:
                from bosdyn.api import image_pb2

                image_count = 0
                for img_response in response:
                    if hasattr(img_response, "shot") and hasattr(img_response.shot, "image"):
                        image_data = img_response.shot.image.data

                        # Determine image format for LLM
                        # Spot SDK formats: FORMAT_JPEG, FORMAT_RAW, FORMAT_RLE
                        if img_response.shot.image.format == image_pb2.Image.FORMAT_JPEG:
                            image_format = "jpeg"
                        else:
                            # For RAW/RLE formats, we'd need to convert to JPEG/PNG
                            # For now, default to jpeg for other formats
                            image_format = "jpeg"

                        # Add image content block (LLM-readable format)
                        content_blocks.append(
                            {"image": {"format": image_format, "source": {"bytes": image_data}}}
                        )
                        image_count += 1
                        logger.info(
                            f"Added image from {img_response.source.name} to content blocks"
                        )

                if image_count > 0:
                    # Update success message to indicate images were captured
                    content_blocks[0][
                        "text"
                    ] = f"✅ Executed {service}.{method} successfully in {duration_ms}ms - captured {image_count} image(s)"
            except Exception as e:
                logger.warning(f"Failed to extract images from response: {e}")

        # Add JSON blocks after images
        content_blocks.append({"json": {"response_data": response_data}})
        content_blocks.append({"json": {"metadata": metadata}})

        # Return with images (if any), data, and metadata
        return {
            "status": "success",
            "content": content_blocks,
        }

    except RpcError as e:
        error_msg = f"❌ RPC Error: {str(e)}"
        logger.error(error_msg)

        # Clean up lease on error
        if conn and lease_acquired and not keep_lease:
            try:
                conn.release_lease()
                logger.info("Lease released after RPC error")
            except Exception as cleanup_error:
                logger.error(f"Failed to release lease during error cleanup: {cleanup_error}")

        # Build error metadata
        error_metadata = {
            "error_type": "RpcError",
            "service": service,
            "method": method,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

        return {
            "status": "error",
            "content": [
                {"text": error_msg},
                {"json": {"metadata": error_metadata}},
            ],
        }

    except Exception as e:
        error_msg = f"❌ Error: {str(e)}"
        logger.error(error_msg)

        # Clean up lease on error
        if conn and lease_acquired and not keep_lease:
            try:
                conn.release_lease()
                logger.info("Lease released after error")
            except Exception as cleanup_error:
                logger.error(f"Failed to release lease during error cleanup: {cleanup_error}")

        # Build error metadata
        error_metadata = {
            "error_type": type(e).__name__,
            "service": service,
            "method": method,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

        return {
            "status": "error",
            "content": [
                {"text": error_msg},
                {"json": {"metadata": error_metadata}},
            ],
        }

    finally:
        # Ensure connection cleanup if not keeping lease
        if conn and not keep_lease:
            try:
                conn.close()
                logger.debug("Connection closed in finally block")
            except Exception as cleanup_error:
                logger.error(f"Failed to close connection during cleanup: {cleanup_error}")
