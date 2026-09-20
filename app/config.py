from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    daraja_consumer_key: str
    daraja_consumer_secret: str
    daraja_shortcode: str
    daraja_passkey: str
    daraja_callback_url: str
    database_url: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()