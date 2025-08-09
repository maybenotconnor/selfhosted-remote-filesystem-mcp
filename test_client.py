#!/usr/bin/env python3
"""
Test client for Remote Filesystem MCP Server
"""

import asyncio
import sys
from fastmcp import Client


async def test_server(server_url: str, token: str):
    """Test the MCP server with various operations."""
    
    print(f"🔗 Connecting to: {server_url}")
    print(f"🔑 Using token: {token[:20]}...")
    print("-" * 60)
    
    client = Client(server_url, auth=token)
    
    try:
        async with client:
            print("✅ Connected successfully!")
            
            # Test 1: List root directory
            print("\n📁 Test 1: List root directory")
            try:
                files = await client.call_tool("list_directory", {})
                print(f"   Found {len(files)} items")
                for file in files[:5]:  # Show first 5
                    print(f"   - {file['name']} ({'dir' if file['is_directory'] else 'file'})")
            except Exception as e:
                print(f"   ❌ Error: {e}")
            
            # Test 2: Create a test file
            print("\n📝 Test 2: Write test file")
            try:
                result = await client.call_tool("write_file", {
                    "path": "test_file.txt",
                    "content": "Hello from MCP test client!\nThis is a test file."
                })
                print(f"   ✅ Created: {result['relative_path']}")
                print(f"   Bytes written: {result['bytes_written']}")
            except Exception as e:
                print(f"   ❌ Error: {e}")
            
            # Test 3: Read the test file
            print("\n📖 Test 3: Read test file")
            try:
                content = await client.call_tool("read_file", {
                    "path": "test_file.txt"
                })
                print(f"   Type: {content['type']}")
                print(f"   Content preview: {content['content'][:50]}...")
            except Exception as e:
                print(f"   ❌ Error: {e}")
            
            # Test 4: Create a directory
            print("\n📁 Test 4: Create directory")
            try:
                result = await client.call_tool("create_directory", {
                    "path": "test_directory"
                })
                print(f"   ✅ Created: {result['relative_path']}")
            except Exception as e:
                print(f"   ❌ Error: {e}")
            
            # Test 5: Search for files
            print("\n🔍 Test 5: Search for .txt files")
            try:
                matches = await client.call_tool("search_files", {
                    "pattern": "*.txt"
                })
                print(f"   Found {len(matches)} .txt files")
                for match in matches[:3]:  # Show first 3
                    print(f"   - {match['relative_path']}")
            except Exception as e:
                print(f"   ❌ Error: {e}")
            
            # Test 6: Get file info
            print("\n📊 Test 6: Get file info")
            try:
                info = await client.call_tool("get_file_info", {
                    "path": "test_file.txt"
                })
                print(f"   Path: {info['relative_path']}")
                print(f"   Size: {info['size']} bytes")
                print(f"   Modified: {info['modified']}")
            except Exception as e:
                print(f"   ❌ Error: {e}")
            
            # Test 7: Edit file
            print("\n✏️ Test 7: Edit file")
            try:
                result = await client.call_tool("edit_file", {
                    "path": "test_file.txt",
                    "search": "Hello",
                    "replace": "Greetings"
                })
                print(f"   ✅ Edited: {result['relative_path']}")
                print(f"   Replacements: {result['replacements']}")
            except Exception as e:
                print(f"   ❌ Error: {e}")
            
            # Test 8: Clean up (optional)
            print("\n🧹 Test 8: Clean up test files")
            try:
                # Delete test file
                result = await client.call_tool("delete_file", {
                    "path": "test_file.txt"
                })
                print(f"   ✅ Deleted file: {result['relative_path']}")
                
                # Delete test directory
                result = await client.call_tool("delete_file", {
                    "path": "test_directory",
                    "recursive": True
                })
                print(f"   ✅ Deleted directory: {result['relative_path']}")
            except Exception as e:
                print(f"   ❌ Error: {e}")
            
            print("\n" + "=" * 60)
            print("✅ All tests completed!")
            
    except Exception as e:
        print(f"\n❌ Connection error: {e}")
        sys.exit(1)


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python test_client.py <token> [server_url]")
        print("\nExample:")
        print("  python test_client.py 'your-jwt-token-here'")
        print("  python test_client.py 'your-jwt-token-here' 'http://localhost:8080/mcp'")
        sys.exit(1)
    
    token = sys.argv[1]
    server_url = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:8080/mcp"
    
    asyncio.run(test_server(server_url, token))


if __name__ == "__main__":
    main()