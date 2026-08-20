from contextlib import asynccontextmanager
from app.config import settings
from fastapi import FastAPI


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


@app.get('/health', tags=['system'])
def health():
    return {'status': 'ok'}