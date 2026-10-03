import re

_MULTIPLE_SPACES = re.compile(r"[ \t]+")


def normalize_text(text: str) -> str:
    """Normalize formatting without changing the meaning of the text."""
    text = text.strip()
    text = _MULTIPLE_SPACES.sub(" ", text)

    return text
