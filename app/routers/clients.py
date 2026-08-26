import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Client
from app.schemas import ClientCreate, ClientCreateResponse, ClientResponse
from app.dependencies import get_current_client

router = APIRouter(prefix='/clients', tags=['clients'])

#test api key pPiFSPrIC5oTceZ2UT6DNG2BEmb2Sks_6Jk5PYq31_A

@router.post(
    '',
    response_model=ClientCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary='Create a new client',
)
def create_client(
    payload: ClientCreate,
    db: Session = Depends(get_db),
) -> Client:
    existing = db.scalar(select(Client).where(Client.email == payload.email))
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='Client with this email already exists',
        )

    #TODO: hash API keys, currently stored in plaintext.
    client = Client(
        name=payload.name,
        email=payload.email,
        api_key=secrets.token_urlsafe(32),
    )

    db.add(client)
    db.commit()
    db.refresh(client)

    return client


@router.get(
    "/me",
    response_model=ClientResponse,
    summary='Get current client info',
)
def get_current_client_info(
    current_client: Client = Depends(get_current_client),
) -> Client:
    return current_client