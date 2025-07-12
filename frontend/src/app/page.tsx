'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';

export default function Home() {
  const [prompt, setPrompt] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim()) return;

    setIsSubmitting(true);
    
    // TODO: Add API call to backend here
    console.log('Submitting prompt:', prompt);
    
    // Simulate API call
    setTimeout(() => {
      setIsSubmitting(false);
      setPrompt('');
    }, 1000);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50">
      <div className="max-w-6xl mx-auto p-6">
        {/* Header */}
        <div className="text-center mb-8 pt-8">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 via-purple-600 to-indigo-600 bg-clip-text text-transparent mb-2">
            Agentable
          </h1>
          <p className="text-gray-600 text-lg">
            Your AI crew manager
          </p>
        </div>

        {/* Prompt Input Section */}
        <div className="max-w-4xl mx-auto">
          <Card className="border-0 shadow-lg bg-white/80 backdrop-blur-sm">
            <div className="bg-gradient-to-r from-blue-500 to-purple-500 text-white p-6">
              <CardTitle className="text-lg font-medium">
                Create Task
              </CardTitle>
            </div>
            <CardContent className="p-6">
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="prompt" className="text-sm font-medium text-gray-700">
                    Describe what you need
                  </Label>
                  <Textarea
                    id="prompt"
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value)}
                    placeholder="What would you like your AI crew to help you with?"
                    className="min-h-[120px] resize-none border-gray-300 focus:border-purple-500 focus:ring-purple-500 bg-white/50"
                    disabled={isSubmitting}
                  />
                </div>
                
                <Button
                  type="submit"
                  disabled={!prompt.trim() || isSubmitting}
                  className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white shadow-lg hover:shadow-xl transition-all duration-200"
                  size="lg"
                >
                  {isSubmitting ? (
                    <div className="flex items-center gap-2">
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                      Creating crew...
                    </div>
                  ) : (
                    'Create AI Crew'
                  )}
                </Button>
              </form>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
