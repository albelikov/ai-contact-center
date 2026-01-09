"""
Класифікатор заявок мешканців
Універсальний класифікатор контактного центру
Використовує довідник з references.py
"""
from typing import Optional, Dict, List
from dataclasses import dataclass
import re

@dataclass
class ClassificationResult:
    """Результат класифікації запиту"""
    id: str  # Змінено на str для UUID
    problem: str
    type: str
    subtype: str
    location: Optional[str]
    response: str
    executor: str
    urgency: str  # emergency, short, standard, info
    response_time: int  # години
    confidence: float
    needs_operator: bool = False


# Резервні дані (використовуються якщо довідник порожній)
FALLBACK_CLASSIFIER_DATA: List[Dict] = [
    {
        "id": 1,
        "problem": "Благоустрій прибудинкової території",
        "type": "Утримання будинку та прибудинкової території в зимовий період",
        "subtype": "розчистка снігу",
        "location": "прибудинкова територія",
        "response": "Вашу заявку щодо розчистки снігу на прибудинковій території прийнято. Роботи будуть виконані управителем вашого будинку протягом 24 годин.",
        "executor": "Управителі багатоквартирних будинків",
        "urgency": "short",
        "response_time": 24,
        "keywords": ["сніг", "розчистка", "прибрати", "замело", "снігопад", "двір", "територія"]
    },
    {
        "id": 2,
        "problem": "Благоустрій прибудинкової території",
        "type": "Благоустрій та санітарний стан",
        "subtype": "впавше дерево",
        "location": "на машину/дорогу",
        "response": "Надійшла заявка про дерево, що впало. Муніципальна аварійна служба Аварійна служба виконає роботи протягом 3 годин.",
        "executor": "Аварійна служба",
        "urgency": "emergency",
        "response_time": 3,
        "keywords": ["дерево", "впало", "машина", "автомобіль", "гілка", "розпилити", "впавше"]
    },
    {
        "id": 3,
        "problem": "Експлуатація і ремонт житлового фонду",
        "type": "Покрівля",
        "subtype": "протікання даху",
        "location": "квартира",
        "response": "Ваша заява щодо протікання даху прийнята. Муніципальна аварійна служба знеструмить квартиру до просихання та передасть заявку управителю для включення до планових робіт.",
        "executor": "Аварійна служба",
        "urgency": "emergency",
        "response_time": 3,
        "keywords": ["протікає", "дах", "стеля", "вода", "капає", "мокро", "покрівля", "протікання"]
    },
    {
        "id": 4,
        "problem": "Інженерні мережі",
        "type": "Опалення. Експлуатація і ремонт системи",
        "subtype": "відсутність опалення",
        "location": "квартира/будинок",
        "response": "Заявку щодо відсутності опалення прийнято. Аварійна служба перевірить систему опалення протягом 3 годин. Якщо проблема у зовнішніх мережах - заявку буде передано до Служба теплопостачання.",
        "executor": "Служба теплопостачання",
        "urgency": "emergency",
        "response_time": 3,
        "keywords": ["опалення", "холодно", "батареї", "радіатор", "тепло", "гаряча", "батарея", "нема опалення"]
    },
    {
        "id": 5,
        "problem": "Інженерні мережі",
        "type": "Опалення. Експлуатація і ремонт системи",
        "subtype": "протікання радіатора",
        "location": "квартира",
        "response": "Заявку щодо протікання радіатора опалення прийнято. Муніципальна аварійна служба локалізує аварійну ситуацію зі збереженням максимальної можливості надання послуги іншим мешканцям.",
        "executor": "Аварійна служба",
        "urgency": "emergency",
        "response_time": 3,
        "keywords": ["тече", "радіатор", "батарея", "опалення", "протікає"]
    },
    {
        "id": 6,
        "problem": "Інженерні мережі",
        "type": "Холодна вода",
        "subtype": "відсутність водопостачання",
        "location": "будинок",
        "response": "Заявку щодо відсутності холодної води прийнято. Аварійна бригада Служба водопостачання виїде на місце протягом 2 годин для встановлення причини та усунення несправності.",
        "executor": "Служба водопостачання",
        "urgency": "emergency",
        "response_time": 2,
        "keywords": ["вода", "водопостачання", "кран", "немає води", "відключили воду", "холодна вода"]
    },
    {
        "id": 7,
        "problem": "Інженерні мережі",
        "type": "Холодна вода",
        "subtype": "протікання води",
        "location": "підвал/під'їзд",
        "response": "Заявку щодо протікання холодної води прийнято. Муніципальна аварійна служба негайно відрядить майстра для усунення аварії.",
        "executor": "Аварійна служба",
        "urgency": "emergency",
        "response_time": 3,
        "keywords": ["тече", "прорвало", "труба", "вентиль", "затоплює", "вода"]
    },
    {
        "id": 8,
        "problem": "Інженерні мережі",
        "type": "Електропостачання",
        "subtype": "відключення світла",
        "location": "квартира/будинок",
        "response": "Інформація про планові відключення електроенергії доступна на офіційному сайті ДТЕК. Для повідомлення про аварійне відключення зверніться за номером 104 або через додаток ДТЕК.",
        "executor": "ДТЕК",
        "urgency": "info",
        "response_time": 0,
        "keywords": ["світло", "електрика", "відключили", "немає світла", "струм", "електроенергія", "лампочка"]
    },
    {
        "id": 9,
        "problem": "Інженерні мережі",
        "type": "Ліфтове господарство",
        "subtype": "несправність ліфта",
        "location": "під'їзд",
        "response": "Заявку щодо несправності ліфта прийнято. Спеціалісти ліфтової служби виїдуть для діагностики та ремонту протягом 4 годин.",
        "executor": "Ліфтова служба",
        "urgency": "short",
        "response_time": 4,
        "keywords": ["ліфт", "застряг", "не працює", "кабіна", "ліфтовий"]
    },
    {
        "id": 10,
        "problem": "Громадський транспорт",
        "type": "Маршрутки та автобуси",
        "subtype": "скарга на роботу транспорту",
        "location": "маршрут",
        "response": "Вашу скаргу на роботу громадського транспорту зареєстровано. Департамент транспорту розгляне звернення протягом 5 робочих днів та надасть письмову відповідь.",
        "executor": "Департамент транспорту",
        "urgency": "standard",
        "response_time": 120,
        "keywords": ["маршрутка", "автобус", "водій", "транспорт", "їде", "не зупинився", "графік", "розклад"]
    },
    {
        "id": 11,
        "problem": "Надзвичайні ситуації та цивільний захист населення",
        "type": "Руйнування",
        "subtype": "руйнування транспортних комунікацій",
        "location": "міст/дамба/переїзди/дорога",
        "response": "Заявку про руйнування інфраструктури прийнято. Управління з питань надзвичайних ситуацій негайно відрядить фахівців для огляду та оперативного реагування.",
        "executor": "Управління з питань НС",
        "urgency": "emergency",
        "response_time": 1,
        "keywords": ["руйнування", "міст", "дорога", "яма", "провал", "аварія", "обвал", "тріщина"]
    },
    {
        "id": 12,
        "problem": "Благоустрій прибудинкової території",
        "type": "Благоустрій та санітарний стан",
        "subtype": "вивіз сміття",
        "location": "контейнерний майданчик",
        "response": "Заявку щодо вивозу сміття прийнято. Відповідальна служба виконає вивіз протягом 24 годин.",
        "executor": "Служба вивозу сміття",
        "urgency": "short",
        "response_time": 24,
        "keywords": ["сміття", "контейнер", "вивіз", "смердить", "баки", "сміттєвий"]
    }
]


