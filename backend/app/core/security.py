import logging

from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext

from app.core.settings import settings

logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


# --- RSA Key Loading ---
def load_rsa_private_key() -> str:
    """Load RSA private key from configured path."""
    try:
        with open(settings.JWT_PRIVATE_KEY_PATH) as f:
            return f.read()
    except FileNotFoundError:
        logger.critical("FATAL: JWT private key not found.")
        raise


def load_rsa_public_key() -> str:
    """Load RSA public key from configured path."""
    try:
        with open(settings.JWT_PUBLIC_KEY_PATH) as f:
            return f.read()
    except FileNotFoundError:
        logger.critical("FATAL: JWT public key not found.")
        raise


JWT_PRIVATE_KEY = load_rsa_private_key()
JWT_PUBLIC_KEY = load_rsa_public_key()


# --- Password Hashing ---
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password using argon2."""
    return pwd_context.hash(password)
