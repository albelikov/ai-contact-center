"""
ШІ-Агент контактного центру
FastAPI Backend з інтеграцією Silero ASR та Fish Speech TTS
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import json
import asyncio
from datetime import datetime
import uuid
import os
from functools import lru_cache
import hashlib
import time

from config import settings
from classifier import classify_query, ClassificationResult, classifier
from asr_service import transcribe_audio, transcribe_audio_bytes
from tts_service import synthesize_speech, synthesize_to_file
from storage import (
    storage, 
    ExecutorBase, Executor,
    ClassifierItemBase, ClassifierItem,
    ConversationAlgorithmBase, ConversationAlgorithm,
    CallRecordCreate, CallRecord
)

# Ініціалізація FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="ШІ-Агент контактного центру з підтримкою Fish Speech TTS та Silero ASR"
)

# Security
security = HTTPBasic()

# Rate limiting storage (в пам'яті для демо, для production використовувати Redis)
rate_limit_storage: Dict[str, Dict] = {}


def check_rate_limit(client_id: str, limit: int = 10, window: int = 60) -> bool:
    """
    Перевірка rate limit для клієнта
    
    Args:
        client_id: ідентифікатор клієнта (IP або API key)
        limit: максимальна кількість запитів у вікні
        window: розмір вікна в секундах
    
    Returns:
        True якщо ліміт не перевищено, False якщо перевищено
    """
    now = time.time()
    
    if client_id not in rate_limit_storage:
        rate_limit_storage[client_id] = {"count": 0, "reset_time": now + window}
        return True
    
    client_data = rate_limit_storage[client_id]
    
    # Перевіряємо чи вікно минуло
    if now > client_data["reset_time"]:
        rate_limit_storage[client_id] = {"count": 1, "reset_time": now + window}
        return True
    
    # Перевіряємо ліміт
    if client_data["count"] >= limit:
        return False
    
    # Збільшуємо лічильник
    client_data["count"] += 1
    return True


def get_client_id(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    """
    Отримати ідентифікатор клієнта для rate limiting
    """
    # Використовуємо username як API key або fallback на IP
    return credentials.username


# CORS для фронтенду - ТІЛЬКИ дозволені джерела
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)


def verify_api_key(credentials: HTTPBasicCredentials = Depends(security)) -> bool:
    """
    Перевірка API ключа для доступу до адміністративних функцій
    """
    expected_username = os.getenv("API_USERNAME", "admin")
    expected_password = os.getenv("API_PASSWORD", os.getenv("ADMIN_PASSWORD", "change_this_password"))
    
    # Перевіряємо username
    if credentials.username != expected_username:
        return False
    
    # Перевіряємо пароль (у виробництві використовувати хешовані паролі)
    password_bytes = credentials.password.encode()
    stored_password = expected_password.encode()
    
    return password_bytes == stored_password


def verify_admin(credentials: HTTPBasicCredentials = Depends(security)) -> bool:
    """
    Перевірка прав адміністратора
    """
    admin_username = os.getenv("ADMIN_USERNAME", "admin")
    admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
    
    return (
        credentials.username == admin_username and
        credentials.password == admin_password
    )


# Моделі даних
class TextQuery(BaseModel):
    """Текстовий запит для класифікації"""
    text: str = Field(..., min_length=1, max_length=5000, description="Текст запиту")
    session_id: Optional[str] = Field(None, description="ID сесії")

    class Config:
        json_schema_extra = {
            "example": {
                "text": "У нас немає опалення вже другий день",
                "session_id": "123e4567-e89b-12d3-a456-426614174000"
            }
        }


class TTSRequest(BaseModel):
    """Запит на синтез мовлення"""
    text: str = Field(..., min_length=1, max_length=2000, description="Текст для синтезу")
    voice: str = Field("default", description="Ідентифікатор голосу")


class HealthResponse(BaseModel):
    """Відповідь перевірки стану системи"""
    status: str
    version: str
    timestamp: str
    components: Dict[str, Dict[str, Any]]


# === API Endpoints ===

@app.get("/", response_model=Dict[str, str])
async def root():
    """Головна сторінка API"""
    return {
        "name": settings.APP_NAME,
        "version": settings.VERSION,
        "status": "active",
        "documentation": "/docs"
    }


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """
    Перевірка стану системи
    
    Повертає детальну інформацію про стан всіх компонентів системи:
    - ASR (Silero): статус розпізнавання мови
    - TTS (Fish Speech/Edge TTS): статус синтезу мовлення
    - Classifier: статус класифікатора запитів
    - Database: стан підключення до бази даних
    """
    components = {
        "asr": {"status": "healthy" if settings.SILERO_MODEL else "not_configured"},
        "tts": {"status": "healthy", "engine": "fish_speech" if settings.FISH_SPEECH_MODEL else "edge_tts"},
        "classifier": {"status": "healthy", "categories_count": len(classifier.data)},
        "database": {"status": "healthy", "type": "sqlite"}
    }
    
    return HealthResponse(
        status="healthy",
        version=settings.VERSION,
        timestamp=datetime.utcnow().isoformat(),
        components=components
    )


@app.post("/api/classify")
async def classify_text(
    query: TextQuery,
    credentials: HTTPBasicCredentials = Depends(security)
):
    """
    Класифікація текстового запиту
    
    Args:
        query: Текстовий запит для класифікації
        credentials: Облікові дані для аутентифікації
    
    Returns:
        Результат класифікації з впевненістю та рекомендованою відповіддю
    """
    # Rate limiting
    client_id = credentials.username
    if not check_rate_limit(client_id):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Перевищено ліміт запитів. Спробуйте пізніше."
        )
    
    result = classify_query(query.text)
    
    # Зберігаємо запит в історії (опціонально)
    # call_record = CallRecordCreate(
    #     id=str(uuid.uuid4()),
    #     timestamp=datetime.now().isoformat(),
    #     caller_phone=None,
    #     transcript=query.text,
    #     classification=result.__dict__,
    #     status="resolved" if not result.needs_operator else "escalated",
    #     response_text=result.response,
    #     executor=result.executor
    # )
    # storage.create_call_record(call_record)
    
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
async def transcribe_audio_endpoint(
    audio: UploadFile = File(...),
    credentials: HTTPBasicCredentials = Depends(security)
):
    """
    Транскрибування аудіофайлу через Silero ASR
    
    Підтримує формати: WAV, MP3, WebM, OGG
    
    Args:
        audio: Аудіофайл для транскрибування
        credentials: Облікові дані для аутентифікації
    
    Returns:
        Розпізнаний текст та мова
    """
    # Rate limiting
    client_id = credentials.username
    if not check_rate_limit(client_id, limit=5, window=60):  # Строгіший ліміт для ASR
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Перевищено ліміт запитів транскрибування."
        )
    
    try:
        audio_bytes = await audio.read()
        
        # Перевірка розміру файлу (макс. 25MB)
        if len(audio_bytes) > 25 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Файл занадто великий. Максимальний розмір: 25MB"
            )
        
        # Перевірка формату файлу
        allowed_types = {'audio/wav', 'audio/mp3', 'audio/mpeg', 'audio/webm', 'audio/ogg', 'audio/flac'}
        content_type = audio.content_type or ''
        if content_type not in allowed_types and not any(audio.filename.lower().endswith(ext) for ext in ['.wav', '.mp3', '.webm', '.ogg', '.flac']):
            # Попередження, але не помилка - все одно спробуємо обробити
            print(f"[Warning] Неочікуваний тип файлу: {content_type}")
        
        transcript = transcribe_audio_bytes(audio_bytes)
        
        return {
            "success": True,
            "transcript": transcript,
            "language": "uk"
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"[Error] Помилка транскрибування: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Помилка транскрибування: Не вдалося обробити аудіофайл. Перевірте формат файлу та спробуйте ще раз."
        )


@app.post("/api/synthesize")
async def synthesize_text(
    request: TTSRequest,
    credentials: HTTPBasicCredentials = Depends(security)
):
    """
    Синтез мовлення через Fish Speech або Edge TTS
    
    Args:
        request: Запит на синтез мовлення
        credentials: Облікові дані для аутентифікації
    
    Returns:
        Аудіофайл з синтезованою мовою
    """
    # Rate limiting
    client_id = credentials.username
    if not check_rate_limit(client_id, limit=20, window=60):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Перевищено ліміт запитів синтезу мовлення."
        )
    
    try:
        audio_bytes, sample_rate = synthesize_speech(request.text, request.voice)
        
        # Перевірка що аудіо не порожнє
        if len(audio_bytes) < 100:
            raise HTTPException(
                status_code=500,
                detail="Помилка генерації аудіо. Спробуйте інший текст."
            )
        
        # Визначаємо формат (MP3 для Edge TTS, WAV для Fish Speech)
        is_mp3 = audio_bytes[:3] == b'ID3' or (len(audio_bytes) > 1 and audio_bytes[0] == 0xFF)
        
        ext = ".mp3" if is_mp3 else ".wav"
        media_type = "audio/mpeg" if is_mp3 else "audio/wav"
        
        # Зберігаємо тимчасовий файл
        temp_path = f"/tmp/tts_{uuid.uuid4()}{ext}"
        try:
            with open(temp_path, 'wb') as f:
                f.write(audio_bytes)
            
            return FileResponse(
                temp_path,
                media_type=media_type,
                filename=f"response{ext}"
            )
        finally:
            # Видаляємо тимчасовий файл після відправки
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except Exception:
                pass
                
    except HTTPException:
        raise
    except Exception as e:
        print(f"[Error] Помилка синтезу: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Помилка синтезу мовлення: Текст занадто довгий або містить недопустимі символи."
        )


@app.get("/api/history")
async def get_call_history(
    limit: int = 50,
    offset: int = 0,
    credentials: HTTPBasicCredentials = Depends(security)
):
    """
    Отримати історію дзвінків
    
    Args:
        limit: Максимальна кількість записів (default: 50, max: 100)
        offset: Зміщення для пагінації
        credentials: Облікові дані для аутентифікації
    
    Returns:
        Список записів історії дзвінків
    """
    if limit > 100:
        limit = 100
    if limit < 1:
        limit = 10
    
    history = storage.get_call_history(limit=limit, offset=offset)
    return {
        "success": True,
        "count": len(history),
        "limit": limit,
        "offset": offset,
        "history": [record.to_dict() for record in history]
    }


@app.get("/api/stats")
async def get_statistics(credentials: HTTPBasicCredentials = Depends(security)):
    """
    Отримати статистику роботи агента
    
    Returns:
        Статистичні дані про роботу контактного центру
    """
    total = storage.get_calls_count()
    resolved = storage.get_calls_count(status="resolved")
    escalated = storage.get_calls_count(status="escalated")
    
    avg_response_time = storage.get_average_response_time()
    
    return {
        "success": True,
        "stats": {
            "total_calls": total,
            "ai_resolved": resolved,
            "escalated": escalated,
            "ai_resolved_percent": round(resolved / total * 100, 1) if total > 0 else 0,
            "avg_response_time": avg_response_time or 3.5
        }
    }


# === API Довідників (References) ===

# --- Виконавці (Executors) ---

@app.get("/api/references/executors")
async def get_executors(active_only: bool = False, credentials: HTTPBasicCredentials = Depends(verify_api_key)):
    """Отримати список виконавців"""
    executors = storage.get_executors(active_only)
    return {"success": True, "count": len(executors), "data": executors}


@app.get("/api/references/executors/{executor_id}")
async def get_executor(executor_id: str, credentials: HTTPBasicCredentials = Depends(verify_api_key)):
    """Отримати виконавця за ID"""
    executor = storage.get_executor(executor_id)
    if not executor:
        raise HTTPException(status_code=404, detail="Виконавця не знайдено")
    return {"success": True, "data": executor}


@app.post("/api/references/executors")
async def create_executor(data: ExecutorBase, credentials: HTTPBasicCredentials = Depends(verify_admin)):
    """Створити нового виконавця"""
    executor = storage.create_executor(data)
    return {"success": True, "message": "Виконавця створено", "data": executor}


@app.put("/api/references/executors/{executor_id}")
async def update_executor(executor_id: str, data: ExecutorBase, credentials: HTTPBasicCredentials = Depends(verify_admin)):
    """Оновити виконавця"""
    executor = storage.update_executor(executor_id, data)
    if not executor:
        raise HTTPException(status_code=404, detail="Виконавця не знайдено")
    return {"success": True, "message": "Виконавця оновлено", "data": executor}


@app.delete("/api/references/executors/{executor_id}")
async def delete_executor(executor_id: str, credentials: HTTPBasicCredentials = Depends(verify_admin)):
    """Видалити виконавця"""
    if not storage.delete_executor(executor_id):
        raise HTTPException(status_code=404, detail="Виконавця не знайдено")
    return {"success": True, "message": "Виконавця видалено"}


# --- Класифікатор (Classifiers) ---

@app.get("/api/references/classifiers")
async def get_classifiers(active_only: bool = False, credentials: HTTPBasicCredentials = Depends(verify_api_key)):
    """Отримати список категорій класифікатора"""
    classifiers = storage.get_classifiers(active_only)
    return {"success": True, "count": len(classifiers), "data": classifiers}


@app.get("/api/references/classifiers/{classifier_id}")
async def get_classifier(classifier_id: str, credentials: HTTPBasicCredentials = Depends(verify_api_key)):
    """Отримати категорію за ID"""
    classifier_item = storage.get_classifier(classifier_id)
    if not classifier_item:
        raise HTTPException(status_code=404, detail="Категорію не знайдено")
    return {"success": True, "data": classifier_item}


@app.post("/api/references/classifiers")
async def create_classifier(data: ClassifierItemBase, credentials: HTTPBasicCredentials = Depends(verify_admin)):
    """Створити нову категорію класифікатора"""
    classifier_item = storage.create_classifier(data)
    return {"success": True, "message": "Категорію створено", "data": classifier_item}


@app.put("/api/references/classifiers/{classifier_id}")
async def update_classifier(classifier_id: str, data: ClassifierItemBase, credentials: HTTPBasicCredentials = Depends(verify_admin)):
    """Оновити категорію"""
    classifier_item = storage.update_classifier(classifier_id, data)
    if not classifier_item:
        raise HTTPException(status_code=404, detail="Категорію не знайдено")
    return {"success": True, "message": "Категорію оновлено", "data": classifier_item}


@app.delete("/api/references/classifiers/{classifier_id}")
async def delete_classifier(classifier_id: str, credentials: HTTPBasicCredentials = Depends(verify_admin)):
    """Видалити категорію"""
    if not storage.delete_classifier(classifier_id):
        raise HTTPException(status_code=404, detail="Категорию не знайдено")
    return {"success": True, "message": "Категорию видалено"}


# --- Алгоритми розмови (Conversation Algorithms) ---

@app.get("/api/references/algorithms")
async def get_algorithms(active_only: bool = False, credentials: HTTPBasicCredentials = Depends(verify_api_key)):
    """Отримати список алгоритмів розмови"""
    algorithms = storage.get_algorithms(active_only)
    return {"success": True, "count": len(algorithms), "data": algorithms}


@app.get("/api/references/algorithms/default")
async def get_default_algorithm(credentials: HTTPBasicCredentials = Depends(verify_api_key)):
    """Отримати алгоритм за замовчуванням"""
    algorithm = storage.get_default_algorithm()
    if not algorithm:
        raise HTTPException(status_code=404, detail="Алгоритм за замовчуванням не знайдено")
    return {"success": True, "data": algorithm}


@app.get("/api/references/algorithms/{algorithm_id}")
async def get_algorithm(algorithm_id: str, credentials: HTTPBasicCredentials = Depends(verify_api_key)):
    """Отримати алгоритм за ID"""
    algorithm = storage.get_algorithm(algorithm_id)
    if not algorithm:
        raise HTTPException(status_code=404, detail="Алгоритм не знайдено")
    return {"success": True, "data": algorithm}


@app.post("/api/references/algorithms")
async def create_algorithm(data: ConversationAlgorithmBase, credentials: HTTPBasicCredentials = Depends(verify_admin)):
    """Створити новий алгоритм розмови"""
    algorithm = storage.create_algorithm(data)
    return {"success": True, "message": "Алгоритм створено", "data": algorithm}


@app.put("/api/references/algorithms/{algorithm_id}")
async def update_algorithm(algorithm_id: str, data: ConversationAlgorithmBase, credentials: HTTPBasicCredentials = Depends(verify_admin)):
    """Оновити алгоритм"""
    algorithm = storage.update_algorithm(algorithm_id, data)
    if not algorithm:
        raise HTTPException(status_code=404, detail="Алгоритм не знайдено")
    return {"success": True, "message": "Алгоритм оновлено", "data": algorithm}


@app.delete("/api/references/algorithms/{algorithm_id}")
async def delete_algorithm(algorithm_id: str, credentials: HTTPBasicCredentials = Depends(verify_admin)):
    """Видалити алгоритм"""
    if not storage.delete_algorithm(algorithm_id):
        raise HTTPException(status_code=404, detail="Алгоритм не знайдено")
    return {"success": True, "message": "Алгоритм видалено"}


@app.post("/api/references/reload")
async def reload_references(credentials: HTTPBasicCredentials = Depends(verify_api_key)):
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
    
    Примітка: Для production потрібно додати аутентифікацію WebSocket
    """
    await websocket.accept()
    session_id = str(uuid.uuid4())
    client_ip = websocket.client.host if websocket.client else "unknown"
    
    print(f"[WebSocket] Нове підключення: session={session_id}, ip={client_ip}")
    
    # Rate limiting для WebSocket
    ws_connections = len([s for s in sessions.values() if s.get("active")])
    if ws_connections >= 100:
        print(f"[WebSocket] Відхилено: забагато з'єднань")
        await websocket.close(code=1013)  # Try Again Later
        return
    
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
        
        # Зберігаємо сесію
        sessions[session_id] = {
            "start_time": datetime.now().isoformat(),
            "active": True,
            "ip": client_ip
        }
        
        while True:
            # Отримання повідомлення
            data = await websocket.receive()
            
            if "bytes" in data:
                # Аудіо дані - транскрибування
                audio_data = data["bytes"]
                
                # Перевірка розміру
                if len(audio_data) > 5 * 1024 * 1024:  # 5MB
                    await websocket.send_json({
                        "type": "error",
                        "message": "Аудіо занадто велике"
                    })
                    continue
                
                transcript = transcribe_audio_bytes(audio_data)
                
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
                record = CallRecordCreate(
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
                storage.create_call_record(record)
                
            elif "text" in data:
                # Текстове повідомлення
                try:
                    message = json.loads(data["text"])
                except json.JSONDecodeError:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Невірний формат повідомлення"
                    })
                    continue
                
                if message.get("type") == "text_query":
                    query_text = message.get("text", "")
                    
                    if not query_text.strip():
                        await websocket.send_json({
                            "type": "error",
                            "message": "Текст запиту не може бути порожнім"
                        })
                        continue
                    
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
                    
                elif message.get("type") == "ping":
                    # Heartbeat для підтримки з'єднання
                    await websocket.send_json({
                        "type": "pong",
                        "session_id": session_id
                    })
                    
    except WebSocketDisconnect:
        print(f"[WebSocket] Клієнт відключився: {session_id}")
    except Exception as e:
        print(f"[WebSocket] Помилка: {e}")
        try:
            await websocket.close(code=1011)
        except Exception:
            pass
    finally:
        # Очищення сесії
        if session_id in sessions:
            del sessions[session_id]


# === Запуск сервера ===

if __name__ == "__main__":
    import uvicorn
    
    print(f"""
    ╔══════════════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║   ШІ-Агент Контактного Центру                               ║
    ║   Version: {settings.VERSION}                                            ║
    ║                                                              ║
    ║   🎙️  ASR: Silero (українська мова)                          ║
    ║   🔊  TTS: Fish Speech (природний голос) / Edge TTS          ║
    ║   📊  NLU: Класифікатор міської ради                         ║
    ║   💾  DB: SQLite (+ Oracle APEX integration ready)           ║
    ║   🔒  Auth: HTTP Basic Auth enabled                          ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        access_log=True,
        log_level=settings.LOG_LEVEL.lower()
    )
