from pathlib import Path


class ExtractionError(Exception):
    """Raised when a manual cannot be turned into usable text."""


def load_text(path: Path) -> str:
    try:
        text = path.read_text(encoding='utf-8')
    except UnicodeDecodeError as e:
        raise ExtractionError('File is not valid UTF-8 text.') from e
    except OSError as e:
        raise ExtractionError(f'Could not read file: {e}') from e

    if not text.strip():
        raise ExtractionError('File is empty.')

    return text