"""
Сховище даних - персистентне зберігання для контактного центру
Підтримує SQLite та інтеграцію з Oracle APEX
"""
import json
import os
import sqlite3
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict, field
import uuid


# ============================================
# Моделі даних (Pydantic-сумісні dataclasses)
# ============================================

@dataclass
class ExecutorBase:
    """Базовий клас для виконавця"""
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    work_hours: Optional[str] = None
    description: Optional[str] = None
    is_active: bool = True


@dataclass
class Executor(ExecutorBase):
    """Виконавець з ID"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ClassifierItemBase:
    """Базовий клас для елемента класифікатора"""
    problem: str
    subtype: str
    response: str
    executor: str
    type: Optional[str] = None
    location: Optional[str] = None
    executor_id: Optional[str] = None
    urgency: str = "standard"  # emergency, short, standard, info
    response_time: int = 24
    keywords: List[str] = field(default_factory=list)
    is_active: bool = True


@dataclass
class ClassifierItem(ClassifierItemBase):
    """Елемент класифікатора з ID"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ConversationAlgorithmBase:
    """Базовий клас для алгоритму розмови"""
    name: str
    description: Optional[str] = None
    steps: List[Dict[str, Any]] = field(default_factory=list)
    trigger_keywords: List[str] = field(default_factory=list)
    is_default: bool = False
    is_active: bool = True


@dataclass
class ConversationAlgorithm(ConversationAlgorithmBase):
    """Алгоритм розмови з ID"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class CallRecordBase:
    """Базовий клас для запису дзвінка"""
    caller_phone: Optional[str] = None
    transcript: str = ""
    classification: Dict[str, Any] = field(default_factory=dict)
    status: str = "resolved"  # resolved, escalated
    response_text: str = ""
    executor: str = ""


@dataclass
class CallRecordCreate(CallRecordBase):
    """Створення запису дзвінка"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class CallRecord(CallRecordCreate):
    """Повний запис дзвінка"""
    duration_seconds: int = 0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


# ============================================
# Storage Service
# ============================================

