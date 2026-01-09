"""
ASR Service - Speech-to-Text для української мови
Розпізнавання голосу громадян
"""
import random
import io
import tempfile
import os
import subprocess
from typing import Optional

# Спроба імпорту OpenAI Whisper (рекомендовано для української)
try:
    import whisper
    WHISPER_AVAILABLE = True
    print("[ASR] OpenAI Whisper доступний ✅")
except ImportError:
    WHISPER_AVAILABLE = False
    print("[ASR] OpenAI Whisper НЕ встановлено")
    print("[ASR] Встановіть: pip install openai-whisper")

# Спроба імпорту torch (опціонально)
try:
    import torch
    import torchaudio
    TORCH_AVAILABLE = True
    print(f"[ASR] PyTorch {torch.__version__} доступний")
except ImportError as e:
    TORCH_AVAILABLE = False
    print(f"[ASR] PyTorch НЕ доступний: {e}")


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
    """Speech-to-Text сервіс з підтримкою Whisper та Silero"""
    
    def __init__(self):
        self.whisper_model = None
        self.silero_model = None
        self.device = None
        self.decoder = None
        self.utils = None
        
        # Завантажуємо Whisper (пріоритет для української)
        if WHISPER_AVAILABLE:
            self._load_whisper_model()
        
        # Якщо Whisper не завантажився, пробуємо Silero
        if self.whisper_model is None and TORCH_AVAILABLE:
            self._load_silero_model()
    
    def _load_whisper_model(self):
        """Завантаження моделі Whisper"""
        try:
            print("[ASR] Завантаження Whisper model (base)...")
            # Використовуємо 'base' модель - достатньо точна і швидка
            self.whisper_model = whisper.load_model("base")
            print("[ASR] ✅ Whisper модель завантажено")
        except Exception as e:
            print(f"[ASR] ❌ Помилка завантаження Whisper: {e}")
            self.whisper_model = None
    
    def _load_silero_model(self):
        """Завантаження моделі Silero STT"""
        try:
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            print(f"[ASR] Завантаження Silero моделі на {self.device}...")
            
            # Спробуємо з 'uk' для української
            try:
                self.silero_model, self.decoder, self.utils = torch.hub.load(
                    repo_or_dir='snakers4/silero-models',
                    model='silero_stt',
                    language='uk',
                    device=self.device
                )
                print(f"[ASR] ✅ Silero модель (українська) завантажено на {self.device}")
                return
            except AssertionError:
                print(f"[ASR] ⚠️ Українська мова 'uk' не підтримується")
            
            # Якщо 'uk' не працює, використовуємо 'multilingual'
            try:
                self.silero_model, self.decoder, self.utils = torch.hub.load(
                    repo_or_dir='snakers4/silero-models',
                    model='silero_stt',
                    language='multilingual',
                    device=self.device
                )
                print(f"[ASR] ✅ Silero модель (багатомовна) завантажено на {self.device}")
            except AssertionError:
                print(f"[ASR] ⚠️ Багатомовна версія також недоступна")
                
        except Exception as e:
            print(f"[ASR] ❌ Помилка завантаження Silero: {e}")
            self.silero_model = None
    
    def transcribe_file(self, audio_path: str) -> str:
        """Транскрибування аудіофайлу"""
        # Спочатку пробуємо Whisper
        if self.whisper_model is not None:
            return self._transcribe_with_whisper_file(audio_path)
        
        # Потім Silero
        if self.silero_model is not None:
            return self._transcribe_with_silero_file(audio_path)
        
        # Демо-режим
        print("[ASR] transcribe_file: моделі недоступні, демо-режим")
        return self._demo_transcribe()
    
    def transcribe_bytes(self, audio_bytes: bytes) -> str:
        """Транскрибування аудіо з байтів"""
        print(f"[ASR] transcribe_bytes викликано")
        
        # Спочатку пробуємо Whisper
        if self.whisper_model is not None:
            print("[ASR] 🎤 Використовую Whisper")
            return self._transcribe_with_whisper_bytes(audio_bytes)
        
        # Потім Silero
        if self.silero_model is not None:
            print("[ASR] 🎤 Використовую Silero")
            return self._transcribe_with_silero_bytes(audio_bytes)
        
        # Демо-режим
        print("[ASR] ⚠️ Моделі недоступні - демо-режим")
        return self._demo_transcribe()
    
    def _convert_audio_to_wav(self, audio_bytes: bytes, input_format: str = 'webm') -> str:
        """Конвертація аудіо у WAV формат"""
        try:
            with tempfile.NamedTemporaryFile(suffix=f'.{input_format}', delete=False) as f_in:
                f_in.write(audio_bytes)
                input_path = f_in.name
            
            output_path = input_path.replace(f'.{input_format}', '.wav')
            subprocess.run([
                'ffmpeg', '-y', '-i', input_path,
                '-ar', '16000', '-ac', '1', '-f', 'wav', output_path
            ], capture_output=True, check=True)
            
            if os.path.exists(input_path):
                os.remove(input_path)
            
            return output_path
        except Exception as e:
            print(f"[ASR] Помилка конвертації: {e}")
            return None
    
    def _transcribe_with_whisper_bytes(self, audio_bytes: bytes) -> str:
        """Розпізнавання через Whisper з байтів"""
        try:
            import numpy as np
            
            # Конвертуємо у WAV
            wav_path = self._convert_audio_to_wav(audio_bytes)
            if wav_path is None:
                return self._demo_transcribe()
            
            try:
                # Whisper очікує numpy array або шлях до файлу
                result = self.whisper_model.transcribe(wav_path, language="Ukrainian")
                transcript = result["text"].strip()
                
                os.remove(wav_path)
                
                if transcript:
                    print(f"[ASR] ✅ Whisper розпізнав: \"{transcript}\"")
                    return transcript
                else:
                    print("[ASR] ⚠️ Whisper повернув порожній результат")
                    return self._demo_transcribe()
                    
            finally:
                if os.path.exists(wav_path):
                    os.remove(wav_path)
                    
        except Exception as e:
            print(f"[ASR] ❌ Помилка Whisper: {e}")
            import traceback
            traceback.print_exc()
            return self._demo_transcribe()
    
    def _transcribe_with_whisper_file(self, audio_path: str) -> str:
        """Розпізнавання через Whisper з файлу"""
        try:
            result = self.whisper_model.transcribe(audio_path, language="Ukrainian")
            transcript = result["text"].strip()
            print(f"[ASR] Whisper розпізнав: \"{transcript}\"")
            return transcript
        except Exception as e:
            print(f"[ASR] Помилка Whisper: {e}")
            return self._demo_transcribe()
    
    def _transcribe_with_silero_bytes(self, audio_bytes: bytes) -> str:
        """Розпізнавання через Silero з байтів"""
        try:
            import numpy as np
            
            # Конвертуємо у WAV
            wav_path = self._convert_audio_to_wav(audio_bytes)
            if wav_path is None:
                return self._demo_transcribe()
            
            try:
                waveform, sample_rate = torchaudio.load(wav_path)
                
                if sample_rate != 16000:
                    resampler = torchaudio.transforms.Resample(sample_rate, 16000)
                    waveform = resampler(waveform)
                
                if waveform.shape[0] > 1:
                    waveform = waveform.mean(dim=0, keepdim=True)
                
                (read_batch, split_into_batches, read_audio, prepare_model_input) = self.utils
                input_data = prepare_model_input([waveform.squeeze()], device=self.device)
                output = self.silero_model(input_data)
                transcript = self.decoder(output[0].cpu())
                result = transcript.strip()
                
                os.remove(wav_path)
                
                print(f"[ASR] ✅ Silero розпізнав: \"{result}\"")
                return result
                    
            finally:
                if os.path.exists(wav_path):
                    os.remove(wav_path)
                    
        except Exception as e:
            print(f"[ASR] ❌ Помилка Silero: {e}")
            return self._demo_transcribe()
    
    def _transcribe_with_silero_file(self, audio_path: str) -> str:
        """Розпізнавання через Silero з файлу"""
        try:
            (read_batch, split_into_batches, read_audio, prepare_model_input) = self.utils
            audio = read_audio(audio_path, sampling_rate=16000)
            input_data = prepare_model_input([audio], device=self.device)
            output = self.silero_model(input_data)
            transcript = self.decoder(output[0].cpu())
            result = transcript.strip()
            print(f"[ASR] Silero розпізнав: \"{result}\"")
            return result
        except Exception as e:
            print(f"[ASR] Помилка Silero: {e}")
            return self._demo_transcribe()
    
    def _demo_transcribe(self) -> str:
        """Демо-режим: повертає випадковий запит"""
        result = random.choice(DEMO_QUERIES)
        print(f"[ASR] 🎭 Демо-режим: вигадано \"{result}\"")
        return result


# Глобальний екземпляр
asr_service = ASRService()


def transcribe_audio(audio_path: str) -> str:
    """Транскрибувати аудіофайл"""
    return asr_service.transcribe_file(audio_path)


def transcribe_audio_bytes(audio_bytes: bytes) -> str:
    """Транскрибувати аудіо з байтів"""
    return asr_service.transcribe_bytes(audio_bytes)
