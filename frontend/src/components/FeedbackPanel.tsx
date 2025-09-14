import React, { useState } from 'react';
import { Analysis } from '../types/api';

interface FeedbackPanelProps {
  analysis: Analysis;
}

interface ConceptSuggestion {
  concept: string;
  suggestion: string;
}

// Simple mapping for practice suggestions
const getPracticeSuggestions = (missingConcepts: string[]): ConceptSuggestion[] => {
  const suggestionMap: Record<string, string> = {
    'time complexity': 'Review Big-O notation and analyze algorithm efficiency',
    'space complexity': 'Practice memory optimization and space-time tradeoffs',
    'binary search': 'Practice binary search problems and variants',
    'dynamic programming': 'Work through classic DP problems (fibonacci, coin change)',
    'recursion': 'Practice recursive thinking and base case identification',
    'data structures': 'Review arrays, linked lists, trees, and hash tables',
    'sorting': 'Study different sorting algorithms and their properties',
    'graph algorithms': 'Practice BFS, DFS, and pathfinding algorithms',
    'tree traversal': 'Master inorder, preorder, and postorder traversals',
    'hash tables': 'Practice hash-based solutions and collision handling',
  };

  return missingConcepts
    .slice(0, 3) // Limit to top 3 suggestions
    .map(concept => ({
      concept: concept.toLowerCase(),
      suggestion: suggestionMap[concept.toLowerCase()] || `Review and practice ${concept} fundamentals`
    }));
};


function CollapsibleSection({ title, children, defaultOpen = false, icon }: {
  title: string;
  children: React.ReactNode;
  defaultOpen?: boolean;
  icon: string;
}) {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-4 py-3 bg-gray-50 hover:bg-gray-100 flex items-center justify-between text-left transition-colors"
        aria-expanded={isOpen}
      >
        <div className="flex items-center space-x-2">
          <span className="text-lg">{icon}</span>
          <span className="font-medium text-gray-800">{title}</span>
        </div>
        <svg
          className={`w-5 h-5 text-gray-500 transition-transform ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      {isOpen && (
        <div className="p-4 bg-white animate-fade-in">
          {children}
        </div>
      )}
    </div>
  );
}

function getScoreColor(score: number) {
  if (score >= 8) return 'from-success-500 to-success-600';
  if (score >= 6) return 'from-warning-500 to-warning-600';
  return 'from-danger-500 to-danger-600';
}

function getScoreText(score: number) {
  if (score >= 8) return 'Excellent';
  if (score >= 6) return 'Good';
  if (score >= 4) return 'Fair';
  return 'Needs Improvement';
}

export function FeedbackPanel({ analysis }: FeedbackPanelProps) {
  const practiceSuggestions = getPracticeSuggestions(analysis.missing_concepts);

  return (
    <div className="space-y-3">
      {/* Compact Score Display */}
      <div className="flex items-center justify-center">
        <div className={`w-12 h-12 rounded-full bg-gradient-to-br ${getScoreColor(analysis.score)} flex items-center justify-center shadow-sm`}>
          <div className="text-center">
            <div className="text-lg font-bold text-white">{analysis.score}</div>
            <div className="text-xs text-white/80">/ 10</div>
          </div>
        </div>
        <div className="ml-3 text-center">
          <div className="text-sm font-semibold text-gray-800">{getScoreText(analysis.score)}</div>
          <div className="text-xs text-gray-500">Score</div>
        </div>
      </div>

      {/* Compact Overview */}
      <div className="grid grid-cols-2 gap-2">
        <div className="bg-success-50 border border-success-200 rounded-lg p-2 text-center">
          <div className="text-lg font-bold text-success-800">{analysis.concepts_covered.length}</div>
          <div className="text-xs text-success-600">Covered</div>
        </div>
        <div className="bg-danger-50 border border-danger-200 rounded-lg p-2 text-center">
          <div className="text-lg font-bold text-danger-800">{analysis.missing_concepts.length}</div>
          <div className="text-xs text-danger-600">Missing</div>
        </div>
      </div>

      {/* Compact Concepts */}
      {(analysis.concepts_covered.length > 0 || analysis.missing_concepts.length > 0) && (
        <div className="bg-gray-50 rounded-lg p-3 border border-gray-200">
          {analysis.concepts_covered.length > 0 && (
            <div className="mb-2">
              <div className="text-xs font-medium text-success-800 mb-1">✅ Covered</div>
              <div className="flex flex-wrap gap-1">
                {analysis.concepts_covered.map((concept, index) => (
                  <span
                    key={index}
                    className="inline-flex items-center px-2 py-0.5 rounded-full text-xs bg-success-100 text-success-800 border border-success-200"
                  >
                    {concept}
                  </span>
                ))}
              </div>
            </div>
          )}
          
          {analysis.missing_concepts.length > 0 && (
            <div>
              <div className="text-xs font-medium text-danger-800 mb-1">❌ Missing</div>
              <div className="flex flex-wrap gap-1">
                {analysis.missing_concepts.map((concept, index) => (
                  <span
                    key={index}
                    className="inline-flex items-center px-2 py-0.5 rounded-full text-xs bg-danger-100 text-danger-800 border border-danger-200"
                  >
                    {concept}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Compact Practice Suggestions */}
      {practiceSuggestions.length > 0 && (
        <div className="bg-primary-50 rounded-lg p-3 border border-primary-200">
          <div className="flex items-center space-x-1 mb-2">
            <span className="text-primary-500">💡</span>
            <h4 className="text-xs font-medium text-primary-800">Practice Next</h4>
          </div>
          <div className="space-y-1">
            {practiceSuggestions.map((item, index) => (
              <div key={index} className="text-xs text-primary-700">
                • <span className="font-medium capitalize">{item.concept}:</span> {item.suggestion}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Compact Quality Metrics */}
      <div className="grid grid-cols-2 gap-2">
        <div className="text-center p-2 bg-gray-50 rounded border">
          <div className="text-sm font-semibold text-gray-800 capitalize">{analysis.quality}</div>
          <div className="text-xs text-gray-600">Quality</div>
        </div>
        <div className="text-center p-2 bg-gray-50 rounded border">
          <div className="text-sm font-semibold text-gray-800 capitalize">{analysis.depth}</div>
          <div className="text-xs text-gray-600">Depth</div>
        </div>
      </div>

      {/* Collapsible Detailed Analysis */}
      {analysis.detailed_analysis && (
        <CollapsibleSection title="Detailed Analysis" icon="🔍" defaultOpen={false}>
          <div className="prose prose-sm max-w-none">
            <p className="text-gray-700 text-sm leading-relaxed whitespace-pre-wrap">
              {analysis.detailed_analysis}
            </p>
          </div>
        </CollapsibleSection>
      )}
    </div>
  );
}