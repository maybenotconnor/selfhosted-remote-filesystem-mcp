#!/usr/bin/env python3
"""
Remote Filesystem MCP Server
A secure, self-hostable MCP server for remote file system operations
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional, Annotated
from fastmcp import FastMCP, Context
from fastmcp.exceptions import ToolError
from fastmcp.server.dependencies import get_access_token, AccessToken

# Load local modules
from path_validator import PathValidator
from auth_config import setup_authentication, check_scope
import file_operations as file_ops

# Get configuration from environment
data_dir = os.getenv("DATA_DIR", "/data")
config_dir = os.getenv("CONFIG_DIR", "/config")
port = int(os.getenv("PORT", "8080"))

# Ensure directories exist
Path(data_dir).mkdir(exist_ok=True, parents=True)
Path(config_dir).mkdir(exist_ok=True, parents=True)

# Initialize path validator with single data directory
path_validator = PathValidator(data_dir)

# Setup authentication (always enabled)
auth = setup_authentication()

# Initialize FastMCP server
mcp = FastMCP(
    name="Remote Filesystem MCP",
    instructions="Secure file system access via MCP. All operations require JWT authentication.",
    auth=auth
)

# Print server information
print("\n" + "━"*60)
print("🚀 Remote Filesystem MCP Server")
print("━"*60)
print(f"📁 Data directory: {data_dir}")
print(f"🔐 Authentication: Enabled")
print(f"📍 Server ready at: http://localhost:{port}/mcp")
print("━"*60 + "\n")


# ============================================================================
# FILE OPERATION TOOLS
# ============================================================================

@mcp.tool(
    name="read_text_file",
    description="""Read the complete contents of a file from the file system as text. Handles various text encodings and provides detailed error messages if the file cannot be read. Use this tool when you need to examine the contents of a single file. Use the 'head' parameter to read only the first N lines of a file, or the 'tail' parameter to read only the last N lines of a file. Operates on the file as text regardless of extension. Only works within allowed directories.""",
    tags={"filesystem", "read", "essential"},
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True
    }
)
async def read_text_file(
    path: Annotated[str, "Path to the file"],
    tail: Annotated[Optional[int], "If provided, returns only the last N lines of the file"] = None,
    head: Annotated[Optional[int], "If provided, returns only the first N lines of the file"] = None,
    encoding: Annotated[Optional[str], "Text encoding (default: utf-8)"] = None,
    ctx: Context = None
) -> Dict[str, Any]:
    """Read the complete contents of a file from the file system as text."""
    # Check authentication scope
    token: AccessToken = get_access_token()
    if not check_scope("read", token.scopes):
        raise ToolError("Insufficient permissions: 'read' scope required")
    
    # Validate path
    validated_path = path_validator.validate_path(path)
    
    # Check for head/tail parameters
    if head and tail:
        raise ToolError("Cannot specify both head and tail parameters simultaneously")
    
    # Handle head/tail reading
    if head or tail:
        result = await file_ops.read_file_lines(validated_path, head=head, tail=tail, encoding=encoding)
    else:
        # Read entire file
        result = await file_ops.read_file(validated_path, encoding)
    
    # Add relative path for clarity
    result["relative_path"] = path_validator.get_relative_path(validated_path)
    
    return result

@mcp.tool(
    name="read_media_file",
    description="""Read an image or audio file. Returns the base64 encoded data and MIME type. Only works within allowed directories.""",
    tags={"filesystem", "read", "media"},
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True
    }
)
async def read_media_file(
    path: Annotated[str, "Path to the media file"],
    ctx: Context = None
) -> Dict[str, Any]:
    """Read an image or audio file and return base64 encoded data."""
    # Check authentication scope
    token: AccessToken = get_access_token()
    if not check_scope("read", token.scopes):
        raise ToolError("Insufficient permissions: 'read' scope required")
    
    # Validate path
    validated_path = path_validator.validate_path(path)
    
    # Read media file
    result = await file_ops.read_media_file(validated_path)
    
    # Add relative path
    result["relative_path"] = path_validator.get_relative_path(validated_path)
    
    return result


@mcp.tool(
    name="read_multiple_files",
    description="""Read the contents of multiple files simultaneously. This is more efficient than reading files one by one when you need to analyze or compare multiple files. Each file's content is returned with its path as a reference. Failed reads for individual files won't stop the entire operation. Only works within allowed directories.""",
    tags={"filesystem", "read", "batch"},
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True
    }
)
async def read_multiple_files(
    paths: Annotated[List[str], "List of file paths to read"],
    ctx: Context = None
) -> List[Dict[str, Any]]:
    """Read multiple files simultaneously."""
    # Check authentication scope
    token: AccessToken = get_access_token()
    if not check_scope("read", token.scopes):
        raise ToolError("Insufficient permissions: 'read' scope required")
    
    # Read all files in parallel
    tasks = []
    for path in paths:
        async def read_single(p):
            try:
                validated_path = path_validator.validate_path(p)
                result = await file_ops.read_file(validated_path)
                result["path"] = p
                result["relative_path"] = path_validator.get_relative_path(validated_path)
                return result
            except Exception as e:
                return {
                    "path": p,
                    "error": str(e),
                    "content": None
                }
        tasks.append(read_single(path))
    
    results = await asyncio.gather(*tasks)
    return results


@mcp.tool(
    name="write_file",
    description="""Create a new file or completely overwrite an existing file with new content. Use with caution as it will overwrite existing files without warning. Handles text content with proper encoding. Only works within allowed directories.""",
    tags={"filesystem", "write", "essential"},
    annotations={
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": True
    }
)
async def write_file(
    path: Annotated[str, "Path to the file"],
    content: Annotated[str, "Content to write to the file"],
    encoding: Annotated[str, "Text encoding (default: utf-8)"] = "utf-8",
    create_dirs: Annotated[bool, "Whether to create parent directories if they don't exist"] = True,
    ctx: Context = None
) -> Dict[str, Any]:
    """Create a new file or completely overwrite an existing file."""
    # Check authentication scope
    token: AccessToken = get_access_token()
    if not check_scope("write", token.scopes):
        raise ToolError("Insufficient permissions: 'write' scope required")
    
    # Validate path
    validated_path = path_validator.validate_path(path)
    
    # Write file
    result = await file_ops.write_file(validated_path, content, encoding, create_dirs)
    
    # Add relative path
    result["relative_path"] = path_validator.get_relative_path(validated_path)
    
    return result


@mcp.tool(
    name="list_directory",
    description="""Get a detailed listing of all files and directories in a specified path. Results clearly distinguish between files and directories with [FILE] and [DIR] prefixes. This tool is essential for understanding directory structure and finding specific files within a directory. Only works within allowed directories.""",
    tags={"filesystem", "read", "essential"},
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True
    }
)
async def list_directory(
    path: Annotated[str, "Directory path (defaults to data directory root)"] = "",
    recursive: Annotated[bool, "Whether to list recursively"] = False,
    pattern: Annotated[Optional[str], "Optional glob pattern to filter results"] = None,
    ctx: Context = None
) -> List[str]:
    """Get a detailed listing of all files and directories."""
    # Check authentication scope
    token: AccessToken = get_access_token()
    if not check_scope("read", token.scopes):
        raise ToolError("Insufficient permissions: 'read' scope required")
    
    # Default to data directory if no path specified
    if not path:
        path = data_dir
    
    # Validate path
    validated_path = path_validator.validate_path(path)
    
    # List directory
    items = await file_ops.list_directory(validated_path, recursive, pattern)
    
    # Format with [FILE] and [DIR] prefixes
    formatted_items = []
    for item in items:
        prefix = "[DIR]" if item["is_directory"] else "[FILE]"
        rel_path = path_validator.get_relative_path(item["path"])
        formatted_items.append(f"{prefix} {rel_path}")
    
    return formatted_items


@mcp.tool(
    name="list_directory_with_sizes",
    description="""Get a detailed listing of all files and directories in a specified path, including sizes. Results clearly distinguish between files and directories with [FILE] and [DIR] prefixes. This tool is useful for understanding directory structure and finding specific files within a directory. Only works within allowed directories.""",
    tags={"filesystem", "read", "detailed"},
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True
    }
)
async def list_directory_with_sizes(
    path: Annotated[str, "Directory path"] = "",
    sortBy: Annotated[str, "Sort entries by 'name' or 'size'"] = "name",
    ctx: Context = None
) -> Dict[str, Any]:
    """Get a detailed listing with sizes."""
    # Check authentication scope
    token: AccessToken = get_access_token()
    if not check_scope("read", token.scopes):
        raise ToolError("Insufficient permissions: 'read' scope required")
    
    # Default to data directory if no path specified
    if not path:
        path = data_dir
    
    # Validate path
    validated_path = path_validator.validate_path(path)
    
    # List directory with sizes
    result = await file_ops.list_directory_with_sizes(validated_path, sortBy)
    
    return result


@mcp.tool(
    name="directory_tree",
    description="""Get a recursive tree view of files and directories as a JSON structure. Each entry includes 'name', 'type' (file/directory), and 'children' for directories. Files have no children array, while directories always have a children array (which may be empty). The output is formatted with 2-space indentation for readability. Only works within allowed directories.""",
    tags={"filesystem", "read", "structure"},
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True
    }
)
async def directory_tree(
    path: Annotated[str, "Directory path"] = "",
    ctx: Context = None
) -> str:
    """Get a recursive tree view of files and directories."""
    # Check authentication scope
    token: AccessToken = get_access_token()
    if not check_scope("read", token.scopes):
        raise ToolError("Insufficient permissions: 'read' scope required")
    
    # Default to data directory if no path specified
    if not path:
        path = data_dir
    
    # Validate path
    validated_path = path_validator.validate_path(path)
    
    # Build directory tree
    tree = await file_ops.build_directory_tree(validated_path)
    
    # Return as formatted JSON string
    return json.dumps(tree, indent=2)


@mcp.tool(
    name="edit_file",
    description="""Edit a file by searching and replacing text. Only works within allowed directories.""",
    tags={"filesystem", "write", "modify"},
    annotations={
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False
    }
)
async def edit_file(
    path: Annotated[str, "Path to the file"],
    search: Annotated[str, "Text to search for"],
    replace: Annotated[str, "Text to replace with"],
    encoding: Annotated[str, "Text encoding"] = "utf-8",
    ctx: Context = None
) -> Dict[str, Any]:
    """Edit a file by searching and replacing text."""
    # Check authentication scope
    token: AccessToken = get_access_token()
    if not check_scope("write", token.scopes):
        raise ToolError("Insufficient permissions: 'write' scope required")
    
    # Validate path
    validated_path = path_validator.validate_path(path)
    
    # Edit file
    result = await file_ops.edit_file(validated_path, search, replace, encoding)
    
    # Add relative path
    result["relative_path"] = path_validator.get_relative_path(validated_path)
    
    return result


@mcp.tool(
    name="create_directory",
    description="""Create a new directory or ensure a directory exists. Can create multiple nested directories in one operation. If the directory already exists, this operation will succeed silently. Perfect for setting up directory structures for projects or ensuring required paths exist. Only works within allowed directories.""",
    tags={"filesystem", "write", "organize"},
    annotations={
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True
    }
)
async def create_directory(
    path: Annotated[str, "Path for the new directory"],
    parents: Annotated[bool, "Whether to create parent directories if needed"] = True,
    ctx: Context = None
) -> Dict[str, Any]:
    """Create a new directory or ensure it exists."""
    # Check authentication scope
    token: AccessToken = get_access_token()
    if not check_scope("write", token.scopes):
        raise ToolError("Insufficient permissions: 'write' scope required")
    
    # Validate path
    validated_path = path_validator.validate_path(path)
    
    # Create directory
    result = await file_ops.create_directory(validated_path, parents)
    
    # Add relative path
    result["relative_path"] = path_validator.get_relative_path(validated_path)
    
    return result


@mcp.tool(
    name="move_file",
    description="""Move or rename files and directories. Can move files between directories and rename them in a single operation. If the destination exists, the operation will fail. Works across different directories and can be used for simple renaming within the same directory. Both source and destination must be within allowed directories.""",
    tags={"filesystem", "write", "organize"},
    annotations={
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False
    }
)
async def move_file(
    source: Annotated[str, "Source path"],
    destination: Annotated[str, "Destination path"],
    overwrite: Annotated[bool, "Whether to overwrite existing destination"] = False,
    ctx: Context = None
) -> Dict[str, Any]:
    """Move or rename a file or directory."""
    # Check authentication scope
    token: AccessToken = get_access_token()
    if not check_scope("write", token.scopes):
        raise ToolError("Insufficient permissions: 'write' scope required")
    
    # Validate paths
    validated_source = path_validator.validate_path(source)
    validated_dest = path_validator.validate_path(destination)
    
    # Move file
    result = await file_ops.move_file(validated_source, validated_dest, overwrite)
    
    # Add relative paths
    result["relative_source"] = path_validator.get_relative_path(validated_source)
    result["relative_destination"] = path_validator.get_relative_path(validated_dest)
    
    return result


@mcp.tool(
    name="delete_file",
    description="""Delete a file or directory. Use with extreme caution as this operation cannot be undone. For directories, use the recursive parameter to delete non-empty directories. Only works within allowed directories.""",
    tags={"filesystem", "write", "dangerous"},
    annotations={
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": True
    }
)
async def delete_file(
    path: Annotated[str, "Path to delete"],
    recursive: Annotated[bool, "Whether to delete directories recursively"] = False,
    ctx: Context = None
) -> Dict[str, Any]:
    """Delete a file or directory."""
    # Check authentication scope
    token: AccessToken = get_access_token()
    if not check_scope("write", token.scopes):
        raise ToolError("Insufficient permissions: 'write' scope required")
    
    # Validate path
    validated_path = path_validator.validate_path(path)
    
    # Delete path
    result = await file_ops.delete_path(validated_path, recursive)
    
    # Add relative path
    result["relative_path"] = path_validator.get_relative_path(validated_path)
    
    return result


@mcp.tool(
    name="search_files",
    description="""Recursively search for files and directories matching a pattern. Searches through all subdirectories from the starting path. The search is case-insensitive and matches partial names. Returns full paths to all matching items. Great for finding files when you don't know their exact location. Only searches within allowed directories.""",
    tags={"filesystem", "read", "search"},
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True
    }
)
async def search_files(
    path: Annotated[str, "Base path for search (defaults to data directory)"] = "",
    pattern: Annotated[str, "Glob pattern for file names"] = "*",
    content: Annotated[Optional[str], "Optional text to search within files"] = None,
    ignore_patterns: Annotated[Optional[List[str]], "List of patterns to exclude"] = None,
    ctx: Context = None
) -> List[Dict[str, Any]]:
    """Recursively search for files matching patterns."""
    # Check authentication scope
    token: AccessToken = get_access_token()
    if not check_scope("read", token.scopes):
        raise ToolError("Insufficient permissions: 'read' scope required")
    
    # Default to data directory if no path specified
    if not path:
        path = data_dir
    
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


@mcp.tool(
    name="get_file_info",
    description="""Retrieve detailed metadata about a file or directory. Returns comprehensive information including size, creation time, last modified time, permissions, and type. This tool is perfect for understanding file characteristics without reading the actual content. Only works within allowed directories.""",
    tags={"filesystem", "read", "metadata"},
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True
    }
)
async def get_file_info(
    path: Annotated[str, "Path to examine"],
    ctx: Context = None
) -> Dict[str, Any]:
    """Get detailed information about a file or directory."""
    # Check authentication scope
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


@mcp.tool(
    name="list_allowed_directories",
    description="""Returns the list of root directories that this server is allowed to access. Use this to understand which directories are available before trying to access files.""",
    tags={"filesystem", "info", "essential"},
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True
    }
)
async def list_allowed_directories(
    ctx: Context = None
) -> List[str]:
    """Returns the list of allowed directories."""
    # No authentication check needed - this is informational
    return [data_dir]


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
    # Run the server
    mcp.run(transport="http", host="0.0.0.0", port=port)