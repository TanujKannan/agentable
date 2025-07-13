import React from 'react';
import ReactMarkdown from 'react-markdown';

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

export const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({ content, className }) => {
  // Convert URLs to markdown format if they're not already
  const preprocessContent = (text: string): string => {
    // First, handle existing markdown links and images
    if (text.includes('![') || text.includes('[')) {
      return text;
    }
    
    // Convert standalone URLs to markdown format
    const urlRegex = /(https?:\/\/[^\s]+)/g;
    
    return text.replace(urlRegex, (url) => {
      // Check if it's likely an image URL
      if (url.match(/\.(jpg|jpeg|png|gif|webp|svg)(\?.*)?$/i)) {
        return `![Generated Image](${url})`;
      }
      // Otherwise, create a clickable link
      return `[${url}](${url})`;
    });
  };

  const processedContent = preprocessContent(content);

  return (
    <div className={`max-w-none ${className}`}>
      <ReactMarkdown
        components={{
          // Custom link renderer with target="_blank"
          a: ({ href, children, ...props }) => (
            <a
              href={href}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:text-blue-800 underline"
              {...props}
            >
              {children}
            </a>
          ),
          // Custom image renderer with styling
          img: ({ src, alt, ...props }) => (
            <img
              src={src}
              alt={alt}
              className="rounded-lg shadow-sm max-w-full h-auto border border-gray-200"
              {...props}
            />
          ),
          // Custom paragraph styling
          p: ({ children, ...props }) => (
            <p className="mb-2 leading-relaxed" {...props}>
              {children}
            </p>
          ),
          // Custom heading styling
          h1: ({ children, ...props }) => (
            <h1 className="text-lg font-semibold mb-2" {...props}>
              {children}
            </h1>
          ),
          h2: ({ children, ...props }) => (
            <h2 className="text-md font-semibold mb-2" {...props}>
              {children}
            </h2>
          ),
          h3: ({ children, ...props }) => (
            <h3 className="text-sm font-semibold mb-1" {...props}>
              {children}
            </h3>
          ),
          // Custom code styling
          code: ({ children, ...props }) => (
            <code className="bg-gray-100 px-1 py-0.5 rounded text-sm font-mono" {...props}>
              {children}
            </code>
          ),
          // Custom blockquote styling
          blockquote: ({ children, ...props }) => (
            <blockquote className="border-l-4 border-gray-300 pl-4 italic" {...props}>
              {children}
            </blockquote>
          ),
        }}
      >
        {processedContent}
      </ReactMarkdown>
    </div>
  );
}; 