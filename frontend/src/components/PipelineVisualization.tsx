'use client';

import { useEffect, useState } from 'react';
import { Badge } from '@/components/ui/badge';
import { CheckCircle, Clock, Play, AlertCircle } from 'lucide-react';

interface Agent {
  id: number;
  role: string;
  status: 'pending' | 'ready' | 'running' | 'completed' | 'error';
}

interface Task {
  id: number;
  description: string;
  agent_id: number;
  status: 'pending' | 'running' | 'completed' | 'error';
}

interface PipelineData {
  agents: Agent[];
  tasks: Task[];
}

interface PipelineVisualizationProps {
  pipelineData: PipelineData | null;
  agentUpdates: Array<{
    agent_id?: number;
    task_id?: number;
    agent_status?: string;
    task_status?: string;
    pipeline_status?: string;
  }>;
}

export default function PipelineVisualization({ pipelineData, agentUpdates }: PipelineVisualizationProps) {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [pipelineStatus, setPipelineStatus] = useState<'idle' | 'running' | 'completed' | 'error'>('idle');

  // Initialize pipeline data
  useEffect(() => {
    if (pipelineData) {
      setAgents(pipelineData.agents);
      setTasks(pipelineData.tasks);
      setPipelineStatus('idle');
    }
  }, [pipelineData]);

  // Update agent and task statuses based on updates
  useEffect(() => {
    agentUpdates.forEach(update => {
      if (update.pipeline_status) {
        setPipelineStatus(update.pipeline_status as any);
      }
      
      if (update.agent_id !== undefined && update.agent_status) {
        setAgents(prev => prev.map(agent => 
          agent.id === update.agent_id 
            ? { ...agent, status: update.agent_status as any }
            : agent
        ));
      }
      
      if (update.task_id !== undefined && update.task_status) {
        setTasks(prev => prev.map(task => 
          task.id === update.task_id 
            ? { ...task, status: update.task_status as any }
            : task
        ));
      }
    });
  }, [agentUpdates]);

  const getAgentEmoji = (index: number) => {
    const emojis = ['🤖', '👨‍💻', '🎨', '📊', '🔍', '⚡', '🛠️', '📝', '🎯', '🚀'];
    return emojis[index % emojis.length];
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending':
        return 'bg-gray-100 text-gray-600 border-gray-200';
      case 'ready':
        return 'bg-blue-100 text-blue-600 border-blue-200';
      case 'running':
        return 'bg-[#17A589]/10 text-[#17A589] border-[#17A589]/20';
      case 'completed':
        return 'bg-green-100 text-green-600 border-green-200';
      case 'error':
        return 'bg-red-100 text-red-600 border-red-200';
      default:
        return 'bg-gray-100 text-gray-600 border-gray-200';
    }
  };

  const getProgressPercentage = () => {
    if (tasks.length === 0) return 0;
    const completedTasks = tasks.filter(task => task.status === 'completed').length;
    return (completedTasks / tasks.length) * 100;
  };

  if (!pipelineData) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-gray-400 text-sm text-center">
          Pipeline visualization will appear here when your AI crew starts working...
        </p>
      </div>
    );
  }

  return (
    <div className="h-full p-6 space-y-6">
      {/* Pipeline Status */}
      <div className="text-center">
        <h3 className="text-lg font-semibold text-[#1F3A93] mb-2">Pipeline Status</h3>
        <Badge className={`px-4 py-2 text-sm font-medium ${getStatusColor(pipelineStatus)}`}>
          {pipelineStatus.charAt(0).toUpperCase() + pipelineStatus.slice(1)}
        </Badge>
        
        {/* Progress Bar */}
        <div className="mt-4">
          <div className="flex justify-between text-sm text-gray-600 mb-1">
            <span>Progress</span>
            <span>{Math.round(getProgressPercentage())}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-[#17A589] h-2 rounded-full transition-all duration-500 ease-out"
              style={{ width: `${getProgressPercentage()}%` }}
            />
          </div>
        </div>
      </div>

      {/* Sequential Agent Pipeline */}
      <div className="space-y-6">
        <h4 className="text-md font-medium text-[#2C3E50] text-center">Agent Pipeline</h4>
        
        {/* Horizontal Agent Flow */}
        <div className="flex items-center justify-center space-x-4 overflow-x-auto pb-4">
          {agents.map((agent, index) => (
            <div key={agent.id} className="flex items-center">
              {/* Agent Node */}
              <div className="flex flex-col items-center min-w-[120px]">
                {/* Agent Square */}
                <div className={`w-16 h-16 rounded-lg border-2 transition-all duration-500 flex items-center justify-center text-2xl ${getStatusColor(agent.status)}`}>
                  {getAgentEmoji(index)}
                </div>
                
                {/* Agent Info */}
                <div className="mt-2 text-center">
                  <h5 className="font-medium text-sm truncate max-w-[120px]">{agent.role}</h5>
                  <p className="text-xs opacity-75 capitalize">{agent.status}</p>
                  <p className="text-xs text-gray-500">
                    {tasks.filter(task => task.agent_id === agent.id && task.status === 'completed').length}/{tasks.filter(task => task.agent_id === agent.id).length} tasks
                  </p>
                </div>
              </div>
              
              {/* Arrow to next agent */}
              {index < agents.length - 1 && (
                <div className="flex items-center mx-4">
                  <div className="text-2xl text-gray-400">→</div>
                </div>
              )}
            </div>
          ))}
        </div>
        
      </div>

      {/* Summary */}
      <div className="border-t pt-4">
        <div className="grid grid-cols-2 gap-4 text-center">
          <div>
            <p className="text-2xl font-bold text-[#1F3A93]">{agents.length}</p>
            <p className="text-sm text-gray-600">Total Agents</p>
          </div>
          <div>
            <p className="text-2xl font-bold text-[#17A589]">{tasks.length}</p>
            <p className="text-sm text-gray-600">Total Tasks</p>
          </div>
        </div>
      </div>
    </div>
  );
}