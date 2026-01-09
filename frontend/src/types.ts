// ===========================================
// Типи даних для ШІ-Агента Контактного Центру
// ===========================================

// Категорія класифікатора
export interface ClassifierCategory {
  id: string;
  problem: string;
  type?: string;
  subtype: string;
  location?: string;
  response: string;
  executor: string;
  executor_id?: string;
  urgency: 'emergency' | 'short' | 'standard' | 'info';
  response_time: number;
  keywords?: string[];
  is_active: boolean;
}

// Виконавець
export interface Executor {
  id: string;
  name: string;
  phone?: string;
  email?: string;
  work_hours?: string;
  description?: string;
  is_active: boolean;
}

// Алгоритм розмови
export interface ConversationAlgorithm {
  id: string;
  name: string;
  description?: string;
  steps: ConversationStep[];
  trigger_keywords?: string[];
  is_default: boolean;
  is_active: boolean;
}

// Крок алгоритму
export interface ConversationStep {
  id: string;
  type: 'greeting' | 'question' | 'response' | 'escalation';
  text: string;
  action?: string;
}

// Результат класифікації
export interface ClassificationResult {
  id: string;
  problem: string;
  type: string;
  subtype: string;
  location?: string;
  response: string;
  executor: string;
  urgency: 'emergency' | 'short' | 'standard' | 'info';
  response_time: number;
  confidence: number;
  needs_operator: boolean;
}

// Запис дзвінка
export interface CallRecord {
  id: string;
  timestamp: string;
  caller_phone?: string;
  transcript: string;
  classification: {
    problem: string;
    subtype: string;
    executor: string;
  };
  status: 'resolved' | 'escalated';
  response_text: string;
  executor: string;
}

// Повідомлення чату
export interface ChatMessage {
  id: number;
  text: string;
  isUser: boolean;
  timestamp: string;
}

// Стан дзвінка
export type CallState = 
  | 'idle' 
  | 'ringing' 
  | 'active' 
  | 'processing' 
  | 'responding' 
  | 'ended';

// Статистика
export interface Stats {
  totalCalls: number;
  aiResolved: number;
  escalated: number;
  avgResponseTime: number;
}

// Налаштування TTS
export interface TTSSettings {
  useFishSpeech: boolean;
  voice: string;
}

// API Response типи
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  message?: string;
  count?: number;
}

export interface HealthResponse {
  status: string;
  version: string;
  timestamp: string;
  components: {
    asr: { status: string };
    tts: { status: string; engine: string };
    classifier: { status: string; categories_count: number };
    database: { status: string; type: string };
  };
}

// Помилка API
export interface ApiError {
  detail: string;
}
