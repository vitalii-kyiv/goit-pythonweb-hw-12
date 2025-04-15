from sqlalchemy.ext.asyncio import AsyncSession

from src.repository.contacts_repository import ContactRepository
from src.schemas.contact_schema import ContactCreateSchema, ContactUpdateSchema
from src.entity.models import User


class ContactService:
    """
    Service layer for handling business logic related to contacts.

    Attributes:
        db (AsyncSession): The database session.
        current_user (User): The currently authenticated user.
        contact_repository (ContactRepository): Repository for contact operations.
    """

    def __init__(self, db: AsyncSession, current_user: User):
        self.db = db
        self.current_user = current_user
        self.contact_repository = ContactRepository(db)

    async def create_contact(self, body: ContactCreateSchema):
        """
        Create a new contact for the current user.

        Args:
            body (ContactCreateSchema): Contact creation data.

        Returns:
            The newly created contact.
        """
        return await self.contact_repository.create_contact(body, self.current_user.id)

    async def get_contacts(
        self, limit: int = 100, offset: int = 0, search: str | None = None
    ):
        """
        Retrieve a list of user's contacts with optional pagination and search.

        Args:
            limit (int): Maximum number of contacts to return.
            offset (int): Number of contacts to skip.
            search (str | None): Optional search keyword.

        Returns:
            A list of matching contacts.
        """
        return await self.contact_repository.get_contacts(
            limit, offset, search, self.current_user.id
        )

    async def get_contact(self, contact_id: int):
        """
        Retrieve a contact by ID if it belongs to the current user.

        Args:
            contact_id (int): Contact ID.

        Returns:
            The contact if found and owned by the current user, otherwise None.
        """
        contact = await self.contact_repository.get_contact_by_id(contact_id)
        if contact and contact.user_id != self.current_user.id:
            return None  # or raise 403 Forbidden
        return contact

    async def update_contact(self, contact_id: int, body: ContactUpdateSchema):
        """
        Update an existing contact if owned by the current user.

        Args:
            contact_id (int): Contact ID.
            body (ContactUpdateSchema): Updated contact data.

        Returns:
            The updated contact or None if not found or unauthorized.
        """
        contact = await self.get_contact(contact_id)
        if contact is None:
            return None
        return await self.contact_repository.update_contact(contact_id, body)

    async def remove_contact(self, contact_id: int):
        """
        Delete a contact by ID if it belongs to the current user.

        Args:
            contact_id (int): Contact ID.

        Returns:
            The deleted contact or None if not found or unauthorized.
        """
        contact = await self.get_contact(contact_id)
        if contact is None:
            return None
        return await self.contact_repository.remove_contact(contact_id)

    async def get_upcoming_birthdays(self):
        """
        Retrieve contacts with upcoming birthdays within 7 days.

        Returns:
            A list of contacts with birthdays coming soon.
        """
        return await self.contact_repository.get_upcoming_birthdays(
            self.current_user.id
        )
