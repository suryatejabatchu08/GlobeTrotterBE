from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date

from sqlalchemy import Column, Integer, String, ForeignKey
from app.core.database import Base

class Stop(BaseModel):
    id: str
    trip_id: str
    name: str
    location: str  # City/Place name
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    arrival_date: Optional[date] = None
    departure_date: Optional[date] = None
    order: int  # Order in the trip
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class Activity(Base):
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True)
    stop_id = Column(Integer, ForeignKey("stops.id"))
    fsq_place_id = Column(String)
    name = Column(String)
    category = Column(String)
    estimated_cost = Column(Integer)
