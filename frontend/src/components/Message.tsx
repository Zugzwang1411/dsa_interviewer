import { useState } from 'react';

interface MessageProps {
  type: 'user' | 'bot';
  content: string;
}

interface CodeBlockProps {
  code: string;
  language?: string;
}

function CodeBlock({ code, language }: CodeBlockProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  return (
    <div className="relative my-3">
      <div className="bg-gray-900 rounded-lg overflow-hidden">
        {/* Code block header */}
        <div className="flex items-center justify-between px-4 py-2 bg-gray-800 border-b border-gray-700">
          <span className="text-xs font-medium text-gray-300">
            {language || 'code'}
          </span>
          <button
            onClick={handleCopy}
            className="flex items-center space-x-1 px-2 py-1 text-xs bg-gray-700 hover:bg-gray-600 text-gray-200 rounded transition-colors"
            title="Copy to clipboard"
          >
            {copied ? (
              <>
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                <span>Copied!</span>
              </>
            ) : (
              <>
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
                <span>Copy</span>
              </>
            )}
          </button>
        </div>
        {/* Code content */}
        <pre className="p-4 overflow-x-auto text-sm font-mono text-gray-100 leading-relaxed">
          <code>{code}</code>
        </pre>
      </div>
    </div>
  );
}

function formatMessageContent(content: string) {
  // Simple regex to detect code blocks (```...```)
  const codeBlockRegex = /```(\w+)?\n?([\s\S]*?)```/g;
  const parts: Array<{ type: 'text' | 'code'; content: string; language?: string }> = [];
  let lastIndex = 0;
  let match;

  while ((match = codeBlockRegex.exec(content)) !== null) {
    // Add text before the code block
    if (match.index > lastIndex) {
      const textContent = content.slice(lastIndex, match.index);
      if (textContent.trim()) {
        parts.push({ type: 'text', content: textContent });
      }
    }

    // Add the code block
    const language = match[1] || undefined;
    const code = match[2] || '';
    parts.push({ type: 'code', content: code.trim(), language });
    
    lastIndex = match.index + match[0].length;
  }

  // Add any remaining text
  if (lastIndex < content.length) {
    const textContent = content.slice(lastIndex);
    if (textContent.trim()) {
      parts.push({ type: 'text', content: textContent });
    }
  }

  // If no code blocks found, return the whole content as text
  if (parts.length === 0) {
    parts.push({ type: 'text', content });
  }

  return parts;
}

function formatText(text: string): React.ReactNode {
  // Simple markdown formatting: **bold**, *italic*, `code`
  const result: React.ReactNode[] = [];
  let currentIndex = 0;
  
  // Split by lines to handle line breaks
  const lines = text.split('\n');
  
  lines.forEach((line, lineIndex) => {
    if (lineIndex > 0) {
      result.push(<br key={`br-${lineIndex}`} />);
    }
    
    // Process the line for formatting
    const formattedLine = processLineFormatting(line, currentIndex);
    result.push(...formattedLine.content);
    currentIndex = formattedLine.nextIndex;
  });
  
  return result.length > 0 ? result : text;
}

function processLineFormatting(text: string, startIndex: number): { content: React.ReactNode[]; nextIndex: number } {
  const result: React.ReactNode[] = [];
  let currentIndex = startIndex;
  let remainingText = text;
  
  // Process formatting in order of precedence: bold, then italic, then code
  while (remainingText.length > 0) {
    // Try to find the next formatting
    const boldMatch = remainingText.match(/\*\*(.*?)\*\*/);
    const italicMatch = remainingText.match(/(?<!\*)\*([^*]+?)\*(?!\*)/); // Avoid matching parts of bold
    const codeMatch = remainingText.match(/`([^`]+?)`/);
    
    // Find which match comes first
    const matches = [
      { match: boldMatch, type: 'bold' as const, length: boldMatch ? boldMatch[0].length : 0 },
      { match: italicMatch, type: 'italic' as const, length: italicMatch ? italicMatch[0].length : 0 },
      { match: codeMatch, type: 'code' as const, length: codeMatch ? codeMatch[0].length : 0 }
    ].filter(m => m.match).sort((a, b) => a.match!.index! - b.match!.index!);
    
    if (matches.length === 0) {
      // No more formatting, add remaining text
      if (remainingText.trim()) {
        result.push(remainingText);
      }
      break;
    }
    
    const firstMatch = matches[0];
    const match = firstMatch.match!;
    
    // Add text before the match
    if (match.index! > 0) {
      result.push(remainingText.substring(0, match.index!));
    }
    
    // Add the formatted element
    const content = match[1];
    switch (firstMatch.type) {
      case 'bold':
        result.push(<strong key={currentIndex++}>{content}</strong>);
        break;
      case 'italic':
        result.push(<em key={currentIndex++}>{content}</em>);
        break;
      case 'code':
        result.push(<code key={currentIndex++} className="bg-gray-100 px-1 py-0.5 rounded text-sm font-mono">{content}</code>);
        break;
    }
    
    // Move to the text after the match
    remainingText = remainingText.substring(match.index! + match[0].length);
  }
  
  return { content: result, nextIndex: currentIndex };
}

export function Message({ type, content }: MessageProps) {
  const messageParts = formatMessageContent(content);

  return (
    <div className={`flex ${type === 'user' ? 'justify-end' : 'justify-start'} mb-4`}>
      <div className={`flex items-start space-x-3 max-w-[85%] ${type === 'user' ? 'flex-row-reverse space-x-reverse' : ''}`}>
        {/* Avatar */}
        <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white text-sm font-bold flex-shrink-0 ${
          type === 'bot'
            ? 'bg-gradient-to-br from-primary-500 to-accent-600'
            : 'bg-gradient-to-br from-success-500 to-primary-500'
        }`}>
          {type === 'bot' ? 'AI' : 'U'}
        </div>
        
        {/* Message bubble */}
        <div className={`rounded-2xl shadow-soft ${
          type === 'user'
            ? 'bg-gradient-to-br from-primary-500 to-primary-600 text-white rounded-br-md'
            : 'bg-white text-gray-800 border border-gray-200 rounded-bl-md'
        }`}>
          <div className="px-4 py-3">
            {messageParts.map((part, index) => (
              <div key={index}>
                {part.type === 'text' ? (
                  <div className="whitespace-pre-wrap leading-relaxed">
                    {formatText(part.content.trim())}
                  </div>
                ) : (
                  <CodeBlock code={part.content} language={part.language} />
                )}
              </div>
            ))}
          </div>
          
          {/* Message metadata */}
          <div className={`px-4 pb-2 text-xs ${
            type === 'user' ? 'text-primary-100' : 'text-gray-400'
          }`}>
            {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </div>
        </div>
      </div>
    </div>
  );
}