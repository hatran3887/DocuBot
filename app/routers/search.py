from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_client
from app.models import Client
from app.schemas import SearchRequest, SearchResponse, SearchResultItem
from app.services.retrieval import retrieve

router = APIRouter(prefix="/search", tags=["search"])


@router.post('', response_model=SearchResponse)
def search(
    payload: SearchRequest,
    db: Session = Depends(get_db),
    current_client: Client = Depends(get_current_client),
) -> SearchResponse:
    chunks = retrieve(
        db=db,
        client_id=current_client.id,
        question=payload.question,
        top_k=payload.top_k,
    )

    return SearchResponse(
        question=payload.question,
        results=[SearchResultItem.model_validate(chunk) for chunk in chunks],
    )