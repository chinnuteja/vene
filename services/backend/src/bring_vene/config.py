from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore", env_file=".env")
    database_url: str = "postgresql+psycopg://invalid@127.0.0.1:1/unconfigured"
    bring_vene_mode: str = "fixture"
    bring_vene_development: bool = False
    demo_guided: bool = False
    cookie_secure: bool = True
    session_hours: int = 8
    frontend_origin: str = "https://bring-vene.invalid"
    livekit_url: str = ""
    livekit_api_key: str = ""
    livekit_api_secret: str = ""
    voice_provider: str = "fixture"
    voice_admission_wait_seconds: float = 0
    deepgram_api_key: str = ""
    deepgram_model: str = "nova-3"
    model_provider: str = "fixture"
    openai_api_key: str = ""
    openai_model: str = "gpt-6-astra"
    deepseek_api_key: str = ""
    deepseek_model: str = "deepseek-flash"
    model_timeout_seconds: float = 20
    tts_provider: str = "fixture"
    cartesia_api_key: str = ""
    cartesia_voice_id: str = ""
    cartesia_model: str = "sonic-3-2026-01-12"
    speech_quiet_seconds: float = .7
    speech_cooldown_seconds: float = 10
    speech_ttl_seconds: int = 90
    office_url: str = ""
    office_token: str = ""
    office_timeout_seconds: float = 1.0
    office_callback_url: str = ""
    office_callback_secret: str = ""
    continuity_retention_days: int = 7
    # Dial-in (credential-gated): the phone bridge's shared token and the number callers dial.
    phone_bridge_token: str = ""
    phone_dial_number: str = ""
