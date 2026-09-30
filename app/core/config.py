"""
Application configuration and global path resolution.
"""

import os
from pathlib import Path
from pydantic import BaseModel, Field


class Settings(BaseModel):
    """System settings for local-first execution and filesystem bindings."""
    
    app_name: str = "PricePulse BD"
    app_version: str = "0.1.0"
    debug: bool = Field(default=False)
    cors_origins: list[str] = Field(
        default=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:8000",
            "http://127.0.0.1:8000",
        ]
    )
    
    # Project paths
    project_root: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parent.parent.parent
    )
    
    @property
    def data_dir(self) -> Path:
        return self.project_root / "data"

    @property
    def taxonomy_dir(self) -> Path:
        return self.data_dir / "taxonomy"

    @property
    def fixtures_dir(self) -> Path:
        return self.data_dir / "fixtures"

    @property
    def default_sqlite_path(self) -> Path:
        return self.project_root / "pricepulse.db"

    @property
    def database_url(self) -> str:
        env_url = os.getenv("DATABASE_URL")
        if env_url:
            return env_url
        return f"sqlite:///{self.default_sqlite_path.as_posix()}"


settings = Settings()
