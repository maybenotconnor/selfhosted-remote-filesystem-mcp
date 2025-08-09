#!/usr/bin/env python3
"""
Remote Filesystem MCP Server
A secure, self-hostable MCP server for remote file system operations
"""

import os
import sys
import json
import asyncio
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from fastmcp import FastMCP, Context, ToolError
from fastmcp.server.dependencies import get_access_token, AccessToken

# Load local modules
from path_validator import PathValidator
from auth_config import setup_authentication, check_scope
import file_operations as file_ops

# Load environment variables
load_dotenv()

# Initialize path validator with allowed directories
allowed_dirs = os.getenv("ALLOWED_DIRECTORIES", "/data").split(",")
allowed_dirs = [d.strip() for d in allowed_dirs if d.strip()]

if not allowed_dirs:
    print("❌ ERROR: No allowed directories configured!")
    print("Set ALLOWED_DIRECTORIES environment variable")
    sys.exit(1)

path_validator = PathValidator(allowed_dirs)

# Setup authentication
auth = setup_authentication()

# Initialize FastMCP server
mcp = FastMCP(
    name="Remote Filesystem MCP",
    instructions="""
    This is a secure remote filesystem MCP server that provides file operations.
    All paths are validated against allowed directories for security.
    Authentication is required for all operations.
    """,
    auth=auth
)

# Print server information
print("\n" + "="*60)
print("🚀 REMOTE FILESYSTEM MCP SERVER")
print("="*60)
print(f"📁 Allowed Directories:")
for dir_path in path_validator.allowed_directories:
    print(f"   - {dir_path}")
print(f"🔒 Authentication: {'Enabled' if auth else 'DISABLED ⚠️'}")
print(f"🌐 Transport: HTTP/SSE")
print("="*60 + "\n")


# ============================================================================
# FILE OPERATION TOOLS
# ============================================================================

@mcp.tool
async def read_file(
    path: str,
    encoding: Optional[str] = None,
    ctx: Context = None
) -> Dict[str, Any]:
    """Read the contents of a file.
    
    Args:
        path: Path to the file (absolute or relative to allowed directories)
        encoding: Optional text encoding (default: utf-8)
        ctx: MCP context
        
    Returns:
        File contents and metadata
    """
    # Check authentication scope
    if auth:
        token: AccessToken = get_access_token()
        if not check_scope("read", token.scopes):
            raise ToolError("Insufficient permissions: 'read' scope required")
    
    # Validate path
    validated_path = path_validator.validate_path(path)
    
    # Read file
    result = await file_ops.read_file(validated_path, encoding)
    
    # Add relative path for clarity
    result["relative_path"] = path_validator.get_relative_path(validated_path)
    
    return result


@mcp.tool
async def write_file(
    path: str,
    content: str,
    encoding: str = "utf-8",
    create_dirs: bool = True,
    ctx: Context = None
) -> Dict[str, Any]:
    """Write content to a file.
    
    Args:
        path: Path to the file (absolute or relative to allowed directories)
        content: Content to write (text or base64 encoded binary)
        encoding: Text encoding (default: utf-8)
        create_dirs: Whether to create parent directories if they don't exist
        ctx: MCP context
        
    Returns:
        Operation result
    """
    # Check authentication scope
    if auth:
        token: AccessToken = get_access_token()
        if not check_scope("write", token.scopes):
            raise ToolError("Insufficient permissions: 'write' scope required")
    
    # Check if write operations are enabled
    if os.getenv("ENABLE_WRITE", "true").lower() != "true":
        raise ToolError("Write operations are disabled on this server")
    
    # Validate path
    validated_path = path_validator.validate_path(path)
    
    # Write file
    result = await file_ops.write_file(validated_path, content, encoding, create_dirs)
    
    # Add relative path
    result["relative_path"] = path_validator.get_relative_path(validated_path)
    
    return result


