import os
import json
from pathlib import Path
from typing import Optional, Dict
from fastmcp.server.auth.providers.jwt import JWTVerifier, RSAKeyPair


def setup_authentication() -> JWTVerifier:
    """Set up authentication with automatic key generation and persistence.
    
    Returns:
        JWTVerifier configured with persistent keys
    """
    config_dir = Path(os.getenv("CONFIG_DIR", "/config"))
    config_dir.mkdir(exist_ok=True, parents=True)
    
    keys_file = config_dir / "jwt_keys.json"
    tokens_file = config_dir / "tokens.txt"
    
    # Try to load existing keys
    if keys_file.exists():
        print("🔐 Loading existing authentication keys...")
        with open(keys_file, 'r') as f:
            keys_data = json.load(f)
        public_key = keys_data['public_key']
        private_key = keys_data['private_key']
        first_run = False
    else:
        # Generate new keys on first run
        print("🔐 First run detected - generating authentication keys...")
        key_pair = RSAKeyPair.generate()
        public_key = key_pair.public_key
        private_key = key_pair.private_key
        
        # Save keys for persistence
        keys_data = {
            'public_key': str(public_key),  # Convert SecretStr to string
            'private_key': str(private_key)  # Convert SecretStr to string
        }
        with open(keys_file, 'w') as f:
            json.dump(keys_data, f, indent=2)
        
        # Set permissions for security
        keys_file.chmod(0o600)
        first_run = True
    
    # Create auth provider
    auth = JWTVerifier(
        public_key=public_key,
        issuer="filesystem-mcp",
        audience="filesystem-mcp"
    )
    
    # Generate tokens (always on first run, or if tokens file missing)
    if first_run or not tokens_file.exists():
        key_pair = RSAKeyPair(public_key=public_key, private_key=private_key)
        
        # Generate three tokens with different access levels
        tokens = {
            'admin': key_pair.create_token(
                subject="admin",
                issuer="filesystem-mcp",
                audience="filesystem-mcp",
                scopes=["read", "write", "admin"]
            ),
            'readonly': key_pair.create_token(
                subject="readonly",
                issuer="filesystem-mcp",
                audience="filesystem-mcp",
                scopes=["read"]
            )
        }
        
        # Save tokens to file for reference
        with open(tokens_file, 'w') as f:
            f.write("=" * 60 + "\n")
            f.write("🔑 AUTHENTICATION TOKENS\n")
            f.write("=" * 60 + "\n\n")
            f.write("Admin Token (full access):\n")
            f.write(tokens['admin'] + "\n\n")
            f.write("Read-Only Token:\n")
            f.write(tokens['readonly'] + "\n\n")
            f.write("=" * 60 + "\n")
            f.write("Use in Authorization header: Bearer <token>\n")
        
        # Set secure permissions on tokens file
        tokens_file.chmod(0o600)
        
        # Display secure message (never log actual tokens)
        if first_run:
            print("\n" + "━" * 60)
            print("🔐 AUTHENTICATION SETUP COMPLETE")
            print("━" * 60)
            print("\n✅ Tokens generated and saved securely")
            print(f"📁 Location: {tokens_file}")
            print("\n🔑 To retrieve your tokens, run:")
            print(f"   docker exec {os.getenv('HOSTNAME', 'filesystem-mcp')} cat /config/tokens.txt")
            print("\n" + "━" * 60 + "\n")
    else:
        print(f"💡 Using existing tokens from: {tokens_file}")
    
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