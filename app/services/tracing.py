from contextlib import contextmanager
from typing import Any, Iterator
from uuid import UUID, uuid4

from langfuse import get_client, propagate_attributes

from app.config import settings


class _NullSpan:
    """Stands in for a LangfuseSpan when tracing is disabled."""

    def update(self, **kwargs: Any) -> None:
        pass


_NULL_SPAN = _NullSpan()


class _Trace:
    """Wraps the root observation of one chat request."""

    def __init__(self, root: Any, trace_id: str) -> None:
        self._root = root
        self.id = trace_id

    @contextmanager
    def span(self, name: str) -> Iterator[Any]:
        """Yield a child span. Callers use span.update(output=...)."""
        if self._root is None:
            yield _NULL_SPAN
            return
        with get_client().start_as_current_observation(
            as_type="span", name=name
        ) as span:
            yield span

    def output(self, answer: str, refused: bool = False) -> None:
        if self._root is None:
            return
        self._root.update(output={"answer": answer, "refused": refused})

    def error(self, message: str) -> None:
        if self._root is None:
            return
        self._root.update(
            output={"error": message},
            level="ERROR",
            status_message=message[:500],
        )


@contextmanager
def trace_chat(
    question: str,
    client_id: UUID,
    conversation_id: UUID,
) -> Iterator[_Trace]:
    if not settings.langfuse_enabled:
        yield _Trace(None, str(uuid4()))
        return

    client = get_client()

    with client.start_as_current_observation(
        as_type="span",
        name="chat",
        input={"question": question},
    ) as root:
        with propagate_attributes(
            user_id=str(client_id),
            session_id=str(conversation_id),
            tags=["chat", f"model:{settings.chat_model}"],
        ):
            yield _Trace(root, root.trace_id)


def record_feedback(trace_id: str, rating: str, comment: str | None) -> None:
    if not settings.langfuse_enabled:
        return
    get_client().create_score(
        trace_id=trace_id,
        name="user_feedback",
        value=1 if rating == "up" else 0,
        data_type="NUMERIC",
        comment=comment,
    )