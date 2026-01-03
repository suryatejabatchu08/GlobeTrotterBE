from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime

class Stop(BaseModel):
    id: str
    trip_id: str
    name: str
    location: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    arrival_date: Optional[date] = None
    departure_date: Optional[date] = None
    order: int
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
