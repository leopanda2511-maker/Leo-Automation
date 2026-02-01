from passlib.context import CryptContext
import bcrypt

# Use bcrypt directly to avoid passlib compatibility issues
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password"""
    # Ensure password is bytes and not too long
    if isinstance(password, str):
        password = password.encode('utf-8')
    # Truncate if necessary (bcrypt limit is 72 bytes)
    if len(password) > 72:
        password = password[:72]
    # Hash using bcrypt directly
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password, salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    try:
        # Ensure password is bytes
        if isinstance(plain_password, str):
            plain_password = plain_password.encode('utf-8')
        # Truncate if necessary
        if len(plain_password) > 72:
            plain_password = plain_password[:72]
        # Verify using bcrypt directly
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(plain_password, hashed_bytes)
    except Exception:
        return False
