from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Client

api_key_header = APIKeyHeader(name='X-API-Key', auto_error=False)


def get_current_client(
    api_key: str | None = Depends(api_key_header),
    db: Session = Depends(get_db)
) -> Client:
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Missing API key',
            headers={'WWW-Authenticate': 'ApiKey'}
        )

    client = db.scalar(select(Client).where(Client.api_key == api_key))

    if client is None or not client.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid API key',
            headers={'WWW-Authenticate': 'ApiKey'}
        )

    return client