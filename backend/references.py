"""
Модуль довідників (справочників)
Класифікатор, Виконавці, Алгоритми розмови
"""
import json
import os
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

# Шлях до файлів даних
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)


# === Pydantic Models ===

class ExecutorBase(BaseModel):
    """Базова модель виконавця"""
    name: str = Field(..., description="Назва виконавця/служби")
    phone: Optional[str] = Field(None, description="Телефон")
    email: Optional[str] = Field(None, description="Email")
    work_hours: Optional[str] = Field(None, description="Години роботи")
    description: Optional[str] = Field(None, description="Опис")
    is_active: bool = Field(True, description="Чи активний")

class Executor(ExecutorBase):
    """Виконавець з ID"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: Optional[str] = None


class ClassifierItemBase(BaseModel):
    """Базова модель категорії класифікатора"""
    problem: str = Field(..., description="Категорія проблеми")
    type: str = Field(..., description="Тип проблеми")
    subtype: str = Field(..., description="Підтип проблеми")
    location: Optional[str] = Field(None, description="Локація")
    response: str = Field(..., description="Шаблон відповіді")
    executor_id: Optional[str] = Field(None, description="ID виконавця")
    executor_name: Optional[str] = Field(None, description="Назва виконавця (якщо немає ID)")
    urgency: str = Field("standard", description="Терміновість: emergency, short, standard, info")
    response_time: int = Field(24, description="Час відповіді в годинах")
    keywords: List[str] = Field(default_factory=list, description="Ключові слова для пошуку")
    is_active: bool = Field(True, description="Чи активна категорія")

class ClassifierItem(ClassifierItemBase):
    """Категорія класифікатора з ID"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: Optional[str] = None


class ConversationStepBase(BaseModel):
    """Крок алгоритму розмови"""
    order: int = Field(..., description="Порядковий номер")
    type: str = Field(..., description="Тип: greeting, question, response, farewell, transfer")
    text: str = Field(..., description="Текст для озвучення")
    condition: Optional[str] = Field(None, description="Умова виконання (Python вираз)")
    next_step: Optional[int] = Field(None, description="Наступний крок (якщо не послідовний)")
    wait_for_input: bool = Field(False, description="Чекати відповідь користувача")
    save_to: Optional[str] = Field(None, description="Зберегти відповідь в змінну")

class ConversationAlgorithmBase(BaseModel):
    """Базова модель алгоритму розмови"""
    name: str = Field(..., description="Назва алгоритму")
    description: Optional[str] = Field(None, description="Опис")
    trigger_keywords: List[str] = Field(default_factory=list, description="Ключові слова для запуску")
    classifier_ids: List[str] = Field(default_factory=list, description="ID категорій класифікатора")
    steps: List[ConversationStepBase] = Field(default_factory=list, description="Кроки розмови")
    is_default: bool = Field(False, description="Алгоритм за замовчуванням")
    is_active: bool = Field(True, description="Чи активний")

