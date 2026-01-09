import React, { useState, useEffect, useRef, useCallback } from 'react';
import { 
  Phone, Mic, MicOff, Volume2, VolumeX, ArrowRightLeft, 
  FileText, Clock, AlertTriangle, 
  CheckCircle, PhoneCall, PhoneOff, Headphones, BarChart3, History,
  Zap, Droplets, Flame, Building2, Bus, HelpCircle, MessageSquare,
  Wifi, WifiOff, Settings, Database, Plus, Pencil, Trash2, X, Save,
  Users, ListTree, MessageCircle, RefreshCw, AlertCircle
} from 'lucide-react';

// Конфігурація бекенду
const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';
const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws/call';

// Локальний класифікатор для fallback режиму
const CLASSIFIER_DATA = [
  {
    id: '1',
    problem: 'Благоустрій території',
    type: 'Утримання території в зимовий період',
    subtype: 'розчистка снігу',
    location: 'прибудинкова територія',
    response: 'Вашу заявку щодо розчистки снігу прийнято. Роботи будуть виконані протягом 24 годин.',
    executor: 'Управитель будинку',
    urgency: 'short',
    responseTime: 24,
    keywords: ['сніг', 'розчистка', 'прибрати', 'замело', 'снігопад', 'двір'],
    is_active: true
  },
  {
    id: '2',
    problem: 'Благоустрій території',
    type: 'Благоустрій та санітарний стан',
    subtype: 'впавше дерево',
    location: 'на машину',
    response: 'Надійшла заявка про дерево, що впало. Аварійна служба виконає роботи протягом 3 годин.',
    executor: 'Аварійна служба',
    urgency: 'emergency',
    responseTime: 3,
    keywords: ['дерево', 'впало', 'машина', 'автомобіль', 'гілка', 'розпилити'],
    is_active: true
  },
  {
    id: '3',
    problem: 'Ремонт житлового фонду',
    type: 'Покрівля',
    subtype: 'протікання даху',
    location: 'квартира',
    response: 'Ваша заява щодо протікання даху прийнята. Аварійна служба вже направлена.',
    executor: 'Аварійна служба',
    urgency: 'emergency',
    responseTime: 3,
    keywords: ['протікає', 'дах', 'стеля', 'вода', 'капає', 'мокро', 'покрівля'],
    is_active: true
  },
  {
    id: '4',
    problem: 'Інженерні мережі',
    type: 'Опалення',
    subtype: 'відсутність опалення',
    location: 'квартира',
    response: 'Заявку щодо відсутності опалення прийнято. Перевірка системи буде виконана протягом 3 годин.',
    executor: 'Служба теплопостачання',
    urgency: 'emergency',
    responseTime: 3,
    keywords: ['опалення', 'холодно', 'батареї', 'радіатор', 'тепло', 'гаряча'],
    is_active: true
  },
  {
    id: '5',
    problem: 'Інженерні мережі',
    type: 'Водопостачання',
    subtype: 'відсутність води',
    location: 'будинок',
    response: 'Заявку щодо відсутності води прийнято. Бригада виїде протягом 2 годин.',
    executor: 'Служба водопостачання',
    urgency: 'emergency',
    responseTime: 2,
    keywords: ['вода', 'водопостачання', 'кран', 'немає води', 'відключили воду'],
    is_active: true
  },
  {
    id: '6',
    problem: 'Інженерні мережі',
    type: 'Електропостачання',
    subtype: 'відключення світла',
    location: 'квартира/будинок',
    response: 'Інформація про відключення електроенергії доступна на сайті постачальника. Для аварій зверніться за номером 104.',
    executor: 'Електропостачання',
    urgency: 'info',
    responseTime: 0,
    keywords: ['світло', 'електрика', 'відключили', 'немає світла', 'струм'],
    is_active: true
  },
  {
    id: '7',
    problem: 'Громадський транспорт',
    type: 'Маршрутки та автобуси',
    subtype: 'скарга на транспорт',
    location: 'маршрут',
    response: 'Вашу скаргу на роботу транспорту зареєстровано. Відповідь надійде протягом 5 робочих днів.',
    executor: 'Департамент транспорту',
    urgency: 'standard',
    responseTime: 120,
    keywords: ['маршрутка', 'автобус', 'водій', 'транспорт', 'їде', 'не зупинився'],
    is_active: true
  },
  {
    id: '8',
    problem: 'Надзвичайні ситуації',
    type: 'Руйнування інфраструктури',
    subtype: 'пошкодження дороги',
    location: 'дорога',
    response: 'Заявку про пошкодження інфраструктури прийнято. Фахівці негайно виїдуть на місце.',
    executor: 'Управління НС',
    urgency: 'emergency',
    responseTime: 1,
    keywords: ['руйнування', 'міст', 'дорога', 'яма', 'провал', 'аварія'],
    is_active: true
  }
];

