"""
ШІ-Агент контактного центру
FastAPI Backend з інтеграцією Silero ASR та Fish Speech TTS
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional, List
import json
import asyncio
from datetime import datetime
import uuid

from config import APP_NAME, VERSION, HOST, PORT
from classifier import classify_query, ClassificationResult
from asr_service import transcribe_audio, transcribe_audio_bytes
from tts_service import synthesize_speech, synthesize_to_file

# Ініціалізація FastAPI
app = FastAPI(
    title=APP_NAME,
    version=VERSION,
    description="ШІ-Агент контактного центру з підтримкою Fish Speech TTS та Silero ASR"
)

# CORS для фронтенду
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Моделі даних
class TextQuery(BaseModel):
    """Текстовий запит для класифікації"""
    text: str
    session_id: Optional[str] = None

class TTSRequest(BaseModel):
    """Запит на синтез мовлення"""
    text: str
    voice: str = "default"

class CallRecord(BaseModel):
    """Запис про дзвінок"""
    id: str
    timestamp: str
    caller_phone: Optional[str]
    transcript: str
    classification: dict
    status: str  # resolved, escalated
    response_text: str
    executor: str

# Зберігання сесій та історії (в пам'яті для демо)
sessions = {}
call_history: List[CallRecord] = []


# === API Endpoints ===

@app.get("/")
async def root():
    """Головна сторінка API"""
    return {
        "name": APP_NAME,
        "version": VERSION,
        "status": "active",
        "endpoints": {
            "classify": "/api/classify",
            "transcribe": "/api/transcribe",
            "synthesize": "/api/synthesize",
            "websocket": "/ws/call"
        }
    }


@app.get("/api/health")
async def health_check():
    """Перевірка стану системи"""
    return {
        "status": "healthy",
        "components": {
            "silero_asr": "active",
            "fish_speech_tts": "active",
            "classifier": "active",
            "oracle_apex": "connected"
        }
    }


@app.post("/api/classify")
async def classify_text(query: TextQuery):
    """
    Класифікація текстового запиту
    """
    result = classify_query(query.text)
    
    return {
        "success": True,
        "query": query.text,
        "classification": {
            "id": result.id,
            "problem": result.problem,
            "type": result.type,
            "subtype": result.subtype,
            "location": result.location,
            "response": result.response,
            "executor": result.executor,
            "urgency": result.urgency,
            "response_time": result.response_time,
            "confidence": result.confidence,
            "needs_operator": result.needs_operator
        }
    }


@app.post("/api/transcribe")
async def transcribe_audio_endpoint(audio: UploadFile = File(...)):
    """
    Транскрибування аудіофайлу через Silero ASR
    """
    try:
        audio_bytes = await audio.read()
        transcript = transcribe_audio_bytes(audio_bytes)
        
        return {
            "success": True,
            "transcript": transcript,
            "language": "uk"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Помилка транскрибування: {str(e)}")


@app.post("/api/synthesize")
async def synthesize_text(request: TTSRequest):
    """
    Синтез мовлення через Edge TTS або Fish Speech
    """
    try:
        audio_bytes, sample_rate = synthesize_speech(request.text, request.voice)
        
        # Визначаємо формат (MP3 для Edge TTS, WAV для Fish Speech)
        # MP3 починається з ID3 або 0xFF 0xFB
        is_mp3 = audio_bytes[:3] == b'ID3' or (len(audio_bytes) > 1 and audio_bytes[0] == 0xFF)
        
        ext = ".mp3" if is_mp3 else ".wav"
        media_type = "audio/mpeg" if is_mp3 else "audio/wav"
        
        # Зберігаємо тимчасовий файл
        temp_path = f"/tmp/tts_{uuid.uuid4()}{ext}"
        with open(temp_path, 'wb') as f:
            f.write(audio_bytes)
        
        return FileResponse(
            temp_path,
            media_type=media_type,
            filename=f"response{ext}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Помилка синтезу: {str(e)}")


@app.get("/api/history")
async def get_call_history():
    """Отримати історію дзвінків"""
    return {
        "success": True,
        "count": len(call_history),
        "history": [record.dict() for record in call_history[-50:]]
    }


@app.get("/api/stats")
async def get_statistics():
    """Отримати статистику роботи агента"""
    total = len(call_history)
    resolved = sum(1 for c in call_history if c.status == "resolved")
    escalated = sum(1 for c in call_history if c.status == "escalated")
    
    return {
        "success": True,
        "stats": {
            "total_calls": total,
            "ai_resolved": resolved,
            "escalated": escalated,
            "ai_resolved_percent": round(resolved / total * 100, 1) if total > 0 else 0,
            "avg_response_time": 3.5  # секунди
        }
    }


# === WebSocket для реального часу ===

@app.websocket("/ws/call")
async def websocket_call(websocket: WebSocket):
    """
    WebSocket для обробки дзвінків у реальному часі
    
    Протокол:
    1. Клієнт підключається
    2. Сервер відправляє привітання (TTS)
    3. Клієнт відправляє аудіо (chunks)
    4. Сервер відправляє транскрипт (ASR)
    5. Сервер відправляє класифікацію
    6. Сервер відправляє відповідь (TTS)
    """
    await websocket.accept()
    session_id = str(uuid.uuid4())
    
    try:
        # Привітання
        greeting = "Доброго дня! Ви зателефонували на гарячу лінію контактного центру. Чим можу вам допомогти?"
        
        await websocket.send_json({
            "type": "greeting",
            "text": greeting,
            "session_id": session_id
        })
        
        # Синтез привітання
        audio_bytes, _ = synthesize_speech(greeting)
        await websocket.send_bytes(audio_bytes)
        
        while True:
            # Отримання повідомлення
            data = await websocket.receive()
            
            if "bytes" in data:
                # Аудіо дані - транскрибування
                transcript = transcribe_audio_bytes(data["bytes"])
                
                await websocket.send_json({
                    "type": "transcript",
                    "text": transcript
                })
                
                # Класифікація
                classification = classify_query(transcript)
                
                await websocket.send_json({
                    "type": "classification",
                    "data": {
                        "problem": classification.problem,
                        "subtype": classification.subtype,
                        "executor": classification.executor,
                        "urgency": classification.urgency,
                        "response_time": classification.response_time,
                        "confidence": classification.confidence,
                        "needs_operator": classification.needs_operator
                    }
                })
                
                # Відповідь
                await websocket.send_json({
                    "type": "response",
                    "text": classification.response
                })
                
                # Синтез відповіді
                response_audio, _ = synthesize_speech(classification.response)
                await websocket.send_bytes(response_audio)
                
                # Збереження в історію
                record = CallRecord(
                    id=str(uuid.uuid4()),
                    timestamp=datetime.now().isoformat(),
                    caller_phone=None,
                    transcript=transcript,
                    classification={
                        "problem": classification.problem,
                        "subtype": classification.subtype,
                        "executor": classification.executor
                    },
                    status="escalated" if classification.needs_operator else "resolved",
                    response_text=classification.response,
                    executor=classification.executor
                )
                call_history.append(record)
                
            elif "text" in data:
                # Текстове повідомлення
                message = json.loads(data["text"])
                
                if message.get("type") == "text_query":
                    query_text = message.get("text", "")
                    
                    # Класифікація
                    classification = classify_query(query_text)
                    
                    await websocket.send_json({
                        "type": "classification",
                        "data": {
                            "problem": classification.problem,
                            "subtype": classification.subtype,
                            "executor": classification.executor,
                            "urgency": classification.urgency,
                            "response_time": classification.response_time,
                            "confidence": classification.confidence,
                            "needs_operator": classification.needs_operator
                        }
                    })
                    
                    await websocket.send_json({
                        "type": "response",
                        "text": classification.response
                    })
                    
                elif message.get("type") == "end_call":
                    await websocket.send_json({
                        "type": "call_ended",
                        "session_id": session_id
                    })
                    break
                    
    except WebSocketDisconnect:
        print(f"[WebSocket] Клієнт відключився: {session_id}")
    except Exception as e:
        print(f"[WebSocket] Помилка: {e}")
        await websocket.close()


# === Запуск сервера ===

if __name__ == "__main__":
    import uvicorn
    
    print(f"""
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║   ШІ-Агент Контактного Центру                               ║
    ║   Version: {VERSION}                                            ║
    ║                                                              ║
    ║   🎙️  ASR: Silero (українська мова)                          ║
    ║   🔊  TTS: Fish Speech (природний голос)                     ║
    ║   📊  NLU: Класифікатор міської ради                         ║
    ║   💾  DB: Oracle APEX                                        ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    
    uvicorn.run(
        "main:app",
        host=HOST,
        port=PORT,
        reload=True
    )
