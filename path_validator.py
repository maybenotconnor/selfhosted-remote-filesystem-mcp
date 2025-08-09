import os
import pathlib
from typing import Optional


class PathValidator:
    """Validates and sanitizes file paths for security."""
    
    def __init__(self, data_directory: str):
        """Initialize with the data directory.
        
        Args:
            data_directory: The single allowed data directory
        """
        # Expand and resolve the data directory
        expanded = os.path.expandvars(os.path.expanduser(data_directory))
        self.data_dir = pathlib.Path(expanded).resolve()
    
    def validate_path(self, requested_path: str) -> str:
        """Validate that a path is within the data directory.
        
        Args:
            requested_path: The path to validate
            
        Returns:
            The resolved absolute path
            
        Raises:
            ValueError: If path is outside the data directory
        """
        # Expand the requested path
        expanded = os.path.expandvars(os.path.expanduser(requested_path))
        
        # Handle both absolute and relative paths
        if os.path.isabs(expanded):
            resolved = pathlib.Path(expanded).resolve()
        else:
            # For relative paths, resolve relative to data directory
            resolved = (self.data_dir / expanded).resolve()
        
        # Check if resolved path is within data directory
        try:
            resolved.relative_to(self.data_dir)
            return str(resolved)
        except ValueError:
            raise ValueError(f"Access denied: Path '{requested_path}' is outside data directory")
    
    def is_path_allowed(self, path: str) -> bool:
        """Check if a path is allowed without raising an exception.
        
        Args:
            path: The path to check
            
        Returns:
            True if path is allowed, False otherwise
        """
        try:
            self.validate_path(path)
            return True
        except ValueError:
            return False
    
    def get_relative_path(self, absolute_path: str) -> str:
        """Get relative path from the data directory.
        
        Args:
            absolute_path: The absolute path
            
        Returns:
            Relative path string
        """
        try:
            return str(pathlib.Path(absolute_path).relative_to(self.data_dir))
        except ValueError:
            return absolute_path