// Зразки голосових запитів для демо
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

// ===========================================
// Компонент візуалізації аудіо
// ===========================================
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

// ===========================================
// Компонент повідомлення в чаті
// ===========================================
const ChatMessageComponent = ({ message }) => (
  <div className={`flex ${message.isUser ? 'justify-end' : 'justify-start'} mb-3`}>
    <div className={`max-w-[80%] rounded-2xl px-4 py-3 ${
      message.isUser 
        ? 'bg-blue-600 text-white rounded-br-md' 
        : 'bg-gray-100 text-gray-800 rounded-bl-md'
    }`}>
      <p className="text-sm leading-relaxed">{message.text}</p>
      <span className={`text-xs mt-1 block ${message.isUser ? 'text-blue-200' : 'text-gray-500'}`}>
        {message.timestamp}
      </span>
    </div>
  </div>
);

// ===========================================
// Компонент бейджа терміновості
// ===========================================
const CategoryBadge = ({ urgency }) => {
  const styles = {
    emergency: 'bg-red-100 text-red-800 border-red-300',
    short: 'bg-yellow-100 text-yellow-800 border-yellow-300',
    info: 'bg-blue-100 text-blue-800 border-blue-300',
    standard: 'bg-green-100 text-green-800 border-green-300'
  };
  
  const texts = {
    emergency: 'Аварійний',
    short: 'Терміновий',
    info: 'Інформація',
    standard: 'Стандартний'
  };
  
  return (
    <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full border ${styles[urgency]}`}>
      <AlertTriangle className="w-4 h-4" />
      <span className="text-sm font-medium">{texts[urgency]}</span>
    </div>
  );
};

// ===========================================
// Компонент панелі стану системи
// ===========================================
const SystemStatus = ({ isConnected, useFishSpeech }) => (
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
);

// ===========================================
// Компонент швидкої статистики
// ===========================================
const QuickStats = ({ stats }) => {
  const aiResolvedPercent = stats.totalCalls > 0 
    ? Math.round((stats.aiResolved / stats.totalCalls) * 100) 
    : 0;
  
  return (
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
  );
};

// ===========================================
// Головний компонент App
// ===========================================
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
  const [error, setError] = useState(null);

  // Стани для довідників
  const [executors, setExecutors] = useState([]);
  const [classifiers, setClassifiers] = useState([]);
  const [algorithms, setAlgorithms] = useState([]);
  const [refLoading, setRefLoading] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [currentRefType, setCurrentRefType] = useState('classifiers');

  // Стани для голосового режиму
  const [isRecording, setIsRecording] = useState(false);
  const [lastTranscript, setLastTranscript] = useState('');

  // Refs
  const chatEndRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const wsRef = useRef(null);
  const audioContextRef = useRef(null);
  const audioQueueRef = useRef([]);
  const isPlayingRef = useRef(false);
  const recognitionRef = useRef(null);
  const mediaStreamRef = useRef(null);
  const recordingTimeoutRef = useRef(null);

  // Ініціалізація AudioContext
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
          const data = await response.json();
          setIsConnected(true);
          console.log('[Backend] Підключено:', data);
        } else {
          setIsConnected(false);
          setError('Бекенд повернув помилку');
        }
      } catch (err) {
        setIsConnected(false);
        setError('Бекенд недоступний. Використовується fallback режим.');
        console.log('[Backend] Недоступний, fallback режим');
      }
    };
    
    checkBackend();
    const interval = setInterval(checkBackend, 30000);  // Перевірка кожні 30 секунд
    return () => clearInterval(interval);
  }, []);

  // Прокрутка чату донизу при новому повідомленні
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages]);

  // Оновлення статистики при завершенні дзвінка
  useEffect(() => {
    if (callState === 'ended') {
      setStats(prev => ({
        totalCalls: prev.totalCalls + 1,
        avgResponseTime: Math.round((prev.avgResponseTime * prev.totalCalls + 3.5) / (prev.totalCalls + 1) * 10) / 10
      }));
    }
  }, [callState]);

  // Функція класифікації запиту (локальна)
  const classifyQueryLocal = useCallback((query) => {
    const lowerQuery = query.toLowerCase();
    let bestMatch = null;
    let highestScore = 0;

    CLASSIFIER_DATA.forEach(item => {
      let score = 0;
      item.keywords?.forEach(keyword => {
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

    if (bestMatch && highestScore > 0) {
      return {
        id: bestMatch.id,
        problem: bestMatch.problem,
        type: bestMatch.type || '',
        subtype: bestMatch.subtype,
        location: bestMatch.location,
        response: bestMatch.response,
        executor: bestMatch.executor,
        urgency: bestMatch.urgency,
        response_time: bestMatch.responseTime,
        confidence: Math.min(0.95, 0.6 + highestScore * 0.1),
        needs_operator: false
      };
    }

    return {
      id: '0',
      problem: 'Загальне питання',
      type: 'Консультація',
      subtype: 'потребує оператора',
      location: undefined,
      response: 'Вибачте, я не зміг точно визначити тип вашого звернення. Зачекайте, будь ласка, я переключу вас на оператора.',
      executor: 'Оператор контактного центру',
      urgency: 'standard',
      response_time: 0,
      confidence: 0.3,
      needs_operator: true
    };
  }, []);

  // Відтворення WAV аудіо з байтів
  const playAudioBytes = useCallback(async (audioBytes) => {
    return new Promise((resolve) => {
      if (!audioContextRef.current || !isSpeakerOn) {
        resolve();
        return;
      }
      
      try {
        setIsSpeaking(true);
        
        audioBytes.arrayBuffer().then(arrayBuffer => {
          const audioCtx = audioContextRef.current;
          if (!audioCtx) {
            setIsSpeaking(false);
            resolve();
            return;
          }
          audioCtx.decodeAudioData(arrayBuffer).then(audioBuffer => {
            const source = audioCtx.createBufferSource();
            source.buffer = audioBuffer;
            source.connect(audioCtx.destination);
            
            source.onended = () => {
              setIsSpeaking(false);
              resolve();
            };
            
            source.start();
          }).catch(err => {
            console.error('Декодування аудіо не вдалося:', err);
            setIsSpeaking(false);
            resolve();
          });
        }).catch(err => {
          console.error('Помилка конвертації в arrayBuffer:', err);
          setIsSpeaking(false);
          resolve();
        });
      } catch (error) {
        console.error('Помилка відтворення аудіо:', error);
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
    
    try {
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
            console.log('[Audio] TTS бекенд недоступний, використовую Web Speech');
            await new Promise(resolve => speakWithWebSpeech(text, resolve));
          }
        } catch (error) {
          console.error('[Audio] Помилка TTS:', error);
          await new Promise(resolve => speakWithWebSpeech(text, resolve));
        }
      } else {
        await new Promise(resolve => speakWithWebSpeech(text, resolve));
      }
    } catch (error) {
      console.error('[Audio] Неочікувана помилка:', error);
      setIsSpeaking(false);
    }
    
    isPlayingRef.current = false;
    setIsSpeaking(false);
    
    if (callback) {
      try {
        callback();
      } catch (e) {
        console.error('[Audio] Помилка callback:', e);
      }
    }
    
    setTimeout(() => processAudioQueue(), 50);
  }, [isConnected, useFishSpeech, playAudioBytes, speakWithWebSpeech]);

  // Синтез мовлення через Fish Speech API з чергою
  const synthesizeSpeech = useCallback((text, callback) => {
    audioQueueRef.current.push({ text, callback, useBackend: true });
    processAudioQueue();
  }, [processAudioQueue]);

  // Ініціалізація Web Speech API
  useEffect(() => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = true;
      recognitionRef.current.lang = 'uk-UA';
      
      recognitionRef.current.onresult = (event) => {
        const result = Array.from(event.results)
          .map(result => result[0].transcript)
          .join('');
        setLastTranscript(result);
        
        if (event.results[0].isFinal) {
          processVoiceText(result);
        }
      };
      
      recognitionRef.current.onerror = (event) => {
        console.log('[WebSpeech] Помилка:', event.error);
        setIsRecording(false);
        
        if (event.error === 'network' && isConnected) {
          console.log('[WebSpeech] Помилка мережі, перехід на бекенд ASR');
          startBackendRecording();
          return;
        }
        
        if (event.error === 'no-speech') {
          setLastTranscript('[Не почуто голос - спробуйте ще]');
          setTimeout(() => {
            if (callState !== 'idle' && callState !== 'ended') {
              startListening();
            }
          }, 1000);
        } else if (event.error === 'aborted') {
          // Нормально при рестарті
        } else if (event.error === 'not-allowed') {
          setCallState('idle');
          setError('Доступ до мікрофона заборонено. Дозвольте доступ у налаштуваннях браузера.');
        }
      };
      
      recognitionRef.current.onend = () => {
        console.log('[WebSpeech] Закінчено');
        setIsRecording(false);
      };
    }
  }, [callState, isConnected]);

  // Backend ASR через MediaRecorder
  const startBackendRecording = useCallback(async () => {
    console.log('[BackendASR] Початок запису...');
    try {
      if (!mediaStreamRef.current) {
        mediaStreamRef.current = await navigator.mediaDevices.getUserMedia({ 
          audio: { 
            sampleRate: 16000,
            channelCount: 1,
            echoCancellation: true,
            noiseSuppression: true
          } 
        });
      }
      
      audioChunksRef.current = [];
      const mimeType = MediaRecorder.isTypeSupported('audio/webm') ? 'audio/webm' : 'audio/mp4';
      mediaRecorderRef.current = new MediaRecorder(mediaStreamRef.current, { mimeType });
      
      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };
      
      mediaRecorderRef.current.onstop = async () => {
        console.log('[BackendASR] Запис закінчено, відправка на бекенд...');
        setLastTranscript('[Обробка голосу...]');
        
        const audioBlob = new Blob(audioChunksRef.current, { type: mimeType });
        
        try {
          const formData = new FormData();
          formData.append('audio', audioBlob, 'recording.webm');
          
          const response = await fetch(`${BACKEND_URL}/api/transcribe`, {
            method: 'POST',
            body: formData
          });
          
          if (response.ok) {
            const data = await response.json();
            console.log('[BackendASR] Результат:', data);
            const transcribedText = data.transcript || data.text || '';
            
            if (transcribedText.trim()) {
              setLastTranscript(transcribedText);
              processVoiceText(transcribedText);
            } else {
              setLastTranscript('[Не вдалось розпізнати]');
              setTimeout(() => {
                if (callState !== 'idle' && callState !== 'ended') {
                  startListening();
                }
              }, 1000);
            }
          } else {
            console.error('[BackendASR] Помилка транскрибування:', response.status);
            setLastTranscript('[Помилка розпізнавання]');
            setError('Помилка розпізнавання голосу на сервері');
          }
        } catch (error) {
          console.error('[BackendASR] Помилка:', error);
          setLastTranscript('[Помилка з\'єднання]');
          setError('Помилка з\'єднання з сервером розпізнавання');
        }
        
        setIsRecording(false);
      };
      
      mediaRecorderRef.current.start();
      setIsRecording(true);
      setCallState('processing');
      setLastTranscript('[Говоріть...]');
      
      // Автоматична зупинка через 10 секунд
      recordingTimeoutRef.current = setTimeout(() => {
        if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
          console.log('[BackendASR] Автозупинка через 10с');
          mediaRecorderRef.current.stop();
        }
      }, 10000);
      
    } catch (error) {
      console.error('[BackendASR] Помилка початку запису:', error);
      setIsRecording(false);
      if (error.name === 'NotAllowedError') {
        setError('Доступ до мікрофона заборонено. Дозвольте доступ у налаштуваннях браузера.');
      }
    }
  }, [callState]);

  const stopBackendRecording = useCallback(() => {
    if (recordingTimeoutRef.current) {
      clearTimeout(recordingTimeoutRef.current);
    }
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      console.log('[BackendASR] Зупинка запису...');
      mediaRecorderRef.current.stop();
    }
  }, []);

  // Обробка розпізнаного тексту
  const processVoiceText = useCallback(async (userText) => {
    if (!userText.trim()) {
      setCallState('idle');
      return;
    }
    
    // Додаємо повідомлення користувача
    const userMsg = {
      id: Date.now(),
      text: userText,
      isUser: true,
      timestamp: new Date().toLocaleTimeString('uk-UA', { hour: '2-digit', minute: '2-digit' })
    };
    setChatMessages(prev => [...prev, userMsg]);
    
    setCallState('processing');
    setError(null);
    
    try {
      let result;
      
      if (isConnected) {
        const classifyRes = await fetch(`${BACKEND_URL}/api/classify`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text: userText })
        });
        
        if (classifyRes.ok) {
          const classifyData = await classifyRes.json();
          result = classifyData.classification;
        } else {
          throw new Error('Помилка класифікації');
        }
      } else {
        result = classifyQueryLocal(userText);
      }
      
      setClassification(result);
      
      const responseText = result.response || 'Дякую за ваше звернення.';
      const agentMsg = {
        id: Date.now() + 1,
        text: responseText,
        isUser: false,
        timestamp: new Date().toLocaleTimeString('uk-UA', { hour: '2-digit', minute: '2-digit' })
      };
      setChatMessages(prev => [...prev, agentMsg]);
      
      // Озвучуємо відповідь
      setCallState('responding');
      await new Promise((resolve) => {
        synthesizeSpeech(responseText, () => {
          const followUp = 'Чи можу я ще чимось допомогти?';
          const followUpMsg = {
            id: Date.now() + 2,
            text: followUp,
            isUser: false,
            timestamp: new Date().toLocaleTimeString('uk-UA', { hour: '2-digit', minute: '2-digit' })
          };
          setChatMessages(prev => [...prev, followUpMsg]);
          
          synthesizeSpeech(followUp, () => {
            resolve();
          });
        });
      });
      
      startListening();
    } catch (error) {
      console.error('Помилка обробки:', error);
      setError('Сталася помилка при обробці запиту. Спробуйте ще раз.');
      setCallState('active');
    }
  }, [isConnected, classifyQueryLocal, synthesizeSpeech]);

  // Почати голосовий діалог
  const startVoiceCall = useCallback(async () => {
    if (!recognitionRef.current) {
      setError('Ваш браузер не підтримує розпізнавання голосу. Використовуйте Chrome.');
      return;
    }
    
    setCallState('active');
    setChatMessages([]);
    setClassification(null);
    setLastTranscript('');
    setError(null);
    
    const greeting = 'Доброго дня! Ви зателефонували на гарячу лінію. Чим можу допомогти?';
    const greetingMsg = {
      id: Date.now(),
      text: greeting,
      isUser: false,
      timestamp: new Date().toLocaleTimeString('uk-UA', { hour: '2-digit', minute: '2-digit' })
    };
    setChatMessages([greetingMsg]);
    
    setCallState('responding');
    console.log('[Voice] Початок привітання TTS...');
    
    await new Promise((resolve) => {
      synthesizeSpeech(greeting, () => {
        console.log('[Voice] Привітання закінчено, початок прослуховування...');
        setCallState('processing');
        setTimeout(() => {
          try {
            console.log('[Voice] Виклик startListening...');
            startListening();
            resolve();
          } catch (e) {
            console.error('[Voice] Помилка startListening:', e);
            resolve();
          }
        }, 300);
      });
    });
  }, [synthesizeSpeech]);

  // Почати прослуховування
  const startListening = useCallback(() => {
    console.log('[Voice] startListening, useBackendASR:', isConnected);
    
    if (isConnected) {
      startBackendRecording();
    } else if (recognitionRef.current) {
      try {
        try {
          recognitionRef.current.abort();
        } catch {
          // Ігноруємо
        }
        
        setTimeout(() => {
          setIsRecording(true);
          setCallState('processing');
          console.log('[WebSpeech] Початок розпізнавання...');
          recognitionRef.current?.start();
        }, 100);
      } catch (e) {
        console.error('[WebSpeech] Помилка початку розпізнавання:', e);
      }
    } else {
      console.error('[Voice] Немає методу ASR');
      setError('Розпізнавання голосу недоступне');
    }
  }, [isConnected, startBackendRecording]);

  // Зупинити прослуховування
  const stopListening = useCallback(() => {
    if (isConnected) {
      stopBackendRecording();
    } else if (recognitionRef.current && isRecording) {
      recognitionRef.current.stop();
      setIsRecording(false);
    }
  }, [isConnected, isRecording, stopBackendRecording]);

  // Симуляція вхідного дзвінка
  const simulateIncomingCall = useCallback(async () => {
    setCallState('ringing');
    setChatMessages([]);
    setTranscript('');
    setClassification(null);
    setError(null);
    
    setTimeout(async () => {
      setCallState('active');
      
      const greeting = 'Доброго дня! Ви зателефонували на гарячу лінію контактного центру. Чим можу вам допомогти?';
      
      const greetingMsg = {
        id: 1,
        text: greeting,
        isUser: false,
        timestamp: new Date().toLocaleTimeString('uk-UA', { hour: '2-digit', minute: '2-digit' })
      };
      setChatMessages([greetingMsg]);
      
      await new Promise((resolve) => {
        synthesizeSpeech(greeting, () => {
          setTimeout(() => {
            const randomQuery = SAMPLE_QUERIES[Math.floor(Math.random() * SAMPLE_QUERIES.length)];
            processUserQuery(randomQuery);
            resolve();
          }, 1000);
        });
      });
    }, 1500);
  }, [synthesizeSpeech]);

  // Обробка запиту користувача
  const processUserQuery = useCallback(async (query) => {
    setCallState('processing');
    setTranscript(query);
    
    await new Promise((resolve) => {
      synthesizeSpeech(query, () => {
        const userMsg = {
          id: Date.now(),
          text: query,
          isUser: true,
          timestamp: new Date().toLocaleTimeString('uk-UA', { hour: '2-digit', minute: '2-digit' })
        };
        setChatMessages(prev => [...prev, userMsg]);

        setTimeout(async () => {
          const result = isConnected 
            ? await fetchClassification(query)
            : classifyQueryLocal(query);
          setClassification(result);

          setTimeout(() => {
            generateResponse(result, query);
            resolve();
          }, 800);
        }, 1000);
      });
    });
  }, [isConnected, classifyQueryLocal, synthesizeSpeech]);

  // Отримання класифікації з бекенду
  const fetchClassification = async (query) => {
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
      console.error('Помилка класифікації:', error);
    }
    return classifyQueryLocal(query);
  };

  // Генерація відповіді
  const generateResponse = useCallback(async (classification, originalQuery) => {
    setCallState('responding');
    
    let response;
    let needsEscalation = false;
    
    if (classification && classification.confidence > 0.7) {
      response = classification.response;
    } else {
      response = 'Вибачте, я не зміг точно визначити тип вашого звернення. Зачекайте, я переключу вас на оператора.';
      needsEscalation = true;
    }
    
    const agentMsg = {
      id: Date.now(),
      text: response,
      isUser: false,
      timestamp: new Date().toLocaleTimeString('uk-UA', { hour: '2-digit', minute: '2-digit' })
    };
    setChatMessages(prev => [...prev, agentMsg]);
    
    await new Promise((resolve) => {
      synthesizeSpeech(response, () => {
        setStats(prev => ({
          totalCalls: prev.totalCalls + 1,
          aiResolved: needsEscalation ? prev.aiResolved : prev.aiResolved + 1,
          escalated: needsEscalation ? prev.escalated + 1 : prev.escalated,
          avgResponseTime: Math.round((prev.avgResponseTime * prev.totalCalls + 3.5) / (prev.totalCalls + 1) * 10) / 10
        }));
        
        const historyRecord = {
          id: Date.now().toString(),
          timestamp: new Date().toLocaleString('uk-UA'),
          query: originalQuery,
          category: classification?.subtype || 'Не визначено',
          status: needsEscalation ? 'escalated' : 'resolved',
          executor: classification?.executor || 'Оператор'
        };
        setCallHistory(prev => [historyRecord, ...prev.slice(0, 9)]);
        
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
          
          await new Promise((res) => {
            synthesizeSpeech(closingMsg.text, () => {
              setCallState('active');
              res();
            });
          });
        }, 500);
        
        resolve();
      });
    });
  }, [synthesizeSpeech]);

  // Завершення дзвінка
  const endCall = useCallback(() => {
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
      setError(null);
    }, 1500);
  }, []);

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

      {/* Повідомлення про помилку */}
      {error && (
        <div className="max-w-7xl mx-auto px-4 py-2">
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-red-500" />
            <span className="text-red-700">{error}</span>
            <button 
              onClick={() => setError(null)}
              className="ml-auto text-red-500 hover:text-red-700"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>
      )}

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
                          <ChatMessageComponent key={msg.id} message={msg} />
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
                          <span className="text-gray-500">Категория:</span>
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
                          <p className="font-medium">{classification.response_time} год.</p>
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
                      <>
                        <button
                          onClick={simulateIncomingCall}
                          className="flex-1 bg-gradient-to-r from-gray-500 to-gray-600 text-white py-4 rounded-xl font-semibold flex items-center justify-center gap-2 hover:from-gray-600 hover:to-gray-700 transition-all shadow-lg"
                        >
                          <PhoneCall className="w-5 h-5" />
                          Демо
                        </button>
                        <button
                          onClick={startVoiceCall}
                          className="flex-1 bg-gradient-to-r from-green-500 to-emerald-600 text-white py-4 rounded-xl font-semibold flex items-center justify-center gap-2 hover:from-green-600 hover:to-emerald-700 transition-all shadow-lg"
                        >
                          <Mic className="w-5 h-5" />
                          Почати розмову
                        </button>
                      </>
                    ) : (
                      <>
                        {isRecording && (
                          <div className="flex-1 bg-red-500 text-white py-4 rounded-xl font-semibold flex items-center justify-center gap-2 animate-pulse">
                            <Mic className="w-5 h-5" />
                            Слухаю... Говоріть!
                          </div>
                        )}
                        <button
                          onClick={() => {
                            if (isRecording) stopListening();
                            endCall();
                          }}
                          className={`${isRecording ? 'flex-none px-6' : 'flex-1'} bg-gradient-to-r from-red-500 to-red-600 text-white py-4 rounded-xl font-semibold flex items-center justify-center gap-2 hover:from-red-600 hover:to-red-700 transition-all shadow-lg`}
                        >
                          <PhoneOff className="w-5 h-5" />
                          Завершити
                        </button>
                      </>
                    )}
                  </div>
                  
                  {/* Останній транскрипт */}
                  {lastTranscript && (
                    <div className="mt-3 p-3 bg-blue-50 rounded-lg">
                      <p className="text-xs text-blue-600 font-medium mb-1">Розпізнано (ASR):</p>
                      <p className="text-sm text-blue-800">{lastTranscript}</p>
                    </div>
                  )}
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
                          <span>Категория: {call.category}</span>
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
                  <button
                    onClick={() => setShowAddModal(true)}
                    className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                  >
                    <Plus className="w-4 h-4" />
                    Додати
                  </button>
                </div>

                <div className="text-center py-12 text-gray-400">
                  <Database className="w-12 h-12 mx-auto mb-3" />
                  <p>Підключіться до бекенду для роботи з довідниками</p>
                </div>
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
                      <p>python main_fixed.py</p>
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
            <SystemStatus isConnected={isConnected} useFishSpeech={useFishSpeech} />
            <QuickStats stats={stats} />

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
