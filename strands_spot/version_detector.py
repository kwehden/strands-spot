"""SDK Version Detection Module

Provides simple version detection for metadata and logging purposes only.
Thread-safe singleton pattern with caching for performance.
"""

import re
import threading
from typing import Optional


class SDKVersionDetector:
    """Simple SDK version detector for metadata/logging purposes."""
    
    _cached_version: Optional[str] = None
    _detection_lock = threading.Lock()
    
    @classmethod
    def detect_version(cls) -> str:
        """Detect installed SDK version with caching.
        
        Returns:
            str: SDK version string (e.g., "4.5.2", "5.1.1") or "unknown"
            
        Raises:
            ImportError: If bosdyn package not found
        """
        if cls._cached_version is not None:
            return cls._cached_version
            
        with cls._detection_lock:
            if cls._cached_version is not None:  # Double-check
                return cls._cached_version
                
            try:
                import bosdyn
                version = getattr(bosdyn, '__version__', 'unknown')
                cls._cached_version = version
                return version
            except ImportError:
                raise ImportError("Spot SDK not found. Install with: pip install bosdyn-client")
    
    @classmethod
    def validate_version(cls, version: str) -> bool:
        """Validate version format and support range.
        
        Args:
            version: Version string to validate
            
        Returns:
            bool: True if version is supported
            
        Raises:
            ValueError: If version format is invalid or unsupported
        """
        if version == "unknown":
            raise ValueError("Cannot validate unknown SDK version")
            
        # Validate X.Y.Z format (strict - no additional characters)
        if not re.match(r'^\d+\.\d+\.\d+$', version):
            raise ValueError("Invalid version format. Expected 'X.Y.Z' (e.g., '4.5.2')")
        
        # Extract major version
        try:
            major_version = int(version.split('.')[0])
        except (ValueError, IndexError):
            raise ValueError("Invalid version format. Expected 'X.Y.Z' (e.g., '4.5.2')")
        
        # Check support range (4.0.0+ and 5.x series)
        if major_version < 4:
            raise ValueError("Unsupported SDK version. Minimum supported: 4.0.0")
        elif major_version > 5:
            raise ValueError("Unsupported SDK version. Supported: 4.0.0+ and 5.x series")
            
        return True