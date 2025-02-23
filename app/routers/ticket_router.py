from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.db.session import get_db
from app.services.ticket_service import TicketService
from app.repositories.ticket_repository import TicketRepository
from app.redis_cache import RedisCache
from app.schemas import (
    TicketCreate,
    TicketResponse,
    PaginationParams,
    PaginatedResponse,
    BookingResponse
)
import redis
from app.core.config import settings

router = APIRouter()

# Redis client
redis_client = redis.from_url(settings.REDIS_URL)
redis_cache = RedisCache(redis_client)


# Dependency for TicketService
async def get_ticket_service(db: AsyncSession = Depends(get_db)) -> TicketService:
    repository = TicketRepository(db)
    return TicketService(repository, redis_cache)


@router.post("/tickets", response_model=BookingResponse)
async def book_ticket(
        ticket: TicketCreate,
        service: TicketService = Depends(get_ticket_service)
):
    response, status_code = await service.book_ticket(ticket)
    return response


@router.get("/tickets/{ticket_id}", response_model=TicketResponse)
async def get_ticket_details(
        ticket_id: int,
        service: TicketService = Depends(get_ticket_service)
):
    ticket = await service.get_ticket_details(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


@router.get("/tickets", response_model=PaginatedResponse)
async def list_tickets(
        page: int = Query(1, ge=1),
        size: int = Query(10, ge=1, le=100),
        service: TicketService = Depends(get_ticket_service)
):
    pagination = PaginationParams(page=page, size=size)
    return await service.get_list_of_tickets(pagination)


@router.delete("/tickets/{ticket_id}", response_model=BookingResponse)
async def cancel_ticket(
        ticket_id: int,
        service: TicketService = Depends(get_ticket_service)
):
    response, status_code = await service.cancel_ticket(ticket_id)
    return response
