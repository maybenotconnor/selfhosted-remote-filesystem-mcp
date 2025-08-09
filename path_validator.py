import os
import pathlib
from typing import List, Optional


class PathValidator:
    """Validates and sanitizes file paths for security."""
    
    def __init__(self, allowed_directories: List[str]):
        """Initialize with list of allowed base directories.
        
        Args:
            allowed_directories: List of absolute paths that are allowed for access
        """
        self.allowed_directories = []
        for dir_path in allowed_directories:
            # Expand environment variables and resolve path
            expanded = os.path.expandvars(os.path.expanduser(dir_path))
            resolved = pathlib.Path(expanded).resolve()
            self.allowed_directories.append(str(resolved))
    
    def validate_path(self, requested_path: str) -> str:
        """Validate that a path is within allowed directories.
        
        Args:
            requested_path: The path to validate
            
        Returns:
            The resolved absolute path
            
        Raises:
            ValueError: If path is outside allowed directories
        """
        # Expand and resolve the requested path
        expanded = os.path.expandvars(os.path.expanduser(requested_path))
        
        # Handle both absolute and relative paths
        if os.path.isabs(expanded):
            resolved = pathlib.Path(expanded).resolve()
        else:
            # For relative paths, try each allowed directory
            resolved = None
            for allowed_dir in self.allowed_directories:
                potential_path = pathlib.Path(allowed_dir) / expanded
                if potential_path.exists():
                    resolved = potential_path.resolve()
                    break
            
            if resolved is None:
                # If file doesn't exist, resolve relative to first allowed dir
                if self.allowed_directories:
                    resolved = (pathlib.Path(self.allowed_directories[0]) / expanded).resolve()
                else:
                    raise ValueError("No allowed directories configured")
        
        # Check if resolved path is within allowed directories
        resolved_str = str(resolved)
        for allowed_dir in self.allowed_directories:
            if resolved_str.startswith(allowed_dir):
                return resolved_str
        
        raise ValueError(f"Access denied: Path '{requested_path}' is outside allowed directories")
    
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
    
    def get_relative_path(self, absolute_path: str, base_dir: Optional[str] = None) -> str:
        """Get relative path from an allowed base directory.
        
        Args:
            absolute_path: The absolute path
            base_dir: Optional base directory, uses first allowed if not specified
            
        Returns:
            Relative path string
        """
        if not base_dir and self.allowed_directories:
            base_dir = self.allowed_directories[0]
        
        if base_dir:
            try:
                return str(pathlib.Path(absolute_path).relative_to(base_dir))
            except ValueError:
                pass
        
        return absolute_path