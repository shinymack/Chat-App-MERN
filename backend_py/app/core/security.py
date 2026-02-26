import datetime
import jwt
import bcrypt
from app.core.config import settings
from typing import Optional, Union

def hash_password(password: str) -> str:
    """Hashes a password using bcrypt."""
    salt = bcrypt.gensalt(rounds=10)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a bcrypt hash."""
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

def create_access_token(user_id: Union[str, int]) -> str:
    """Creates a JWT access token valid for 7 days (matches Node implementation)."""
    expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=7)
    to_encode = {"userId": str(user_id), "exp": expire}
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret, algorithm="HS256")
    return encoded_jwt

def verify_access_token(token: str) -> Optional[str]:
    """Verifies and decodes a JWT token, extracting the userId."""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        return payload.get("userId")
    except jwt.ExpiredSignatureError:
        return None
    except jwt.PyJWTError:
        return None
