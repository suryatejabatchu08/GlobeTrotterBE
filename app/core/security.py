from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.database import get_supabase
from supabase import Client
from typing import Optional
import logging

logger = logging.getLogger(__name__)

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    supabase: Client = Depends(get_supabase)
) -> dict:
    \"\"\"
    Validate JWT token and return current user.
    Supabase handles JWT validation automatically.
    \"\"\"
    try:
        token = credentials.credentials
        
        # Get user from Supabase using the token
        user_response = supabase.auth.get_user(token)
        
        if not user_response or not user_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user_response.user
        
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    supabase: Client = Depends(get_supabase)
) -> Optional[dict]:
    \"\"\"
    Optional authentication - returns user if authenticated, None otherwise.
    Used for endpoints that can be accessed both publicly and privately.
    \"\"\"
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        user_response = supabase.auth.get_user(token)
        return user_response.user if user_response else None
    except:
        return None
