"""
TTS Service - Text-to-Speech для української мови
Підтримує: Edge TTS (Microsoft), Fish Speech (GPU)
"""
import asyncio
import io
import wave
import tempfile
import os
from typing import Tuple

# Спроба імпорту edge-tts (основний TTS без GPU)
try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
    print("[TTS] Edge TTS доступний")
except ImportError:
    EDGE_TTS_AVAILABLE = False
    print("[TTS] Edge TTS не встановлено. Встановіть: pip install edge-tts")

# Спроба імпорту Fish Speech (потребує GPU)
try:
    import torch
    import numpy as np
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


class TTSService:
    """
    Сервіс синтезу мовлення з підтримкою кількох движків:
    1. Edge TTS (Microsoft) - безкоштовний, без GPU, гарна якість
    2. Fish Speech - потребує GPU, найкраща якість
    """
    
    # Українські голоси Edge TTS
    EDGE_VOICES = {
        "female": "uk-UA-PolinaNeural",  # Жіночий голос
        "male": "uk-UA-OstapNeural",      # Чоловічий голос
        "default": "uk-UA-PolinaNeural"
    }
    
    def __init__(self):
        self.sample_rate = 24000
        self.fish_speech_model = None
        self._init_fish_speech()
    
    def _init_fish_speech(self):
        """Спроба ініціалізації Fish Speech (якщо є GPU)"""
        if not TORCH_AVAILABLE:
            return
            
        try:
            if torch.cuda.is_available():
                from fish_speech.inference import TTSInference
                self.fish_speech_model = TTSInference(
                    model_path="fish-speech-1.4",
                    device="cuda"
                )
                print("[TTS] Fish Speech завантажено (GPU)")
        except Exception as e:
            print(f"[TTS] Fish Speech недоступний: {e}")
            self.fish_speech_model = None
    
    def synthesize(self, text: str, voice: str = "default") -> Tuple[bytes, int]:
        """
        Синтез мовлення з тексту
        
        Args:
            text: Текст українською мовою
            voice: Голос (female, male, default)
            
        Returns:
            Tuple[bytes, int]: (MP3/WAV байти, sample rate)
        """
        # Пріоритет 1: Fish Speech (якщо є GPU)
        if self.fish_speech_model is not None:
            try:
                return self._synthesize_fish_speech(text, voice)
            except Exception as e:
                print(f"[TTS] Fish Speech помилка: {e}")
        
        # Пріоритет 2: Edge TTS (без GPU)
        if EDGE_TTS_AVAILABLE:
            try:
                return self._synthesize_edge_tts(text, voice)
            except Exception as e:
                print(f"[TTS] Edge TTS помилка: {e}")
        
        # Fallback: генерація тиші
        print("[TTS] Жоден TTS движок не доступний!")
        return self._generate_silence(), self.sample_rate
    
    def _synthesize_edge_tts(self, text: str, voice: str = "default") -> Tuple[bytes, int]:
        """Синтез через Microsoft Edge TTS"""
        import concurrent.futures
        
        voice_name = self.EDGE_VOICES.get(voice, self.EDGE_VOICES["default"])
        
        def _run_in_thread():
            """Запуск edge-tts в окремому потоці з власним event loop"""
            async def _generate():
                communicate = edge_tts.Communicate(text, voice_name)
                
                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                    tmp_path = tmp.name
                
                await communicate.save(tmp_path)
                
                with open(tmp_path, "rb") as f:
                    audio_bytes = f.read()
                
                os.unlink(tmp_path)
                return audio_bytes
            
            return asyncio.run(_generate())
        
        # Запускаємо в окремому потоці, щоб уникнути конфлікту event loop
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(_run_in_thread)
            audio_bytes = future.result(timeout=30)
        
        print(f"[TTS] Edge TTS синтезував: {text[:50]}...")
        return audio_bytes, self.sample_rate
    
    def _synthesize_fish_speech(self, text: str, voice: str = "default") -> Tuple[bytes, int]:
        """Синтез через Fish Speech (GPU)"""
        audio = self.fish_speech_model.synthesize(
            text=text,
            speaker=voice,
            language="uk"
        )
        
        wav_bytes = self._audio_to_wav(audio)
        print(f"[TTS] Fish Speech синтезував: {text[:50]}...")
        return wav_bytes, 44100
    
    def _audio_to_wav(self, audio) -> bytes:
        """Конвертація numpy array в WAV"""
        import numpy as np
        buffer = io.BytesIO()
        
        with wave.open(buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(44100)
            
            audio_normalized = np.clip(audio, -1.0, 1.0)
            audio_int16 = (audio_normalized * 32767).astype(np.int16)
            wav_file.writeframes(audio_int16.tobytes())
        
        buffer.seek(0)
        return buffer.read()
    
    def _generate_silence(self) -> bytes:
        """Генерація тихого аудіо як fallback"""
        import numpy as np
        duration = 1.0
        num_samples = int(self.sample_rate * duration)
        audio = np.zeros(num_samples, dtype=np.int16)
        
        buffer = io.BytesIO()
        with wave.open(buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(self.sample_rate)
            wav_file.writeframes(audio.tobytes())
        
        buffer.seek(0)
        return buffer.read()
    
    def get_available_voices(self) -> dict:
        """Отримати список доступних голосів"""
        return {
            "edge_tts": list(self.EDGE_VOICES.keys()) if EDGE_TTS_AVAILABLE else [],
            "fish_speech": ["default"] if self.fish_speech_model else []
        }


# Глобальний екземпляр
tts_service = TTSService()


def synthesize_speech(text: str, voice: str = "default") -> Tuple[bytes, int]:
    """Синтезувати мовлення з тексту"""
    return tts_service.synthesize(text, voice)


def synthesize_to_file(text: str, output_path: str, voice: str = "default") -> bool:
    """Синтезувати мовлення та зберегти у файл"""
    try:
        audio_bytes, _ = tts_service.synthesize(text, voice)
        with open(output_path, 'wb') as f:
            f.write(audio_bytes)
        return True
    except Exception as e:
        print(f"[TTS] Помилка збереження: {e}")
        return False
