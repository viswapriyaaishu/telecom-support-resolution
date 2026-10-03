from telecom_support_ingestion.redact import redact_sensitive_data


def test_redact_email() -> None:
    text = "Please contact me at customer@example.com."

    assert redact_sensitive_data(text) == (
        "Please contact me at [EMAIL]."
    )


def test_redact_mailto_email() -> None:
    text = "Email me at mailto:customer@example.com."

    assert redact_sensitive_data(text) == (
        "Email me at [EMAIL]."
    )


def test_redact_phone_number() -> None:
    text = "Call me at +1 800-555-0199."

    assert redact_sensitive_data(text) == (
        "Call me at [PHONE]."
    )


def test_redact_account_number_with_context() -> None:
    text = "My account number is 123456789."

    assert redact_sensitive_data(text) == (
        "My account number is [ACCOUNT_NUMBER]."
    )


def test_redact_account_number_with_hash() -> None:
    text = "My account #123456789 needs to be checked."

    assert redact_sensitive_data(text) == (
        "My account [ACCOUNT_NUMBER] needs to be checked."
    )


def test_redact_ip_address() -> None:
    text = "The router is using IP address 192.168.1.10."

    assert redact_sensitive_data(text) == (
        "The router is using IP address [IP_ADDRESS]."
    )


def test_preserve_normal_amounts() -> None:
    text = "My monthly bill is 1500 rupees."

    assert redact_sensitive_data(text) == (
        "My monthly bill is 1500 rupees."
    )


def test_preserve_dates() -> None:
    text = "The issue started on 2026-09-30."

    assert redact_sensitive_data(text) == (
        "The issue started on 2026-09-30."
    )


def test_preserve_short_numbers() -> None:
    text = "I restarted the router 2 times and waited 10 minutes."

    assert redact_sensitive_data(text) == (
        "I restarted the router 2 times and waited 10 minutes."
    )


def test_redact_multiple_sensitive_values() -> None:
    text = (
        "My account number is 123456789. "
        "Email me at customer@example.com or call +1 800-555-0199."
    )

    assert redact_sensitive_data(text) == (
        "My account number is [ACCOUNT_NUMBER]. "
        "Email me at [EMAIL] or call [PHONE]."
    )


def test_empty_text() -> None:
    assert redact_sensitive_data("") == ""


def test_text_without_sensitive_data() -> None:
    text = "My broadband connection drops every evening."

    assert redact_sensitive_data(text) == text
