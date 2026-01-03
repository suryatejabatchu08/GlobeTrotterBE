from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date


class TripBase(BaseModel):
    name: str
    start_date: date
    end_date: date
    photo_url: Optional[str] = None
    description: Optional[str] = None


class TripCreate(TripBase):
    pass


class TripUpdate(BaseModel):
    name: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    photo_url: Optional[str] = None
    description: Optional[str] = None
    is_public: Optional[bool] = None


class TripResponse(TripBase):
    id: str
    user_id: str
    is_public: bool
    share_token: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TripListResponse(BaseModel):
    trips: List[TripResponse]
    total: int


class ShareTripResponse(BaseModel):
    share_url: str
    share_token: str
