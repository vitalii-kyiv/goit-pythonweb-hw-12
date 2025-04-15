import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.core.depend_service import get_current_user
from src.services.contacts_services import ContactService
from src.schemas.contact_schema import (
    ContactCreateSchema,
    ContactResponseSchema,
    ContactUpdateSchema,
)
from src.entity.models import User

router = APIRouter(prefix="/contacts", tags=["contacts"])
logger = logging.getLogger("uvicorn.error")


@router.get("/", response_model=list[ContactResponseSchema])
async def get_contacts(
    limit: int = Query(10, ge=1, le=500),
    offset: int = Query(0, ge=0),
    search: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve a list of user's contacts with optional pagination and search.

    :param limit: Maximum number of contacts to return (default: 10)
    :param offset: Number of contacts to skip (default: 0)
    :param search: Optional search filter for name or email
    :param db: Database session
    :param current_user: Authenticated user
    :return: List of contacts
    """
    service = ContactService(db, current_user)
    return await service.get_contacts(limit, offset, search)


@router.get("/birthdays/upcoming", response_model=list[ContactResponseSchema])
async def get_upcoming_birthdays(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve a list of contacts with birthdays in the upcoming 7 days.

    :param db: Database session
    :param current_user: Authenticated user
    :return: List of contacts with upcoming birthdays
    """
    service = ContactService(db, current_user)
    return await service.get_upcoming_birthdays()


@router.get("/{contact_id}", response_model=ContactResponseSchema)
async def get_contact(
    contact_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve a contact by its ID.

    :param contact_id: Contact ID
    :param db: Database session
    :param current_user: Authenticated user
    :return: Contact details if found
    """
    service = ContactService(db, current_user)
    contact = await service.get_contact(contact_id)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact


@router.post("/", response_model=ContactResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_contact(
    body: ContactCreateSchema,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new contact for the current user.

    :param body: Contact creation data
    :param db: Database session
    :param current_user: Authenticated user
    :return: Created contact
    """
    service = ContactService(db, current_user)
    return await service.create_contact(body)


@router.put("/{contact_id}", response_model=ContactResponseSchema)
async def update_contact(
    contact_id: int,
    body: ContactUpdateSchema,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update an existing contact's information.

    :param contact_id: Contact ID
    :param body: Updated contact data
    :param db: Database session
    :param current_user: Authenticated user
    :return: Updated contact if found
    """
    service = ContactService(db, current_user)
    contact = await service.update_contact(contact_id, body)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(
    contact_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete a contact by its ID.

    :param contact_id: Contact ID
    :param db: Database session
    :param current_user: Authenticated user
    """
    service = ContactService(db, current_user)
    await service.remove_contact(contact_id)
    return None
