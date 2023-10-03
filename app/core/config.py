from pydantic import BaseSettings, AnyHttpUrl, PostgresDsn

class Settings(BaseSettings):
    # App settings
    app_name: str
    app_version: str
    app_secret: str
    app_description: str
    app_url: AnyHttpUrl
    app_port: int
    app_debug: bool
    app_reload: bool

    # Database settings
    database_url: PostgresDsn

    class Config:
        env_file = ".env"
