"""
TTS Service - Fish Speech Text-to-Speech для української мови
Синтез голосу для відповідей агента
"""
import torch
import numpy as np
from typing import Optional, Tuple
import io
import wave
import struct

from config import FISH_SPEECH_DEVICE, FISH_SPEECH_SAMPLE_RATE


class FishSpeechTTS:
    """
    Fish Speech Text-to-Speech для української мови
    
    Fish Speech - це open-source TTS модель з підтримкою багатьох мов,
    включаючи українську. Має дуже природне звучання та можливість
    клонування голосу.
    
    GitHub: https://github.com/fishaudio/fish-speech
    Ліцензія: Apache 2.0 / CC-BY-NC-SA 4.0
    """
    
    def __init__(self):
        self.model = None
        self.device = torch.device(FISH_SPEECH_DEVICE if torch.cuda.is_available() else 'cpu')
        self.sample_rate = FISH_SPEECH_SAMPLE_RATE
        self._load_model()
    
    def _load_model(self):
        """Завантаження моделі Fish Speech"""
        try:
            # Fish Speech завантажується через їх API
            # pip install git+https://github.com/fishaudio/fish-speech.git
            
            # Спроба імпорту Fish Speech
            try:
                from fish_speech.inference import TTSInference
                self.model = TTSInference(
                    model_path="fish-speech-1.4",
                    device=self.device
                )
                print(f"[Fish Speech TTS] Модель завантажено на {self.device}")
            except ImportError:
                print("[Fish Speech TTS] Fish Speech не встановлено, використовується fallback режим")
                self.model = None
                
        except Exception as e:
            print(f"[Fish Speech TTS] Помилка завантаження моделі: {e}")
            self.model = None
    
    def synthesize(self, text: str, voice: str = "default") -> Tuple[bytes, int]:
        """
        Синтез мовлення з тексту
        
        Args:
            text: Текст для синтезу українською мовою
            voice: Ідентифікатор голосу (для клонування)
            
        Returns:
            Tuple[bytes, int]: (аудіо байти у форматі WAV, sample rate)
        """
        if self.model is None:
            return self._fallback_synthesize(text)
        
        try:
            # Синтез через Fish Speech
            audio = self.model.synthesize(
                text=text,
                speaker=voice,
                language="uk"  # Українська мова
            )
            
            # Конвертація в WAV байти
            wav_bytes = self._audio_to_wav(audio)
            
            return wav_bytes, self.sample_rate
            
        except Exception as e:
            print(f"[Fish Speech TTS] Помилка синтезу: {e}")
            return self._fallback_synthesize(text)
    
    def synthesize_to_file(self, text: str, output_path: str, voice: str = "default") -> bool:
        """Синтез мовлення та збереження у файл"""
        try:
            audio_bytes, sample_rate = self.synthesize(text, voice)
            
            with open(output_path, 'wb') as f:
                f.write(audio_bytes)
            
            print(f"[Fish Speech TTS] Аудіо збережено: {output_path}")
            return True
            
        except Exception as e:
            print(f"[Fish Speech TTS] Помилка збереження: {e}")
            return False
    
    def _audio_to_wav(self, audio: np.ndarray) -> bytes:
        """Конвертація numpy array в WAV байти"""
        buffer = io.BytesIO()
        
        with wave.open(buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(self.sample_rate)
            
            # Нормалізація та конвертація в int16
            audio_normalized = np.clip(audio, -1.0, 1.0)
            audio_int16 = (audio_normalized * 32767).astype(np.int16)
            wav_file.writeframes(audio_int16.tobytes())
        
        buffer.seek(0)
        return buffer.read()
    
    def _fallback_synthesize(self, text: str) -> Tuple[bytes, int]:
        """
        Fallback синтез для демонстрації без реальної моделі
        Генерує тиху аудіо-заглушку
        """
        print(f"[Fish Speech TTS] Fallback режим для тексту: {text[:50]}...")
        
        # Генеруємо 2 секунди тихого аудіо як заглушку
        duration = 2.0
        num_samples = int(self.sample_rate * duration)
        
        # Тихий сигнал з невеликим шумом
        audio = np.random.uniform(-0.001, 0.001, num_samples).astype(np.float32)
        
        return self._audio_to_wav(audio), self.sample_rate
    
    def clone_voice(self, reference_audio: bytes, voice_id: str) -> bool:
        """
        Клонування голосу з референсного аудіо
        
        Fish Speech дозволяє клонувати голос з 10-30 секунд аудіо.
        Це може бути використано для створення голосу оператора.
        """
        if self.model is None:
            print("[Fish Speech TTS] Клонування недоступне у fallback режимі")
            return False
        
        try:
            # Fish Speech voice cloning API
            self.model.clone_voice(
                audio_bytes=reference_audio,
                voice_id=voice_id
            )
            print(f"[Fish Speech TTS] Голос '{voice_id}' успішно клоновано")
            return True
            
        except Exception as e:
            print(f"[Fish Speech TTS] Помилка клонування голосу: {e}")
            return False


# Глобальний екземпляр TTS
tts_service = FishSpeechTTS()


def synthesize_speech(text: str, voice: str = "default") -> Tuple[bytes, int]:
    """Синтезувати мовлення з тексту"""
    return tts_service.synthesize(text, voice)


def synthesize_to_file(text: str, output_path: str, voice: str = "default") -> bool:
    """Синтезувати мовлення та зберегти у файл"""
    return tts_service.synthesize_to_file(text, output_path, voice)
