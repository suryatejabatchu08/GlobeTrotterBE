from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date


class Trip(BaseModel):
    id: str
    user_id: str
    name: str
    start_date: date
    end_date: date
    photo_url: Optional[str] = None
    description: Optional[str] = None
    is_public: bool = False
    share_token: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
