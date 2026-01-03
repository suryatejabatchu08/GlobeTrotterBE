from pydantic import BaseModel
from typing import Optional
from datetime import datetime, time


class ActivityBase(BaseModel):
    name: str
    description: Optional[str] = None
    activity_type: str
    scheduled_time: Optional[time] = None
    duration_minutes: Optional[int] = None
    cost: Optional[float] = None
    currency: str = "USD"
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    foursquare_id: Optional[str] = None
    order: int = 0


class ActivityCreate(ActivityBase):
    stop_id: str


class ActivityUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    activity_type: Optional[str] = None
    scheduled_time: Optional[time] = None
    duration_minutes: Optional[int] = None
    cost: Optional[float] = None
    currency: Optional[str] = None
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    order: Optional[int] = None


class ActivityResponse(ActivityBase):
    id: str
    stop_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

from pydantic import BaseModel

class ActivityCreate(BaseModel):
    fsq_place_id: str
    name: str
    category: str

from pydantic import BaseModel
from typing import Optional

class ScheduleActivityCreate(BaseModel):
    trip_id: str
    city: str
    day: int
    fsq_place_id: str
    name: str
    category: Optional[str] = None
    estimated_cost: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class ScheduleActivityUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    estimated_cost: Optional[int] = None
    day: Optional[int] = None
