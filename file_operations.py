import os
import json
import base64
import shutil
import aiofiles
import pathlib
import mimetypes
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathspec import PathSpec
from pathspec.patterns import GitWildMatchPattern


async def read_file(path: str, encoding: Optional[str] = None) -> Dict[str, Any]:
    """Read a file and return its contents.
    
    Args:
        path: Validated absolute path to the file
        encoding: Optional encoding, defaults to auto-detect
        
    Returns:
        Dictionary with file contents and metadata
    """
    file_path = pathlib.Path(path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    
    if not file_path.is_file():
        raise ValueError(f"Path is not a file: {path}")
    
    # Detect MIME type
    mime_type, _ = mimetypes.guess_type(path)
    
    # Determine if file is binary
    is_binary = mime_type and (
        mime_type.startswith('image/') or 
        mime_type.startswith('audio/') or
        mime_type.startswith('video/') or
        mime_type.startswith('application/octet-stream')
    )
    
    if is_binary:
        # Read binary file
        async with aiofiles.open(path, 'rb') as f:
            content = await f.read()
            encoded = base64.b64encode(content).decode('utf-8')
            return {
                "type": "binary",
                "content": encoded,
                "mime_type": mime_type or "application/octet-stream",
                "size": len(content)
            }
    else:
        # Read text file
        try:
            encoding = encoding or 'utf-8'
            async with aiofiles.open(path, 'r', encoding=encoding) as f:
                content = await f.read()
                return {
                    "type": "text",
                    "content": content,
                    "mime_type": mime_type or "text/plain",
                    "encoding": encoding,
                    "lines": content.count('\n') + 1
                }
        except UnicodeDecodeError:
            # Fallback to binary if text decoding fails
            async with aiofiles.open(path, 'rb') as f:
                content = await f.read()
                encoded = base64.b64encode(content).decode('utf-8')
                return {
                    "type": "binary",
                    "content": encoded,
                    "mime_type": "application/octet-stream",
                    "size": len(content)
                }


async def write_file(path: str, content: str, encoding: str = 'utf-8', create_dirs: bool = True) -> Dict[str, Any]:
    """Write content to a file.
    
    Args:
        path: Validated absolute path to the file
        content: Content to write
        encoding: Text encoding
        create_dirs: Whether to create parent directories
        
    Returns:
        Dictionary with operation result
    """
    file_path = pathlib.Path(path)
    
    # Create parent directories if needed
    if create_dirs and not file_path.parent.exists():
        file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Check if content is base64 encoded binary
    is_binary = False
    try:
        # Try to detect base64 encoded content
        if len(content) > 0 and all(c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=' for c in content.replace('\n', '')):
            decoded = base64.b64decode(content, validate=True)
            is_binary = True
    except Exception:
        is_binary = False
    
    if is_binary:
        # Write binary file
        async with aiofiles.open(path, 'wb') as f:
            await f.write(base64.b64decode(content))
        written_bytes = len(base64.b64decode(content))
    else:
        # Write text file
        async with aiofiles.open(path, 'w', encoding=encoding) as f:
            await f.write(content)
        written_bytes = len(content.encode(encoding))
    
    return {
        "path": str(file_path),
        "bytes_written": written_bytes,
        "created": not file_path.exists(),
        "type": "binary" if is_binary else "text"
    }


async def list_directory(path: str, recursive: bool = False, pattern: Optional[str] = None) -> List[Dict[str, Any]]:
    """List files in a directory.
    
    Args:
        path: Validated absolute path to the directory
        recursive: Whether to list recursively
        pattern: Optional glob pattern to filter files
        
    Returns:
        List of file/directory information
    """
    dir_path = pathlib.Path(path)
    
    if not dir_path.exists():
        raise FileNotFoundError(f"Directory not found: {path}")
    
    if not dir_path.is_dir():
        raise ValueError(f"Path is not a directory: {path}")
    
    items = []
    
    if recursive:
        # Recursive listing
        for item in dir_path.rglob(pattern or '*'):
            items.append(_get_file_info(item))
    else:
        # Non-recursive listing
        for item in dir_path.glob(pattern or '*'):
            items.append(_get_file_info(item))
    
    return sorted(items, key=lambda x: (not x['is_directory'], x['name']))


def _get_file_info(path: pathlib.Path) -> Dict[str, Any]:
    """Get information about a file or directory.
    
    Args:
        path: Path object
        
    Returns:
        Dictionary with file/directory information
    """
    stat = path.stat()
    
    return {
        "name": path.name,
        "path": str(path),
        "is_directory": path.is_dir(),
        "is_file": path.is_file(),
        "size": stat.st_size if path.is_file() else None,
        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
        "mime_type": mimetypes.guess_type(str(path))[0] if path.is_file() else None,
        "permissions": oct(stat.st_mode)[-3:]
    }


async def edit_file(path: str, search: str, replace: str, encoding: str = 'utf-8') -> Dict[str, Any]:
    """Edit a file by searching and replacing text.
    
    Args:
        path: Validated absolute path to the file
        search: Text to search for
        replace: Text to replace with
        encoding: Text encoding
        
    Returns:
        Dictionary with operation result
    """
    file_path = pathlib.Path(path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    
    if not file_path.is_file():
        raise ValueError(f"Path is not a file: {path}")
    
    # Read file
    async with aiofiles.open(path, 'r', encoding=encoding) as f:
        content = await f.read()
    
    # Count replacements
    count = content.count(search)
    
    if count == 0:
        return {
            "path": str(file_path),
            "replacements": 0,
            "message": f"No occurrences of '{search}' found"
        }
    
    # Replace content
    new_content = content.replace(search, replace)
    
    # Write back
    async with aiofiles.open(path, 'w', encoding=encoding) as f:
        await f.write(new_content)
    
    return {
        "path": str(file_path),
        "replacements": count,
        "message": f"Replaced {count} occurrence(s)"
    }


async def create_directory(path: str, parents: bool = True) -> Dict[str, Any]:
    """Create a directory.
    
    Args:
        path: Validated absolute path for the directory
        parents: Whether to create parent directories
        
    Returns:
        Dictionary with operation result
    """
    dir_path = pathlib.Path(path)
    
    if dir_path.exists():
        if dir_path.is_dir():
            return {
                "path": str(dir_path),
                "created": False,
                "message": "Directory already exists"
            }
        else:
            raise ValueError(f"Path exists but is not a directory: {path}")
    
    dir_path.mkdir(parents=parents, exist_ok=True)
    
    return {
        "path": str(dir_path),
        "created": True,
        "message": "Directory created successfully"
    }


async def move_file(source: str, destination: str, overwrite: bool = False) -> Dict[str, Any]:
    """Move or rename a file or directory.
    
    Args:
        source: Validated absolute source path
        destination: Validated absolute destination path
        overwrite: Whether to overwrite existing destination
        
    Returns:
        Dictionary with operation result
    """
    src_path = pathlib.Path(source)
    dst_path = pathlib.Path(destination)
    
    if not src_path.exists():
        raise FileNotFoundError(f"Source not found: {source}")
    
    if dst_path.exists() and not overwrite:
        raise FileExistsError(f"Destination already exists: {destination}")
    
    # If destination is a directory, move source into it
    if dst_path.is_dir():
        dst_path = dst_path / src_path.name
    
    shutil.move(str(src_path), str(dst_path))
    
    return {
        "source": str(src_path),
        "destination": str(dst_path),
        "message": "Moved successfully"
    }


async def delete_path(path: str, recursive: bool = False) -> Dict[str, Any]:
    """Delete a file or directory.
    
    Args:
        path: Validated absolute path to delete
        recursive: Whether to delete directories recursively
        
    Returns:
        Dictionary with operation result
    """
    target_path = pathlib.Path(path)
    
    if not target_path.exists():
        raise FileNotFoundError(f"Path not found: {path}")
    
    if target_path.is_file():
        target_path.unlink()
        return {
            "path": str(target_path),
            "type": "file",
            "message": "File deleted successfully"
        }
    elif target_path.is_dir():
        if recursive:
            shutil.rmtree(str(target_path))
            return {
                "path": str(target_path),
                "type": "directory",
                "message": "Directory deleted recursively"
            }
        else:
            try:
                target_path.rmdir()
                return {
                    "path": str(target_path),
                    "type": "directory",
                    "message": "Empty directory deleted"
                }
            except OSError:
                raise ValueError(f"Directory not empty. Use recursive=true to delete: {path}")


async def search_files(path: str, pattern: str, content: Optional[str] = None, 
                       ignore_patterns: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """Search for files matching patterns and optionally containing specific content.
    
    Args:
        path: Validated absolute base path for search
        pattern: Glob pattern for file names
        content: Optional text to search within files
        ignore_patterns: List of patterns to ignore (gitignore style)
        
    Returns:
        List of matching files with information
    """
    base_path = pathlib.Path(path)
    
    if not base_path.exists():
        raise FileNotFoundError(f"Path not found: {path}")
    
    # Setup ignore patterns
    ignore_spec = None
    if ignore_patterns:
        ignore_spec = PathSpec.from_lines(GitWildMatchPattern, ignore_patterns)
    
    matches = []
    
    # Search for files
    for file_path in base_path.rglob(pattern):
        if not file_path.is_file():
            continue
        
        # Check ignore patterns
        if ignore_spec:
            rel_path = file_path.relative_to(base_path)
            if ignore_spec.match_file(str(rel_path)):
                continue
        
        # Check content if specified
        if content:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_content = f.read()
                    if content not in file_content:
                        continue
            except (UnicodeDecodeError, PermissionError):
                continue
        
        matches.append(_get_file_info(file_path))
    
    return matches


async def get_file_info(path: str) -> Dict[str, Any]:
    """Get detailed information about a file or directory.
    
    Args:
        path: Validated absolute path
        
    Returns:
        Dictionary with detailed file/directory information
    """
    target_path = pathlib.Path(path)
    
    if not target_path.exists():
        raise FileNotFoundError(f"Path not found: {path}")
    
    info = _get_file_info(target_path)
    
    # Add additional details
    if target_path.is_file():
        # Try to get line count for text files
        try:
            with open(target_path, 'r', encoding='utf-8') as f:
                lines = sum(1 for _ in f)
                info['lines'] = lines
                info['is_text'] = True
        except (UnicodeDecodeError, PermissionError):
            info['is_text'] = False
    
    elif target_path.is_dir():
        # Count items in directory
        items = list(target_path.iterdir())
        info['item_count'] = len(items)
        info['file_count'] = sum(1 for item in items if item.is_file())
        info['dir_count'] = sum(1 for item in items if item.is_dir())
    
    return info