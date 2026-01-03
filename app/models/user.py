from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class User(BaseModel):
    id: str  # Supabase Auth UUID
    email: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    language_preference: str = "en"
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
