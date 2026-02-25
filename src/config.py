"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Settings for the News MCP Server.

    Reads from environment variables (or a .env file if present).
    """

    database_url: str = "postgresql://postgres:changeme@127.0.0.1:5432/newsdb"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


# Singleton – import this instance everywhere.
settings = Settings()
