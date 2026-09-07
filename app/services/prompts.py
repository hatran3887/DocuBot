from app.services.retrieval import RetrievedChunk

SYSTEM_PROMPT = """You are a customer support chatbot for a product manual.

Rules:
- Answer only using the numbered sources below.
- If the sources do not contain the answer, say you do not know and suggest contacting support. Do not guess.
- Cite the sources you used as [1], [2] and so on.
- Do not use knowledge outside the sources.
- Answer in the same language as the question.
- Be concise. Answer in two or three sentences unless steps are needed.
"""


def build_user_prompt(question: str, chunks: list[RetrievedChunk]) -> str:
    parts = []

    for i, chunk in enumerate(chunks, start=1):
        header = f'[{i}]'
        if chunk.section_title:
            header += f' {chunk.section_title}'
        parts.append(f'{header}\n{chunk.content}')

    sources = '\n\n'.join(parts)
    return f'Source:\n\n{sources}\n\nQuestion: {question}'

