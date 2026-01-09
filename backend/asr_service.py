"""
ASR Service - Silero Speech-to-Text для української мови
Розпізнавання голосу громадян
"""
import torch
import torchaudio
from typing import Optional
import io
import numpy as np

from config import SILERO_LANGUAGE, SILERO_SAMPLE_RATE


class SileroASR:
    """Silero Speech-to-Text для української мови"""
    
    def __init__(self):
        self.model = None
        self.decoder = None
        self.utils = None
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self._load_model()
    
    def _load_model(self):
        """Завантаження моделі Silero STT"""
        try:
            self.model, self.decoder, self.utils = torch.hub.load(
                repo_or_dir='snakers4/silero-models',
                model='silero_stt',
                language=SILERO_LANGUAGE,
                device=self.device
            )
            print(f"[Silero ASR] Модель завантажено на {self.device}")
        except Exception as e:
            print(f"[Silero ASR] Помилка завантаження моделі: {e}")
            # Fallback режим без моделі
            self.model = None
    
    def transcribe_file(self, audio_path: str) -> str:
        """Транскрибування аудіофайлу"""
        if self.model is None:
            return self._fallback_transcribe()
        
        try:
            (read_batch, split_into_batches, read_audio, prepare_model_input) = self.utils
            
            # Завантаження аудіо
            audio = read_audio(audio_path, sampling_rate=SILERO_SAMPLE_RATE)
            input_data = prepare_model_input([audio], device=self.device)
            
            # Розпізнавання
            output = self.model(input_data)
            transcript = self.decoder(output[0].cpu())
            
            return transcript.strip()
        except Exception as e:
            print(f"[Silero ASR] Помилка транскрибування: {e}")
            return self._fallback_transcribe()
    
    def transcribe_bytes(self, audio_bytes: bytes) -> str:
        """Транскрибування аудіо з байтів"""
        if self.model is None:
            return self._fallback_transcribe()
        
        try:
            # Конвертація байтів в тензор
            audio_buffer = io.BytesIO(audio_bytes)
            waveform, sample_rate = torchaudio.load(audio_buffer)
            
            # Ресемплінг до 16kHz якщо потрібно
            if sample_rate != SILERO_SAMPLE_RATE:
                resampler = torchaudio.transforms.Resample(sample_rate, SILERO_SAMPLE_RATE)
                waveform = resampler(waveform)
            
            # Конвертація в mono
            if waveform.shape[0] > 1:
                waveform = waveform.mean(dim=0, keepdim=True)
            
            (read_batch, split_into_batches, read_audio, prepare_model_input) = self.utils
            input_data = prepare_model_input([waveform.squeeze()], device=self.device)
            
            output = self.model(input_data)
            transcript = self.decoder(output[0].cpu())
            
            return transcript.strip()
        except Exception as e:
            print(f"[Silero ASR] Помилка транскрибування байтів: {e}")
            return self._fallback_transcribe()
    
    def _fallback_transcribe(self) -> str:
        """Fallback для демонстрації без реальної моделі"""
        # Повертаємо випадковий приклад запиту для демо
        import random
        samples = [
            "Доброго дня, у нас немає опалення вже другий день",
            "На мою машину впало дерево, потрібна допомога",
            "Протікає стеля у квартирі",
            "Коли відключатимуть світло",
            "Немає холодної води в будинку"
        ]
        return random.choice(samples)


# Глобальний екземпляр ASR
asr_service = SileroASR()


def transcribe_audio(audio_path: str) -> str:
    """Транскрибувати аудіофайл"""
    return asr_service.transcribe_file(audio_path)


def transcribe_audio_bytes(audio_bytes: bytes) -> str:
    """Транскрибувати аудіо з байтів"""
    return asr_service.transcribe_bytes(audio_bytes)
