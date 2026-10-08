import os
import hashlib
import base64
import secrets
from cryptography.fernet import Fernet
from app.core.config import settings


def generate_pkce() -> tuple[str, str]:
    """Generates PKCE (code_verifier, code_challenge) per RFC 7636."""
    verifier_bytes = secrets.token_bytes(32)
    code_verifier = base64.urlsafe_b64encode(verifier_bytes).decode("utf-8").rstrip("=")
    
    sha256_hash = hashlib.sha256(code_verifier.encode("utf-8")).digest()
    code_challenge = base64.urlsafe_b64encode(sha256_hash).decode("utf-8").rstrip("=")
    return code_verifier, code_challenge


def _get_fernet() -> Fernet:
    """Derives a 32-byte Fernet key from settings.ENCRYPTION_KEY."""
    raw_key = settings.ENCRYPTION_KEY.encode("utf-8")
    key_32 = hashlib.sha256(raw_key).digest()
    fernet_key = base64.urlsafe_b64encode(key_32)
    return Fernet(fernet_key)


def encrypt_token(plain_token: str) -> str:
    """Encrypts an access token before storing in MongoDB."""
    f = _get_fernet()
    return f.encrypt(plain_token.encode("utf-8")).decode("utf-8")


def decrypt_token(encrypted_token: str) -> str:
    """Decrypts an access token from MongoDB."""
    f = _get_fernet()
    return f.decrypt(encrypted_token.encode("utf-8")).decode("utf-8")
