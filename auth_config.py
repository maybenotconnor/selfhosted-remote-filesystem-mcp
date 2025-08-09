import os
import inspect
from typing import Optional
from fastmcp.server.auth import BearerAuthProvider
from fastmcp.server.auth.providers.bearer import RSAKeyPair


def setup_authentication() -> Optional[BearerAuthProvider]:
    """Set up authentication based on environment variables.
    
    Returns:
        BearerAuthProvider if authentication is enabled, None otherwise
    """
    # Check if authentication is disabled
    if os.getenv("DISABLE_AUTH", "false").lower() == "true":
        print("⚠️  WARNING: Authentication is disabled. Server is publicly accessible!")
        return None
    
    # Try to load existing keys from environment
    public_key = os.getenv("JWT_PUBLIC_KEY")
    private_key = os.getenv("JWT_PRIVATE_KEY")
    
    # If keys are provided as file paths, read them
    if public_key and os.path.isfile(public_key):
        with open(public_key, 'r') as f:
            public_key = f.read()
    
    if private_key and os.path.isfile(private_key):
        with open(private_key, 'r') as f:
            private_key = f.read()
    
    # Generate keys if not provided
    if not public_key:
        print("🔐 Generating RSA key pair for authentication...")
        key_pair = RSAKeyPair.generate()
        public_key = key_pair.public_key
        
        # Generate a sample token for testing
        if not private_key:
            private_key = key_pair.private_key
            
            # Generate sample tokens with different scopes
            audience = os.getenv("JWT_AUDIENCE", "filesystem-mcp")
            issuer = os.getenv("JWT_ISSUER", "filesystem-mcp-server")
            
            admin_token = key_pair.create_token(
                subject="admin",
                issuer=issuer,
                audience=audience,
                scopes=["read", "write", "admin"]
            )
            
            readonly_token = key_pair.create_token(
                subject="readonly-user",
                issuer=issuer,
                audience=audience,
                scopes=["read"]
            )
            
            print("\n" + "="*60)
            print("🔑 AUTHENTICATION TOKENS GENERATED")
            print("="*60)
            print("\n📝 Admin Token (full access):")
            print(f"   {admin_token}")
            print("\n📖 Read-Only Token:")
            print(f"   {readonly_token}")
            print("\n💡 Use these tokens in the Authorization header:")
            print("   Authorization: Bearer <token>")
            print("="*60 + "\n")
    
    # Configure authentication provider
    auth = BearerAuthProvider(
        public_key=public_key,
        issuer=os.getenv("JWT_ISSUER", "filesystem-mcp-server"),
        audience=os.getenv("JWT_AUDIENCE", "filesystem-mcp"),
        algorithm=os.getenv("JWT_ALGORITHM", "RS256")
    )
    
    return auth


def check_scope(required_scope: str, scopes: list) -> bool:
    """Check if required scope is present in token scopes.
    
    Args:
        required_scope: The scope required for the operation
        scopes: List of scopes from the token
        
    Returns:
        True if scope is present or 'admin' scope is present
    """
    return required_scope in scopes or "admin" in scopes