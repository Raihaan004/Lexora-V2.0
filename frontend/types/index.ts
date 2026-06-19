export interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
}

export interface ChatSession {
  id: string;
  title: string;
  messages: Message[];
  created_at: string;
}

export interface DocumentInfo {
  id: string;
  filename: string;
  status: 'processing' | 'completed' | 'failed';
  chunk_count?: number;
  file_size_bytes?: number;
  uploaded_at: string;
  error_message?: string;
}

export interface AppState {
  currentSessionId: string | null;
  sessions: ChatSession[];
  documents: DocumentInfo[];
  isLoading: boolean;
  useRag: boolean;
}
