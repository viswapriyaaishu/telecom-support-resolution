from normalize import normalize_text


def test_normalize_text_strips_outer_whitespace() -> None:
    assert normalize_text("  My internet is slow  ") == "My internet is slow"


def test_normalize_text_collapses_multiple_spaces() -> None:
    assert normalize_text("My   internet    is   slow") == "My internet is slow"


def test_normalize_text_preserves_meaningful_content() -> None:
    text = "My internet is slow. I restarted my router twice."

    assert normalize_text(text) == text


def test_normalize_text_handles_empty_text() -> None:
    assert normalize_text("") == ""


def test_normalize_text_handles_whitespace_only_text() -> None:
    assert normalize_text("   \t   ") == ""