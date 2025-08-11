# Remote Filesystem MCP Server

A secure, self-hostable MCP server that gives AI assistants access to your files. Zero configuration required.

## 🌟 Features

- **Zero Config**: Works immediately with `docker-compose up`
- **Secure by Default**: JWT authentication always enabled
- **Simple**: Just mount your data directory and go
- **Persistent**: Tokens survive container restarts

## 📋 Requirements

- Docker and Docker Compose installed
- An MCP-compatible client (Claude Desktop, Continue.dev, etc.)

## 🚀 Quick Start (3 Steps)

### 1. Start the server
```bash
docker-compose up -d
```

### 2. Get your token
```bash
docker exec filesystem-mcp cat /config/tokens.txt
```

### 3. Connect your MCP client
Use the token from step 2 with your MCP client at `http://localhost:8080/mcp`

That's it! Your files in `./data` are now accessible to AI assistants.

## 📦 What You Get

On first run, the server:
1. Creates `./data` directory for your files
2. Creates `./config` directory for JWT keys
3. Generates secure authentication tokens
4. Saves tokens to `./config/tokens.txt`

## 🔐 Authentication

The server automatically generates two tokens on first run:

- **Admin Token**: Full read/write access
- **Read-Only Token**: Read-only access

Tokens are:
- Saved securely to `./config/tokens.txt` with 0600 permissions
- Reused on restarts (persistent)

To retrieve your tokens:
```bash
docker exec filesystem-mcp cat /config/tokens.txt
```

## 📁 File Operations

### Available Tools

| Tool | Description | Required Scope |
|------|-------------|----------------|
| **File Reading** | | |
| `read_text_file` | Read complete file contents as text, with optional head/tail parameters | `read` |
| `read_media_file` | Read images/audio as base64 encoded data | `read` |
| `read_multiple_files` | Read multiple files simultaneously for efficient batch operations | `read` |
| **File Writing** | | |
| `write_file` | Create new file or overwrite existing file | `write` |
| `edit_file` | Search and replace text in files | `write` |
| **Directory Operations** | | |
| `list_directory` | List files/directories with [FILE]/[DIR] prefixes | `read` |
| `list_directory_with_sizes` | List with file sizes and sorting options | `read` |
| `directory_tree` | Recursive JSON tree structure of directories | `read` |
| `create_directory` | Create directories (with parent creation) | `write` |
| **File Management** | | |
| `move_file` | Move or rename files and directories | `write` |
| `delete_file` | Delete files or directories (with recursive option) | `write` |
| **Search & Info** | | |
| `search_files` | Recursively search for files by pattern and content | `read` |
| `get_file_info` | Get detailed metadata about files/directories | `read` |
| `list_allowed_directories` | Show which directories the server can access | none |

### Tool Examples

```python
from fastmcp import Client

# Connect to the server
client = Client(
    "http://localhost:8080/mcp",
    auth="your-token-here"
)

async with client:
    # Check allowed directories first
    dirs = await client.call_tool("list_allowed_directories", {})
    print(f"Accessible directories: {dirs}")
    
    # List directory with prefixes
    files = await client.call_tool("list_directory", {
        "path": "/data"
    })
    # Returns: ["[DIR] documents", "[FILE] readme.txt", ...]
    
    # Read only first 10 lines of a file
    content = await client.call_tool("read_text_file", {
        "path": "/data/large_file.log",
        "head": 10
    })
    
    # Read multiple files at once
    results = await client.call_tool("read_multiple_files", {
        "paths": ["/data/file1.txt", "/data/file2.txt", "/data/file3.txt"]
    })
    
    # List with sizes and sort by size
    listing = await client.call_tool("list_directory_with_sizes", {
        "path": "/data",
        "sortBy": "size"
    })
    
    # Get directory tree as JSON
    tree = await client.call_tool("directory_tree", {
        "path": "/data"
    })
    
    # Search for files containing text
    matches = await client.call_tool("search_files", {
        "path": "/data",
        "pattern": "*.py",
        "content": "import fastmcp"
    })
    
    # Read an image file
    image = await client.call_tool("read_media_file", {
        "path": "/data/photo.jpg"
    })
    # Returns base64 encoded data with MIME type
```

## 📂 Mounting Your Files

By default, the server accesses files in `./data`. You have two options:

### Single Directory
```yaml
# docker-compose.yml
volumes:
  - /path/to/your/files:/data  # Change left side to your directory
```

### Multiple Directories
Mount multiple directories as subdirectories under `/data`:

```yaml
# docker-compose.yml
volumes:
  - ./documents:/data/documents
  - ./projects:/data/projects
  - ./photos:/data/photos
  - /home/user/important:/data/important
```

Now your MCP client can access all directories:
- `/data/documents/*`
- `/data/projects/*`
- `/data/photos/*`
- `/data/important/*`

Example real-world setup:
```yaml
volumes:
  - ~/Documents:/data/docs
  - ~/Projects:/data/projects
  - /mnt/nas/shared:/data/shared
```

## 🌐 Remote Access

For access over the internet, use a reverse proxy with HTTPS:

**Caddy (simplest):**
```caddy
mcp.yourdomain.com {
    reverse_proxy localhost:8080
}
```

**Nginx:**
```nginx
server {
    listen 443 ssl;
    server_name mcp.yourdomain.com;
    location / {
        proxy_pass http://localhost:8080;
    }
}
```

## 🔒 Security

- ✅ JWT authentication always enabled
- ✅ Directory sandboxing prevents access outside `/data`
- ✅ Tokens persist in `./config` (keep this directory secure)
- ✅ Non-root container user
- ✅ Path validation on every operation


## 🛠️ Common Tasks

### View logs
```bash
docker-compose logs -f filesystem-mcp
```

### Restart server
```bash
docker-compose restart
```

### Stop server
```bash
docker-compose down
```

### Check health
```bash
curl http://localhost:8080/health
```

## 🧪 Test Your Setup

```python
# test.py
import asyncio
from fastmcp import Client

async def main():
    client = Client(
        "http://localhost:8080/mcp",
        auth="YOUR_TOKEN_HERE"  # Get from docker-compose logs
    )
    
    async with client:
        files = await client.call_tool("list_directory", {})
        print(f"Found {len(files)} files")

asyncio.run(main())
```


## 📝 License

MIT License

## 🔗 Built With

- [FastMCP](https://github.com/jlowin/fastmcp) - Python MCP framework
- [Model Context Protocol](https://modelcontextprotocol.io) - MCP specification
