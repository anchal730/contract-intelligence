from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    max_file_size: int = 50 * 1024 * 1024
    allowed_extension: str = ".pdf"


settings = Settings()