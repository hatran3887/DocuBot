from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.routers import clients, manuals, search


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(
    title='Docubot',
    description='Docubot API',
    version='0.1.0',
    lifespan=lifespan
)

app.include_router(clients.router)
app.include_router(manuals.router)
app.include_router(search.router)

@app.get('/health', tags=['system'])
def health():
    return {'status': 'ok'}