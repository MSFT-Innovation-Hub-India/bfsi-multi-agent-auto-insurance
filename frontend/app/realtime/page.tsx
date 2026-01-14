'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Shield, 
  FileText, 
  CheckCircle, 
  Loader2,
  AlertCircle,
  Car,
  Calculator,
  Gavel,
  Activity,
  Zap,
  Menu,
  Bell,
  ChevronDown,
  ArrowLeft,
  Clock,
  TrendingUp,
  Users,
  BarChart3,
  Search
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Progress } from '@/components/ui/progress';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { 
  processClaimRealtime, 
  checkRealtimeApiHealth,
  RealtimeClaimState,
  AgentResult,
  formatAgentStatus,
  calculateProgress
} from '@/lib/api-service-realtime';
import { useRouter } from 'next/navigation';

export default function RealtimeClaimProcessor() {
  const router = useRouter();
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [claimId, setClaimId] = useState('');
  const [claimDescription, setClaimDescription] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [claimState, setClaimState] = useState<RealtimeClaimState | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [apiHealthy, setApiHealthy] = useState<boolean | null>(null);
  const [expandedAgent, setExpandedAgent] = useState<string | null>(null);
  const [autoStarted, setAutoStarted] = useState(false);

  // Check for URL parameters on mount
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const urlClaimId = params.get('claimId');
    const urlClaimDescription = params.get('claimDescription');
    const urlClaimantName = params.get('claimantName');
    
    if (urlClaimId) {
      setClaimId(urlClaimId);
    }
    if (urlClaimDescription) {
      setClaimDescription(urlClaimDescription);
    } else if (urlClaimantName) {
      setClaimDescription(`Claim processing for ${urlClaimantName}`);
    }
    
    checkHealth();
  }, []);

  // Auto-start processing if redirected from dashboard
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const autoStart = params.get('autoStart');
    
    if (autoStart === 'true' && claimId && !autoStarted && !isProcessing && apiHealthy) {
      setTimeout(() => {
        setAutoStarted(true);
        handleProcessClaim();
      }, 800);
    }
  }, [apiHealthy, autoStarted, isProcessing, claimId]);

  const checkHealth = async () => {
    try {
      const health = await checkRealtimeApiHealth();
      setApiHealthy(health.orchestrator_initialized);
    } catch (error) {
      setApiHealthy(false);
    }
  };

  const handleProcessClaim = async () => {
    if (!claimId.trim()) {
      setError('Please enter a claim ID');
      return;
    }

    setIsProcessing(true);
    setError(null);
    setClaimState(null);

    try {
      await processClaimRealtime(
        claimId.trim(),
        claimDescription.trim() || `Processing claim ${claimId.trim()}`,
        
        (updatedState) => {
          console.log('🔄 State Update:', {
            agents: Object.keys(updatedState.agents),
            current_agent: updatedState.current_agent,
            overall_status: updatedState.overall_status
          });
          setClaimState(updatedState);
        },
        
        (finalState) => {
          console.log('✅ Final State:', {
            agents: Object.keys(finalState.agents),
            overall_status: finalState.overall_status
          });
          setClaimState(finalState);
          setIsProcessing(false);
        }
      );
    } catch (err: any) {
      setError(err.message || 'Failed to process claim');
      setIsProcessing(false);
    }
  };

  const getAgentIcon = (agentName: string) => {
    if (agentName.includes('Policy')) return FileText;
    if (agentName.includes('Inspection')) return Car;
    if (agentName.includes('Bill')) return Calculator;
    if (agentName.includes('Recommendation')) return Gavel;
    return Activity;
  };

  const getStatusBadgeVariant = (status: string) => {
    switch (status) {
      case 'completed': return 'success';
      case 'processing': return 'default';
      case 'error': return 'error';
      default: return 'secondary';
    }
  };

  const progress = claimState ? calculateProgress(claimState) : 0;
  const agentsList = claimState?.agents ? 
    (Array.isArray(claimState.agents) ? claimState.agents : 
     Object.entries(claimState.agents).map(([key, value]) => ({ 
       ...value,
       agent_name: value.agent_name || key
     })).filter(agent => agent.status)) : [];

  // Debug logging
  React.useEffect(() => {
    if (agentsList.length > 0) {
      console.log('🎯 Current Agents List:', agentsList.map(a => ({
        name: a.agent_name,
        status: a.status
      })));
    }
  }, [agentsList]);

  // Standardized agent name mapping - must match backend!
  const AGENT_NAME_MAP = {
    'POLICY_INSIGHT': 'Policy Insight Agent',
    'COVERAGE_ASSESSMENT': 'Coverage Assessment Agent',
    'INSPECTION': 'Inspection Agent',
    'BILL_ANALYSIS': 'Bill Analysis Agent',
    'FINAL_DECISION': 'Final Decision Agent'
  };

  // Helper function to find agents by standardized role
  const findAgentByRole = (role: 'policy' | 'coverage' | 'inspection' | 'bill' | 'final') => {
    if (!agentsList.length) return null;
    
    const roleToAgentName = {
      'policy': AGENT_NAME_MAP.POLICY_INSIGHT,
      'coverage': AGENT_NAME_MAP.COVERAGE_ASSESSMENT,
      'inspection': AGENT_NAME_MAP.INSPECTION,
      'bill': AGENT_NAME_MAP.BILL_ANALYSIS,
      'final': AGENT_NAME_MAP.FINAL_DECISION
    };
    
    const targetName = roleToAgentName[role];
    return agentsList.find(a => a.agent_name === targetName);
  };

  return (
    <div className="flex h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      {/* Sidebar */}
      <AnimatePresence>
        {sidebarOpen && (
          <motion.aside
            initial={{ x: -300 }}
            animate={{ x: 0 }}
            exit={{ x: -300 }}
            className="w-64 bg-white border-r border-slate-200 shadow-lg flex flex-col"
          >
            <div className="p-6 border-b border-slate-200">
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-blue-600 rounded-lg">
                  <Shield className="h-6 w-6 text-white" />
                </div>
                <div>
                  <h1 className="text-xl font-bold text-slate-900">Global Trust Auto Care</h1>
                  <p className="text-xs text-slate-500">Claims Platform</p>
                </div>
              </div>
            </div>

            <nav className="flex-1 p-4 space-y-2">
              <button
                onClick={() => router.push('/dashboard')}
                className="w-full flex items-center space-x-3 px-4 py-3 rounded-lg text-slate-600 hover:bg-slate-50 transition-all"
              >
                <BarChart3 className="h-5 w-5" />
                <span>Dashboard</span>
              </button>
              
              <button
                className="w-full flex items-center space-x-3 px-4 py-3 rounded-lg bg-blue-50 text-blue-600 font-medium"
              >
                <Zap className="h-5 w-5" />
                <span>Process Claim</span>
              </button>
            </nav>

            <div className="p-4 border-t border-slate-200">
              <div className="flex items-center space-x-3 px-3 py-2 bg-slate-50 rounded-lg">
                <div className={`h-2 w-2 rounded-full ${apiHealthy ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`} />
                <span className="text-sm text-slate-600">
                  {apiHealthy ? 'API Connected' : 'API Offline'}
                </span>
              </div>
            </div>
          </motion.aside>
        )}
      </AnimatePresence>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top Navigation */}
        <header className="bg-white border-b border-slate-200 shadow-sm">
          <div className="flex items-center justify-between px-6 py-4">
            <div className="flex items-center space-x-4">
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setSidebarOpen(!sidebarOpen)}
              >
                <Menu className="h-5 w-5" />
              </Button>
              <div>
                <h2 className="text-2xl font-bold text-slate-900">Real-Time Claim Processing</h2>
                <p className="text-sm text-slate-500">AI-powered claim analysis with live updates</p>
              </div>
            </div>

            <div className="flex items-center space-x-4">
              <Button 
                variant="ghost" 
                size="icon" 
                className="relative"
                onClick={() => router.push('/dashboard')}
              >
                <ArrowLeft className="h-5 w-5" />
              </Button>

              <Button variant="ghost" size="icon" className="relative">
                <Bell className="h-5 w-5" />
                <span className="absolute top-1 right-1 h-2 w-2 bg-red-500 rounded-full" />
              </Button>

              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" className="flex items-center space-x-2">
                    <Avatar className="h-8 w-8">
                      <AvatarFallback className="bg-blue-600 text-white">AD</AvatarFallback>
                    </Avatar>
                    <span className="text-sm font-medium">Admin</span>
                    <ChevronDown className="h-4 w-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-56">
                  <DropdownMenuLabel>My Account</DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem>Profile</DropdownMenuItem>
                  <DropdownMenuItem>Settings</DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem>Logout</DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>
        </header>

        {/* Content Area */}
        <main className="flex-1 overflow-y-auto p-6">
          <div className="max-w-6xl mx-auto space-y-6">
            {/* Input Card */}
            <Card className="border-l-4 border-l-blue-600">
              <CardHeader>
                <CardTitle>Claim Information</CardTitle>
                <CardDescription>Enter claim details to start AI-powered processing</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-slate-700">Claim ID *</label>
                    <Input
                      placeholder="e.g., CLM-2024-001"
                      value={claimId}
                      onChange={(e) => setClaimId(e.target.value)}
                      disabled={isProcessing}
                      className="font-medium"
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-slate-700">Description</label>
                    <Input
                      placeholder="e.g., Vehicle accident claim"
                      value={claimDescription}
                      onChange={(e) => setClaimDescription(e.target.value)}
                      disabled={isProcessing}
                    />
                  </div>
                </div>

                {error && (
                  <motion.div
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="flex items-center space-x-2 p-3 bg-red-50 border border-red-200 rounded-lg"
                  >
                    <AlertCircle className="h-5 w-5 text-red-600" />
                    <p className="text-sm text-red-700">{error}</p>
                  </motion.div>
                )}

                <div className="flex items-center space-x-3">
                  <Button
                    onClick={handleProcessClaim}
                    disabled={isProcessing || !claimId.trim()}
                    className="bg-blue-600 hover:bg-blue-700"
                  >
                    {isProcessing ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Processing...
                      </>
                    ) : (
                      <>
                        <Zap className="mr-2 h-4 w-4" />
                        Process Claim
                      </>
                    )}
                  </Button>

                  {claimState && (
                    <Button
                      variant="outline"
                      onClick={() => {
                        setClaimState(null);
                        setClaimId('');
                        setClaimDescription('');
                        setAutoStarted(false);
                      }}
                    >
                      Reset
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Progress Overview */}
            {claimState && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
              >
                <Card>
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <div>
                        <CardTitle>Processing Status</CardTitle>
                        <CardDescription>
                          Step {claimState.current_step} of 5
                        </CardDescription>
                      </div>
                      <Badge 
                        variant={isProcessing ? 'default' : 'success'}
                        className="text-sm px-4 py-2"
                      >
                        {isProcessing ? 'In Progress' : 'Completed'}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <span className="font-medium text-slate-700">Overall Progress</span>
                        <span className="font-bold text-blue-600">{progress}%</span>
                      </div>
                      <Progress value={progress} className="h-3" />
                    </div>

                    {claimState.current_agent && (
                      <div className="flex items-center space-x-3 p-4 bg-blue-50 rounded-lg border border-blue-200">
                        {isProcessing ? (
                          <Loader2 className="h-5 w-5 text-blue-600 animate-spin" />
                        ) : (
                          <CheckCircle className="h-5 w-5 text-green-600" />
                        )}
                        <div>
                          <p className="text-sm font-medium text-slate-900">
                            {isProcessing ? 'Currently Processing' : 'Last Completed'}
                          </p>
                          <p className="text-sm text-slate-600">{claimState.current_agent}</p>
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </motion.div>
            )}

            {/* Visual Workflow Diagram */}
            {claimState && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
              >
                <Card>
                  <CardHeader>
                    <CardTitle>AI Agent Workflow Processing</CardTitle>
                    <CardDescription>Real-time parallel agent execution flow</CardDescription>
                  </CardHeader>
                  <CardContent className="p-6">
                    <div className="flex items-center justify-center gap-6">
                      {/* Stage 1: Policy Insight - Starting Point */}
                      <motion.div
                        initial={{ scale: 0.8, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        transition={{ delay: 0.2 }}
                        className="flex flex-col items-center"
                      >
                        <div className={`relative ${
                          findAgentByRole('policy')?.status === 'completed'
                            ? 'bg-gradient-to-br from-green-50 to-green-100 border-green-400 shadow-green-200'
                            : findAgentByRole('policy')?.status === 'processing'
                            ? 'bg-gradient-to-br from-blue-50 to-blue-100 border-blue-400 shadow-blue-200 animate-pulse'
                            : 'bg-gradient-to-br from-slate-50 to-slate-100 border-slate-300'
                        } border-2 rounded-2xl p-5 shadow-lg w-[180px]`}>
                          <div className="flex flex-col items-center space-y-3">
                            <div className={`p-3 rounded-xl ${
                              findAgentByRole('policy')?.status === 'completed'
                                ? 'bg-green-100 ring-2 ring-green-300'
                                : findAgentByRole('policy')?.status === 'processing'
                                ? 'bg-blue-100 ring-2 ring-blue-300'
                                : 'bg-slate-100'
                            }`}>
                              {findAgentByRole('policy')?.status === 'processing' ? (
                                <Loader2 className="h-7 w-7 text-blue-600 animate-spin" />
                              ) : findAgentByRole('policy')?.status === 'completed' ? (
                                <CheckCircle className="h-7 w-7 text-green-600" />
                              ) : (
                                <FileText className="h-7 w-7 text-slate-400" />
                              )}
                            </div>
                            <div className="text-center">
                              <h4 className="font-bold text-sm text-slate-900">Policy Insight</h4>
                              <p className="text-xs text-slate-500 mt-1">Starting Point</p>
                            </div>
                          </div>
                          {findAgentByRole('policy')?.status === 'completed' && (
                            <motion.div
                              initial={{ scale: 0 }}
                              animate={{ scale: 1 }}
                              className="absolute -top-2 -right-2 bg-green-500 text-white rounded-full p-1.5 shadow-lg"
                            >
                              <CheckCircle className="h-4 w-4" />
                            </motion.div>
                          )}
                        </div>
                        <Badge variant="outline" className="mt-3 text-xs font-semibold">
                          Step 1
                        </Badge>
                      </motion.div>

                      {/* Arrow Right */}
                      <motion.div
                        initial={{ width: 0, opacity: 0 }}
                        animate={{ width: '60px', opacity: 1 }}
                        transition={{ delay: 0.4 }}
                        className="flex flex-col items-center"
                      >
                        <div className={`h-0.5 w-full ${
                          findAgentByRole('policy')?.status === 'completed'
                            ? 'bg-green-400'
                            : 'bg-slate-300'
                        }`}>
                          <div className={`float-right w-0 h-0 border-l-8 border-t-4 border-b-4 border-t-transparent border-b-transparent ${
                            findAgentByRole('policy')?.status === 'completed'
                              ? 'border-l-green-400'
                              : 'border-l-slate-300'
                          }`} />
                        </div>
                      </motion.div>

                      {/* Stage 2: Parallel Processing Agents */}
                      <motion.div
                        initial={{ scale: 0.9, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        transition={{ delay: 0.5 }}
                        className="relative"
                      >
                        {/* Parallel Processing Badge */}
                        <div className="absolute -top-8 left-1/2 transform -translate-x-1/2 z-10">
                          <Badge className="bg-gradient-to-r from-purple-500 to-blue-500 text-white shadow-lg px-3 py-1">
                            <Zap className="h-3 w-3 mr-1" />
                            Parallel Processing
                          </Badge>
                        </div>

                        <div className="flex flex-col gap-3 p-4 bg-slate-50 rounded-2xl border-2 border-dashed border-slate-300">
                          {/* Coverage Assessment */}
                          <motion.div
                            initial={{ x: -50, opacity: 0 }}
                            animate={{ x: 0, opacity: 1 }}
                            transition={{ delay: 0.6 }}
                            className={`${
                              findAgentByRole('coverage')?.status === 'completed'
                                ? 'bg-gradient-to-r from-green-50 to-emerald-50 border-green-300'
                                : findAgentByRole('coverage')?.status === 'processing'
                                ? 'bg-gradient-to-r from-blue-50 to-cyan-50 border-blue-300'
                                : 'bg-white border-slate-200'
                            } border-2 rounded-xl p-3 shadow-md w-[160px] relative`}>
                            <div className="flex items-center gap-3">
                              <div className={`p-2 rounded-lg ${
                                findAgentByRole('coverage')?.status === 'completed'
                                  ? 'bg-green-100'
                                  : findAgentByRole('coverage')?.status === 'processing'
                                  ? 'bg-blue-100'
                                  : 'bg-slate-100'
                              }`}>
                                {findAgentByRole('coverage')?.status === 'processing' ? (
                                  <Loader2 className="h-5 w-5 text-blue-600 animate-spin" />
                                ) : findAgentByRole('coverage')?.status === 'completed' ? (
                                  <Shield className="h-5 w-5 text-green-600" />
                                ) : (
                                  <Shield className="h-5 w-5 text-slate-400" />
                                )}
                              </div>
                              <div className="flex-1">
                                <h5 className="font-semibold text-xs text-slate-900">Coverage</h5>
                                <p className="text-[10px] text-slate-500">Assessment</p>
                              </div>
                            </div>
                            {findAgentByRole('coverage')?.status === 'completed' && (
                              <motion.div
                                initial={{ scale: 0 }}
                                animate={{ scale: 1 }}
                                className="absolute -top-1 -right-1 bg-green-500 text-white rounded-full p-1"
                              >
                                <CheckCircle className="h-3 w-3" />
                              </motion.div>
                            )}
                          </motion.div>

                          {/* Inspection Agent */}
                          <motion.div
                            initial={{ x: -50, opacity: 0 }}
                            animate={{ x: 0, opacity: 1 }}
                            transition={{ delay: 0.7 }}
                            className={`${
                              findAgentByRole('inspection')?.status === 'completed'
                                ? 'bg-gradient-to-r from-green-50 to-emerald-50 border-green-300'
                                : findAgentByRole('inspection')?.status === 'processing'
                                ? 'bg-gradient-to-r from-blue-50 to-cyan-50 border-blue-300 animate-pulse'
                                : 'bg-white border-slate-200'
                            } border-2 rounded-xl p-3 shadow-md w-[160px] relative`}>
                            <div className="flex items-center gap-3">
                              <div className={`p-2 rounded-lg ${
                                findAgentByRole('inspection')?.status === 'completed'
                                  ? 'bg-green-100'
                                  : findAgentByRole('inspection')?.status === 'processing'
                                  ? 'bg-blue-100'
                                  : 'bg-slate-100'
                              }`}>
                                {findAgentByRole('inspection')?.status === 'processing' ? (
                                  <Loader2 className="h-5 w-5 text-blue-600 animate-spin" />
                                ) : findAgentByRole('inspection')?.status === 'completed' ? (
                                  <Car className="h-5 w-5 text-green-600" />
                                ) : (
                                  <Car className="h-5 w-5 text-slate-400" />
                                )}
                              </div>
                              <div className="flex-1">
                                <h5 className="font-semibold text-xs text-slate-900">Inspection</h5>
                                <p className="text-[10px] text-slate-500">Damage Check</p>
                              </div>
                            </div>
                            {findAgentByRole('inspection')?.status === 'completed' && (
                              <motion.div
                                initial={{ scale: 0 }}
                                animate={{ scale: 1 }}
                                className="absolute -top-1 -right-1 bg-green-500 text-white rounded-full p-1"
                              >
                                <CheckCircle className="h-3 w-3" />
                              </motion.div>
                            )}
                          </motion.div>

                          {/* Bill Synthesis */}
                          <motion.div
                            initial={{ x: -50, opacity: 0 }}
                            animate={{ x: 0, opacity: 1 }}
                            transition={{ delay: 0.8 }}
                            className={`${
                              findAgentByRole('bill')?.status === 'completed'
                                ? 'bg-gradient-to-r from-green-50 to-emerald-50 border-green-300'
                                : findAgentByRole('bill')?.status === 'processing'
                                ? 'bg-gradient-to-r from-blue-50 to-cyan-50 border-blue-300 animate-pulse'
                                : 'bg-white border-slate-200'
                            } border-2 rounded-xl p-3 shadow-md w-[160px] relative`}>
                            <div className="flex items-center gap-3">
                              <div className={`p-2 rounded-lg ${
                                findAgentByRole('bill')?.status === 'completed'
                                  ? 'bg-green-100'
                                  : findAgentByRole('bill')?.status === 'processing'
                                  ? 'bg-blue-100'
                                  : 'bg-slate-100'
                              }`}>
                                {findAgentByRole('bill')?.status === 'processing' ? (
                                  <Loader2 className="h-5 w-5 text-blue-600 animate-spin" />
                                ) : findAgentByRole('bill')?.status === 'completed' ? (
                                  <Calculator className="h-5 w-5 text-green-600" />
                                ) : (
                                  <Calculator className="h-5 w-5 text-slate-400" />
                                )}
                              </div>
                              <div className="flex-1">
                                <h5 className="font-semibold text-xs text-slate-900">Bill Analysis</h5>
                                <p className="text-[10px] text-slate-500">Cost Review</p>
                              </div>
                            </div>
                            {findAgentByRole('bill')?.status === 'completed' && (
                              <motion.div
                                initial={{ scale: 0 }}
                                animate={{ scale: 1 }}
                                className="absolute -top-1 -right-1 bg-green-500 text-white rounded-full p-1"
                              >
                                <CheckCircle className="h-3 w-3" />
                              </motion.div>
                            )}
                          </motion.div>
                        </div>
                        <Badge variant="outline" className="mt-3 text-xs font-semibold mx-auto block w-fit">
                          Step 2
                        </Badge>
                      </motion.div>

                      {/* Arrow Right */}
                      <motion.div
                        initial={{ width: 0, opacity: 0 }}
                        animate={{ width: '60px', opacity: 1 }}
                        transition={{ delay: 0.9 }}
                        className="flex flex-col items-center"
                      >
                        <div className={`h-0.5 w-full ${
                          findAgentByRole('final')?.status === 'processing' || findAgentByRole('final')?.status === 'completed'
                            ? 'bg-green-400'
                            : 'bg-slate-300'
                        }`}>
                          <div className={`float-right w-0 h-0 border-l-8 border-t-4 border-b-4 border-t-transparent border-b-transparent ${
                            findAgentByRole('final')?.status === 'processing' || findAgentByRole('final')?.status === 'completed'
                              ? 'border-l-green-400'
                              : 'border-l-slate-300'
                          }`} />
                        </div>
                      </motion.div>

                      {/* Stage 3: Decision Advisor - Final Step */}
                      <motion.div
                        initial={{ scale: 0.8, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        transition={{ delay: 1.0 }}
                        className="flex flex-col items-center"
                      >
                        <div className={`relative ${
                          findAgentByRole('final')?.status === 'completed'
                            ? 'bg-gradient-to-br from-green-50 to-green-100 border-green-400 shadow-green-200'
                            : findAgentByRole('final')?.status === 'processing'
                            ? 'bg-gradient-to-br from-blue-50 to-blue-100 border-blue-400 shadow-blue-200 animate-pulse'
                            : 'bg-gradient-to-br from-slate-50 to-slate-100 border-slate-300'
                        } border-2 rounded-2xl p-5 shadow-lg w-[180px]`}>
                          <div className="flex flex-col items-center space-y-3">
                            <div className={`p-3 rounded-xl ${
                              findAgentByRole('final')?.status === 'completed'
                                ? 'bg-green-100 ring-2 ring-green-300'
                                : findAgentByRole('final')?.status === 'processing'
                                ? 'bg-blue-100 ring-2 ring-blue-300'
                                : 'bg-slate-100'
                            }`}>
                              {findAgentByRole('final')?.status === 'processing' ? (
                                <Loader2 className="h-7 w-7 text-blue-600 animate-spin" />
                              ) : findAgentByRole('final')?.status === 'completed' ? (
                                <CheckCircle className="h-7 w-7 text-green-600" />
                              ) : (
                                <Gavel className="h-7 w-7 text-slate-400" />
                              )}
                            </div>
                            <div className="text-center">
                              <h4 className="font-bold text-sm text-slate-900">Decision Advisor</h4>
                              <p className="text-xs text-slate-500 mt-1">Final Step</p>
                            </div>
                          </div>
                          {findAgentByRole('final')?.status === 'completed' && (
                            <motion.div
                              initial={{ scale: 0 }}
                              animate={{ scale: 1 }}
                              className="absolute -top-2 -right-2 bg-green-500 text-white rounded-full p-1.5 shadow-lg"
                            >
                              <CheckCircle className="h-4 w-4" />
                            </motion.div>
                          )}
                        </div>
                        <Badge variant="outline" className="mt-3 text-xs font-semibold">
                          Step 3
                        </Badge>
                      </motion.div>
                    </div>

                    {/* Status Legend */}
                    <div className="flex items-center justify-center gap-6 mt-8 pt-6 border-t border-slate-200">
                      <div className="flex items-center gap-2">
                        <div className="w-3 h-3 rounded-full bg-slate-300"></div>
                        <span className="text-xs text-slate-600">Pending</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Loader2 className="w-3 h-3 text-blue-600 animate-spin" />
                        <span className="text-xs text-slate-600">Processing</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="w-3 h-3 rounded-full bg-green-500"></div>
                        <span className="text-xs text-slate-600">Completed</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            )}

            {/* Agent Results */}
            {agentsList.length > 0 && (
              <div className="space-y-4">
                <h3 className="text-lg font-semibold text-slate-900">Agent Processing Results</h3>
                <div className="grid grid-cols-1 gap-4">
                  {agentsList.map((agent, index) => {
                    const AgentIcon = getAgentIcon(agent.agent_name);
                    const isExpanded = expandedAgent === agent.agent_name;
                    const isCompleted = agent.status === 'completed';
                    const isProcessingNow = agent.status === 'processing';

                    return (
                      <motion.div
                        key={agent.agent_name}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: index * 0.1 }}
                      >
                        <Card className={`${
                          isProcessingNow ? 'border-blue-300 shadow-lg' : 
                          isCompleted ? 'border-green-200' : ''
                        } transition-all cursor-pointer hover:shadow-md`}
                          onClick={() => setExpandedAgent(isExpanded ? null : agent.agent_name)}
                        >
                          <CardHeader>
                            <div className="flex items-center justify-between">
                              <div className="flex items-center space-x-3">
                                <div className={`p-2 rounded-lg ${
                                  isCompleted ? 'bg-green-50' : 
                                  isProcessingNow ? 'bg-blue-50' : 
                                  'bg-slate-50'
                                }`}>
                                  {isProcessingNow ? (
                                    <Loader2 className="h-5 w-5 text-blue-600 animate-spin" />
                                  ) : isCompleted ? (
                                    <CheckCircle className="h-5 w-5 text-green-600" />
                                  ) : (
                                    <AgentIcon className="h-5 w-5 text-slate-400" />
                                  )}
                                </div>
                                <div>
                                  <CardTitle className="text-base">{agent.agent_name}</CardTitle>
                                  {agent.processing_time && (
                                    <CardDescription className="flex items-center space-x-1 mt-1">
                                      <Clock className="h-3 w-3" />
                                      <span>{agent.processing_time.toFixed(2)}s</span>
                                    </CardDescription>
                                  )}
                                </div>
                              </div>
                              <Badge variant={getStatusBadgeVariant(agent.status) as any}>
                                {formatAgentStatus(agent.status)}
                              </Badge>
                            </div>
                          </CardHeader>
                          
                          <AnimatePresence>
                            {isExpanded && agent.response && (
                              <motion.div
                                initial={{ height: 0, opacity: 0 }}
                                animate={{ height: 'auto', opacity: 1 }}
                                exit={{ height: 0, opacity: 0 }}
                              >
                                <CardContent>
                                  <div className="p-4 bg-slate-50 rounded-lg border border-slate-200 max-h-96 overflow-y-auto">
                                    <pre className="text-sm text-slate-700 whitespace-pre-wrap font-sans">
                                      {agent.response}
                                    </pre>
                                  </div>
                                </CardContent>
                              </motion.div>
                            )}
                          </AnimatePresence>
                        </Card>
                      </motion.div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Empty State */}
            {!claimState && !isProcessing && (
              <Card className="border-dashed border-2">
                <CardContent className="flex flex-col items-center justify-center py-12">
                  <div className="p-4 bg-blue-50 rounded-full mb-4">
                    <Zap className="h-8 w-8 text-blue-600" />
                  </div>
                  <h3 className="text-lg font-semibold text-slate-900 mb-2">
                    Ready to Process Claims
                  </h3>
                  <p className="text-sm text-slate-500 text-center max-w-md">
                    Enter a claim ID above and click "Process Claim" to start real-time AI analysis
                    with our 5-agent workflow.
                  </p>
                </CardContent>
              </Card>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}
