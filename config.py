from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
from typing import List, Union
from zoneinfo import ZoneInfo


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_ignore_empty=True,
    )

    bot_token: str = Field(..., alias="BOT_TOKEN")
    admin_ids: Union[str, List[int]] = Field(default="", alias="ADMIN_IDS")
    channel_id: int = Field(..., alias="CHANNEL_ID")
    timezone: str = Field(default="Europe/Belgrade", alias="TIMEZONE")
    database_path: str = Field(default="data/tg_family.db", alias="DATABASE_PATH")
    pill_reminder_interval: int = Field(default=15, alias="PILL_REMINDER_INTERVAL")

    @property
    def tz_info(self) -> ZoneInfo:
        return ZoneInfo(self.timezone)

    def get_admin_ids(self) -> List[int]:
        if isinstance(self.admin_ids, str):
            return [int(id.strip()) for id in self.admin_ids.split(",") if id.strip()]
        return self.admin_ids


settings = Settings()
