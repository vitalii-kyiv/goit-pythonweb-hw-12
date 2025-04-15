import logging
from typing import Sequence

from sqlalchemy import select, or_, extract
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date, timedelta

from src.entity.models import Contact
from src.schemas.contact_schema import ContactCreateSchema, ContactUpdateSchema

logger = logging.getLogger("uvicorn.error")


class ContactRepository:
    """
    Repository class for managing Contact entities in the database.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize the repository with a database session.

        :param session: Async SQLAlchemy session
        """
        self.db = session

    async def get_contacts(self, limit: int, offset: int, search: str | None, user_id: int):
        """
        Retrieve a list of contacts with pagination and optional search.

        :param limit: Max number of contacts to return
        :param offset: Number of contacts to skip
        :param search: Optional search string for filtering by name or email
        :param user_id: ID of the user who owns the contacts
        :return: List of contacts
        """
        stmt = select(Contact).where(Contact.user_id == user_id).offset(offset).limit(limit)
        if search:
            stmt = stmt.where(
                or_(
                    Contact.first_name.ilike(f"%{search}%"),
                    Contact.last_name.ilike(f"%{search}%"),
                    Contact.email.ilike(f"%{search}%"),
                )
            )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_contact_by_id(self, contact_id: int) -> Contact | None:
        """
        Retrieve a single contact by its ID.

        :param contact_id: Contact ID
        :return: Contact instance or None if not found
        """
        stmt = select(Contact).filter_by(id=contact_id)
        contact = await self.db.execute(stmt)
        return contact.scalar_one_or_none()

    async def create_contact(self, body: ContactCreateSchema, user_id: int) -> Contact:
        """
        Create a new contact for a specific user.

        :param body: Contact creation data
        :param user_id: ID of the user creating the contact
        :return: Created contact instance
        """
        contact = Contact(**body.model_dump(), user_id=user_id)
        self.db.add(contact)
        await self.db.commit()
        await self.db.refresh(contact)
        return contact

    async def remove_contact(self, contact_id: int) -> Contact | None:
        """
        Delete a contact by its ID.

        :param contact_id: ID of the contact to remove
        :return: Deleted contact instance or None if not found
        """
        contact = await self.get_contact_by_id(contact_id)
        if contact:
            await self.db.delete(contact)
            await self.db.commit()
        return contact

    async def update_contact(self, contact_id: int, body: ContactUpdateSchema) -> Contact | None:
        """
        Update an existing contact.

        :param contact_id: ID of the contact to update
        :param body: Contact update data
        :return: Updated contact instance or None if not found
        """
        contact = await self.get_contact_by_id(contact_id)
        if contact:
            update_data = body.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(contact, key, value)
            await self.db.commit()
            await self.db.refresh(contact)
        return contact

    async def get_upcoming_birthdays(self, user_id: int):
        """
        Retrieve contacts with birthdays in the next 7 days.

        :param user_id: ID of the user who owns the contacts
        :return: List of contacts with upcoming birthdays
        """
        today = date.today()
        next_week = today + timedelta(days=7)
        stmt = select(Contact).where(
            Contact.user_id == user_id,
            or_(
                (extract('month', Contact.birthday) == today.month) & (extract('day', Contact.birthday) >= today.day),
                (extract('month', Contact.birthday) == next_week.month) & (
                    extract('day', Contact.birthday) <= next_week.day),
            )
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()
