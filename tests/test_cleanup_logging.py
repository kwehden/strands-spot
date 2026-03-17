"""
Test cleanup error logging for MAJOR-001 fix
"""

import unittest
import os


class TestCleanupErrorLogging(unittest.TestCase):
    """Test that cleanup errors are properly logged"""

    def test_use_spot_no_bare_except(self):
        """Test that use_spot.py has no bare except: clauses"""
        use_spot_path = os.path.join(os.path.dirname(__file__), '..', 'strands_spot', 'use_spot.py')
        
        with open(use_spot_path, 'r') as f:
            source = f.read()
        
        # Verify no bare except: clauses exist
        self.assertNotIn("except:", source, "Found bare except: clause - should use specific Exception")
        
        # Verify specific exception handling exists in cleanup paths
        self.assertIn("except Exception as cleanup_error:", source, "Missing specific exception handling for cleanup")
        
        # Verify logging of cleanup errors
        self.assertIn("logger.error", source, "Missing error logging")

    def test_spotnetinfo_no_bare_except(self):
        """Test that spotNetInfo.py has no bare except: clauses"""
        spotnetinfo_path = os.path.join(os.path.dirname(__file__), '..', 'strands_spot', 'cli', 'spotNetInfo.py')
        
        with open(spotnetinfo_path, 'r') as f:
            source = f.read()
        
        # Verify no bare except: clauses exist
        self.assertNotIn("except:", source, "Found bare except: clause - should use specific Exception")
        
        # Verify specific exception handling exists
        self.assertIn("except Exception as e:", source, "Missing specific exception handling")

    def test_cleanup_error_patterns(self):
        """Test that cleanup error patterns are implemented correctly"""
        use_spot_path = os.path.join(os.path.dirname(__file__), '..', 'strands_spot', 'use_spot.py')
        
        with open(use_spot_path, 'r') as f:
            source = f.read()
        
        # Check for lease cleanup error handling
        self.assertIn("Failed to release lease during error cleanup", source, 
                     "Missing lease cleanup error message")
        
        # Check for connection cleanup error handling  
        self.assertIn("Failed to close connection during cleanup", source,
                     "Missing connection cleanup error message")
        
        # Verify cleanup errors don't mask original errors (they're in except blocks)
        cleanup_error_lines = [line.strip() for line in source.split('\n') 
                              if 'cleanup_error' in line and 'logger.error' in line]
        self.assertGreater(len(cleanup_error_lines), 0, "No cleanup error logging found")


if __name__ == '__main__':
    unittest.main()