@mcp.tool
async def list_directory(
    path: str = "",
    recursive: bool = False,
    pattern: Optional[str] = None,
    ctx: Context = None
) -> List[Dict[str, Any]]:
    """List files and directories.
    
    Args:
        path: Directory path (defaults to first allowed directory)
        recursive: Whether to list recursively
        pattern: Optional glob pattern to filter results
        ctx: MCP context
        
    Returns:
        List of files and directories with metadata
    """
    # Check authentication scope
    if auth:
        token: AccessToken = get_access_token()
        if not check_scope("read", token.scopes):
            raise ToolError("Insufficient permissions: 'read' scope required")
    
    # Default to first allowed directory if no path specified
    if not path:
        path = path_validator.allowed_directories[0]
    
    # Validate path
    validated_path = path_validator.validate_path(path)
    
    # List directory
    items = await file_ops.list_directory(validated_path, recursive, pattern)
    
    # Add relative paths
    for item in items:
        item["relative_path"] = path_validator.get_relative_path(item["path"])
    
    return items


@mcp.tool
async def edit_file(
    path: str,
    search: str,
    replace: str,
    encoding: str = "utf-8",
    ctx: Context = None
) -> Dict[str, Any]:
    """Edit a file by searching and replacing text.
    
    Args:
        path: Path to the file
        search: Text to search for
        replace: Text to replace with
        encoding: Text encoding (default: utf-8)
        ctx: MCP context
        
    Returns:
        Operation result with replacement count
    """
    # Check authentication scope
    if auth:
        token: AccessToken = get_access_token()
        if not check_scope("write", token.scopes):
            raise ToolError("Insufficient permissions: 'write' scope required")
    
    # Check if write operations are enabled
    if os.getenv("ENABLE_WRITE", "true").lower() != "true":
        raise ToolError("Write operations are disabled on this server")
    
    # Validate path
    validated_path = path_validator.validate_path(path)
    
    # Edit file
    result = await file_ops.edit_file(validated_path, search, replace, encoding)
    
    # Add relative path
    result["relative_path"] = path_validator.get_relative_path(validated_path)
    
    return result


@mcp.tool
async def create_directory(
    path: str,
    parents: bool = True,
    ctx: Context = None
) -> Dict[str, Any]:
    """Create a directory.
    
    Args:
        path: Path for the new directory
        parents: Whether to create parent directories if needed
        ctx: MCP context
        
    Returns:
        Operation result
    """
    # Check authentication scope
    if auth:
        token: AccessToken = get_access_token()
        if not check_scope("write", token.scopes):
            raise ToolError("Insufficient permissions: 'write' scope required")
    
    # Check if write operations are enabled
    if os.getenv("ENABLE_WRITE", "true").lower() != "true":
        raise ToolError("Write operations are disabled on this server")
    
    # Validate path
    validated_path = path_validator.validate_path(path)
    
    # Create directory
    result = await file_ops.create_directory(validated_path, parents)
    
    # Add relative path
    result["relative_path"] = path_validator.get_relative_path(validated_path)
    
    return result


@mcp.tool
async def move_file(
    source: str,
    destination: str,
    overwrite: bool = False,
    ctx: Context = None
) -> Dict[str, Any]:
    """Move or rename a file or directory.
    
    Args:
        source: Source path
        destination: Destination path
        overwrite: Whether to overwrite existing destination
        ctx: MCP context
        
    Returns:
        Operation result
    """
    # Check authentication scope
    if auth:
        token: AccessToken = get_access_token()
        if not check_scope("write", token.scopes):
            raise ToolError("Insufficient permissions: 'write' scope required")
    
    # Check if write operations are enabled
    if os.getenv("ENABLE_WRITE", "true").lower() != "true":
        raise ToolError("Write operations are disabled on this server")
    
    # Validate paths
    validated_source = path_validator.validate_path(source)
    validated_dest = path_validator.validate_path(destination)
    
    # Move file
    result = await file_ops.move_file(validated_source, validated_dest, overwrite)
    
    # Add relative paths
    result["relative_source"] = path_validator.get_relative_path(validated_source)
    result["relative_destination"] = path_validator.get_relative_path(validated_dest)
    
    return result


