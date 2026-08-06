export interface SourceMetadata {
  article_number?: string;
  book?: string;
  page?: number;
  source?: string;
  [key: string]: any;
}

export interface SourceDocument {
  content: string;
  metadata: SourceMetadata;
}

export interface RagStats {
  retrieved_count: number;
  response_time: string;
  source_verified?: boolean;
  engine?: string;
  status?: string;
  search_type?: string;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: SourceDocument[];
  rag_stats?: RagStats;
  timestamp: string;
  isStreaming?: boolean;
}

export interface SavedChat {
  id: string;
  title: string;
  date: string;
  messages: Message[];
}

export interface SuggestionItem {
  id: string;
  category: string;
  title: string;
  subtext: string;
  prompt: string;
  btn_label: string;
  svg_icon: string;
  accent_class: string;
}

export interface SystemStats {
  total_docs: number;
  status: string;
  accuracy: string;
  response_time: string;
  engine: string;
}
