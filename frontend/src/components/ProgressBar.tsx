import { useState } from 'react';

interface ProgressBarProps {
  current: number;
  total: number;
}

interface StepTooltipProps {
  step: number;
  isActive: boolean;
  isCompleted: boolean;
  position: 'left' | 'center' | 'right';
}

function StepTooltip({ step, isActive, isCompleted, position }: StepTooltipProps) {
  const getDifficulty = (step: number) => {
    // Mock difficulty assignment - in real app, this would come from the backend
    const difficulties = ['Easy', 'Medium', 'Easy', 'Hard', 'Medium'];
    return difficulties[step - 1] || 'Medium';
  };

  const getStatus = () => {
    if (isCompleted) return 'Completed';
    if (isActive) return 'In Progress';
    return 'Upcoming';
  };

  const getPositionClasses = () => {
    switch (position) {
      case 'left':
        return 'left-0';
      case 'right':
        return 'right-0';
      default:
        return 'left-1/2 -translate-x-1/2';
    }
  };

  return (
    <div className={`absolute -top-20 ${getPositionClasses()} z-10 opacity-0 group-hover:opacity-100 transition-all duration-200 pointer-events-none`}>
      <div className="bg-gray-900 text-white text-xs rounded-lg px-3 py-2 shadow-lg border border-gray-700 min-w-max">
        <div className="font-medium">Question {step}</div>
        <div className="text-gray-300">{getDifficulty(step)} • {getStatus()}</div>
        
        {/* Arrow */}
        <div className="absolute top-full left-1/2 -translate-x-1/2">
          <div className="border-4 border-transparent border-t-gray-900"></div>
        </div>
      </div>
    </div>
  );
}

export function ProgressBar({ current, total }: ProgressBarProps) {
  const [hoveredStep, setHoveredStep] = useState<number | null>(null);
  const percentage = Math.max(0, Math.min((current / total) * 100, 100));
  
  // Optional: Use hoveredStep for future enhancements
  console.debug('Hovered step:', hoveredStep);



  return (
    <div className="card p-4">
      {/* Compact Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-2">
          <span className="text-lg">📊</span>
          <h3 className="font-semibold text-gray-800">Progress</h3>
          <span className="text-sm text-gray-600">Question {current + 1} of {total}</span>
        </div>
        <div className="text-right">
          <div className="text-lg font-bold text-primary-600">{Math.round(percentage)}%</div>
        </div>
      </div>
      
      {/* Main Progress Bar */}
      <div className="relative mb-4">
        <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden shadow-inner">
          <div
            className="bg-gradient-to-r from-primary-500 via-accent-500 to-success-500 h-3 rounded-full transition-all duration-1000 ease-out shadow-sm"
            style={{ width: `${percentage}%` }}
          ></div>
        </div>
        
        {/* Percentage Label */}
        <div 
          className="absolute top-0 h-3 flex items-center transition-all duration-1000 ease-out"
          style={{ left: `${Math.max(percentage - 5, 5)}%` }}
        >
          <div className="bg-white text-primary-600 px-2 py-0.5 rounded text-xs font-bold shadow-md border transform -translate-y-8">
            {Math.round(percentage)}%
          </div>
        </div>
      </div>
      
      {/* Step Indicators */}
      <div className="flex justify-between items-center relative mb-2">
        {Array.from({ length: total }, (_, i) => {
          const step = i + 1;
          const position = i === 0 ? 'left' : i === total - 1 ? 'right' : 'center';
          
          return (
            <div
              key={i}
              className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold transition-all duration-300 border-2 relative group cursor-pointer ${
                step <= current
                  ? 'bg-success-500 text-white border-success-400 shadow-sm'
                  : step === current + 1
                  ? 'bg-primary-500 text-white border-primary-400 shadow-sm animate-pulse'
                  : 'bg-gray-100 text-gray-500 border-gray-300 hover:bg-gray-200'
              }`}
              onMouseEnter={() => setHoveredStep(step)}
              onMouseLeave={() => setHoveredStep(null)}
            >
              {step <= current ? (
                <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
              ) : step === current + 1 ? (
                <span className="text-xs font-bold">{step}</span>
              ) : (
                <span className="text-xs">{step}</span>
              )}
              
              {/* Tooltip */}
              <StepTooltip 
                step={step}
                isActive={step === current + 1}
                isCompleted={step <= current}
                position={position}
              />
            </div>
          );
        })}
      </div>
    </div>
  );
}