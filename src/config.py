"""Configuración central del prototipo SmartSort."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    telegram_bot_token: str = ""
    telegram_bot_username: str = "SmartSortEcoBot"

    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"

    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    database_backend: str = "sqlite"
    sqlite_path: str = "data/smartsort.db"

    supabase_url: str = ""
    supabase_key: str = ""

    maximo_intentos: int = 3
    tiempo_reintento_seg: int = 300
    tiempo_maximo_sesion_min: int = 10
    tiempo_confirmacion_min: int = 15
    nivel_confianza_minimo: float = 0.6
    sla_respuesta_seg: int = 5

    puntos_acierto_primera: int = 10

    @property
    def telegram_deep_link_base(self) -> str:
        return f"https://t.me/{self.telegram_bot_username.lstrip('@')}"


settings = Settings()
