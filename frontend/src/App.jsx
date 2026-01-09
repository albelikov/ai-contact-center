import React, { useState, useEffect, useRef, useCallback } from 'react';
import { 
  Phone, Mic, MicOff, Volume2, VolumeX, ArrowRightLeft, 
  FileText, Clock, AlertTriangle, 
  CheckCircle, PhoneCall, PhoneOff, Headphones, BarChart3, History,
  Zap, Droplets, Flame, Building2, Bus, HelpCircle, MessageSquare,
  Wifi, WifiOff, Settings, Database, Plus, Pencil, Trash2, X, Save,
  Users, ListTree, MessageCircle, RefreshCw
} from 'lucide-react';

// Конфігурація бекенду
const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';
const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws/call';

// Класифікатор заявок (локальний fallback)
const CLASSIFIER_DATA = [
  {
    id: 1,
    problem: 'Благоустрій території',
    type: 'Утримання території в зимовий період',
    subtype: 'розчистка снігу',
    location: 'прибудинкова територія',
    response: 'Вашу заявку щодо розчистки снігу прийнято. Роботи будуть виконані протягом 24 годин.',
    executor: 'Управитель будинку',
    urgency: 'short',
    responseTime: 24,
    icon: 'building',
    keywords: ['сніг', 'розчистка', 'прибрати', 'замело', 'снігопад', 'двір']
  },
  {
    id: 2,
    problem: 'Благоустрій території',
    type: 'Благоустрій та санітарний стан',
    subtype: 'впавше дерево',
    location: 'на машину',
    response: 'Надійшла заявка про дерево, що впало. Аварійна служба виконає роботи протягом 3 годин.',
    executor: 'Аварійна служба',
    urgency: 'emergency',
    responseTime: 3,
    icon: 'alert',
    keywords: ['дерево', 'впало', 'машина', 'автомобіль', 'гілка', 'розпилити']
  },
  {
    id: 3,
    problem: 'Ремонт житлового фонду',
    type: 'Покрівля',
    subtype: 'протікання даху',
    location: 'квартира',
    response: 'Ваша заява щодо протікання даху прийнята. Аварійна служба вже направлена.',
    executor: 'Аварійна служба',
    urgency: 'emergency',
    responseTime: 3,
    icon: 'droplets',
    keywords: ['протікає', 'дах', 'стеля', 'вода', 'капає', 'мокро', 'покрівля']
  },
  {
    id: 4,
    problem: 'Інженерні мережі',
    type: 'Опалення',
    subtype: 'відсутність опалення',
    location: 'квартира',
    response: 'Заявку щодо відсутності опалення прийнято. Перевірка системи буде виконана протягом 3 годин.',
    executor: 'Служба теплопостачання',
    urgency: 'emergency',
    responseTime: 3,
    icon: 'flame',
    keywords: ['опалення', 'холодно', 'батареї', 'радіатор', 'тепло', 'гаряча']
  },
  {
    id: 5,
    problem: 'Інженерні мережі',
    type: 'Водопостачання',
    subtype: 'відсутність води',
    location: 'будинок',
    response: 'Заявку щодо відсутності води прийнято. Бригада виїде протягом 2 годин.',
    executor: 'Служба водопостачання',
    urgency: 'emergency',
    responseTime: 2,
    icon: 'droplets',
    keywords: ['вода', 'водопостачання', 'кран', 'немає води', 'відключили воду']
  },
  {
    id: 6,
    problem: 'Інженерні мережі',
    type: 'Електропостачання',
    subtype: 'відключення світла',
    location: 'квартира/будинок',
    response: 'Інформація про відключення електроенергії доступна на сайті постачальника. Для аварій зверніться за номером 104.',
    executor: 'Електропостачання',
    urgency: 'info',
    responseTime: 0,
    icon: 'zap',
    keywords: ['світло', 'електрика', 'відключили', 'немає світла', 'струм']
  },
  {
    id: 7,
    problem: 'Громадський транспорт',
    type: 'Маршрутки та автобуси',
    subtype: 'скарга на транспорт',
    location: 'маршрут',
    response: 'Вашу скаргу на роботу транспорту зареєстровано. Відповідь надійде протягом 5 робочих днів.',
    executor: 'Департамент транспорту',
    urgency: 'standard',
    responseTime: 120,
    icon: 'bus',
    keywords: ['маршрутка', 'автобус', 'водій', 'транспорт', 'їде', 'не зупинився']
  },
  {
    id: 8,
    problem: 'Надзвичайні ситуації',
    type: 'Руйнування інфраструктури',
    subtype: 'пошкодження дороги',
    location: 'дорога',
    response: 'Заявку про пошкодження інфраструктури прийнято. Фахівці негайно виїдуть на місце.',
    executor: 'Управління НС',
    urgency: 'emergency',
    responseTime: 1,
    icon: 'alert',
    keywords: ['руйнування', 'міст', 'дорога', 'яма', 'провал', 'аварія']
  }
];

// Зразки голосових запитів
const SAMPLE_QUERIES = [
  'Доброго дня, у нас на території не прибрали сніг вже три дні.',
  'Алло, на мою машину впало дерево, потрібно терміново допомогу!',
  'У моїй квартирі протікає стеля зверху, вода капає на підлогу.',
  'Добрий день, у нас в будинку немає опалення вже другий день.',
  'Коли відключатимуть світло?',
  'Хочу поскаржитися на водія маршрутки.',
  'У нас немає холодної води в будинку з самого ранку.',
  'На дорозі величезна яма, машини не можуть проїхати.'
];

// Компонент візуалізації аудіо
const AudioVisualizer = ({ isActive, type = 'listening' }) => {
  const bars = 5;
  const color = type === 'listening' ? 'bg-red-500' : 'bg-green-500';
  
  return (
    <div className="flex items-center justify-center gap-1 h-12">
      {[...Array(bars)].map((_, i) => (
        <div
          key={i}
          className={`w-1.5 rounded-full transition-all duration-200 ${
            isActive ? `${color} audio-bar` : 'bg-gray-300'
          }`}
          style={{
            height: isActive ? `${20 + Math.random() * 20}px` : '8px',
            animationDelay: `${i * 0.1}s`
          }}
        />
      ))}
    </div>
  );
};