class ConversationAlgorithm(ConversationAlgorithmBase):
    """Алгоритм розмови з ID"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: Optional[str] = None


# === Data Storage ===

class ReferenceStorage:
    """Зберігання довідників у JSON файлах"""
    
    def __init__(self):
        self.executors_file = os.path.join(DATA_DIR, "executors.json")
        self.classifiers_file = os.path.join(DATA_DIR, "classifiers.json")
        self.algorithms_file = os.path.join(DATA_DIR, "algorithms.json")
        
        # Ініціалізація файлів з початковими даними
        self._init_default_data()
    
    def _load_json(self, filepath: str) -> List[Dict]:
        """Завантажити дані з JSON"""
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    def _save_json(self, filepath: str, data: List[Dict]):
        """Зберегти дані в JSON"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _init_default_data(self):
        """Ініціалізація початкових даних"""
        # Виконавці
        if not os.path.exists(self.executors_file):
            default_executors = [
                {
                    "id": "exec-1",
                    "name": "Аварійна служба",
                    "phone": "104",
                    "work_hours": "24/7",
                    "description": "Аварійні ситуації",
                    "is_active": True,
                    "created_at": datetime.now().isoformat()
                },
                {
                    "id": "exec-2",
                    "name": "Управитель будинку",
                    "phone": None,
                    "work_hours": "09:00-18:00",
                    "description": "Обслуговування будинків",
                    "is_active": True,
                    "created_at": datetime.now().isoformat()
                },
                {
                    "id": "exec-3",
                    "name": "Служба теплопостачання",
                    "phone": "15-88",
                    "work_hours": "24/7",
                    "description": "Опалення та гаряча вода",
                    "is_active": True,
                    "created_at": datetime.now().isoformat()
                },
                {
                    "id": "exec-4",
                    "name": "Служба водопостачання",
                    "phone": "15-85",
                    "work_hours": "24/7",
                    "description": "Водопостачання та каналізація",
                    "is_active": True,
                    "created_at": datetime.now().isoformat()
                },
                {
                    "id": "exec-5",
                    "name": "Департамент транспорту",
                    "phone": None,
                    "work_hours": "09:00-18:00",
                    "description": "Громадський транспорт",
                    "is_active": True,
                    "created_at": datetime.now().isoformat()
                }
            ]
            self._save_json(self.executors_file, default_executors)
        
        # Класифікатор
        if not os.path.exists(self.classifiers_file):
            default_classifiers = [
                {
                    "id": "class-1",
                    "problem": "Благоустрій території",
                    "type": "Утримання території в зимовий період",
                    "subtype": "розчистка снігу",
                    "location": "прибудинкова територія",
                    "response": "Вашу заявку щодо розчистки снігу прийнято. Роботи будуть виконані протягом 24 годин.",
                    "executor_id": "exec-2",
                    "executor_name": "Управитель будинку",
                    "urgency": "short",
                    "response_time": 24,
                    "keywords": ["сніг", "розчистка", "прибрати", "замело", "снігопад", "двір"],
                    "is_active": True,
                    "created_at": datetime.now().isoformat()
                },
                {
                    "id": "class-2",
                    "problem": "Благоустрій території",
                    "type": "Благоустрій та санітарний стан",
                    "subtype": "впавше дерево",
                    "location": "на машину",
                    "response": "Надійшла заявка про дерево, що впало. Аварійна служба виконає роботи протягом 3 годин.",
                    "executor_id": "exec-1",
                    "executor_name": "Аварійна служба",
                    "urgency": "emergency",
                    "response_time": 3,
                    "keywords": ["дерево", "впало", "машина", "автомобіль", "гілка", "розпилити"],
                    "is_active": True,
                    "created_at": datetime.now().isoformat()
                },
                {
                    "id": "class-3",
                    "problem": "Ремонт житлового фонду",
                    "type": "Покрівля",
                    "subtype": "протікання даху",
                    "location": "квартира",
                    "response": "Ваша заява щодо протікання даху прийнята. Аварійна служба вже направлена.",
                    "executor_id": "exec-1",
                    "executor_name": "Аварійна служба",
                    "urgency": "emergency",
                    "response_time": 3,
                    "keywords": ["протікає", "дах", "стеля", "вода", "капає", "мокро", "покрівля"],
                    "is_active": True,
                    "created_at": datetime.now().isoformat()
                },
                {
                    "id": "class-4",
                    "problem": "Інженерні мережі",
                    "type": "Опалення",
                    "subtype": "відсутність опалення",
                    "location": "квартира",
                    "response": "Заявку щодо відсутності опалення прийнято. Перевірка системи буде виконана протягом 3 годин.",
                    "executor_id": "exec-3",
                    "executor_name": "Служба теплопостачання",
                    "urgency": "emergency",
                    "response_time": 3,
                    "keywords": ["опалення", "холодно", "батареї", "радіатор", "тепло", "гаряча"],
                    "is_active": True,
                    "created_at": datetime.now().isoformat()
                },
                {
                    "id": "class-5",
                    "problem": "Інженерні мережі",
                    "type": "Водопостачання",
                    "subtype": "відсутність води",
                    "location": "будинок",
                    "response": "Заявку щодо відсутності води прийнято. Бригада виїде протягом 2 годин.",
                    "executor_id": "exec-4",
                    "executor_name": "Служба водопостачання",
                    "urgency": "emergency",
                    "response_time": 2,
                    "keywords": ["вода", "водопостачання", "кран", "немає води", "відключили воду"],
                    "is_active": True,
                    "created_at": datetime.now().isoformat()
                },
                {
                    "id": "class-6",
                    "problem": "Інженерні мережі",
                    "type": "Електропостачання",
                    "subtype": "відключення світла",
                    "location": "квартира/будинок",
                    "response": "Інформація про відключення електроенергії доступна на сайті постачальника. Для аварій зверніться за номером 104.",
                    "executor_id": None,
                    "executor_name": "Електропостачання",
                    "urgency": "info",
                    "response_time": 0,
                    "keywords": ["світло", "електрика", "відключили", "немає світла", "струм"],
                    "is_active": True,
                    "created_at": datetime.now().isoformat()
                },
                {
                    "id": "class-7",
                    "problem": "Громадський транспорт",
                    "type": "Маршрутки та автобуси",
                    "subtype": "скарга на транспорт",
                    "location": "маршрут",
                    "response": "Вашу скаргу на роботу транспорту зареєстровано. Відповідь надійде протягом 5 робочих днів.",
                    "executor_id": "exec-5",
                    "executor_name": "Департамент транспорту",
                    "urgency": "standard",
                    "response_time": 120,
                    "keywords": ["маршрутка", "автобус", "водій", "транспорт", "їде", "не зупинився"],
                    "is_active": True,
                    "created_at": datetime.now().isoformat()
                },
                {
                    "id": "class-8",
                    "problem": "Надзвичайні ситуації",
                    "type": "Руйнування інфраструктури",
                    "subtype": "пошкодження дороги",
                    "location": "дорога",
                    "response": "Заявку про пошкодження інфраструктури прийнято. Фахівці негайно виїдуть на місце.",
                    "executor_id": "exec-1",
                    "executor_name": "Аварійна служба",
                    "urgency": "emergency",
                    "response_time": 1,
                    "keywords": ["руйнування", "міст", "дорога", "яма", "провал", "аварія"],
                    "is_active": True,
                    "created_at": datetime.now().isoformat()
                }
            ]
            self._save_json(self.classifiers_file, default_classifiers)
        
        # Алгоритми розмови
        if not os.path.exists(self.algorithms_file):
            default_algorithms = [
                {
                    "id": "algo-1",
                    "name": "Стандартний алгоритм",
                    "description": "Базовий алгоритм обробки звернень",
                    "trigger_keywords": [],
                    "classifier_ids": [],
                    "is_default": True,
                    "is_active": True,
                    "steps": [
                        {
                            "order": 1,
                            "type": "greeting",
                            "text": "Доброго дня! Ви зателефонували на гарячу лінію контактного центру. Чим можу вам допомогти?",
                            "wait_for_input": True,
                            "save_to": "user_query"
                        },
                        {
                            "order": 2,
                            "type": "response",
                            "text": "{classification_response}",
                            "wait_for_input": False
                        },
                        {
                            "order": 3,
                            "type": "question",
                            "text": "Чи можу я ще чимось допомогти?",
                            "wait_for_input": True,
                            "save_to": "additional_help"
                        },
                        {
                            "order": 4,
                            "type": "farewell",
                            "text": "Дякую за звернення! На все добре!",
                            "wait_for_input": False
                        }
                    ],
                    "created_at": datetime.now().isoformat()
                },
                {
                    "id": "algo-2",
                    "name": "Аварійний алгоритм",
                    "description": "Алгоритм для аварійних ситуацій",
                    "trigger_keywords": ["аварія", "терміново", "небезпека", "затоплення"],
                    "classifier_ids": ["class-2", "class-3"],
                    "is_default": False,
                    "is_active": True,
                    "steps": [
                        {
                            "order": 1,
                            "type": "greeting",
                            "text": "Аварійна лінія! Опишіть ситуацію.",
                            "wait_for_input": True,
                            "save_to": "emergency_description"
                        },
                        {
                            "order": 2,
                            "type": "question",
                            "text": "Назвіть вашу адресу.",
                            "wait_for_input": True,
                            "save_to": "address"
                        },
                        {
                            "order": 3,
                            "type": "response",
                            "text": "Заявку прийнято! Аварійна бригада вже виїжджає. Орієнтовний час прибуття - 30 хвилин.",
                            "wait_for_input": False
                        },
                        {
                            "order": 4,
                            "type": "farewell",
                            "text": "Залишайтесь на зв'язку. Наш оператор може передзвонити для уточнення.",
                            "wait_for_input": False
                        }
                    ],
                    "created_at": datetime.now().isoformat()
                }
            ]
            self._save_json(self.algorithms_file, default_algorithms)
    
    # === Executors CRUD ===
    
    def get_executors(self, active_only: bool = False) -> List[Dict]:
        """Отримати всіх виконавців"""
        executors = self._load_json(self.executors_file)
        if active_only:
            executors = [e for e in executors if e.get("is_active", True)]
        return executors
    
    def get_executor(self, executor_id: str) -> Optional[Dict]:
        """Отримати виконавця за ID"""
        executors = self._load_json(self.executors_file)
        for e in executors:
            if e["id"] == executor_id:
                return e
        return None
    
    def create_executor(self, data: ExecutorBase) -> Dict:
        """Створити виконавця"""
        executors = self._load_json(self.executors_file)
        new_executor = Executor(**data.dict())
        executors.append(new_executor.dict())
        self._save_json(self.executors_file, executors)
        return new_executor.dict()
    
    def update_executor(self, executor_id: str, data: ExecutorBase) -> Optional[Dict]:
        """Оновити виконавця"""
        executors = self._load_json(self.executors_file)
        for i, e in enumerate(executors):
            if e["id"] == executor_id:
                updated = {**e, **data.dict(), "updated_at": datetime.now().isoformat()}
                executors[i] = updated
                self._save_json(self.executors_file, executors)
                return updated
        return None
    
    def delete_executor(self, executor_id: str) -> bool:
        """Видалити виконавця"""
        executors = self._load_json(self.executors_file)
        initial_len = len(executors)
        executors = [e for e in executors if e["id"] != executor_id]
        if len(executors) < initial_len:
            self._save_json(self.executors_file, executors)
            return True
        return False
    
    # === Classifiers CRUD ===
    
    def get_classifiers(self, active_only: bool = False) -> List[Dict]:
        """Отримати всі категорії класифікатора"""
        classifiers = self._load_json(self.classifiers_file)
        if active_only:
            classifiers = [c for c in classifiers if c.get("is_active", True)]
        return classifiers
    
    def get_classifier(self, classifier_id: str) -> Optional[Dict]:
        """Отримати категорію за ID"""
        classifiers = self._load_json(self.classifiers_file)
        for c in classifiers:
            if c["id"] == classifier_id:
                return c
        return None
    
    def create_classifier(self, data: ClassifierItemBase) -> Dict:
        """Створити категорію"""
        classifiers = self._load_json(self.classifiers_file)
        new_classifier = ClassifierItem(**data.dict())
        classifiers.append(new_classifier.dict())
        self._save_json(self.classifiers_file, classifiers)
        return new_classifier.dict()
    
    def update_classifier(self, classifier_id: str, data: ClassifierItemBase) -> Optional[Dict]:
        """Оновити категорію"""
        classifiers = self._load_json(self.classifiers_file)
        for i, c in enumerate(classifiers):
            if c["id"] == classifier_id:
                updated = {**c, **data.dict(), "updated_at": datetime.now().isoformat()}
                classifiers[i] = updated
                self._save_json(self.classifiers_file, classifiers)
                return updated
        return None
    
    def delete_classifier(self, classifier_id: str) -> bool:
        """Видалити категорію"""
        classifiers = self._load_json(self.classifiers_file)
        initial_len = len(classifiers)
        classifiers = [c for c in classifiers if c["id"] != classifier_id]
        if len(classifiers) < initial_len:
            self._save_json(self.classifiers_file, classifiers)
            return True
        return False
    
    # === Algorithms CRUD ===
    
    def get_algorithms(self, active_only: bool = False) -> List[Dict]:
        """Отримати всі алгоритми розмови"""
        algorithms = self._load_json(self.algorithms_file)
        if active_only:
            algorithms = [a for a in algorithms if a.get("is_active", True)]
        return algorithms
    
    def get_algorithm(self, algorithm_id: str) -> Optional[Dict]:
        """Отримати алгоритм за ID"""
        algorithms = self._load_json(self.algorithms_file)
        for a in algorithms:
            if a["id"] == algorithm_id:
                return a
        return None
    
    def get_default_algorithm(self) -> Optional[Dict]:
        """Отримати алгоритм за замовчуванням"""
        algorithms = self._load_json(self.algorithms_file)
        for a in algorithms:
            if a.get("is_default", False) and a.get("is_active", True):
                return a
        # Якщо немає за замовчуванням - перший активний
        for a in algorithms:
            if a.get("is_active", True):
                return a
        return None
    
    def create_algorithm(self, data: ConversationAlgorithmBase) -> Dict:
        """Створити алгоритм"""
        algorithms = self._load_json(self.algorithms_file)
        
        # Якщо новий - за замовчуванням, скидаємо інші
        if data.is_default:
            for a in algorithms:
                a["is_default"] = False
        
        new_algorithm = ConversationAlgorithm(**data.dict())
        algorithms.append(new_algorithm.dict())
        self._save_json(self.algorithms_file, algorithms)
        return new_algorithm.dict()
    
    def update_algorithm(self, algorithm_id: str, data: ConversationAlgorithmBase) -> Optional[Dict]:
        """Оновити алгоритм"""
        algorithms = self._load_json(self.algorithms_file)
        
        # Якщо оновлюємо на за замовчуванням, скидаємо інші
        if data.is_default:
            for a in algorithms:
                if a["id"] != algorithm_id:
                    a["is_default"] = False
        
        for i, a in enumerate(algorithms):
            if a["id"] == algorithm_id:
                updated = {**a, **data.dict(), "updated_at": datetime.now().isoformat()}
                algorithms[i] = updated
                self._save_json(self.algorithms_file, algorithms)
                return updated
        return None
    
    def delete_algorithm(self, algorithm_id: str) -> bool:
        """Видалити алгоритм"""
        algorithms = self._load_json(self.algorithms_file)
        initial_len = len(algorithms)
        algorithms = [a for a in algorithms if a["id"] != algorithm_id]
        if len(algorithms) < initial_len:
            self._save_json(self.algorithms_file, algorithms)
            return True
        return False


# Глобальний екземпляр сховища
storage = ReferenceStorage()
