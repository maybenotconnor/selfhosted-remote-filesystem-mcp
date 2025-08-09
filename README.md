# Remote Filesystem MCP Server

A secure, self-hostable Model Context Protocol (MCP) server for remote file system operations. Built with FastMCP and Python, containerized with Docker for easy deployment.

## 🌟 Features

- **Secure Remote Access**: JWT-based authentication with configurable scopes
- **File Operations**: Read, write, list, edit, move, delete, search files
- **Path Security**: Directory sandboxing to restrict access to allowed paths
- **Docker Ready**: Fully containerized with docker-compose for easy deployment
- **Configurable**: Environment-based configuration for flexibility
- **Production Ready**: Health checks, resource limits, and security best practices

## 🚀 Quick Start

### Using Docker Compose (Recommended)

1. Clone the repository:
```bash
git clone https://github.com/yourusername/remote-filesystem-mcp.git
cd remote-filesystem-mcp/selfhosted-remote-filesystem-mcp
```

2. Copy the environment template:
```bash
cp .env.example .env
```

3. Edit `.env` to configure your settings (optional)

4. Start the server:
```bash
docker-compose up -d
```

The server will start and display authentication tokens in the logs:
```bash
docker-compose logs filesystem-mcp
```

### Using Docker Run

```bash
docker run -d \
  --name filesystem-mcp \
  -p 8080:8080 \
  -v ./data:/data \
  -e ALLOWED_DIRECTORIES=/data \
  filesystem-mcp:latest
```

### Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variables:
```bash
export ALLOWED_DIRECTORIES=/path/to/your/data
export PORT=8080
```

3. Run the server:
```bash
python server.py
```

## 🔐 Authentication

The server uses JWT Bearer token authentication by default. On first startup, it generates tokens automatically:

- **Admin Token**: Full read/write access
- **Read-Only Token**: Read-only access

### Using Authentication Tokens

Include the token in the Authorization header:
```http
Authorization: Bearer <your-token>
```

### Generating Custom Tokens

You can generate your own RSA key pair and tokens:

```python
from fastmcp.server.auth.providers.bearer import RSAKeyPair

# Generate key pair
key_pair = RSAKeyPair.generate()

# Create token with custom scopes
token = key_pair.create_token(
    subject="my-client",
    issuer="filesystem-mcp-server",
    audience="filesystem-mcp",
    scopes=["read", "write"]
)

print(f"Token: {token}")
print(f"Public Key:\n{key_pair.public_key}")
```

### Disabling Authentication (NOT Recommended)

Set `DISABLE_AUTH=true` in your environment variables. This makes the server publicly accessible!

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

## 🐳 Docker Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ALLOWED_DIRECTORIES` | Comma-separated list of allowed paths | `/data` |
| `PORT` | Server port | `8080` |
| `HOST` | Server host | `0.0.0.0` |
| `ENABLE_WRITE` | Enable write operations | `true` |
| `DISABLE_AUTH` | Disable authentication (not recommended) | `false` |
| `JWT_AUDIENCE` | Expected JWT audience | `filesystem-mcp` |
| `JWT_ISSUER` | JWT issuer | `filesystem-mcp-server` |
| `JWT_ALGORITHM` | JWT signing algorithm | `RS256` |
| `JWT_PUBLIC_KEY` | RSA public key (PEM format or file path) | Auto-generated |
| `JWT_PRIVATE_KEY` | RSA private key (PEM format or file path) | Auto-generated |

### Volume Mounts

Mount your data directories into the container:

```yaml
volumes:
  - /host/path/documents:/data/documents
  - /host/path/projects:/data/projects
```

Then set:
```yaml
environment:
  ALLOWED_DIRECTORIES: "/data/documents,/data/projects"
```

### Using with Reverse Proxy (Nginx/Caddy)

For production deployments, use a reverse proxy with HTTPS:

**Nginx example:**
```nginx
server {
    listen 443 ssl http2;
    server_name mcp.yourdomain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**Caddy example:**
```caddy
mcp.yourdomain.com {
    reverse_proxy localhost:8080
}
```

## 🔒 Security Considerations

1. **Always use authentication** in production environments
2. **Use HTTPS** when exposing to the internet (via reverse proxy)
3. **Limit allowed directories** to only what's necessary
4. **Set read-only mode** (`ENABLE_WRITE=false`) when write access isn't needed
5. **Use strong JWT keys** and rotate them regularly
6. **Monitor access logs** for suspicious activity
7. **Set resource limits** in docker-compose to prevent DoS

## 🏗️ Architecture

```
┌─────────────────────────────────────┐
│         MCP Client (AI)             │
└─────────────┬───────────────────────┘
              │ HTTP/SSE + JWT
┌─────────────▼───────────────────────┐
│      FastMCP Server (Python)        │
│  ┌────────────────────────────┐     │
│  │   Authentication Layer      │     │
│  │   (JWT Bearer Tokens)       │     │
│  └────────────┬───────────────┘     │
│  ┌────────────▼───────────────┐     │
│  │   Path Validator           │     │
│  │   (Security Sandbox)       │     │
│  └────────────┬───────────────┘     │
│  ┌────────────▼───────────────┐     │
│  │   File Operations          │     │
│  │   (Async I/O)              │     │
│  └────────────┬───────────────┘     │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│         File System                 │
│      (Allowed Directories)          │
└─────────────────────────────────────┘
```

## 📊 Monitoring

### Health Check

The server provides a health endpoint:
```bash
curl http://localhost:8080/health
```

Response:
```json
{
  "status": "healthy",
  "service": "remote-filesystem-mcp",
  "authentication": "enabled",
  "allowed_directories": 2
}
```

### Logs

View server logs:
```bash
docker-compose logs -f filesystem-mcp
```

## 🧪 Testing

### Test with curl

```bash
# Get auth token from server logs first
TOKEN="your-token-here"

# List files
curl -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -X POST http://localhost:8080/mcp \
  -d '{"method": "tools/call", "params": {"name": "list_directory", "arguments": {"path": "/data"}}}'
```

### Test with Python Client

```python
import asyncio
from fastmcp import Client

async def test_server():
    client = Client(
        "http://localhost:8080/mcp",
        auth="your-token-here"
    )
    
    async with client:
        # Test read operation
        files = await client.call_tool("list_directory", {"path": "/data"})
        print(f"Files: {files}")
        
        # Test write operation (if enabled)
        result = await client.call_tool("write_file", {
            "path": "/data/test.txt",
            "content": "Test content"
        })
        print(f"Write result: {result}")

asyncio.run(test_server())
```

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## 📝 License

MIT License - see LICENSE file for details

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/remote-filesystem-mcp/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/remote-filesystem-mcp/discussions)
- **Documentation**: [MCP Protocol](https://modelcontextprotocol.io)

## 🔗 Related Projects

- [FastMCP](https://github.com/jlowin/fastmcp) - The Python MCP framework
- [Model Context Protocol](https://modelcontextprotocol.io) - The MCP specification
- [MCP Servers](https://github.com/modelcontextprotocol/servers) - Official MCP server examples