@mcp.tool
async def delete_file(
    path: str,
    recursive: bool = False,
    ctx: Context = None
) -> Dict[str, Any]:
    """Delete a file or directory.
    
    Args:
        path: Path to delete
        recursive: Whether to delete directories recursively
        ctx: MCP context
        
    Returns:
        Operation result
    """
    # Check authentication scope
    if auth:
        token: AccessToken = get_access_token()
        if not check_scope("write", token.scopes):
            raise ToolError("Insufficient permissions: 'write' scope required")
    
    # Check if write operations are enabled
    if os.getenv("ENABLE_WRITE", "true").lower() != "true":
        raise ToolError("Write operations are disabled on this server")
    
    # Validate path
    validated_path = path_validator.validate_path(path)
    
    # Delete path
    result = await file_ops.delete_path(validated_path, recursive)
    
    # Add relative path
    result["relative_path"] = path_validator.get_relative_path(validated_path)
    
    return result


@mcp.tool
async def search_files(
    path: str = "",
    pattern: str = "*",
    content: Optional[str] = None,
    ignore_patterns: Optional[List[str]] = None,
    ctx: Context = None
) -> List[Dict[str, Any]]:
    """Search for files matching patterns and content.
    
    Args:
        path: Base path for search (defaults to first allowed directory)
        pattern: Glob pattern for file names (default: *)
        content: Optional text to search within files
        ignore_patterns: List of gitignore-style patterns to exclude
        ctx: MCP context
        
    Returns:
        List of matching files with metadata
    """
    # Check authentication scope
    if auth:
        token: AccessToken = get_access_token()
        if not check_scope("read", token.scopes):
            raise ToolError("Insufficient permissions: 'read' scope required")
    
    # Default to first allowed directory if no path specified
    if not path:
        path = path_validator.allowed_directories[0]
    
    # Validate path
    validated_path = path_validator.validate_path(path)
    
    # Default ignore patterns
    if ignore_patterns is None:
        ignore_patterns = [
            "*.pyc", "__pycache__/", ".git/", ".svn/", 
            "node_modules/", "*.log", ".DS_Store"
        ]
    
    # Search files
    matches = await file_ops.search_files(validated_path, pattern, content, ignore_patterns)
    
    # Add relative paths
    for match in matches:
        match["relative_path"] = path_validator.get_relative_path(match["path"])
    
    return matches


@mcp.tool
async def get_file_info(
    path: str,
    ctx: Context = None
) -> Dict[str, Any]:
    """Get detailed information about a file or directory.
    
    Args:
        path: Path to examine
        ctx: MCP context
        
    Returns:
        Detailed file/directory information
    """
    # Check authentication scope
    if auth:
        token: AccessToken = get_access_token()
        if not check_scope("read", token.scopes):
            raise ToolError("Insufficient permissions: 'read' scope required")
    
    # Validate path
    validated_path = path_validator.validate_path(path)
    
    # Get file info
    info = await file_ops.get_file_info(validated_path)
    
    # Add relative path
    info["relative_path"] = path_validator.get_relative_path(validated_path)
    
    return info


# ============================================================================
# HEALTH CHECK ENDPOINT
# ============================================================================

@mcp.custom_route("/health", methods=["GET"])
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "service": "remote-filesystem-mcp",
        "authentication": "enabled" if auth else "disabled",
        "allowed_directories": len(path_validator.allowed_directories)
    }


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    # Get port from environment or default
    port = int(os.getenv("PORT", "8080"))
    host = os.getenv("HOST", "0.0.0.0")
    
    print(f"🎯 Starting server on {host}:{port}")
    print(f"📍 MCP endpoint: http://{host}:{port}/mcp")
    print(f"💓 Health check: http://{host}:{port}/health")
    
    # Run the server
    mcp.run(transport="http", host=host, port=port)