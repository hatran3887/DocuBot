from dataclasses import dataclass

from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)
import tiktoken

CHUNK_TOKENS = 512
OVERLAP_TOKENS = 64

HEADERS = [('#', 'h1'), ('##', 'h2'), ('###', 'h3')]

_ENCODER = tiktoken.get_encoding('cl100k_base')


@dataclass
class Chunk:
    index: int
    content: str
    section_title: str | None
    token_count: int


def _splitter() -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        encoding_name='cl100k_base',
        chunk_size=CHUNK_TOKENS,
        chunk_overlap=OVERLAP_TOKENS,
    )


def chunk_markdown(text: str) -> list[Chunk]:
    header_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=HEADERS,
        strip_headers=False,
    )
    sections = header_splitter.split_text(text)

    splitter = _splitter()
    chunks: list[Chunk] = []

    for section in sections:
        title = _title_from(section.metadata)
        for piece in splitter.split_text(section.page_content):
            chunks.append(
                Chunk(
                    index=len(chunks),
                    content=piece,
                    section_title=title,
                    token_count=_count(piece),
                )
            )

    return chunks


def chunk_plain(text: str) -> list[Chunk]:
    splitter = _splitter()
    return [
        Chunk(
            index=i,
            content=piece,
            section_title=None,
            token_count=_count(piece),
        )
        for i, piece in enumerate(splitter.split_text(text))
    ]


def chunk_text(text: str, is_markdown: bool) -> list[Chunk]:
    return chunk_markdown(text) if is_markdown else chunk_plain(text)


def _title_from(metadata: dict[str, str]) -> str | None:
    parts = [metadata[key] for key in ('h1', 'h2', 'h3') if key in metadata]
    return '>'.join(parts)[:255] if parts else None


def _count(text: str) -> int:
    return len(_ENCODER.encode(text))