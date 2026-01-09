"""
Конфігурація ШІ-Агента контактного центру
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Загальні налаштування
APP_NAME = "ШІ-Агент Контактного Центру"
VERSION = "1.0.0"
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# Сервер
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8000))

# ASR (Silero) налаштування
SILERO_MODEL = os.getenv("SILERO_MODEL", "silero_stt")
SILERO_LANGUAGE = "uk"  # Українська мова
SILERO_SAMPLE_RATE = 16000

# TTS (Fish Speech) налаштування
FISH_SPEECH_MODEL = os.getenv("FISH_SPEECH_MODEL", "fish-speech-1.4")
FISH_SPEECH_DEVICE = os.getenv("FISH_SPEECH_DEVICE", "cuda")  # cuda або cpu
FISH_SPEECH_SAMPLE_RATE = 44100

# Класифікатор NLU
NLU_MODEL = os.getenv("NLU_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
NLU_CONFIDENCE_THRESHOLD = 0.7

# Oracle APEX інтеграція
ORACLE_APEX_URL = os.getenv("ORACLE_APEX_URL", "https://apex.oracle.com/pls/apex")
ORACLE_APEX_WORKSPACE = os.getenv("ORACLE_APEX_WORKSPACE", "contact_center")
ORACLE_APEX_API_KEY = os.getenv("ORACLE_APEX_API_KEY", "")

# База даних (локальна для тестування)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./cti_agent.db")

# Логування
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
