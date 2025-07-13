'use client';

import { useState } from 'react';
import { Send } from 'lucide-react';

interface LandingChatInputProps {
  onSubmit: (message: string) => void;
  isLoading?: boolean;
}

export default function LandingChatInput({ onSubmit, isLoading }: LandingChatInputProps) {
  const [message, setMessage] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim() && !isLoading) {
      onSubmit(message);
      setMessage('');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="w-full">
      <div className="relative">
        <textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Describe what you'd like to build or automate..."
          className="w-full resize-none rounded-xl border border-gray-300 p-4 pr-12 text-[#2C3E50] placeholder-gray-500 focus:border-[#1F3A93] focus:outline-none focus:ring-2 focus:ring-[#1F3A93]/20 transition-all duration-200"
          rows={3}
          disabled={isLoading}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              handleSubmit(e);
            }
          }}
        />
        <button
          type="submit"
          disabled={!message.trim() || isLoading}
          className="absolute right-3 bottom-3 flex h-10 w-10 items-center justify-center rounded-lg bg-[#17A589] text-white transition-all duration-200 hover:bg-[#17A589]/90 disabled:bg-gray-300 disabled:cursor-not-allowed"
        >
          {isLoading ? (
            <div className="h-5 w-5 animate-spin rounded-full border-2 border-white border-t-transparent"></div>
          ) : (
            <Send className="h-5 w-5" />
          )}
        </button>
      </div>
    </form>
  );
}