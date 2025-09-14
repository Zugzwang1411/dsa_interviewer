import { useState, useEffect } from 'react';
import { ChatWindow } from './components/ChatWindow';
import { SummaryPage } from './components/SummaryPage';
import { socketService } from './services/socket';
import { Question, Analysis } from './types/api';

function App() {
  const [sessionId, setSessionId] = useState<string>('');
  const [currentQuestion, setCurrentQuestion] = useState<Question | null>(null);
  const [questionsAnswered, setQuestionsAnswered] = useState(0);
  const [isInterviewComplete, setIsInterviewComplete] = useState(false);
  const [interviewSummary, setInterviewSummary] = useState<string>('');
  const [isConnected, setIsConnected] = useState(false);
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [feedback, setFeedback] = useState<string>('');
  const [isTyping, setIsTyping] = useState(false);

  useEffect(() => {
    const socket = socketService.connect();

    socket.on('connect', () => {
      setIsConnected(true);
    });

    socket.on('disconnect', () => {
      setIsConnected(false);
    });

    socketService.on('session_started', (data) => {
      setSessionId(data.session_id);
      setCurrentQuestion(data.first_question);
      setQuestionsAnswered(1);
    });

    socketService.on('bot_typing', () => {
      setIsTyping(true);
    });

    socketService.on('analysis', (data) => {
      console.log('📊 Received analysis:', data);
      setAnalysis(data.analysis);
      setIsTyping(false);
    });

    socketService.on('feedback', (data) => {
      console.log('💬 Received feedback:', data);
      setFeedback(data.feedback);
    });

    socketService.on('next_question', (data) => {
      console.log('➡️ Received next_question:', data);
      setCurrentQuestion(data.question);
      setQuestionsAnswered(prev => prev + 1);
      setAnalysis(null);
      setFeedback('');
    });

    socketService.on('followup_question', (data) => {
      console.log('🔄 Received followup_question:', data);
      console.log('🔄 Setting currentQuestion to:', data.question);
      setCurrentQuestion(data.question);
      setAnalysis(null);
      setFeedback('');
    });

    socketService.on('interview_summary', (data) => {
      console.log('📋 Received interview_summary:', data);
      setInterviewSummary(data.summary);
      setIsInterviewComplete(true);
    });

    socketService.on('error', (data) => {
      console.error('❌ Socket error:', data.message);
    });

    return () => {
      socketService.disconnect();
    };
  }, []);

  const handleStartInterview = () => {
    socketService.startSession('Candidate');
  };

  const handleSendMessage = (message: string) => {
    if (sessionId) {
      socketService.sendMessage(sessionId, message);
    }
  };


  if (isInterviewComplete) {
    return (
      <SummaryPage 
        summary={interviewSummary}
        sessionId={sessionId}
        onRestart={() => window.location.reload()}
      />
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      {/* Header with connection status */}
      <header className="bg-white/80 backdrop-blur-sm border-b border-gray-200 sticky top-0 z-50">
        <div className="container mx-auto px-4 py-3">
          <div className="flex items-center justify-between">
            <h1 className="text-xl font-semibold text-gray-800">
              DSA Interview Assistant
            </h1>
            <div className="flex items-center space-x-2">
              <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-success-500' : 'bg-danger-500'} animate-pulse`}></div>
              <span className="text-sm font-medium text-gray-600">
                {isConnected ? 'Connected' : 'Disconnected'}
              </span>
            </div>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8">
        <div className="max-w-7xl mx-auto">
          
          {!sessionId ? (
            <div className="flex items-center justify-center min-h-[calc(100vh-12rem)]">
              <div className="card p-8 max-w-md w-full text-center animate-fade-in">
                <div className="w-16 h-16 mx-auto mb-6 bg-gradient-to-br from-primary-500 to-accent-500 rounded-full flex items-center justify-center">
                  <span className="text-2xl text-white font-bold">🚀</span>
                </div>
                <h2 className="text-2xl font-semibold mb-4 text-gray-800">Welcome to Your Interview!</h2>
                <p className="text-gray-600 mb-2">
                  Ready to showcase your Data Structures & Algorithms skills?
                </p>
                <p className="text-sm text-gray-500 mb-6">
                  ⏱️ ~15-20 minutes • 🎯 5 questions • 💡 Interactive feedback
                </p>
                <button
                  onClick={handleStartInterview}
                  disabled={!isConnected}
                  className="btn btn-primary w-full py-3 text-base font-medium"
                >
                  {isConnected ? '🎯 Start Interview' : '⏳ Connecting...'}
                </button>
              </div>
            </div>
          ) : (
            <div className="h-[calc(100vh-5rem)] flex flex-col">
              {/* Minimal Progress Bar */}
              <div className="flex-shrink-0 px-4 py-2 bg-white border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <span className="text-sm font-medium text-gray-600">Question {Math.max(1, questionsAnswered)} of 5</span>
                    <div className="w-32 bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-gradient-to-r from-primary-500 to-accent-500 h-2 rounded-full transition-all duration-500"
                        style={{ width: `${(Math.max(1, questionsAnswered) / 5) * 100}%` }}
                      ></div>
                    </div>
                    <span className="text-xs text-gray-500">{Math.round((Math.max(1, questionsAnswered) / 5) * 100)}%</span>
                  </div>
                  <div className="text-xs text-gray-500">DSA Interview</div>
                </div>
              </div>
              
              {/* Main Chat Interface */}
              <div className="flex-1 min-h-0">
                <ChatWindow
                  onSendMessage={handleSendMessage}
                  currentQuestion={currentQuestion}
                  analysis={analysis}
                  feedback={feedback}
                  isTyping={isTyping}
                />
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;
