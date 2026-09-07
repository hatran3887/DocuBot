import time
from dataclasses import dataclass
from decimal import Decimal

from openai import APIStatusError, RateLimitError, APIConnectionError

from app.config import settings
from app.services.prompts import SYSTEM_PROMPT, build_user_prompt
from app.services.retrieval import RetrievedChunk

if settings.langfuse_enabled:
    from langfuse.openai import OpenAI
else:
    from openai import OpenAI


_client = OpenAI(api_key=settings.openai_api_key)


class GenerationError(Exception):
    """Called when a generation error occurs"""


@dataclass
class Generation:
    answer: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    cost: Decimal
    latency_ms: int


def generate_answer(
    question: str,
    chunks: list[RetrievedChunk],
    model: str,
) -> Generation:
    user_prompt = build_user_prompt(question, chunks)
    started = time.perf_counter()

    try:
        response = _client.chat.completions.create(
            model=model,
            temperature=settings.chat_temperature,
            max_tokens=settings.chat_max_tokens,
            messages=[
                {'role': 'system', 'content': SYSTEM_PROMPT},
                {'role': 'user', 'content': user_prompt},
            ],
            **_trace_kwargs(model),
        )
    except (RateLimitError, APIConnectionError) as e:
        raise GenerationError(f"The assistant is busy. Try again: {e}") from e
    except APIStatusError as e:
        raise GenerationError(f"The assistant is unavailable: {e}") from e

    latency_ms = int((time.perf_counter() - started) * 1000)
    usage = response.usage
    prompt_tokens = usage.prompt_tokens if usage else 0
    completion_tokens = usage.completion_tokens if usage else 0

    return Generation(
        answer=(response.choices[0].message.content or '').strip(),
        model=model,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        cost=_cost(model, prompt_tokens, completion_tokens),
        latency_ms=latency_ms,
    )


def _trace_kwargs(model: str) -> dict[str, str]:
    if not settings.langfuse_enabled:
        return {}
    return {'name': f'answer-{model}'}


def _cost(model: str, prompt_tokens: int, completion_tokens: int) -> Decimal:
    prices = settings.cost_per_million.get(model)
    if prices is None:
        return Decimal('0')

    million = Decimal(1_000_000)
    inp = Decimal(prompt_tokens) / million * Decimal(str(prices[0]))
    out = Decimal(completion_tokens) / million * Decimal(str(prices[1]))
    return (inp + out).quantize(Decimal("0.000001"))