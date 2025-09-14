export interface Question {
  id: number;
  question: string;
  difficulty: string;
}

export interface Analysis {
  raw_analysis: string;
  score: number;
  normalized_score: number;
  concepts_covered: string[];
  missing_concepts: string[];
  quality: string;
  depth: string;
  detailed_analysis: string;
}

export interface StartSessionResponse {
  session_id: string;
  welcome: string;
  first_question: Question;
}

export interface MessageResponse {
  status: string;
  processing: boolean;
}

export interface SessionState {
  current_question_idx: number;
  questions_asked: number;
  stage: string;
  current_question: Question | null;
  current_followup_count: number;
  performance_data: any[];
  conversation_history: any[];
}

export interface InterviewSummary {
  session_id: string;
  average_score: number;
  total_questions: number;
  followups_count: number;
  strengths: string[];
  weaknesses: string[];
  recommendations: string[];
}

export interface SocketEvents {
  connected: { message: string };
  session_started: StartSessionResponse;
  bot_typing: { session_id: string };
  analysis: { session_id: string; analysis: Analysis };
  feedback: { session_id: string; feedback: string };
  followup_question: { session_id: string; question: Question };
  next_question: { session_id: string; question: Question };
  interview_summary: { session_id: string; summary: string };
  error: { message: string };
}
