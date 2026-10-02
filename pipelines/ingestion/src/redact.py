import re

# ---------------------------------------------------------------------------
# Sensitive-data patterns
# ---------------------------------------------------------------------------

_MAILTO_PATTERN = re.compile(
    r"mailto:\s*[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
    re.IGNORECASE,
)

_EMAIL_PATTERN = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
)

_ACCOUNT_NUMBER_PATTERN = re.compile(
    r"(?P<prefix>\b(?:account(?:\s+number|\s*#|\s+no\.?)|"
    r"acct(?:\s+number|\s*#|\s+no\.?))"
    r"(?:\s*[:#-]\s*|\s+(?:is\s+|:?\s*))?)"
    r"(?P<number>\d{6,})\b",
    re.IGNORECASE,
)

_IP_ADDRESS_PATTERN = re.compile(
    r"\b(?:"
    r"(?:25[0-5]|2[0-4]\d|1?\d?\d)\."
    r"){3}"
    r"(?:25[0-5]|2[0-4]\d|1?\d?\d)"
    r"\b"
)

_PHONE_PATTERN = re.compile(
    r"(?<![\d-])"
    r"(?!\d{4}-\d{2}-\d{2}\b)"
    r"(?:\+?\d[\d\s().-]{7,}\d)"
    r"(?![\d-])"
)


def _replace_account_number(match: re.Match[str]) -> str:
    prefix = match.group("prefix")

    # Preserve the semantic label while removing the actual identifier.
    prefix = prefix.rstrip(" :#-")

    return f"{prefix} [ACCOUNT_NUMBER]"


def redact_sensitive_data(text: str) -> str:
    """
    Redact sensitive information from text using conservative,
    deterministic pattern matching.

    Ordinary numbers, dates, amounts, and measurements are preserved.
    """

    text = _MAILTO_PATTERN.sub("[EMAIL]", text)
    text = _EMAIL_PATTERN.sub("[EMAIL]", text)

    text = _ACCOUNT_NUMBER_PATTERN.sub(
        _replace_account_number,
        text,
    )

    text = _IP_ADDRESS_PATTERN.sub("[IP_ADDRESS]", text)

    text = _PHONE_PATTERN.sub("[PHONE]", text)

    return text