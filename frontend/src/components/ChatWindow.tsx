import { useState, useRef, useEffect } from 'react';
import { Message } from './Message';
import { Analysis, Question } from '../types/api';

interface ChatWindowProps {
  onSendMessage: (message: string) => void;
  currentQuestion: Question | null;
  analysis: Analysis | null;
  feedback: string;
  isTyping: boolean;
  onContinue: () => void;
  questionsAnswered: number;
  totalQuestions: number;
}

type ChatMessage = {
  type: 'bot' | 'user' | 'analysis' | 'continue-prompt';
  content: string;
  timestamp: Date;
  analysis?: Analysis;
  questionData?: Question;
};

function AnalysisMessage({ msg }: { msg: ChatMessage }) {
  const [showDetailedAnalysis, setShowDetailedAnalysis] = useState(false);

  if (!msg.analysis) return null;

  return (
    <div className="flex justify-start mb-6 animate-fade-in">
      <div className="flex items-start space-x-3 max-w-[90%]">
        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary-500 to-accent-600 flex items-center justify-center text-white text-sm font-bold flex-shrink-0">
          AI
        </div>
        <div className="bg-white border border-gray-200 rounded-2xl rounded-bl-md shadow-soft p-6">
          <div className="mb-4">
            <div className="flex items-center space-x-2 mb-4">
              <span className="text-lg">📊</span>
              <span className="font-semibold text-gray-800">Performance Analysis</span>
            </div>
            
            <div className="space-y-4">
              {/* Score Display */}
              <div className="flex items-center justify-center p-4 bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg">
                <div className={`w-16 h-16 rounded-full bg-gradient-to-br ${
                  msg.analysis.score >= 8 ? 'from-success-500 to-success-600' :
                  msg.analysis.score >= 6 ? 'from-warning-500 to-warning-600' :
                  'from-danger-500 to-danger-600'
                } flex items-center justify-center shadow-lg`}>
                  <div className="text-center">
                    <div className="text-xl font-bold text-white">{msg.analysis.score}</div>
                    <div className="text-xs text-white/80">/ 10</div>
                  </div>
                </div>
                <div className="ml-4">
                  <div className="text-lg font-semibold text-gray-800">
                    {msg.analysis.score >= 8 ? 'Excellent!' : 
                     msg.analysis.score >= 6 ? 'Good Work!' : 
                     msg.analysis.score >= 4 ? 'Keep Improving!' : 'Needs Practice'}
                  </div>
                  <div className="text-sm text-gray-600">
                    Quality: <span className="font-medium capitalize">{msg.analysis.quality}</span> • 
                    Depth: <span className="font-medium capitalize">{msg.analysis.depth}</span>
                  </div>
                </div>
              </div>

              {/* Concepts */}
              {(msg.analysis.concepts_covered.length > 0 || msg.analysis.missing_concepts.length > 0) && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {msg.analysis.concepts_covered.length > 0 && (
                    <div className="bg-success-50 rounded-lg p-3 border border-success-200">
                      <div className="font-medium text-success-800 mb-2">✅ Concepts Covered</div>
                      <div className="flex flex-wrap gap-1">
                        {msg.analysis.concepts_covered.map((concept, idx) => (
                          <span key={idx} className="px-2 py-1 bg-success-100 text-success-800 rounded-full text-xs border border-success-200">
                            {concept}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {msg.analysis.missing_concepts.length > 0 && (
                    <div className="bg-danger-50 rounded-lg p-3 border border-danger-200">
                      <div className="font-medium text-danger-800 mb-2">❌ Areas to Improve</div>
                      <div className="flex flex-wrap gap-1">
                        {msg.analysis.missing_concepts.map((concept, idx) => (
                          <span key={idx} className="px-2 py-1 bg-danger-100 text-danger-800 rounded-full text-xs border border-danger-200">
                            {concept}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Collapsible Detailed Analysis */}
              {msg.analysis.detailed_analysis && (
                <div className="border border-gray-200 rounded-lg overflow-hidden">
                  <button
                    onClick={() => setShowDetailedAnalysis(!showDetailedAnalysis)}
                    className="w-full px-4 py-3 bg-gray-50 hover:bg-gray-100 flex items-center justify-between text-left transition-colors"
                    aria-expanded={showDetailedAnalysis}
                  >
                    <div className="flex items-center space-x-2">
                      <span className="text-sm font-medium text-gray-800">🔍 Detailed Feedback</span>
                    </div>
                    <svg
                      className={`w-5 h-5 text-gray-500 transition-transform ${showDetailedAnalysis ? 'rotate-180' : ''}`}
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>
                  {showDetailedAnalysis && (
                    <div className="p-4 bg-white animate-fade-in">
                      <div className="text-sm text-gray-700 whitespace-pre-wrap leading-relaxed">
                        {msg.analysis.detailed_analysis}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
          <div className="text-xs text-gray-400 mt-4">
            Analysis completed at {msg.timestamp.toLocaleTimeString()}
          </div>
        </div>
      </div>
    </div>
  );
}

export function ChatWindow({ 
  onSendMessage, 
  currentQuestion, 
  analysis, 
  feedback, 
  isTyping 
}: Omit<ChatWindowProps, 'onContinue' | 'questionsAnswered' | 'totalQuestions'>) {
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [showUndo, setShowUndo] = useState(false);
  const [lastUserMessage, setLastUserMessage] = useState<string>('');
  const [lastQuestionId, setLastQuestionId] = useState<number | null>(null);
  const [lastQuestionContent, setLastQuestionContent] = useState<string>('');
  const [hasAnalyzed, setHasAnalyzed] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  // Handle new question
  useEffect(() => {
    if (currentQuestion) {
      // Check if this is a new question (different ID) or a follow-up (same ID but different content)
      const isNewQuestion = currentQuestion.id !== lastQuestionId;
      const isFollowUp = currentQuestion.id === lastQuestionId && currentQuestion.question !== lastQuestionContent;
      
      if (isNewQuestion || isFollowUp) {
        setLastQuestionId(currentQuestion.id);
        setLastQuestionContent(currentQuestion.question);
        setHasAnalyzed(false);
        
        // Add question message
        const questionType = isFollowUp ? 'Follow-up Question' : `Question ${currentQuestion.id}`;
        const questionMessage: ChatMessage = {
          type: 'bot',
          content: `📝 **${questionType}** (${currentQuestion.difficulty?.toUpperCase() || 'MEDIUM'})\n\n${currentQuestion.question}\n\n💡 *Take your time to think through the problem. Consider time complexity, space complexity, and edge cases in your answer.*`,
          timestamp: new Date(),
          questionData: currentQuestion
        };
        
        setMessages(prev => [...prev, questionMessage]);
      }
    }
  }, [currentQuestion, lastQuestionId, lastQuestionContent]);

  // Handle feedback
  useEffect(() => {
    if (feedback && !hasAnalyzed) {
      const feedbackMessage: ChatMessage = {
        type: 'bot',
        content: feedback,
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, feedbackMessage]);
    }
  }, [feedback, hasAnalyzed]);

  // Handle analysis
  useEffect(() => {
    if (analysis && !hasAnalyzed) {
      setHasAnalyzed(true);
      
      const analysisMessage: ChatMessage = {
        type: 'analysis',
        content: 'Here\'s your performance analysis:',
        timestamp: new Date(),
        analysis: analysis
      };
      
      setMessages(prev => [...prev, analysisMessage]);
    }
  }, [analysis, hasAnalyzed]);

  const adjustTextareaHeight = () => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 120) + 'px';
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim()) return;

    const newMessage: ChatMessage = {
      type: 'user',
      content: message,
      timestamp: new Date()
    };
    
    setMessages(prev => [...prev, newMessage]);
    setLastUserMessage(message);
    onSendMessage(message);
    setMessage('');
    setShowUndo(true);
    
    // Hide undo after 6 seconds
    setTimeout(() => setShowUndo(false), 6000);
    
    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleUndo = () => {
    if (lastUserMessage) {
      setMessage(lastUserMessage);
      setMessages(prev => prev.slice(0, -1)); // Remove last user message
      setShowUndo(false);
      textareaRef.current?.focus();
      adjustTextareaHeight();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      if (e.shiftKey) {
        // Allow new line
        return;
      } else if (e.ctrlKey || e.metaKey) {
        // Ctrl/Cmd + Enter also sends
        e.preventDefault();
        handleSubmit(e);
      } else {
        // Plain Enter sends
        e.preventDefault();
        handleSubmit(e);
      }
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setMessage(e.target.value);
    adjustTextareaHeight();
  };

  // Add welcome message for first question
  useEffect(() => {
    if (currentQuestion && currentQuestion.id === 1 && messages.length === 0) {
      const welcomeMessage: ChatMessage = {
        type: 'bot',
        content: `👋 **Welcome to your DSA Interview!**\n\nI'll be asking you 5 questions to assess your problem-solving skills. Take your time and explain your thought process.\n\n---\n\n📝 **Question ${currentQuestion.id}** (${currentQuestion.difficulty?.toUpperCase() || 'MEDIUM'})\n\n${currentQuestion.question}\n\n💡 *Consider time complexity, space complexity, and edge cases in your answer.*`,
        timestamp: new Date(),
        questionData: currentQuestion
      };
      
      setMessages([welcomeMessage]);
      setLastQuestionId(currentQuestion.id);
      setLastQuestionContent(currentQuestion.question);
    }
  }, [currentQuestion, messages.length]);

  const renderMessage = (msg: ChatMessage, index: number) => {
    switch (msg.type) {
      case 'analysis':
        return (
          <AnalysisMessage key={index} msg={msg} />
        );
        
        
      default:
        return (
          <div key={index} className="animate-fade-in">
            <Message
              type={msg.type as 'user' | 'bot'}
              content={msg.content}
            />
          </div>
        );
    }
  };

  const characterCount = message.length;
  const characterLimit = 2000;
  const isNearLimit = characterCount > characterLimit * 0.8;

  return (
    <div className="h-full flex flex-col bg-gray-50">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 scrollbar-thin" aria-live="polite" aria-label="Interview conversation">
        {messages.length === 0 && (
          <div className="flex items-center justify-center h-full text-center">
            <div className="max-w-md">
              <div className="w-16 h-16 mx-auto mb-4 bg-gradient-to-br from-blue-100 to-indigo-100 rounded-full flex items-center justify-center">
                <span className="text-2xl">🤖</span>
              </div>
              <div className="text-gray-600 mb-2">Welcome to your DSA Interview!</div>
              <div className="text-sm text-gray-500">Your first question will appear here shortly...</div>
            </div>
      </div>
        )}

        {messages.map(renderMessage)}
        
        {isTyping && (
          <div className="flex items-start space-x-3 animate-fade-in mb-4" aria-live="polite">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary-500 to-accent-600 flex items-center justify-center text-white text-sm font-bold flex-shrink-0">
              AI
            </div>
            <div className="bg-white border border-gray-200 rounded-xl px-4 py-3 shadow-sm">
              <div className="flex items-center space-x-1">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                <div className="ml-2 text-sm text-gray-500">Analyzing your response...</div>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>
      
      {/* Input Area */}
      <form onSubmit={handleSubmit} className="p-4 bg-white border-t border-gray-200 flex-shrink-0">        
        <div className="flex space-x-3">
          <div className="flex-1 relative">
            <textarea
              ref={textareaRef}
              value={message}
              onChange={handleInputChange}
              onKeyDown={handleKeyDown}
              placeholder="Type your answer here... (Enter to send, Shift+Enter for new line)"
              className="textarea min-h-[2.75rem] max-h-[8rem] pr-16"
              aria-label="Your answer"
            />
            
            {/* Character count */}
            <div className={`absolute bottom-2 right-2 text-xs ${
              isNearLimit ? 'text-warning-600' : 'text-gray-400'
            }`}>
              {characterCount}/{characterLimit}
            </div>
        </div>
          
          <div className="flex flex-col space-y-2">
          <button
            type="submit"
              disabled={!message.trim() || characterCount > characterLimit}
              className="btn btn-primary px-4 py-2 text-sm h-11"
              aria-label="Send message"
            >
              <span className="hidden sm:inline mr-1">Send</span>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
            </button>
            
            {showUndo && (
              <button
                type="button"
                onClick={handleUndo}
                className="btn btn-secondary px-3 py-1 text-xs opacity-75 hover:opacity-100"
                aria-label="Edit last message"
              >
                ↶ Edit
          </button>
            )}
          </div>
        </div>
        
        <div className="mt-2 text-xs text-gray-500">
          💡 <kbd className="px-1.5 py-0.5 bg-gray-100 border border-gray-300 rounded text-xs">Enter</kbd> to send, 
          <kbd className="px-1.5 py-0.5 bg-gray-100 border border-gray-300 rounded text-xs ml-1">Shift+Enter</kbd> for new line
        </div>
      </form>
    </div>
  );
}