class QueryClassifier:
    """Класифікатор запитів громадян"""
    
    def __init__(self):
        self._load_data()
    
    def _load_data(self):
        """Завантаження даних з довідника"""
        try:
            from references import storage
            self.data = storage.get_classifiers(active_only=True)
            if not self.data:
                print("[Classifier] Довідник порожній, використовую резервні дані")
                self.data = FALLBACK_CLASSIFIER_DATA
            else:
                print(f"[Classifier] Завантажено {len(self.data)} категорій з довідника")
        except Exception as e:
            print(f"[Classifier] Помилка завантаження довідника: {e}")
            self.data = FALLBACK_CLASSIFIER_DATA
    
    def reload(self):
        """Перезавантажити дані з довідника"""
        self._load_data()
    
    def _calculate_score(self, query: str, item: Dict) -> float:
        """Розрахунок релевантності запиту до категорії"""
        query_lower = query.lower()
        score = 0.0
        
        # Перевірка ключових слів
        keywords = item.get("keywords", [])
        matched_keywords = sum(1 for kw in keywords if kw in query_lower)
        
        if matched_keywords > 0:
            score += matched_keywords * 0.15
        
        # Перевірка підтипу
        subtype_words = item["subtype"].lower().split()
        if any(word in query_lower for word in subtype_words):
            score += 0.2
        
        # Перевірка типу
        type_words = item["type"].lower().split()
        if any(word in query_lower for word in type_words if len(word) > 3):
            score += 0.1
        
        return min(score, 1.0)
    
    def classify(self, query: str) -> ClassificationResult:
        """Класифікація запиту"""
        best_match = None
        highest_score = 0.0
        
        for item in self.data:
            score = self._calculate_score(query, item)
            if score > highest_score:
                highest_score = score
                best_match = item
        
        if best_match and highest_score > 0.2:
            # Підтримка обох форматів: executor та executor_name
            executor = best_match.get("executor_name") or best_match.get("executor", "Не визначено")
            return ClassificationResult(
                id=str(best_match["id"]),
                problem=best_match["problem"],
                type=best_match["type"],
                subtype=best_match["subtype"],
                location=best_match.get("location"),
                response=best_match["response"],
                executor=executor,
                urgency=best_match["urgency"],
                response_time=best_match["response_time"],
                confidence=min(0.95, 0.5 + highest_score),
                needs_operator=False
            )
        
        # Запит потребує оператора
        return ClassificationResult(
            id=0,
            problem="Загальне питання",
            type="Консультація",
            subtype="потребує оператора",
            location=None,
            response="Вибачте, я не зміг точно визначити тип вашого звернення. Зачекайте, будь ласка, я переключу вас на оператора для детальної консультації.",
            executor="Оператор контактного центру",
            urgency="standard",
            response_time=0,
            confidence=0.3,
            needs_operator=True
        )


# Глобальний екземпляр класифікатора
classifier = QueryClassifier()


def classify_query(query: str) -> ClassificationResult:
    """Класифікувати запит громадянина"""
    return classifier.classify(query)