class StorageService:
    """
    Сервіс для збереження та отримання даних
    
    Підтримує:
    - SQLite для локального зберігання
    - Готовий до інтеграції з Oracle APEX
    """
    
    def __init__(self, db_path: str = "./cti_agent.db"):
        """
        Ініціалізація сховища
        
        Args:
            db_path: Шлях до файлу SQLite бази даних
        """
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Ініціалізація структури бази даних"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Таблиця виконавців
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS executors (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                phone TEXT,
                email TEXT,
                work_hours TEXT,
                description TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TEXT,
                updated_at TEXT
            )
        ''')
        
        # Таблиця класифікатора
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS classifiers (
                id TEXT PRIMARY KEY,
                problem TEXT NOT NULL,
                subtype TEXT NOT NULL,
                type TEXT,
                location TEXT,
                response TEXT NOT NULL,
                executor TEXT NOT NULL,
                executor_id TEXT,
                urgency TEXT DEFAULT 'standard',
                response_time INTEGER DEFAULT 24,
                keywords TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TEXT,
                updated_at TEXT
            )
        ''')
        
        # Таблиця алгоритмів
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS algorithms (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                steps TEXT,
                trigger_keywords TEXT,
                is_default INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                created_at TEXT,
                updated_at TEXT
            )
        ''')
        
        # Таблиця історії дзвінків
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS call_history (
                id TEXT PRIMARY KEY,
                timestamp TEXT,
                caller_phone TEXT,
                transcript TEXT,
                classification TEXT,
                status TEXT,
                response_text TEXT,
                executor TEXT,
                duration_seconds INTEGER,
                created_at TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        
        print(f"[Storage] База даних ініціалізована: {self.db_path}")
    
    def _get_connection(self):
        """Отримання з'єднання з базою даних"""
        return sqlite3.connect(self.db_path)
    
    def _row_to_dict(self, row, columns):
        """Конвертація рядка SQL у словник"""
        return dict(zip(columns, row))
    
    # === Виконавці ===
    
    def create_executor(self, data: ExecutorBase) -> Dict:
        """Створити виконавця"""
        executor = Executor(**data.__dict__ if hasattr(data, '__dict__') else data)
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO executors (id, name, phone, email, work_hours, description, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            executor.id, executor.name, executor.phone, executor.email,
            executor.work_hours, executor.description, 1 if executor.is_active else 0,
            executor.created_at, executor.updated_at
        ))
        
        conn.commit()
        conn.close()
        
        return asdict(executor)
    
    def get_executor(self, executor_id: str) -> Optional[Dict]:
        """Отримати виконавця за ID"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM executors WHERE id = ?', (executor_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            columns = ['id', 'name', 'phone', 'email', 'work_hours', 'description', 'is_active', 'created_at', 'updated_at']
            return self._row_to_dict(row, columns)
        return None
    
    def get_executors(self, active_only: bool = False) -> List[Dict]:
        """Отримати всіх виконавців"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if active_only:
            cursor.execute('SELECT * FROM executors WHERE is_active = 1 ORDER BY name')
        else:
            cursor.execute('SELECT * FROM executors ORDER BY name')
        
        rows = cursor.fetchall()
        conn.close()
        
        columns = ['id', 'name', 'phone', 'email', 'work_hours', 'description', 'is_active', 'created_at', 'updated_at']
        return [self._row_to_dict(row, columns) for row in rows]
    
    def update_executor(self, executor_id: str, data: ExecutorBase) -> Optional[Dict]:
        """Оновити виконавця"""
        executor = self.get_executor(executor_id)
        if not executor:
            return None
        
        updated_at = datetime.now().isoformat()
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE executors SET name=?, phone=?, email=?, work_hours=?, description=?, is_active=?, updated_at=?
            WHERE id=?
        ''', (
            data.name, data.phone, data.email, data.work_hours,
            data.description, 1 if data.is_active else 0, updated_at, executor_id
        ))
        
        conn.commit()
        conn.close()
        
        return self.get_executor(executor_id)
    
    def delete_executor(self, executor_id: str) -> bool:
        """Видалити виконавця"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM executors WHERE id = ?', (executor_id,))
        deleted = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        
        return deleted
    
    # === Класифікатор ===
    
    def create_classifier(self, data: ClassifierItemBase) -> Dict:
        """Створити елемент класифікатора"""
        classifier_item = ClassifierItem(**data.__dict__ if hasattr(data, '__dict__') else data)
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO classifiers (id, problem, subtype, type, location, response, executor, executor_id, urgency, response_time, keywords, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            classifier_item.id, classifier_item.problem, classifier_item.subtype,
            classifier_item.type, classifier_item.location, classifier_item.response,
            classifier_item.executor, classifier_item.executor_id, classifier_item.urgency,
            classifier_item.response_time, json.dumps(classifier_item.keywords),
            1 if classifier_item.is_active else 0, classifier_item.created_at, classifier_item.updated_at
        ))
        
        conn.commit()
        conn.close()
        
        return asdict(classifier_item)
    
    def get_classifier(self, classifier_id: str) -> Optional[Dict]:
        """Отримати елемент класифікатора за ID"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM classifiers WHERE id = ?', (classifier_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            columns = ['id', 'problem', 'subtype', 'type', 'location', 'response', 'executor', 'executor_id', 'urgency', 'response_time', 'keywords', 'is_active', 'created_at', 'updated_at']
            result = self._row_to_dict(row, columns)
            result['keywords'] = json.loads(result['keywords'] or '[]')
            return result
        return None
    
    def get_classifiers(self, active_only: bool = False) -> List[Dict]:
        """Отримати всі елементи класифікатора"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if active_only:
            cursor.execute('SELECT * FROM classifiers WHERE is_active = 1 ORDER BY problem, subtype')
        else:
            cursor.execute('SELECT * FROM classifiers ORDER BY problem, subtype')
        
        rows = cursor.fetchall()
        conn.close()
        
        columns = ['id', 'problem', 'subtype', 'type', 'location', 'response', 'executor', 'executor_id', 'urgency', 'response_time', 'keywords', 'is_active', 'created_at', 'updated_at']
        results = []
        for row in rows:
            result = self._row_to_dict(row, columns)
            result['keywords'] = json.loads(result['keywords'] or '[]')
            results.append(result)
        
        return results
    
    def update_classifier(self, classifier_id: str, data: ClassifierItemBase) -> Optional[Dict]:
        """Оновити елемент класифікатора"""
        classifier_item = self.get_classifier(classifier_id)
        if not classifier_item:
            return None
        
        updated_at = datetime.now().isoformat()
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE classifiers SET problem=?, subtype=?, type=?, location=?, response=?, executor=?, executor_id=?, urgency=?, response_time=?, keywords=?, is_active=?, updated_at=?
            WHERE id=?
        ''', (
            data.problem, data.subtype, data.type, data.location, data.response,
            data.executor, data.executor_id, data.urgency, data.response_time,
            json.dumps(data.keywords), 1 if data.is_active else 0, updated_at, classifier_id
        ))
        
        conn.commit()
        conn.close()
        
        return self.get_classifier(classifier_id)
    
    def delete_classifier(self, classifier_id: str) -> bool:
        """Видалити елемент класифікатора"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM classifiers WHERE id = ?', (classifier_id,))
        deleted = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        
        return deleted
    
    # === Алгоритми ===
    
    def create_algorithm(self, data: ConversationAlgorithmBase) -> Dict:
        """Створити алгоритм"""
        algorithm = ConversationAlgorithm(**data.__dict__ if hasattr(data, '__dict__') else data)
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO algorithms (id, name, description, steps, trigger_keywords, is_default, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            algorithm.id, algorithm.name, algorithm.description,
            json.dumps(algorithm.steps), json.dumps(algorithm.trigger_keywords),
            1 if algorithm.is_default else 0, 1 if algorithm.is_active else 0,
            algorithm.created_at, algorithm.updated_at
        ))
        
        conn.commit()
        conn.close()
        
        return asdict(algorithm)
    
    def get_algorithm(self, algorithm_id: str) -> Optional[Dict]:
        """Отримати алгоритм за ID"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM algorithms WHERE id = ?', (algorithm_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            columns = ['id', 'name', 'description', 'steps', 'trigger_keywords', 'is_default', 'is_active', 'created_at', 'updated_at']
            result = self._row_to_dict(row, columns)
            result['steps'] = json.loads(result['steps'] or '[]')
            result['trigger_keywords'] = json.loads(result['trigger_keywords'] or '[]')
            return result
        return None
    
    def get_default_algorithm(self) -> Optional[Dict]:
        """Отримати алгоритм за замовчуванням"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM algorithms WHERE is_default = 1 AND is_active = 1 LIMIT 1')
        row = cursor.fetchone()
        conn.close()
        
        if row:
            columns = ['id', 'name', 'description', 'steps', 'trigger_keywords', 'is_default', 'is_active', 'created_at', 'updated_at']
            result = self._row_to_dict(row, columns)
            result['steps'] = json.loads(result['steps'] or '[]')
            result['trigger_keywords'] = json.loads(result['trigger_keywords'] or '[]')
            return result
        return None
    
    def get_algorithms(self, active_only: bool = False) -> List[Dict]:
        """Отримати всі алгоритми"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if active_only:
            cursor.execute('SELECT * FROM algorithms WHERE is_active = 1 ORDER BY name')
        else:
            cursor.execute('SELECT * FROM algorithms ORDER BY name')
        
        rows = cursor.fetchall()
        conn.close()
        
        columns = ['id', 'name', 'description', 'steps', 'trigger_keywords', 'is_default', 'is_active', 'created_at', 'updated_at']
        results = []
        for row in rows:
            result = self._row_to_dict(row, columns)
            result['steps'] = json.loads(result['steps'] or '[]')
            result['trigger_keywords'] = json.loads(result['trigger_keywords'] or '[]')
            results.append(result)
        
        return results
    
    def update_algorithm(self, algorithm_id: str, data: ConversationAlgorithmBase) -> Optional[Dict]:
        """Оновити алгоритм"""
        algorithm = self.get_algorithm(algorithm_id)
        if not algorithm:
            return None
        
        updated_at = datetime.now().isoformat()
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE algorithms SET name=?, description=?, steps=?, trigger_keywords=?, is_default=?, is_active=?, updated_at=?
            WHERE id=?
        ''', (
            data.name, data.description, json.dumps(data.steps),
            json.dumps(data.trigger_keywords), 1 if data.is_default else 0,
            1 if data.is_active else 0, updated_at, algorithm_id
        ))
        
        conn.commit()
        conn.close()
        
        return self.get_algorithm(algorithm_id)
    
    def delete_algorithm(self, algorithm_id: str) -> bool:
        """Видалити алгоритм"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM algorithms WHERE id = ?', (algorithm_id,))
        deleted = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        
        return deleted
    
    # === Історія дзвінків ===
    
    def create_call_record(self, data: CallRecordCreate) -> Dict:
        """Створити запис дзвінка"""
        record = CallRecordCreate(**data.__dict__ if hasattr(data, '__dict__') else data)
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO call_history (id, timestamp, caller_phone, transcript, classification, status, response_text, executor, duration_seconds, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            record.id, record.timestamp, record.caller_phone, record.transcript,
            json.dumps(record.classification), record.status, record.response_text,
            record.executor, 0, datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
        
        return asdict(record)
    
    def get_call_history(self, limit: int = 50, offset: int = 0) -> List[Dict]:
        """Отримати історію дзвінків"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM call_history
            ORDER BY timestamp DESC
            LIMIT ? OFFSET ?
        ''', (limit, offset))
        
        rows = cursor.fetchall()
        conn.close()
        
        columns = ['id', 'timestamp', 'caller_phone', 'transcript', 'classification', 'status', 'response_text', 'executor', 'duration_seconds', 'created_at']
        results = []
        for row in rows:
            result = self._row_to_dict(row, columns)
            result['classification'] = json.loads(result['classification'] or '{}')
            results.append(result)
        
        return results
    
    def get_calls_count(self, status: Optional[str] = None) -> int:
        """Отримати кількість дзвінків"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if status:
            cursor.execute('SELECT COUNT(*) FROM call_history WHERE status = ?', (status,))
        else:
            cursor.execute('SELECT COUNT(*) FROM call_history')
        
        count = cursor.fetchone()[0]
        conn.close()
        
        return count
    
    def get_average_response_time(self) -> Optional[float]:
        """Отримати середній час відповіді"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT AVG(duration_seconds) FROM call_history WHERE duration_seconds > 0')
        avg = cursor.fetchone()[0]
        conn.close()
        
        return float(avg) if avg else None
    
    def get_statistics(self) -> Dict:
        """Отримати повну статистику"""
        total = self.get_calls_count()
        resolved = self.get_calls_count(status="resolved")
        escalated = self.get_calls_count(status="escalated")
        avg_time = self.get_average_response_time()
        
        return {
            "total_calls": total,
            "ai_resolved": resolved,
            "escalated": escalated,
            "ai_resolved_percent": round(resolved / total * 100, 1) if total > 0 else 0,
            "avg_response_time": avg_time or 3.5
        }


# Глобальний екземпляр сховища
storage = StorageService()
