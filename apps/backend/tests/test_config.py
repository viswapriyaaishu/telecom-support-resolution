from app.core.config import get_settings


def test_default_settings() -> None:
    settings = get_settings()

    assert settings.app_name == "Telecom Support Resolution API"
    assert settings.app_version == "0.1.0"
    assert settings.environment == "development"
    assert settings.debug is False