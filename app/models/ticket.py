from datetime import datetime
import json
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Enum as SQLEnum,
    Float,
    Text,
    TypeDecorator
)
from sqlalchemy.ext.declarative import declarative_base
from enum import Enum

Base = declarative_base()


class TicketStatus(str, Enum):
    BOOKED = "BOOKED"
    CANCELLED = "CANCELLED"


class JSONEncodedDict(TypeDecorator):
    """Represents an immutable structure as a json-encoded string."""
    impl = Text

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
        return value


class BookingResponse(Base):
    __tablename__ = "booking_responses"

    id = Column(Integer, primary_key=True)
    request_id = Column(String(50), unique=True, nullable=False)
    response_data = Column(JSONEncodedDict, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True)
    booking_reference = Column(String(50), unique=True, nullable=False)
    customer_name = Column(String(100), nullable=False)
    seat_number = Column(String(10), nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(SQLEnum(TicketStatus), nullable=False, default=TicketStatus.BOOKED)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
