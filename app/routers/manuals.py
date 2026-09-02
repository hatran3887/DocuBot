import uuid
from pathlib import Path

from fastapi import(
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status
)
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_client
from app.models import Client, Manual
from app.schemas import ManualResponse

router = APIRouter(prefix="/manuals", tags=["manuals"])


ALLOWED_CONTENT_TYPES = {
    'application/pdf',
    'text/plain',
    'text/markdown',
}


@router.post(
    '/',
    response_model=ManualResponse,
    status_code=status.HTTP_201_CREATED,
    summary='Upload a manual',
)
def upload_manual(
    file: UploadFile = File(...),
    current_client: Client = Depends(get_current_client),
    db: Session = Depends(get_db),
) -> Manual:
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f'Unsupported file type: {file.content_type}',
        )

    contents = file.file.read()
    size = len(contents)

    if size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='File is empty',
        )

    #TODO: Handle production: size limit
    if size > settings.max_upload_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f'File exceeds {settings.max_upload_size} bytes',
        )

    original_name = Path(file.filename or 'upload').name
    suffix = Path(original_name).suffix
    stored_name = f'{uuid.uuid4()}{suffix}'
    destination = settings.upload_dir / stored_name
    destination.write_bytes(contents)

    manual = Manual(
        client_id=current_client.id,
        filename=original_name,
        stored_filename=stored_name,
        status='uploaded',
    )

    db.add(manual)
    db.commit()
    db.refresh(manual)

    return manual


@router.get(
    "/{manual_id}",
    response_model=ManualResponse,
    summary="Get a manual by ID",
)
def get_manual(
    manual_id: uuid.UUID,
    current_client: Client = Depends(get_current_client),
    db: Session = Depends(get_db),
) -> Manual:
    manual = db.get(Manual, manual_id)

    if manual is None or manual.client_id != current_client.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Manual not found",
        )

    return manual