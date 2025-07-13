'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import CloudTaskExecutor from '@/components/ui/sandbox';
import ReactMarkdown from 'react-markdown';

type Status = 'idle' | 'running' | 'complete' | 'error';

export default function Home() {
  const [prompt, setPrompt] = useState('');
  const [status, setStatus] = useState<Status>('idle');
  const [shouldRunSandbox, setShouldRunSandbox] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const [hasStarted, setHasStarted] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim() || status === 'running') return;

    // Start execution
    setHasStarted(true);
    setShouldRunSandbox(false);
    setTimeout(() => setShouldRunSandbox(true), 100);
  };

  const handleSandboxStatusChange = (newStatus: Status) => {
    setStatus(newStatus);
  };

  const getStatusColor = (status: Status) => {
    switch (status) {
      case 'idle': return 'bg-gray-100 text-gray-800';
      case 'running': return 'bg-blue-100 text-blue-800';
      case 'complete': return 'bg-green-100 text-green-800';
      case 'error': return 'bg-red-100 text-red-800';
    }
  };

  const resetSession = () => {
    setPrompt('');
    setStatus('idle');
    setShouldRunSandbox(false);
    setHasStarted(false);
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
          
          {/* Status Badge */}
          <div className="mt-4">
            <Badge className={`${getStatusColor(status)} px-3 py-1 text-sm font-medium`}>
              {status === 'idle' && 'Ready'}
              {status === 'running' && 'AI Crew Working...'}
              {status === 'complete' && 'Task Complete'}
              {status === 'error' && 'Error Occurred'}
            </Badge>
          </div>
        </div>

        {/* Prompt Input Section */}
        <Card className="border-0 shadow-lg bg-white/80 backdrop-blur-sm max-w-2xl mx-auto">
          <div className="bg-gradient-to-r from-blue-500 to-purple-500 text-white p-6">
            <CardTitle className="text-lg font-medium flex items-center justify-between">
              Create Task
              {status !== 'idle' && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={resetSession}
                  className="text-white border-white hover:bg-white hover:text-purple-600"
                >
                  New Task
                </Button>
              )}
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
                  disabled={status === 'running'}
                />
              </div>
              
              <Button
                type="submit"
                disabled={!prompt.trim() || status === 'running'}
                className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white shadow-lg hover:shadow-xl transition-all duration-200"
                size="lg"
              >
                {status === 'running' ? (
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

        {/* Info section when no prompt */}
        {!prompt && (
          <div className="mt-8 text-center text-gray-600">
            <p className="text-lg">Enter a task above to get started with your AI crew</p>
          </div>

          {/* Sandbox/Execution Section */}
          <div>
            <Card className="border-0 shadow-lg bg-white/80 backdrop-blur-sm h-full">
              <CardHeader className="pb-3">
                <CardTitle className="text-lg font-medium text-gray-800">
                  Live Execution
                </CardTitle>
              </CardHeader>
              <CardContent className="p-6 pt-0">
                {hasStarted ? (
                  <CloudTaskExecutor
                    prompt={prompt}
                    shouldRun={shouldRunSandbox}
                    onStatusChange={handleSandboxStatusChange}
                    onResult={(finalResult) => setResult(finalResult)}
                    onClose={() => {}}
                  />
                ) : (
                  <div className="h-64 flex items-center justify-center text-gray-500">
                    <p>Start a task to see the execution here...</p>
                  </div>
                )}

                {/*This is the new section to display the result*/}
                {result && (
                  <>
                    <Separator className="my-4" />
                    <div>
                      <h3 className="text-sm font-medium text-gray-700 mb-2">Final Result:</h3>
                      <div className="bg-green-50 border border-green-200 rounded-lg p-4 max-h-64 overflow-y-auto">
                        <div className="text-sm text-green-800 prose prose-sm max-w-none">
                          <ReactMarkdown>{result}</ReactMarkdown>
                        </div>
                      </div>
                    </div>
                  </>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
