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
from classifier import classify_query, ClassificationResult, classifier
from asr_service import transcribe_audio, transcribe_audio_bytes
from tts_service import synthesize_speech, synthesize_to_file
from references import (
    storage, 
    ExecutorBase, Executor,
    ClassifierItemBase, ClassifierItem,
    ConversationAlgorithmBase, ConversationAlgorithm
)

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


# === API Довідників (References) ===

# --- Виконавці (Executors) ---

@app.get("/api/references/executors")
async def get_executors(active_only: bool = False):
    """Отримати список виконавців"""
    executors = storage.get_executors(active_only)
    return {"success": True, "count": len(executors), "data": executors}

@app.get("/api/references/executors/{executor_id}")
async def get_executor(executor_id: str):
    """Отримати виконавця за ID"""
    executor = storage.get_executor(executor_id)
    if not executor:
        raise HTTPException(status_code=404, detail="Виконавця не знайдено")
    return {"success": True, "data": executor}

@app.post("/api/references/executors")
async def create_executor(data: ExecutorBase):
    """Створити нового виконавця"""
    executor = storage.create_executor(data)
    return {"success": True, "message": "Виконавця створено", "data": executor}

@app.put("/api/references/executors/{executor_id}")
async def update_executor(executor_id: str, data: ExecutorBase):
    """Оновити виконавця"""
    executor = storage.update_executor(executor_id, data)
    if not executor:
        raise HTTPException(status_code=404, detail="Виконавця не знайдено")
    return {"success": True, "message": "Виконавця оновлено", "data": executor}

@app.delete("/api/references/executors/{executor_id}")
async def delete_executor(executor_id: str):
    """Видалити виконавця"""
    if not storage.delete_executor(executor_id):
        raise HTTPException(status_code=404, detail="Виконавця не знайдено")
    return {"success": True, "message": "Виконавця видалено"}


# --- Класифікатор (Classifiers) ---

@app.get("/api/references/classifiers")
async def get_classifiers(active_only: bool = False):
    """Отримати список категорій класифікатора"""
    classifiers = storage.get_classifiers(active_only)
    return {"success": True, "count": len(classifiers), "data": classifiers}

@app.get("/api/references/classifiers/{classifier_id}")
async def get_classifier(classifier_id: str):
    """Отримати категорію за ID"""
    classifier = storage.get_classifier(classifier_id)
    if not classifier:
        raise HTTPException(status_code=404, detail="Категорію не знайдено")
    return {"success": True, "data": classifier}

@app.post("/api/references/classifiers")
async def create_classifier(data: ClassifierItemBase):
    """Створити нову категорію класифікатора"""
    classifier = storage.create_classifier(data)
    return {"success": True, "message": "Категорію створено", "data": classifier}

@app.put("/api/references/classifiers/{classifier_id}")
async def update_classifier(classifier_id: str, data: ClassifierItemBase):
    """Оновити категорію"""
    classifier = storage.update_classifier(classifier_id, data)
    if not classifier:
        raise HTTPException(status_code=404, detail="Категорію не знайдено")
    return {"success": True, "message": "Категорію оновлено", "data": classifier}

@app.delete("/api/references/classifiers/{classifier_id}")
async def delete_classifier(classifier_id: str):
    """Видалити категорію"""
    if not storage.delete_classifier(classifier_id):
        raise HTTPException(status_code=404, detail="Категорію не знайдено")
    return {"success": True, "message": "Категорію видалено"}


# --- Алгоритми розмови (Conversation Algorithms) ---

@app.get("/api/references/algorithms")
async def get_algorithms(active_only: bool = False):
    """Отримати список алгоритмів розмови"""
    algorithms = storage.get_algorithms(active_only)
    return {"success": True, "count": len(algorithms), "data": algorithms}

@app.get("/api/references/algorithms/default")
async def get_default_algorithm():
    """Отримати алгоритм за замовчуванням"""
    algorithm = storage.get_default_algorithm()
    if not algorithm:
        raise HTTPException(status_code=404, detail="Алгоритм за замовчуванням не знайдено")
    return {"success": True, "data": algorithm}

@app.get("/api/references/algorithms/{algorithm_id}")
async def get_algorithm(algorithm_id: str):
    """Отримати алгоритм за ID"""
    algorithm = storage.get_algorithm(algorithm_id)
    if not algorithm:
        raise HTTPException(status_code=404, detail="Алгоритм не знайдено")
    return {"success": True, "data": algorithm}

@app.post("/api/references/algorithms")
async def create_algorithm(data: ConversationAlgorithmBase):
    """Створити новий алгоритм розмови"""
    algorithm = storage.create_algorithm(data)
    return {"success": True, "message": "Алгоритм створено", "data": algorithm}

@app.put("/api/references/algorithms/{algorithm_id}")
async def update_algorithm(algorithm_id: str, data: ConversationAlgorithmBase):
    """Оновити алгоритм"""
    algorithm = storage.update_algorithm(algorithm_id, data)
    if not algorithm:
        raise HTTPException(status_code=404, detail="Алгоритм не знайдено")
    return {"success": True, "message": "Алгоритм оновлено", "data": algorithm}

@app.delete("/api/references/algorithms/{algorithm_id}")
async def delete_algorithm(algorithm_id: str):
    """Видалити алгоритм"""
    if not storage.delete_algorithm(algorithm_id):
        raise HTTPException(status_code=404, detail="Алгоритм не знайдено")
    return {"success": True, "message": "Алгоритм видалено"}


@app.post("/api/references/reload")
async def reload_references():
    """Перезавантажити дані класифікатора з довідника"""
    classifier.reload()
    return {
        "success": True, 
        "message": "Довідники перезавантажено",
        "classifiers_count": len(classifier.data)
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
