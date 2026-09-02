import time

from openai import APIConnectionError, APIStatusError, OpenAI, RateLimitError

from app.config import settings

_client = OpenAI(api_key=settings.openai_api_key)

MAX_RETRIES = 4


class EmbeddingError(Exception):
    """Raised when embeddings could not be generated."""


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Return one vector per input text."""
    vectors: list[list[float]] = []

    for start in range(0, len(texts), settings.embedding_batch_size):
        batch = texts[start: start + settings.embedding_batch_size]
        vectors.extend(_embed_batch(batch))

    return vectors


def _embed_batch(batch: list[str]) -> list[list[float]]:
    for attempt in range(MAX_RETRIES):
        try:
            response = _client.embeddings.create(
                model=settings.embedding_model,
                input=batch,
            )
        except (RateLimitError, APIConnectionError) as e:
            if attempt == MAX_RETRIES - 1:
                raise EmbeddingError(
                    f'Embedding API unavailable after {MAX_RETRIES} attempts: {e}'
                ) from e
            time.sleep(2 ** attempt)
            continue
        except APIStatusError as e:
            raise EmbeddingError(
                f'Embedding API failed: {e}'
            ) from e

        items = sorted(response.data, key=lambda item: item.index)
        return [item.embedding for item in items]

    raise EmbeddingError('Unreachable')