// Компонент повідомлення в чаті
const ChatMessage = ({ message, isUser, timestamp }) => (
  <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-3`}>
    <div className={`max-w-[80%] rounded-2xl px-4 py-3 ${
      isUser 
        ? 'bg-blue-600 text-white rounded-br-md' 
        : 'bg-gray-100 text-gray-800 rounded-bl-md'
    }`}>
      <p className="text-sm leading-relaxed">{message}</p>
      <span className={`text-xs mt-1 block ${isUser ? 'text-blue-200' : 'text-gray-500'}`}>
        {timestamp}
      </span>
    </div>
  </div>
);

// Компонент бейджа категорії
const CategoryBadge = ({ urgency }) => {
  const getUrgencyStyle = () => {
    switch (urgency) {
      case 'emergency': return 'bg-red-100 text-red-800 border-red-300';
      case 'short': return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      case 'info': return 'bg-blue-100 text-blue-800 border-blue-300';
      default: return 'bg-green-100 text-green-800 border-green-300';
    }
  };

  const getUrgencyText = () => {
    switch (urgency) {
      case 'emergency': return 'Аварійний';
      case 'short': return 'Терміновий';
      case 'info': return 'Інформація';
      default: return 'Стандартний';
    }
  };

  return (
    <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full border ${getUrgencyStyle()}`}>
      <AlertTriangle className="w-4 h-4" />
      <span className="text-sm font-medium">{getUrgencyText()}</span>
    </div>
  );
};

