"""
Конфігурація ШІ-Агента контактного центру
"""
import os
from pydantic import BaseModel
from typing import Optional


class Settings(BaseModel):
    """
    Налаштування додатку з валідацією типів
    """
    # Загальні налаштування
    APP_NAME: str = "ШІ-Агент Контактного Центру"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Сервер
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # ASR (Silero) налаштування
    SILERO_MODEL: str = "silero_stt"
    SILERO_LANGUAGE: str = "uk"
    SILERO_SAMPLE_RATE: int = 16000
    
    # TTS (Fish Speech) налаштування
    FISH_SPEECH_MODEL: str = "fish-speech-1.4"
    FISH_SPEECH_DEVICE: str = "cuda"
    FISH_SPEECH_SAMPLE_RATE: int = 44100
    
    # Класифікатор NLU
    NLU_MODEL: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    NLU_CONFIDENCE_THRESHOLD: float = 0.7
    
    # Oracle APEX інтеграція
    ORACLE_APEX_URL: Optional[str] = None
    ORACLE_APEX_WORKSPACE: Optional[str] = None
    ORACLE_APEX_API_KEY: Optional[str] = None
    
    # База даних
    DATABASE_URL: str = "sqlite+aiosqlite:///./cti_agent.db"
    
    # API Аутентифікація
    API_USERNAME: str = "api_user"
    API_PASSWORD: str = "change_this_password"
    
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "admin123"
    
    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173"
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 10
    RATE_LIMIT_WINDOW: int = 60
    
    # Логування
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Завантаження налаштувань
settings = Settings()


def reload_settings():
    """
    Перезавантажити налаштування з .env файлу
    """
    global settings
    settings = Settings()
