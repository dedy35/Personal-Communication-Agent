from app.core.config import Settings


def test_parse_cors_origins_from_csv_string() -> None:
    settings = Settings(cors_allowed_origins="http://localhost:3000,http://127.0.0.1:3000")
    assert settings.cors_allowed_origins == ["http://localhost:3000", "http://127.0.0.1:3000"]


def test_parse_cors_origins_from_json_string() -> None:
    settings = Settings(cors_allowed_origins='["http://localhost:3000", "http://localhost:5173"]')
    assert settings.cors_allowed_origins == ["http://localhost:3000", "http://localhost:5173"]