// Модальне вікно редагування довідників
const ReferenceModal = ({ type, data, executors, onClose, onSave }) => {
  const isEdit = !!data;
  const [formData, setFormData] = useState(data || {});

  const handleSubmit = (e) => {
    e.preventDefault();
    onSave(formData);
  };

  const updateField = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-6 border-b">
          <h2 className="text-xl font-bold">
            {isEdit ? 'Редагування' : 'Новий запис'}: {
              type === 'classifiers' ? 'Категорія' :
              type === 'executors' ? 'Виконавець' : 'Алгоритм'
            }
          </h2>
          <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded-lg">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {type === 'classifiers' && (
            <>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Категорія *</label>
                  <input
                    type="text"
                    value={formData.problem || ''}
                    onChange={(e) => updateField('problem', e.target.value)}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Тип</label>
                  <input
                    type="text"
                    value={formData.type || ''}
                    onChange={(e) => updateField('type', e.target.value)}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Підтип *</label>
                  <input
                    type="text"
                    value={formData.subtype || ''}
                    onChange={(e) => updateField('subtype', e.target.value)}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Локація</label>
                  <input
                    type="text"
                    value={formData.location || ''}
                    onChange={(e) => updateField('location', e.target.value)}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Шаблон відповіді *</label>
                <textarea
                  value={formData.response || ''}
                  onChange={(e) => updateField('response', e.target.value)}
                  rows={3}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Виконавець</label>
                  <select
                    value={formData.executor_id || ''}
                    onChange={(e) => {
                      const exec = executors.find(ex => ex.id === e.target.value);
                      updateField('executor_id', e.target.value);
                      updateField('executor_name', exec?.name || '');
                    }}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">Оберіть виконавця...</option>
                    {executors.map(ex => (
                      <option key={ex.id} value={ex.id}>{ex.name}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Або введіть назву</label>
                  <input
                    type="text"
                    value={formData.executor_name || ''}
                    onChange={(e) => updateField('executor_name', e.target.value)}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="Назва виконавця"
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Терміновість</label>
                  <select
                    value={formData.urgency || 'standard'}
                    onChange={(e) => updateField('urgency', e.target.value)}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="emergency">Аварійний</option>
                    <option value="short">Терміновий</option>
                    <option value="standard">Стандартний</option>
                    <option value="info">Інформаційний</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Час відповіді (год)</label>
                  <input
                    type="number"
                    value={formData.response_time || 24}
                    onChange={(e) => updateField('response_time', parseInt(e.target.value))}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    min="0"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Ключові слова (через кому)</label>
                <input
                  type="text"
                  value={(formData.keywords || []).join(', ')}
                  onChange={(e) => updateField('keywords', e.target.value.split(',').map(s => s.trim()).filter(Boolean))}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="сніг, розчистка, двір"
                />
              </div>
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="is_active"
                  checked={formData.is_active !== false}
                  onChange={(e) => updateField('is_active', e.target.checked)}
                  className="w-4 h-4 text-blue-600 rounded"
                />
                <label htmlFor="is_active" className="text-sm text-gray-700">Активна категорія</label>
              </div>
            </>
          )}

          {type === 'executors' && (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Назва *</label>
                <input
                  type="text"
                  value={formData.name || ''}
                  onChange={(e) => updateField('name', e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Телефон</label>
                  <input
                    type="text"
                    value={formData.phone || ''}
                    onChange={(e) => updateField('phone', e.target.value)}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                  <input
                    type="email"
                    value={formData.email || ''}
                    onChange={(e) => updateField('email', e.target.value)}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Години роботи</label>
                <input
                  type="text"
                  value={formData.work_hours || ''}
                  onChange={(e) => updateField('work_hours', e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="09:00-18:00 або 24/7"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Опис</label>
                <textarea
                  value={formData.description || ''}
                  onChange={(e) => updateField('description', e.target.value)}
                  rows={2}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="is_active"
                  checked={formData.is_active !== false}
                  onChange={(e) => updateField('is_active', e.target.checked)}
                  className="w-4 h-4 text-blue-600 rounded"
                />
                <label htmlFor="is_active" className="text-sm text-gray-700">Активний виконавець</label>
              </div>
            </>
          )}

          {type === 'algorithms' && (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Назва *</label>
                <input
                  type="text"
                  value={formData.name || ''}
                  onChange={(e) => updateField('name', e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Опис</label>
                <textarea
                  value={formData.description || ''}
                  onChange={(e) => updateField('description', e.target.value)}
                  rows={2}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Ключові слова для запуску (через кому)</label>
                <input
                  type="text"
                  value={(formData.trigger_keywords || []).join(', ')}
                  onChange={(e) => updateField('trigger_keywords', e.target.value.split(',').map(s => s.trim()).filter(Boolean))}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="аварія, терміново, небезпека"
                />
              </div>
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="is_default"
                    checked={formData.is_default || false}
                    onChange={(e) => updateField('is_default', e.target.checked)}
                    className="w-4 h-4 text-blue-600 rounded"
                  />
                  <label htmlFor="is_default" className="text-sm text-gray-700">За замовчуванням</label>
                </div>
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="is_active"
                    checked={formData.is_active !== false}
                    onChange={(e) => updateField('is_active', e.target.checked)}
                    className="w-4 h-4 text-blue-600 rounded"
                  />
                  <label htmlFor="is_active" className="text-sm text-gray-700">Активний</label>
                </div>
              </div>
              <div className="bg-gray-50 p-4 rounded-lg">
                <p className="text-sm text-gray-600">
                  Кроки алгоритму можна редагувати через API або безпосередньо в файлі 
                  <code className="bg-gray-200 px-1 mx-1 rounded">backend/data/algorithms.json</code>
                </p>
              </div>
            </>
          )}

          <div className="flex justify-end gap-3 pt-4 border-t">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg"
            >
              Скасувати
            </button>
            <button
              type="submit"
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white hover:bg-blue-700 rounded-lg"
            >
              <Save className="w-4 h-4" />
              {isEdit ? 'Зберегти' : 'Створити'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Головний компонент
const App = () => {
  // Стани
  const [activeView, setActiveView] = useState('dashboard');
  const [callState, setCallState] = useState('idle');
  const [isMuted, setIsMuted] = useState(false);
  const [isSpeakerOn, setIsSpeakerOn] = useState(true);
  const [transcript, setTranscript] = useState('');
  const [classification, setClassification] = useState(null);
  const [chatMessages, setChatMessages] = useState([]);
  const [callHistory, setCallHistory] = useState([]);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [useFishSpeech, setUseFishSpeech] = useState(true);
  const [stats, setStats] = useState({
    totalCalls: 0,
    aiResolved: 0,
    escalated: 0,
    avgResponseTime: 0
  });

  // Стани для довідників
  const [executors, setExecutors] = useState([]);
  const [classifiers, setClassifiers] = useState([]);
  const [algorithms, setAlgorithms] = useState([]);
  const [refLoading, setRefLoading] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [currentRefType, setCurrentRefType] = useState('classifiers');

  const chatEndRef = useRef(null);
  const wsRef = useRef(null);
  const audioContextRef = useRef(null);
  const audioQueueRef = useRef([]);
  const isPlayingRef = useRef(false);

  // Ініціалізація AudioContext для відтворення Fish Speech
  useEffect(() => {
    audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)();
    return () => {
      if (audioContextRef.current) {
        audioContextRef.current.close();
      }
    };
  }, []);

  // Перевірка з'єднання з бекендом
  useEffect(() => {
    const checkBackend = async () => {
      try {
        const response = await fetch(`${BACKEND_URL}/api/health`);
        if (response.ok) {
          setIsConnected(true);
        } else {
          setIsConnected(false);
        }
      } catch (error) {
        setIsConnected(false);
        console.log('Backend not available, using fallback mode');
      }
    };
    
    checkBackend();
    const interval = setInterval(checkBackend, 10000);
    return () => clearInterval(interval);
  }, []);

  // Завантаження довідників
  const fetchReferences = useCallback(async () => {
    if (!isConnected) return;
    setRefLoading(true);
    try {
      const [execRes, classRes, algoRes] = await Promise.all([
        fetch(`${BACKEND_URL}/api/references/executors`),
        fetch(`${BACKEND_URL}/api/references/classifiers`),
        fetch(`${BACKEND_URL}/api/references/algorithms`)
      ]);
      
      if (execRes.ok) {
        const data = await execRes.json();
        setExecutors(data.data || []);
      }
      if (classRes.ok) {
        const data = await classRes.json();
        setClassifiers(data.data || []);
      }
      if (algoRes.ok) {
        const data = await algoRes.json();
        setAlgorithms(data.data || []);
      }
    } catch (error) {
      console.error('Error fetching references:', error);
    }
    setRefLoading(false);
  }, [isConnected]);

  // Завантажити довідники при підключенні
  useEffect(() => {
    if (isConnected) {
      fetchReferences();
    }
  }, [isConnected, fetchReferences]);

  // CRUD операції для довідників
  const createReference = async (type, data) => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/references/${type}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      if (response.ok) {
        fetchReferences();
        setShowAddModal(false);
        // Перезавантажити класифікатор
        await fetch(`${BACKEND_URL}/api/references/reload`, { method: 'POST' });
      }
    } catch (error) {
      console.error('Create error:', error);
    }
  };

  const updateReference = async (type, id, data) => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/references/${type}/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      if (response.ok) {
        fetchReferences();
        setEditingItem(null);
        await fetch(`${BACKEND_URL}/api/references/reload`, { method: 'POST' });
      }
    } catch (error) {
      console.error('Update error:', error);
    }
  };

  const deleteReference = async (type, id) => {
    if (!confirm('Видалити цей запис?')) return;
    try {
      const response = await fetch(`${BACKEND_URL}/api/references/${type}/${id}`, {
        method: 'DELETE'
      });
      if (response.ok) {
        fetchReferences();
        await fetch(`${BACKEND_URL}/api/references/reload`, { method: 'POST' });
      }
    } catch (error) {
      console.error('Delete error:', error);
    }
  };

  // Прокрутка чату донизу
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages]);

  // Відтворення WAV аудіо з байтів (Fish Speech) з чергою
  const playAudioBytes = useCallback((audioBytes) => {
    return new Promise(async (resolve) => {
      if (!audioContextRef.current || !isSpeakerOn) {
        resolve();
        return;
      }
      
      try {
        setIsSpeaking(true);
        const arrayBuffer = audioBytes instanceof ArrayBuffer ? audioBytes : await audioBytes.arrayBuffer();
        const audioBuffer = await audioContextRef.current.decodeAudioData(arrayBuffer);
        
        const source = audioContextRef.current.createBufferSource();
        source.buffer = audioBuffer;
        source.connect(audioContextRef.current.destination);
        
        source.onended = () => {
          setIsSpeaking(false);
          resolve();
        };
        
        source.start();
      } catch (error) {
        console.error('Error playing audio:', error);
        setIsSpeaking(false);
        resolve();
      }
    });
  }, [isSpeakerOn]);

  // Fallback: Web Speech API TTS
  const speakWithWebSpeech = useCallback((text, callback) => {
    if (!('speechSynthesis' in window) || !isSpeakerOn) {
      if (callback) setTimeout(callback, 1000);
      return;
    }
    
    setIsSpeaking(true);
    window.speechSynthesis.cancel();
    
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'uk-UA';
    utterance.rate = 0.95;
    utterance.pitch = 1;
    utterance.volume = 1;
    
    const voices = window.speechSynthesis.getVoices();
    const ukrainianVoice = voices.find(v => v.lang.includes('uk')) || 
                          voices.find(v => v.lang.includes('ru')) ||
                          voices.find(v => v.name.includes('Google')) ||
                          voices[0];
    if (ukrainianVoice) {
      utterance.voice = ukrainianVoice;
    }
    
    utterance.onend = () => {
      setIsSpeaking(false);
      if (callback) callback();
    };
    
    utterance.onerror = () => {
      setIsSpeaking(false);
      if (callback) callback();
    };
    
    window.speechSynthesis.speak(utterance);
  }, [isSpeakerOn]);

  // Обробник черги аудіо
  const processAudioQueue = useCallback(async () => {
    if (isPlayingRef.current || audioQueueRef.current.length === 0) return;
    
    isPlayingRef.current = true;
    const { text, callback, useBackend } = audioQueueRef.current.shift();
    
    if (useBackend && isConnected && useFishSpeech) {
      try {
        setIsSpeaking(true);
        const response = await fetch(`${BACKEND_URL}/api/synthesize`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text, voice: 'default' })
        });
        
        if (response.ok) {
          const audioBlob = await response.blob();
          await playAudioBytes(audioBlob);
        } else {
          await new Promise(resolve => speakWithWebSpeech(text, resolve));
        }
      } catch (error) {
        console.error('TTS error:', error);
        await new Promise(resolve => speakWithWebSpeech(text, resolve));
      }
    } else {
      await new Promise(resolve => speakWithWebSpeech(text, resolve));
    }
    
    isPlayingRef.current = false;
    if (callback) callback();
    
    // Обробити наступний елемент черги
    processAudioQueue();
  }, [isConnected, useFishSpeech, playAudioBytes, speakWithWebSpeech]);

  // Синтез мовлення через Fish Speech API з чергою
  const synthesizeSpeech = useCallback(async (text, callback) => {
    audioQueueRef.current.push({ text, callback, useBackend: true });
    processAudioQueue();
  }, [processAudioQueue]);

  // Функція класифікації запиту (локальна)
  const classifyQueryLocal = (query) => {
    const lowerQuery = query.toLowerCase();
    let bestMatch = null;
    let highestScore = 0;

    CLASSIFIER_DATA.forEach(item => {
      let score = 0;
      item.keywords.forEach(keyword => {
        if (lowerQuery.includes(keyword)) {
          score += 3;
        }
      });
      
      if (item.subtype.toLowerCase().split(' ').some(word => lowerQuery.includes(word))) {
        score += 2;
      }
      
      if (score > highestScore) {
        highestScore = score;
        bestMatch = item;
      }
    });

    return highestScore > 0 ? { ...bestMatch, confidence: Math.min(0.95, 0.6 + highestScore * 0.1) } : null;
  };

  // Класифікація через бекенд
  const classifyQuery = useCallback(async (query) => {
    if (!isConnected) {
      return classifyQueryLocal(query);
    }
    
    try {
      const response = await fetch(`${BACKEND_URL}/api/classify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: query })
      });
      
      if (response.ok) {
        const data = await response.json();
        return data.classification;
      }
    } catch (error) {
      console.error('Classification error:', error);
    }
    
    return classifyQueryLocal(query);
  }, [isConnected]);

  // Симуляція вхідного дзвінка
  const simulateIncomingCall = async () => {
    setCallState('ringing');
    setChatMessages([]);
    setTranscript('');
    setClassification(null);

    // Підняття через 1.5 секунди
    setTimeout(async () => {
      setCallState('active');
      
      // Привітання від агента
      const greeting = 'Доброго дня! Ви зателефонували на гарячу лінію контактного центру. Чим можу вам допомогти?';
      
      const greetingMsg = {
        id: 1,
        text: greeting,
        isUser: false,
        timestamp: new Date().toLocaleTimeString('uk-UA', { hour: '2-digit', minute: '2-digit' })
      };
      setChatMessages([greetingMsg]);
      
      // Озвучуємо привітання через Fish Speech або Web Speech
      await synthesizeSpeech(greeting, () => {
        // Після привітання - запит громадянина
        setTimeout(() => {
          const randomQuery = SAMPLE_QUERIES[Math.floor(Math.random() * SAMPLE_QUERIES.length)];
          processUserQuery(randomQuery);
        }, 1000);
      });
    }, 1500);
  };

  // Обробка запиту користувача
  const processUserQuery = async (query) => {
    setCallState('processing');
    setTranscript(query);

    // Озвучуємо запит громадянина (імітація того, що ми чуємо)
    await synthesizeSpeech(query, async () => {
      // Додаємо повідомлення користувача
      const userMsg = {
        id: Date.now(),
        text: query,
        isUser: true,
        timestamp: new Date().toLocaleTimeString('uk-UA', { hour: '2-digit', minute: '2-digit' })
      };
      setChatMessages(prev => [...prev, userMsg]);

      // Класифікація
      setTimeout(async () => {
        const result = await classifyQuery(query);
        setClassification(result);

        // Генерація відповіді
        setTimeout(() => {
          generateResponse(result, query);
        }, 800);
      }, 1000);
    });
  };

  // Генерація відповіді
  const generateResponse = async (classification, originalQuery) => {
    setCallState('responding');

    let response;
    let needsEscalation = false;

    if (classification && classification.confidence > 0.7) {
      response = classification.response;
    } else {
      response = 'Вибачте, я не зміг точно визначити тип вашого звернення. Зачекайте, я переключу вас на оператора.';
      needsEscalation = true;
    }

    // Додаємо відповідь агента
    const agentMsg = {
      id: Date.now(),
      text: response,
      isUser: false,
      timestamp: new Date().toLocaleTimeString('uk-UA', { hour: '2-digit', minute: '2-digit' })
    };
    setChatMessages(prev => [...prev, agentMsg]);

    // Озвучуємо відповідь
    await synthesizeSpeech(response, () => {
      // Оновлення статистики
      setStats(prev => ({
        totalCalls: prev.totalCalls + 1,
        aiResolved: needsEscalation ? prev.aiResolved : prev.aiResolved + 1,
        escalated: needsEscalation ? prev.escalated + 1 : prev.escalated,
        avgResponseTime: Math.round((prev.avgResponseTime * prev.totalCalls + 3.5) / (prev.totalCalls + 1) * 10) / 10
      }));

      // Додаємо в історію
      const historyRecord = {
        id: Date.now(),
        timestamp: new Date().toLocaleString('uk-UA'),
        query: originalQuery,
        category: classification?.subtype || 'Не визначено',
        status: needsEscalation ? 'escalated' : 'resolved',
        executor: classification?.executor || 'Оператор'
      };
      setCallHistory(prev => [historyRecord, ...prev.slice(0, 9)]);

      // Завершуючі слова
      setTimeout(async () => {
        let closingMsg;
        if (needsEscalation) {
          closingMsg = {
            id: Date.now() + 1,
            text: 'Переключаю на оператора. Будь ласка, залишайтесь на лінії.',
            isUser: false,
            timestamp: new Date().toLocaleTimeString('uk-UA', { hour: '2-digit', minute: '2-digit' })
          };
        } else {
          closingMsg = {
            id: Date.now() + 1,
            text: 'Чи можу я ще чимось допомогти?',
            isUser: false,
            timestamp: new Date().toLocaleTimeString('uk-UA', { hour: '2-digit', minute: '2-digit' })
          };
        }
        setChatMessages(prev => [...prev, closingMsg]);
        await synthesizeSpeech(closingMsg.text, () => {
          setCallState('active');
        });
      }, 500);
    });
  };

  // Завершення дзвінка
  const endCall = () => {
    window.speechSynthesis?.cancel();
    setIsSpeaking(false);
    setCallState('ended');
    
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    
    setTimeout(() => {
      setCallState('idle');
      setTranscript('');
      setClassification(null);
    }, 1500);
  };

  // Відсоток AI-вирішених
  const aiResolvedPercent = stats.totalCalls > 0 
    ? Math.round((stats.aiResolved / stats.totalCalls) * 100) 
    : 0;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Хедер */}
      <header className="bg-gradient-to-r from-blue-600 to-indigo-700 text-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="bg-white/20 p-3 rounded-xl">
                <Phone className="w-6 h-6" />
              </div>
              <div>
                <h1 className="text-2xl font-bold">ШІ-Агент Контактного Центру</h1>
                <p className="text-blue-200 text-sm">Голосовий помічник з Fish Speech</p>
              </div>
            </div>
            
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2 bg-white/10 px-4 py-2 rounded-full">
                <Clock className="w-4 h-4" />
                <span className="text-sm">Режим: 24/7</span>
              </div>
              <div className={`flex items-center gap-2 px-4 py-2 rounded-full ${
                isConnected ? 'bg-green-500' : 'bg-yellow-500'
              }`}>
                {isConnected ? <Wifi className="w-4 h-4" /> : <WifiOff className="w-4 h-4" />}
                <span className="text-sm font-medium">
                  {isConnected ? 'Fish Speech' : 'Web Speech'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Навігація */}
        <div className="flex gap-2 mb-6">
          {[
            { id: 'dashboard', icon: PhoneCall, label: 'Дзвінки' },
            { id: 'history', icon: History, label: 'Історія' },
            { id: 'stats', icon: BarChart3, label: 'Статистика' },
            { id: 'references', icon: Database, label: 'Довідники' },
            { id: 'settings', icon: Settings, label: 'Налаштування' }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveView(tab.id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all ${
                activeView === tab.id
                  ? 'bg-blue-600 text-white shadow-md'
                  : 'bg-white text-gray-600 hover:bg-gray-100'
              }`}
            >
              <tab.icon className="w-5 h-5" />
              {tab.label}
            </button>
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Головна панель */}
          <div className="lg:col-span-2">
            {activeView === 'dashboard' && (
              <div className="bg-white rounded-2xl shadow-md overflow-hidden">
                {/* Панель керування дзвінком */}
                <div className="bg-gradient-to-r from-gray-800 to-gray-900 text-white p-6">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className={`w-16 h-16 rounded-full flex items-center justify-center ${
                        callState === 'idle' ? 'bg-gray-700' :
                        callState === 'ringing' ? 'bg-yellow-500 animate-pulse' :
                        callState === 'active' || callState === 'processing' || callState === 'responding' ? 'bg-green-500' :
                        'bg-red-500'
                      }`}>
                        {callState === 'ringing' ? (
                          <PhoneCall className="w-8 h-8 animate-bounce" />
                        ) : callState === 'ended' ? (
                          <PhoneOff className="w-8 h-8" />
                        ) : (
                          <Headphones className="w-8 h-8" />
                        )}
                      </div>
                      <div>
                        <h3 className="text-xl font-semibold">
                          {callState === 'idle' && 'Очікування дзвінка'}
                          {callState === 'ringing' && 'Вхідний дзвінок...'}
                          {callState === 'active' && 'Активний дзвінок'}
                          {callState === 'processing' && 'Обробка запиту...'}
                          {callState === 'responding' && 'ШІ відповідає...'}
                          {callState === 'ended' && 'Дзвінок завершено'}
                        </h3>
                        <p className="text-gray-400 text-sm">
                          {callState !== 'idle' && '+380 XX XXX XX XX'}
                        </p>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-3">
                      <button
                        onClick={() => setIsMuted(!isMuted)}
                        className={`p-3 rounded-full ${isMuted ? 'bg-red-500' : 'bg-gray-700 hover:bg-gray-600'}`}
                      >
                        {isMuted ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
                      </button>
                      <button
                        onClick={() => {
                          setIsSpeakerOn(!isSpeakerOn);
                          if (isSpeakerOn) {
                            window.speechSynthesis?.cancel();
                          }
                        }}
                        className={`p-3 rounded-full ${!isSpeakerOn ? 'bg-red-500' : 'bg-gray-700 hover:bg-gray-600'}`}
                      >
                        {isSpeakerOn ? <Volume2 className="w-5 h-5" /> : <VolumeX className="w-5 h-5" />}
                      </button>
                    </div>
                  </div>

                  {/* Візуалізація аудіо */}
                  <div className="mt-6 flex items-center justify-center gap-8">
                    <div className="text-center">
                      <p className="text-xs text-gray-400 mb-2">Громадянин говорить</p>
                      <AudioVisualizer isActive={callState === 'processing' || (isSpeaking && callState !== 'responding')} type="listening" />
                    </div>
                    <ArrowRightLeft className="w-6 h-6 text-gray-500" />
                    <div className="text-center">
                      <p className="text-xs text-gray-400 mb-2">ШІ відповідає</p>
                      <AudioVisualizer isActive={isSpeaking && callState === 'responding'} type="speaking" />
                    </div>
                  </div>
                </div>

                {/* Чат */}
                <div className="p-6">
                  <div className="h-80 overflow-y-auto bg-gray-50 rounded-xl p-4 mb-4">
                    {chatMessages.length === 0 ? (
                      <div className="h-full flex flex-col items-center justify-center text-gray-400">
                        <MessageSquare className="w-12 h-12 mb-3" />
                        <p>Натисніть кнопку для симуляції дзвінка</p>
                        <p className="text-sm mt-2">
                          {isConnected 
                            ? 'Голос Fish Speech активний' 
                            : 'Використовується голос браузера'}
                        </p>
                      </div>
                    ) : (
                      <>
                        {chatMessages.map(msg => (
                          <ChatMessage
                            key={msg.id}
                            message={msg.text}
                            isUser={msg.isUser}
                            timestamp={msg.timestamp}
                          />
                        ))}
                        <div ref={chatEndRef} />
                      </>
                    )}
                  </div>

                  {/* Класифікація */}
                  {classification && (
                    <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 mb-4">
                      <div className="flex items-center justify-between mb-3">
                        <h4 className="font-semibold text-gray-800">Результат класифікації</h4>
                        <CategoryBadge urgency={classification.urgency} />
                      </div>
                      <div className="grid grid-cols-2 gap-3 text-sm">
                        <div>
                          <span className="text-gray-500">Категорія:</span>
                          <p className="font-medium">{classification.problem}</p>
                        </div>
                        <div>
                          <span className="text-gray-500">Тип:</span>
                          <p className="font-medium">{classification.subtype}</p>
                        </div>
                        <div>
                          <span className="text-gray-500">Виконавець:</span>
                          <p className="font-medium">{classification.executor}</p>
                        </div>
                        <div>
                          <span className="text-gray-500">Термін:</span>
                          <p className="font-medium">{classification.responseTime || classification.response_time} год.</p>
                        </div>
                        <div className="col-span-2">
                          <span className="text-gray-500">Впевненість:</span>
                          <div className="flex items-center gap-2 mt-1">
                            <div className="flex-1 bg-gray-200 rounded-full h-2">
                              <div 
                                className="bg-green-500 h-2 rounded-full transition-all"
                                style={{ width: `${classification.confidence * 100}%` }}
                              />
                            </div>
                            <span className="font-medium text-green-600">
                              {Math.round(classification.confidence * 100)}%
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Кнопки керування */}
                  <div className="flex gap-3">
                    {callState === 'idle' ? (
                      <button
                        onClick={simulateIncomingCall}
                        className="flex-1 bg-gradient-to-r from-green-500 to-emerald-600 text-white py-4 rounded-xl font-semibold flex items-center justify-center gap-2 hover:from-green-600 hover:to-emerald-700 transition-all shadow-lg"
                      >
                        <PhoneCall className="w-5 h-5" />
                        Симулювати вхідний дзвінок
                      </button>
                    ) : (
                      <button
                        onClick={endCall}
                        className="flex-1 bg-gradient-to-r from-red-500 to-red-600 text-white py-4 rounded-xl font-semibold flex items-center justify-center gap-2 hover:from-red-600 hover:to-red-700 transition-all shadow-lg"
                      >
                        <PhoneOff className="w-5 h-5" />
                        Завершити дзвінок
                      </button>
                    )}
                  </div>
                </div>
              </div>
            )}

            {activeView === 'history' && (
              <div className="bg-white rounded-2xl shadow-md p-6">
                <h2 className="text-xl font-bold text-gray-800 mb-4">Історія дзвінків</h2>
                {callHistory.length === 0 ? (
                  <div className="text-center py-12 text-gray-400">
                    <History className="w-12 h-12 mx-auto mb-3" />
                    <p>Історія дзвінків порожня</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {callHistory.map(call => (
                      <div key={call.id} className="border rounded-xl p-4 hover:bg-gray-50">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm text-gray-500">{call.timestamp}</span>
                          <span className={`text-xs px-2 py-1 rounded-full ${
                            call.status === 'resolved' 
                              ? 'bg-green-100 text-green-700' 
                              : 'bg-yellow-100 text-yellow-700'
                          }`}>
                            {call.status === 'resolved' ? 'Вирішено ШІ' : 'Передано оператору'}
                          </span>
                        </div>
                        <p className="text-gray-800 mb-2">{call.query}</p>
                        <div className="flex items-center gap-4 text-sm text-gray-500">
                          <span>Категорія: {call.category}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {activeView === 'stats' && (
              <div className="bg-white rounded-2xl shadow-md p-6">
                <h2 className="text-xl font-bold text-gray-800 mb-6">Статистика роботи</h2>
                <div className="grid grid-cols-2 gap-4 mb-6">
                  <div className="bg-blue-50 rounded-xl p-4">
                    <p className="text-sm text-blue-600 mb-1">Всього дзвінків</p>
                    <p className="text-3xl font-bold text-blue-800">{stats.totalCalls}</p>
                  </div>
                  <div className="bg-green-50 rounded-xl p-4">
                    <p className="text-sm text-green-600 mb-1">Вирішено ШІ</p>
                    <p className="text-3xl font-bold text-green-800">{aiResolvedPercent}%</p>
                  </div>
                  <div className="bg-yellow-50 rounded-xl p-4">
                    <p className="text-sm text-yellow-600 mb-1">Передано оператору</p>
                    <p className="text-3xl font-bold text-yellow-800">{stats.escalated}</p>
                  </div>
                  <div className="bg-purple-50 rounded-xl p-4">
                    <p className="text-sm text-purple-600 mb-1">Сер. час відповіді</p>
                    <p className="text-3xl font-bold text-purple-800">{stats.avgResponseTime}с</p>
                  </div>
                </div>
                
                <div className="border rounded-xl p-4">
                  <h3 className="font-semibold mb-3">Ефективність ШІ-агента</h3>
                  <div className="h-4 bg-gray-200 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-gradient-to-r from-green-500 to-emerald-500 transition-all"
                      style={{ width: `${aiResolvedPercent}%` }}
                    />
                  </div>
                  <p className="text-sm text-gray-500 mt-2">
                    {stats.aiResolved} з {stats.totalCalls} дзвінків оброблено автоматично
                  </p>
                </div>
              </div>
            )}

            {activeView === 'references' && (
              <div className="bg-white rounded-2xl shadow-md p-6">
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-xl font-bold text-gray-800">Довідники</h2>
                  <div className="flex gap-2">
                    <button
                      onClick={fetchReferences}
                      disabled={refLoading}
                      className="flex items-center gap-2 px-3 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg text-sm"
                    >
                      <RefreshCw className={`w-4 h-4 ${refLoading ? 'animate-spin' : ''}`} />
                      Оновити
                    </button>
                    <button
                      onClick={() => { setShowAddModal(true); setEditingItem(null); }}
                      className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                    >
                      <Plus className="w-4 h-4" />
                      Додати
                    </button>
                  </div>
                </div>

                {/* Підменю довідників */}
                <div className="flex gap-2 mb-4 border-b pb-4">
                  {[
                    { id: 'classifiers', icon: ListTree, label: 'Класифікатор', count: classifiers.length },
                    { id: 'executors', icon: Users, label: 'Виконавці', count: executors.length },
                    { id: 'algorithms', icon: MessageCircle, label: 'Алгоритми', count: algorithms.length }
                  ].map(tab => (
                    <button
                      key={tab.id}
                      onClick={() => setCurrentRefType(tab.id)}
                      className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm transition-all ${
                        currentRefType === tab.id
                          ? 'bg-blue-100 text-blue-700 font-medium'
                          : 'bg-gray-50 text-gray-600 hover:bg-gray-100'
                      }`}
                    >
                      <tab.icon className="w-4 h-4" />
                      {tab.label}
                      <span className="bg-white px-2 py-0.5 rounded-full text-xs">{tab.count}</span>
                    </button>
                  ))}
                </div>

                {!isConnected ? (
                  <div className="text-center py-12 text-gray-400">
                    <WifiOff className="w-12 h-12 mx-auto mb-3" />
                    <p>Підключіться до бекенду для роботи з довідниками</p>
                  </div>
                ) : refLoading ? (
                  <div className="text-center py-12">
                    <RefreshCw className="w-8 h-8 mx-auto mb-3 animate-spin text-blue-500" />
                    <p className="text-gray-500">Завантаження...</p>
                  </div>
                ) : (
                  <>
                    {/* Таблиця класифікатора */}
                    {currentRefType === 'classifiers' && (
                      <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                          <thead className="bg-gray-50">
                            <tr>
                              <th className="px-4 py-3 text-left font-medium text-gray-600">Категорія</th>
                              <th className="px-4 py-3 text-left font-medium text-gray-600">Підтип</th>
                              <th className="px-4 py-3 text-left font-medium text-gray-600">Виконавець</th>
                              <th className="px-4 py-3 text-left font-medium text-gray-600">Термін</th>
                              <th className="px-4 py-3 text-left font-medium text-gray-600">Дії</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y">
                            {classifiers.map(item => (
                              <tr key={item.id} className="hover:bg-gray-50">
                                <td className="px-4 py-3">{item.problem}</td>
                                <td className="px-4 py-3">{item.subtype}</td>
                                <td className="px-4 py-3">{item.executor_name || item.executor}</td>
                                <td className="px-4 py-3">
                                  <span className={`px-2 py-1 rounded text-xs ${
                                    item.urgency === 'emergency' ? 'bg-red-100 text-red-700' :
                                    item.urgency === 'short' ? 'bg-yellow-100 text-yellow-700' :
                                    'bg-green-100 text-green-700'
                                  }`}>
                                    {item.response_time} год
                                  </span>
                                </td>
                                <td className="px-4 py-3">
                                  <div className="flex gap-2">
                                    <button
                                      onClick={() => setEditingItem({ type: 'classifiers', data: item })}
                                      className="p-1.5 text-blue-600 hover:bg-blue-50 rounded"
                                    >
                                      <Pencil className="w-4 h-4" />
                                    </button>
                                    <button
                                      onClick={() => deleteReference('classifiers', item.id)}
                                      className="p-1.5 text-red-600 hover:bg-red-50 rounded"
                                    >
                                      <Trash2 className="w-4 h-4" />
                                    </button>
                                  </div>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}

                    {/* Таблиця виконавців */}
                    {currentRefType === 'executors' && (
                      <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                          <thead className="bg-gray-50">
                            <tr>
                              <th className="px-4 py-3 text-left font-medium text-gray-600">Назва</th>
                              <th className="px-4 py-3 text-left font-medium text-gray-600">Телефон</th>
                              <th className="px-4 py-3 text-left font-medium text-gray-600">Години роботи</th>
                              <th className="px-4 py-3 text-left font-medium text-gray-600">Статус</th>
                              <th className="px-4 py-3 text-left font-medium text-gray-600">Дії</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y">
                            {executors.map(item => (
                              <tr key={item.id} className="hover:bg-gray-50">
                                <td className="px-4 py-3 font-medium">{item.name}</td>
                                <td className="px-4 py-3">{item.phone || '-'}</td>
                                <td className="px-4 py-3">{item.work_hours || '-'}</td>
                                <td className="px-4 py-3">
                                  <span className={`px-2 py-1 rounded text-xs ${
                                    item.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'
                                  }`}>
                                    {item.is_active ? 'Активний' : 'Неактивний'}
                                  </span>
                                </td>
                                <td className="px-4 py-3">
                                  <div className="flex gap-2">
                                    <button
                                      onClick={() => setEditingItem({ type: 'executors', data: item })}
                                      className="p-1.5 text-blue-600 hover:bg-blue-50 rounded"
                                    >
                                      <Pencil className="w-4 h-4" />
                                    </button>
                                    <button
                                      onClick={() => deleteReference('executors', item.id)}
                                      className="p-1.5 text-red-600 hover:bg-red-50 rounded"
                                    >
                                      <Trash2 className="w-4 h-4" />
                                    </button>
                                  </div>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}

                    {/* Таблиця алгоритмів */}
                    {currentRefType === 'algorithms' && (
                      <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                          <thead className="bg-gray-50">
                            <tr>
                              <th className="px-4 py-3 text-left font-medium text-gray-600">Назва</th>
                              <th className="px-4 py-3 text-left font-medium text-gray-600">Опис</th>
                              <th className="px-4 py-3 text-left font-medium text-gray-600">Кроків</th>
                              <th className="px-4 py-3 text-left font-medium text-gray-600">Статус</th>
                              <th className="px-4 py-3 text-left font-medium text-gray-600">Дії</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y">
                            {algorithms.map(item => (
                              <tr key={item.id} className="hover:bg-gray-50">
                                <td className="px-4 py-3 font-medium">
                                  {item.name}
                                  {item.is_default && (
                                    <span className="ml-2 px-2 py-0.5 bg-blue-100 text-blue-700 text-xs rounded">
                                      За замовчуванням
                                    </span>
                                  )}
                                </td>
                                <td className="px-4 py-3 text-gray-500">{item.description || '-'}</td>
                                <td className="px-4 py-3">{item.steps?.length || 0}</td>
                                <td className="px-4 py-3">
                                  <span className={`px-2 py-1 rounded text-xs ${
                                    item.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'
                                  }`}>
                                    {item.is_active ? 'Активний' : 'Неактивний'}
                                  </span>
                                </td>
                                <td className="px-4 py-3">
                                  <div className="flex gap-2">
                                    <button
                                      onClick={() => setEditingItem({ type: 'algorithms', data: item })}
                                      className="p-1.5 text-blue-600 hover:bg-blue-50 rounded"
                                    >
                                      <Pencil className="w-4 h-4" />
                                    </button>
                                    <button
                                      onClick={() => deleteReference('algorithms', item.id)}
                                      className="p-1.5 text-red-600 hover:bg-red-50 rounded"
                                    >
                                      <Trash2 className="w-4 h-4" />
                                    </button>
                                  </div>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </>
                )}
              </div>
            )}

            {activeView === 'settings' && (
              <div className="bg-white rounded-2xl shadow-md p-6">
                <h2 className="text-xl font-bold text-gray-800 mb-6">Налаштування</h2>
                
                <div className="space-y-6">
                  {/* Статус підключення */}
                  <div className="border rounded-xl p-4">
                    <h3 className="font-semibold mb-3">Статус підключення</h3>
                    <div className="flex items-center gap-3">
                      <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
                      <span>{isConnected ? 'Підключено до бекенду' : 'Бекенд недоступний'}</span>
                    </div>
                    <p className="text-sm text-gray-500 mt-2">
                      URL: {BACKEND_URL}
                    </p>
                  </div>
                  
                  {/* Вибір TTS */}
                  <div className="border rounded-xl p-4">
                    <h3 className="font-semibold mb-3">Синтез мовлення (TTS)</h3>
                    <div className="space-y-3">
                      <label className="flex items-center gap-3 cursor-pointer">
                        <input
                          type="radio"
                          name="tts"
                          checked={useFishSpeech}
                          onChange={() => setUseFishSpeech(true)}
                          disabled={!isConnected}
                          className="w-4 h-4 text-blue-600"
                        />
                        <div>
                          <p className="font-medium">Fish Speech (реалістичний голос)</p>
                          <p className="text-sm text-gray-500">Потребує підключення до бекенду з GPU</p>
                        </div>
                      </label>
                      <label className="flex items-center gap-3 cursor-pointer">
                        <input
                          type="radio"
                          name="tts"
                          checked={!useFishSpeech}
                          onChange={() => setUseFishSpeech(false)}
                          className="w-4 h-4 text-blue-600"
                        />
                        <div>
                          <p className="font-medium">Web Speech API (голос браузера)</p>
                          <p className="text-sm text-gray-500">Працює без бекенду, але звучить роботизовано</p>
                        </div>
                      </label>
                    </div>
                  </div>
                  
                  {/* Інструкція запуску бекенду */}
                  <div className="border rounded-xl p-4 bg-gray-50">
                    <h3 className="font-semibold mb-3">Запуск Fish Speech бекенду</h3>
                    <div className="bg-gray-800 text-green-400 p-4 rounded-lg font-mono text-sm overflow-x-auto">
                      <p># Встановлення залежностей</p>
                      <p>cd backend</p>
                      <p>pip install -r requirements.txt</p>
                      <p>pip install fish-speech</p>
                      <p></p>
                      <p># Запуск сервера</p>
                      <p>python main.py</p>
                    </div>
                    <p className="text-sm text-gray-500 mt-3">
                      Для роботи Fish Speech потрібна відеокарта NVIDIA з CUDA.
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Бокова панель */}
          <div className="space-y-6">
            {/* Статус системи */}
            <div className="bg-white rounded-2xl shadow-md p-6">
              <h3 className="font-semibold text-gray-800 mb-4">Статус системи</h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-gray-600">Fish Speech TTS</span>
                  <span className={`flex items-center gap-1 ${isConnected ? 'text-green-600' : 'text-yellow-600'}`}>
                    <CheckCircle className="w-4 h-4" /> 
                    {isConnected ? 'Активний' : 'Fallback'}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-600">Silero ASR</span>
                  <span className={`flex items-center gap-1 ${isConnected ? 'text-green-600' : 'text-gray-400'}`}>
                    <CheckCircle className="w-4 h-4" /> 
                    {isConnected ? 'Активний' : 'Вимкнено'}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-600">Класифікатор</span>
                  <span className="flex items-center gap-1 text-green-600">
                    <CheckCircle className="w-4 h-4" /> Активний
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-600">Бекенд</span>
                  <span className={`flex items-center gap-1 ${isConnected ? 'text-green-600' : 'text-red-500'}`}>
                    {isConnected ? <Wifi className="w-4 h-4" /> : <WifiOff className="w-4 h-4" />}
                    {isConnected ? 'Підключено' : 'Офлайн'}
                  </span>
                </div>
              </div>
            </div>

            {/* Швидка статистика */}
            <div className="bg-gradient-to-br from-blue-600 to-indigo-700 rounded-2xl shadow-md p-6 text-white">
              <h3 className="font-semibold mb-4">Сьогодні</h3>
              <div className="space-y-4">
                <div>
                  <p className="text-blue-200 text-sm">Оброблено дзвінків</p>
                  <p className="text-3xl font-bold">{stats.totalCalls}</p>
                </div>
                <div>
                  <p className="text-blue-200 text-sm">Автоматично вирішено</p>
                  <p className="text-3xl font-bold">{aiResolvedPercent}%</p>
                </div>
              </div>
            </div>

            {/* Інструкція */}
            <div className={`border rounded-2xl p-6 ${
              isConnected 
                ? 'bg-green-50 border-green-200' 
                : 'bg-yellow-50 border-yellow-200'
            }`}>
              <h3 className={`font-semibold mb-3 flex items-center gap-2 ${
                isConnected ? 'text-green-800' : 'text-yellow-800'
              }`}>
                <Volume2 className="w-5 h-5" /> 
                {isConnected ? 'Fish Speech активний!' : 'Увімкніть звук!'}
              </h3>
              <p className={`text-sm mb-3 ${isConnected ? 'text-green-700' : 'text-yellow-700'}`}>
                {isConnected 
                  ? 'Використовується реалістичний голос Fish Speech.'
                  : 'Бекенд недоступний. Використовується голос браузера.'}
              </p>
              <ol className={`text-sm space-y-1 ${isConnected ? 'text-green-700' : 'text-yellow-700'}`}>
                <li>1. Натисніть "Симулювати дзвінок"</li>
                <li>2. ШІ привітає заявника</li>
                <li>3. Заявник озвучить проблему</li>
                <li>4. ШІ класифікує та відповість</li>
              </ol>
            </div>
          </div>
        </div>
      </div>

      {/* Модальне вікно редагування */}
      {(showAddModal || editingItem) && (
        <ReferenceModal
          type={editingItem?.type || currentRefType}
          data={editingItem?.data}
          executors={executors}
          onClose={() => { setShowAddModal(false); setEditingItem(null); }}
          onSave={(data) => {
            if (editingItem) {
              updateReference(editingItem.type, editingItem.data.id, data);
            } else {
              createReference(currentRefType, data);
            }
          }}
        />
      )}

      {/* Футер */}
      <footer className="bg-gray-800 text-gray-400 py-6 mt-12">
        <div className="max-w-7xl mx-auto px-4 text-center">
          <p className="mb-2">ШІ-Агент Контактного Центру</p>
          <p className="text-sm">
            Powered by <span className="text-white">
              {isConnected ? 'Fish Speech TTS + Silero ASR' : 'Web Speech API'}
            </span>
          </p>
        </div>
      </footer>
    </div>
  );
};

export default App;
