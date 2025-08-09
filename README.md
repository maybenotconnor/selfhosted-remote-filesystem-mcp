# Remote Filesystem MCP Server

A secure, self-hostable MCP server that gives AI assistants access to your files. Zero configuration required.

## 🌟 Features

- **Zero Config**: Works immediately with `docker-compose up`
- **Secure by Default**: JWT authentication always enabled
- **Simple**: Just mount your data directory and go
- **Persistent**: Tokens survive container restarts
- **Production Ready**: Built for real-world use

## 🚀 Quick Start (3 Steps)

### 1. Start the server
```bash
docker-compose up -d
```

### 2. Get your token
```bash
docker-compose logs filesystem-mcp
```

### 3. Connect your MCP client
Use the token from step 2 with your MCP client at `http://localhost:8080/mcp`

That's it! Your files in `./data` are now accessible to AI assistants.

## 📦 What You Get

On first run, the server:
1. Creates `./data` directory for your files
2. Creates `./config` directory for JWT keys
3. Generates secure authentication tokens
4. Shows tokens in the logs (save these!)

On subsequent runs:
- Uses existing tokens from `./config`
- Tokens persist across restarts

## 🔐 Authentication

The server automatically generates two tokens on first run:

- **Admin Token**: Full read/write access
- **Read-Only Token**: Read-only access

Tokens are:
- Displayed in logs on first run
- Saved to `./config/tokens.txt`
- Reused on restarts (persistent)

To see your tokens again:
```bash
cat ./config/tokens.txt
```

## 📁 File Operations

### Available Tools

| Tool | Description | Required Scope |
|------|-------------|----------------|
| `read_file` | Read file contents | `read` |
| `write_file` | Write content to file | `write` |
| `list_directory` | List files and directories | `read` |
| `edit_file` | Search and replace in files | `write` |
| `create_directory` | Create new directories | `write` |
| `move_file` | Move or rename files | `write` |
| `delete_file` | Delete files or directories | `write` |
| `search_files` | Search for files by pattern/content | `read` |
| `get_file_info` | Get detailed file information | `read` |

### Example: Using with MCP Client

```python
from fastmcp import Client

# Connect to the server
client = Client(
    "http://localhost:8080/mcp",
    auth="your-token-here"
)

async with client:
    # List files
    files = await client.call_tool("list_directory", {
        "path": "/data",
        "recursive": True
    })
    
    # Read a file
    content = await client.call_tool("read_file", {
        "path": "/data/example.txt"
    })
    
    # Write a file
    result = await client.call_tool("write_file", {
        "path": "/data/new_file.txt",
        "content": "Hello, World!"
    })
```

## 📂 Mounting Your Files

By default, the server accesses files in `./data`. To use a different directory:

```yaml
# docker-compose.yml
volumes:
  - /path/to/your/files:/data  # Change left side to your directory
```

Example:
```yaml
volumes:
  - ~/Documents:/data           # Give access to your Documents folder
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
