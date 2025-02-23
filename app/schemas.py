from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict
from datetime import datetime
from enum import Enum


class TicketStatus(str, Enum):
    BOOKED = "BOOKED"
    CANCELLED = "CANCELLED"


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    size: int = Field(default=10, ge=1, le=100)


class TicketCreate(BaseModel):
    passenger_name: str = Field(..., min_length=2, max_length=100)
    seat_number: str = Field(..., pattern="^[A-Z][0-9]+$")
    amount: float = Field(..., gt=0)


class TicketResponse(BaseModel):
    id: int
    booking_reference: str
    passenger_name: str
    seat_number: str
    amount: float
    status: TicketStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PaginatedResponse(BaseModel):
    items: List[TicketResponse]
    total: int
    page: int
    size: int
    pages: int


class BookingResponse(BaseModel):
    status: str
    code: str
    message: str
    booking_reference: Optional[str] = None
    ticket_details: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
