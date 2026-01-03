from pydantic import BaseModel
from typing import Optional
from datetime import datetime, time


class Activity(BaseModel):
    id: str
    stop_id: str
    name: str
    description: Optional[str] = None
    activity_type: str  # e.g., 'restaurant', 'museum', 'hotel', 'attraction'
    scheduled_time: Optional[time] = None
    duration_minutes: Optional[int] = None
    cost: Optional[float] = None
    currency: str = "USD"
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    foursquare_id: Optional[str] = None
    order: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
