from typing import Optional, List, Tuple
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.ticket import Ticket, BookingResponse, TicketStatus


class TicketRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_ticket(self, ticket_data: dict) -> Ticket:
        ticket = Ticket(**ticket_data)
        self.session.add(ticket)
        await self.session.commit()
        return ticket

    async def get_ticket(self, booking_reference: str) -> Optional[Ticket]:
        result = await self.session.execute(
            select(Ticket).filter_by(booking_reference=booking_reference)
        )
        return result.scalar_one_or_none()

    async def get_ticket_by_id(self, ticket_id: int) -> Optional[Ticket]:
        result = await self.session.execute(
            select(Ticket).filter_by(id=ticket_id)
        )
        return result.scalar_one_or_none()

    async def get_tickets_paginated(self, page: int, size: int) -> Tuple[List[Ticket], int]:
        offset = (page - 1) * size

        # Get total count
        count_query = select(func.count()).select_from(Ticket)
        total = await self.session.scalar(count_query)

        # Get paginated results
        query = select(Ticket).offset(offset).limit(size)
        result = await self.session.execute(query)
        tickets = result.scalars().all()

        return tickets, total

    async def update_ticket_status(self, booking_reference: str, status: TicketStatus) -> Optional[Ticket]:
        ticket = await self.get_ticket(booking_reference)
        if ticket:
            ticket.status = status
            await self.session.commit()
        return ticket

    async def save_booking_response(self, request_id: str, response: dict) -> BookingResponse:
        booking_response = BookingResponse(
            request_id=request_id,
            response_data=response
        )
        self.session.add(booking_response)
        await self.session.commit()
        return booking_response

    async def get_booking_response(self, request_id: str) -> Optional[BookingResponse]:
        result = await self.session.execute(
            select(BookingResponse).filter_by(request_id=request_id)
        )
        return result.scalar_one_or_none()
