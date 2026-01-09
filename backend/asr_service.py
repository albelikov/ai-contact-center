"""
ASR Service - Speech-to-Text для української мови
Розпізнавання голосу громадян
"""
import random
from typing import Optional

# Спроба імпорту torch (опціонально)
try:
    import torch
    import torchaudio
    TORCH_AVAILABLE = True
    print("[ASR] PyTorch доступний")
except ImportError:
    TORCH_AVAILABLE = False
    print("[ASR] PyTorch не встановлено - ASR працює в демо-режимі")


# Демо-запити для fallback режиму
DEMO_QUERIES = [
    "Доброго дня, у нас немає опалення вже другий день",
    "На мою машину впало дерево, потрібна допомога",
    "Протікає стеля у квартирі, вода капає",
    "Коли відключатимуть світло в нашому районі",
    "Немає холодної води в будинку з самого ранку",
    "У нас на території не прибрали сніг",
    "Хочу поскаржитися на водія маршрутки",
    "На дорозі величезна яма"
]


class ASRService:
    """Speech-to-Text сервіс"""
    
    def __init__(self):
        self.model = None
        self.device = None
        
        if TORCH_AVAILABLE:
            self._load_silero_model()
    
    def _load_silero_model(self):
        """Завантаження моделі Silero STT"""
        try:
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            self.model, self.decoder, self.utils = torch.hub.load(
                repo_or_dir='snakers4/silero-models',
                model='silero_stt',
                language='uk',
                device=self.device
            )
            print(f"[ASR] Silero модель завантажено на {self.device}")
        except Exception as e:
            print(f"[ASR] Помилка завантаження Silero: {e}")
            self.model = None
    
    def transcribe_file(self, audio_path: str) -> str:
        """Транскрибування аудіофайлу"""
        if self.model is None:
            return self._demo_transcribe()
        
        try:
            (read_batch, split_into_batches, read_audio, prepare_model_input) = self.utils
            audio = read_audio(audio_path, sampling_rate=16000)
            input_data = prepare_model_input([audio], device=self.device)
            output = self.model(input_data)
            transcript = self.decoder(output[0].cpu())
            return transcript.strip()
        except Exception as e:
            print(f"[ASR] Помилка: {e}")
            return self._demo_transcribe()
    
    def transcribe_bytes(self, audio_bytes: bytes) -> str:
        """Транскрибування аудіо з байтів"""
        if self.model is None or not TORCH_AVAILABLE:
            print("[ASR] Модель недоступна - демо-режим")
            return self._demo_transcribe()
        
        try:
            import io
            import tempfile
            import subprocess
            import os
            
            # Спробуємо визначити формат і конвертувати якщо потрібно
            audio_buffer = io.BytesIO(audio_bytes)
            
            # Спершу спробуємо напряму
            try:
                waveform, sample_rate = torchaudio.load(audio_buffer)
            except Exception as load_error:
                print(f"[ASR] Пряме завантаження не вдалося: {load_error}")
                # Конвертуємо через ffmpeg
                with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as f_in:
                    f_in.write(audio_bytes)
                    input_path = f_in.name
                
                output_path = input_path.replace('.webm', '.wav')
                try:
                    subprocess.run([
                        'ffmpeg', '-y', '-i', input_path,
                        '-ar', '16000', '-ac', '1', '-f', 'wav', output_path
                    ], capture_output=True, check=True)
                    
                    waveform, sample_rate = torchaudio.load(output_path)
                finally:
                    # Очищуємо тимчасові файли
                    if os.path.exists(input_path):
                        os.remove(input_path)
                    if os.path.exists(output_path):
                        os.remove(output_path)
            
            if sample_rate != 16000:
                resampler = torchaudio.transforms.Resample(sample_rate, 16000)
                waveform = resampler(waveform)
            
            if waveform.shape[0] > 1:
                waveform = waveform.mean(dim=0, keepdim=True)
            
            (read_batch, split_into_batches, read_audio, prepare_model_input) = self.utils
            input_data = prepare_model_input([waveform.squeeze()], device=self.device)
            output = self.model(input_data)
            transcript = self.decoder(output[0].cpu())
            print(f"[ASR] Розпізнано: {transcript.strip()}")
            return transcript.strip()
        except Exception as e:
            print(f"[ASR] Помилка: {e}")
            return self._demo_transcribe()
    
    def _demo_transcribe(self) -> str:
        """Демо-режим: повертає випадковий запит"""
        return random.choice(DEMO_QUERIES)


# Глобальний екземпляр
asr_service = ASRService()


def transcribe_audio(audio_path: str) -> str:
    """Транскрибувати аудіофайл"""
    return asr_service.transcribe_file(audio_path)


def transcribe_audio_bytes(audio_bytes: bytes) -> str:
    """Транскрибувати аудіо з байтів"""
    return asr_service.transcribe_bytes(audio_bytes)
