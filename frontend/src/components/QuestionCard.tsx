import { useState } from 'react';
import { Question } from '../types/api';

interface QuestionCardProps {
  question: Question;
}

// Mock key concepts for demonstration - in a real app, this would come from the API
const getKeyConcepts = (difficulty: string, questionText: string): string[] => {
  // Simple heuristics to suggest key concepts based on question content
  const concepts: string[] = [];
  const lowerQuestion = questionText.toLowerCase();
  
  if (lowerQuestion.includes('array') || lowerQuestion.includes('list')) {
    concepts.push('Arrays');
  }
  if (lowerQuestion.includes('tree') || lowerQuestion.includes('node')) {
    concepts.push('Trees', 'Recursion');
  }
  if (lowerQuestion.includes('graph') || lowerQuestion.includes('vertex')) {
    concepts.push('Graphs', 'BFS/DFS');
  }
  if (lowerQuestion.includes('sort') || lowerQuestion.includes('order')) {
    concepts.push('Sorting');
  }
  if (lowerQuestion.includes('search') || lowerQuestion.includes('find')) {
    concepts.push('Search Algorithms');
  }
  if (lowerQuestion.includes('dynamic') || lowerQuestion.includes('optimal')) {
    concepts.push('Dynamic Programming');
  }
  if (lowerQuestion.includes('hash') || lowerQuestion.includes('map')) {
    concepts.push('Hash Tables');
  }
  
  // Add complexity analysis for all questions
  concepts.push('Time Complexity', 'Space Complexity');
  
  // Add difficulty-specific concepts
  if (difficulty.toLowerCase() === 'hard') {
    concepts.push('Advanced Algorithms');
  } else if (difficulty.toLowerCase() === 'medium') {
    concepts.push('Algorithm Design');
  }
  
  return [...new Set(concepts)]; // Remove duplicates
};

export function QuestionCard({ question }: QuestionCardProps) {
  const [showConcepts, setShowConcepts] = useState(false);
  
  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty.toLowerCase()) {
      case 'easy':
        return {
          bg: 'bg-success-100',
          text: 'text-success-800',
          border: 'border-success-200',
          icon: '🟢'
        };
      case 'medium':
        return {
          bg: 'bg-warning-100',
          text: 'text-warning-800',
          border: 'border-warning-200',
          icon: '🟡'
        };
      case 'hard':
        return {
          bg: 'bg-danger-100',
          text: 'text-danger-800',
          border: 'border-danger-200',
          icon: '🔴'
        };
      default:
        return {
          bg: 'bg-gray-100',
          text: 'text-gray-800',
          border: 'border-gray-200',
          icon: '⚪'
        };
    }
  };

  const difficultyStyle = getDifficultyColor(question.difficulty);
  const keyConcepts = getKeyConcepts(question.difficulty, question.question);

  return (
    <div className="card h-full flex flex-col">
      {/* Compact Header */}
      <div className="p-3 border-b border-gray-100 flex-shrink-0">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <span className="text-lg">❓</span>
            <h3 className="font-semibold text-gray-800 text-sm">Question #{question.id}</h3>
          </div>
          <span
            className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${difficultyStyle.bg} ${difficultyStyle.text} ${difficultyStyle.border} border`}
          >
            <span className="mr-1">{difficultyStyle.icon}</span>
            {question.difficulty.toUpperCase()}
          </span>
        </div>
      </div>

      {/* Metadata Row - Compact */}
      <div className="px-3 py-2 bg-gray-50 border-b border-gray-100 flex-shrink-0">
        <div className="flex items-center justify-between text-xs">
          <span className="text-gray-500">DSA Interview</span>
          <button
            onClick={() => setShowConcepts(!showConcepts)}
            className="flex items-center space-x-1 text-primary-600 hover:text-primary-700 font-medium transition-colors"
            aria-expanded={showConcepts}
          >
            <span>Key Concepts</span>
            <svg
              className={`w-3 h-3 transition-transform ${showConcepts ? 'rotate-180' : ''}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
        </div>
      </div>

      {/* Key Concepts (Collapsible) */}
      {showConcepts && (
        <div className="px-3 py-2 bg-primary-50 border-b border-primary-100 animate-fade-in flex-shrink-0">
          <div className="flex flex-wrap gap-1">
            {keyConcepts.map((concept, index) => (
              <span
                key={index}
                className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-white text-primary-700 border border-primary-200"
              >
                {concept}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Question Content - Main */}
      <div className="flex-1 p-4 flex items-center justify-center">
        <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl p-4 border-2 border-primary-200 shadow-sm w-full">
          <div className="prose max-w-none">
            <p className="text-gray-900 leading-relaxed font-semibold text-base mb-0">
              {question.question}
            </p>
          </div>
        </div>
      </div>

      {/* Tips Section - Compact */}
      <div className="px-3 pb-3 flex-shrink-0">
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-2 border border-blue-200">
          <div className="text-xs">
            <div className="font-medium text-blue-800 mb-1">💡 Tips</div>
            <div className="text-blue-700 space-y-0.5">
              <div>• Think aloud & explain your approach</div>
              <div>• Consider time & space complexity</div>
              <div>• Discuss edge cases & trade-offs</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}