import { useState } from 'react';
import { apiService } from '../services/api';

interface SummaryPageProps {
  summary: string;
  sessionId: string;
  onRestart: () => void;
}

interface StatCardProps {
  icon: string;
  label: string;
  value: string | number;
  color: 'primary' | 'success' | 'warning' | 'accent';
}

function StatCard({ icon, label, value, color }: StatCardProps) {
  const getColorClasses = (color: string) => {
    switch (color) {
      case 'success':
        return 'from-success-500 to-success-600';
      case 'warning':
        return 'from-warning-500 to-warning-600';
      case 'accent':
        return 'from-accent-500 to-accent-600';
      default:
        return 'from-primary-500 to-primary-600';
    }
  };

  return (
    <div className="card p-6 text-center">
      <div className={`w-12 h-12 mx-auto mb-3 rounded-full bg-gradient-to-br ${getColorClasses(color)} flex items-center justify-center`}>
        <span className="text-xl text-white">{icon}</span>
      </div>
      <div className="text-2xl font-bold text-gray-800">{value}</div>
      <div className="text-sm text-gray-600">{label}</div>
    </div>
  );
}

export function SummaryPage({ summary, sessionId, onRestart }: SummaryPageProps) {
  const [copyStatus, setCopyStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [isDownloading, setIsDownloading] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(summary);
      setCopyStatus('success');
      setTimeout(() => setCopyStatus('idle'), 3000);
    } catch (error) {
      console.error('Failed to copy:', error);
      setCopyStatus('error');
      setTimeout(() => setCopyStatus('idle'), 3000);
    }
  };

  const handleDownload = async () => {
    setIsDownloading(true);
    try {
      console.log('Starting download for session:', sessionId);
      const data = await apiService.exportSession(sessionId);
      console.log('Data received successfully:', data);
      
      const blob = new Blob([JSON.stringify(data, null, 2)], {
        type: 'application/json',
      });
      
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `interview-session-${sessionId}.json`;
      a.style.display = 'none';
      
      document.body.appendChild(a);
      a.click();
      
      // Clean up
      setTimeout(() => {
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      }, 100);
      
    } catch (error: any) {
      console.error('Failed to download session data:', error);
      
      // Provide more specific error messages and solutions
      let errorMessage = 'Unknown error';
      let showFallback = false;
      
      if (error.code === 'ERR_BLOCKED_BY_CLIENT') {
        errorMessage = 'Request blocked by browser extension or ad blocker.';
        showFallback = true;
      } else if (error.code === 'ERR_NETWORK') {
        errorMessage = 'Network error. Please check your connection and try again.';
      } else if (error.response) {
        errorMessage = `Server error: ${error.response.status} - ${error.response.data?.message || 'Unknown server error'}`;
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      if (showFallback) {
        const userChoice = confirm(
          `${errorMessage}\n\n` +
          'This is likely caused by an ad blocker or browser extension.\n\n' +
          'Would you like to try a fallback download method?\n\n' +
          'If this continues to fail, please:\n' +
          '1. Disable ad blockers for this site\n' +
          '2. Try in an incognito/private window\n' +
          '3. Try a different browser'
        );
        
        if (userChoice) {
          // Fallback: Create a simple text download with the summary
          const fallbackData = {
            session_id: sessionId,
            summary: summary,
            timestamp: new Date().toISOString(),
            note: 'This is a fallback download due to API access issues'
          };
          
          const blob = new Blob([JSON.stringify(fallbackData, null, 2)], {
            type: 'application/json',
          });
          
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `interview-session-fallback-${sessionId}.json`;
          a.style.display = 'none';
          
          document.body.appendChild(a);
          a.click();
          
          setTimeout(() => {
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
          }, 100);
        }
      } else {
        alert(`Download failed: ${errorMessage}`);
      }
    } finally {
      setIsDownloading(false);
    }
  };

  // Extract basic stats from summary (simple parsing)
  const getBasicStats = () => {
    // This is a simplified approach - in a real app, the backend would provide structured data
    const lines = summary.split('\n');
    let avgScore = 'N/A';
    let questionsCount = '5';  // Default from the interview flow
    let followupsCount = 'N/A';
    
    for (const line of lines) {
      if (line.toLowerCase().includes('average') || line.toLowerCase().includes('score')) {
        const scoreMatch = line.match(/(\d+\.?\d*)/);
        if (scoreMatch) {
          avgScore = parseFloat(scoreMatch[1]).toFixed(1);
        }
      }
      if (line.toLowerCase().includes('follow') && line.toLowerCase().includes('question')) {
        const followupMatch = line.match(/(\d+)/);
        if (followupMatch) {
          followupsCount = followupMatch[1];
        }
      }
    }
    
    return { avgScore, questionsCount, followupsCount };
  };

  const stats = getBasicStats();

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      <div className="container mx-auto px-4 py-12">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="text-center mb-12 animate-fade-in">
            <div className="w-20 h-20 mx-auto mb-6 bg-gradient-to-br from-success-500 to-primary-500 rounded-full flex items-center justify-center shadow-lg">
              <span className="text-3xl text-white">🎉</span>
            </div>
            <h1 className="text-4xl font-bold text-gray-800 mb-4">
              Interview Complete!
            </h1>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Great job! You've successfully completed your DSA interview. 
              Here's your comprehensive performance summary.
            </p>
          </div>

          {/* Stats Overview */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8 animate-fade-in">
            <StatCard 
              icon="🎯" 
              label="Average Score" 
              value={stats.avgScore}
              color="primary"
            />
            <StatCard 
              icon="📝" 
              label="Questions Answered" 
              value={stats.questionsCount}
              color="success"
            />
            <StatCard 
              icon="💬" 
              label="Follow-ups" 
              value={stats.followupsCount}
              color="accent"
            />
          </div>
          
          {/* Main Summary */}
          <div className="card p-8 mb-8 animate-fade-in">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-semibold text-gray-800">
                📊 Performance Summary
              </h2>
              <button
                onClick={handleCopy}
                className={`btn px-4 py-2 text-sm transition-all ${
                  copyStatus === 'success' 
                    ? 'btn-success' 
                    : copyStatus === 'error' 
                    ? 'btn-danger' 
                    : 'btn-secondary'
                }`}
                disabled={copyStatus !== 'idle'}
                aria-label="Copy summary to clipboard"
              >
                {copyStatus === 'success' ? (
                  <>
                    <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    Copied!
                  </>
                ) : copyStatus === 'error' ? (
                  <>
                    <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                    Failed
                  </>
                ) : (
                  <>
                    <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                    </svg>
                    Copy
                  </>
                )}
              </button>
            </div>
            
            <div className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-xl p-6 border border-gray-200">
              <div className="prose prose-gray max-w-none">
                <div className="whitespace-pre-wrap text-gray-700 leading-relaxed font-mono text-sm">
                  {summary}
                </div>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row justify-center gap-4 animate-fade-in">
            <button
              onClick={handleDownload}
              disabled={isDownloading}
              className="btn btn-success px-8 py-4 text-lg font-semibold"
              aria-label="Download complete session data"
            >
              {isDownloading ? (
                <>
                  <svg className="w-5 h-5 mr-3 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  Preparing Download...
                </>
              ) : (
                <>
                  <svg className="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  📄 Download Session Data
                </>
              )}
            </button>
            
            <a
              href={`http://localhost:8000/api/session/${sessionId}/export`}
              target="_blank"
              rel="noopener noreferrer"
              className="btn btn-secondary px-8 py-4 text-lg font-semibold"
              aria-label="Open session data in new tab"
            >
              <svg className="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
              </svg>
              🔗 Open Session Data in New Tab
            </a>
            
            <button
              onClick={onRestart}
              className="btn btn-primary px-8 py-4 text-lg font-semibold"
              aria-label="Start a new interview session"
            >
              <svg className="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              🚀 Start New Interview
            </button>
          </div>

          {/* Footer */}
          <div className="text-center mt-12 text-gray-500">
            <p className="text-sm">
              Thank you for using DSA Interview Assistant! 
              Keep practicing and improving your skills. 💪
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}