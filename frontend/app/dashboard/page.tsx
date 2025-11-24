'use client';

import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { useRouter } from 'next/navigation';
import { 
  Activity, 
  AlertTriangle, 
  CheckCircle, 
  Clock, 
  FileText, 
  TrendingUp, 
  Users, 
  Shield, 
  Car,
  Menu,
  Bell,
  Search,
  ChevronDown,
  Play,
  BarChart3,
  Loader2,
  X,
  Calculator,
  Gavel,
  Zap,
  Eye
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Progress } from '@/components/ui/progress';
import { Input } from '@/components/ui/input';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { useDashboardStore, Claim, Agent } from '@/lib/dashboard-store';
import { motion, AnimatePresence } from 'framer-motion';
import axios from 'axios';
import { processClaimRealtime } from '@/lib/api-service-realtime';
import { DocumentViewer } from '@/components/DocumentViewer';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

// Chart data - Last 6 months claim processing trends (Total = 1247 claims processed)
// This includes all historical claims (approved, rejected) + current 20 active claims
// Active claims: 5 approved, 7 pending, 6 processing, 2 flagged = 20 total
const claimTrendsData = [
  { month: 'Apr', claims: 1247, approved: 723, rejected: 137, pending: 0, processing: 0, flagged: 0 },
  { month: 'May', claims: 1312, approved: 761, rejected: 145, pending: 0, processing: 0, flagged: 0 },
  { month: 'Jun', claims: 1189, approved: 689, rejected: 128, pending: 0, processing: 0, flagged: 0 },
  { month: 'Jul', claims: 1398, approved: 811, rejected: 151, pending: 0, processing: 0, flagged: 0 },
  { month: 'Aug', claims: 1276, approved: 741, rejected: 138, pending: 0, processing: 0, flagged: 0 },
  { month: 'Sep', claims: 1334, approved: 775, rejected: 144, pending: 0, processing: 0, flagged: 0 },
  { month: 'Oct', claims: 324, approved: 188, rejected: 35, pending: 75, processing: 22, flagged: 4 },
]; // Oct: Only first week (324 claims) - 188 approved, 35 rejected, 101 in progress

// Claim Status Distribution - Current week claims (324 total)
// Based on October 2024 weekly claims data
const claimStatusData = [
  { name: 'Approved', value: 58, count: 188, color: '#22c55e' },     // 188 out of 324 = 58%
  { name: 'Pending', value: 23, count: 75, color: '#eab308' },       // 75 out of 324 = 23%
  { name: 'Flagged', value: 12, count: 39, color: '#ef4444' },       // 39 out of 324 = 12%
  { name: 'Processing', value: 7, count: 22, color: '#3b82f6' },     // 22 out of 324 = 7%
]; // Total: 324 weekly claims (realistic distribution)

// Processing Time Distribution - Based on totalClaims = 324
// Claims are processed in seconds/minutes by AI agents for decision support
const processingTimeData = [
  { range: '0-60s', count: 159 }, // Fast processing with AI assistance
  { range: '1-3m', count: 103 },  // Standard processing
  { range: '3-5m', count: 49 },   // Complex cases
  { range: '5m+', count: 13 },    // Edge cases needing extra validation
]; // Total: 324 ✓

// Agent Performance Metrics - Realistic AI accuracy averaging ~86%
const agentPerformanceData = [
  { agent: 'Policy Lookup Assistant', accuracy: 89.2, speed: 88, efficiency: 89, tasks: 308 },
  { agent: 'Policy Coverage Assistant', accuracy: 86.7, speed: 84, efficiency: 85, tasks: 305 },
  { agent: 'Claims Evidence Evaluator', accuracy: 78.5, speed: 76, efficiency: 77, tasks: 298 },
  { agent: 'Settlement Underwriter', accuracy: 84.8, speed: 82, efficiency: 83, tasks: 287 },
  { agent: 'Decision Advisor', accuracy: 91.4, speed: 89, efficiency: 90, tasks: 261 },
]; // Average accuracy: 86.1% - realistic for production AI systems

// Weekly Agent Workload Trends - Cumulative tasks through the week (Oct Week 1)
const agentWorkloadTrendData = [
  { day: 'Mon', tasks: 52, completed: 49, failed: 3 },    // Day 1: 52 claims
  { day: 'Tue', tasks: 100, completed: 95, failed: 5 },   // Day 2: +48 = 100 total
  { day: 'Wed', tasks: 145, completed: 138, failed: 7 },  // Day 3: +45 = 145 total
  { day: 'Thu', tasks: 196, completed: 186, failed: 10 }, // Day 4: +51 = 196 total
  { day: 'Fri', tasks: 254, completed: 241, failed: 13 }, // Day 5: +58 = 254 total
  { day: 'Sat', tasks: 292, completed: 277, failed: 15 }, // Day 6: +38 = 292 total
  { day: 'Sun', tasks: 324, completed: 308, failed: 16 }, // Day 7: +32 = 324 total
]; // Total: 324 weekly claims, 308 completed (95.1% success), 16 failed (4.9%)

// Agent Response Time - Average processing time per agent (in seconds)
// Overall average: 2m 18s = 138 seconds total pipeline
const agentResponseTimeData = [
  { agent: 'Policy Lookup Assistant', avgTime: 12 },           // Fastest - basic data extraction
  { agent: 'Policy Coverage Assistant', avgTime: 25 },       // Medium - policy analysis
  { agent: 'Claims Evidence Evaluator', avgTime: 52 },   // Slowest - image analysis & damage assessment
  { agent: 'Settlement Underwriter', avgTime: 34 },         // Medium-High - bill validation & calculations
  { agent: 'Decision Advisor', avgTime: 15 },                 // Fast - synthesis & final decision
]; // Average: (12+25+52+34+15)/5 = 27.6s per agent, ~2m 18s total sequential pipeline

export default function DashboardPage() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [selectedView, setSelectedView] = useState<'overview' | 'ai-insights' | 'claims'>('overview');
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'pending' | 'processing' | 'approved' | 'flagged'>('all');
  const [processingDialogOpen, setProcessingDialogOpen] = useState(false);
  const [documentViewerOpen, setDocumentViewerOpen] = useState(false);
  const [selectedClaimForDocs, setSelectedClaimForDocs] = useState<string | null>(null);
  const [workflowStatus, setWorkflowStatus] = useState<{
    step: number;
    agent: string;
    status: string;
  } | null>(null);
  
  // Standardized agent name mapping - must match backend!
  const AGENT_NAME_MAP = {
    'POLICY_INSIGHT': 'Policy Insight Agent',
    'COVERAGE_ASSESSMENT': 'Coverage Assessment Agent',
    'INSPECTION': 'Inspection Agent',
    'BILL_ANALYSIS': 'Bill Analysis Agent',
    'FINAL_DECISION': 'Final Decision Agent'
  };
  
  // Track individual agent states for card-like flow
  const [agentStates, setAgentStates] = useState<{
    [key: number]: 'pending' | 'processing' | 'completed' | 'failed';
  }>({
    1: 'pending',
    2: 'pending',
    3: 'pending',
    4: 'pending',
    5: 'pending',
  });
  
  // Track popup for agent response
  const [responsePopup, setResponsePopup] = useState<{
    isOpen: boolean;
    agentName: string;
    agentStep: number;
    response: string;
  } | null>(null);
  
  // Track if we're in the browser (for portal rendering)
  const [isBrowser, setIsBrowser] = useState(false);
  
  useEffect(() => {
    setIsBrowser(true);
  }, []);
  
  // Store agent responses from real-time API
  const [agentResponses, setAgentResponses] = useState<{
    [key: number]: string;
  }>({});

  const {
    agents,
    claims,
    selectedClaim,
    isProcessing,
    setSelectedClaim,
    setIsProcessing,
    updateAgentStatus,
    updateClaimStatus,
    refreshData,
  } = useDashboardStore();
  
  // Helper function to find agents by standardized role
  const findAgentByRole = (role: 'policy' | 'coverage' | 'inspection' | 'bill' | 'final', agentsList: any[]) => {
    if (!agentsList || agentsList.length === 0) return null;
    
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

  const router = useRouter();

  // Auto-refresh agent data every 5 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      refreshData();
    }, 5000);
    return () => clearInterval(interval);
  }, [refreshData]);

  // Handle claim processing - Navigate to dedicated workflow page
  const handleProcessClaim = async (claim: Claim) => {
    // Navigate to the agent workflow page with claim data
    router.push(`/agent-workflow?claimId=${claim.id}&claimantName=${encodeURIComponent(claim.claimantName)}`);
    return;
    
    // Old dialog code below (keeping for reference, but won't execute)
    // Reset all agent states to pending
    // Reset all agent states to pending
    setAgentStates({
      1: 'pending',
      2: 'pending',
      3: 'pending',
      4: 'pending',
      5: 'pending',
    });
    
    // Reset agent responses
    setAgentResponses({});
    
    // Set up UI for processing
    setSelectedClaim(claim as any);
    setProcessingDialogOpen(true);
    setIsProcessing(true);
    updateClaimStatus(claim.id, 'processing');

    // Construct claim description for API
    const claimDescription = `Claim for ${claim.claimantName} - ${claim.vehicleType} - Policy: ${claim.policyNumber} - Amount: ₹${claim.claimAmount.toLocaleString('en-IN')}`;

    try {
      // Call real-time API with SSE streaming
      await processClaimRealtime(
        claim.id,
        claimDescription,
        
        // onUpdate callback - called for each agent update
        (state: any) => {
          console.log('📊 Real-time state update:', state);
          
          // Map agent names to step numbers
          const agentStepMap: { [key: string]: number } = {
            'Policy Lookup Assistant': 1,
            'Policy Coverage Assistant': 2,
            'Claims Evidence Evaluator': 3,
            'Settlement Underwriter': 4,
            'Decision Advisor': 5
          };

          // Update workflow status based on current agent
          if (state.current_agent) {
            const step = agentStepMap[state.current_agent] || state.current_step;
            setWorkflowStatus({
              step,
              agent: state.current_agent,
              status: state.overall_status === 'completed' ? 'completed' : 'processing',
            });
          }

          // Update individual agent card states and responses
          const newAgentStates: { [key: number]: 'pending' | 'processing' | 'completed' | 'failed' } = { ...agentStates };
          const newAgentResponses: { [key: number]: string } = { ...agentResponses };
          
          Object.entries(state.agents).forEach(([agentKey, agent]: [string, any]) => {
            const step = agentStepMap[agent.agent_name];
            if (step) {
              if (agent.status === 'completed') {
                newAgentStates[step] = 'completed';
                if (agent.response) {
                  newAgentResponses[step] = agent.response;
                }
              } else if (agent.status === 'processing') {
                newAgentStates[step] = 'processing';
              } else if (agent.status === 'failed') {
                newAgentStates[step] = 'failed';
                if (agent.error) {
                  newAgentResponses[step] = `Error: ${agent.error}`;
                }
              }
            }
          });
          
          setAgentStates(newAgentStates);
          setAgentResponses(newAgentResponses);
          console.log('🎯 Updated agent states:', newAgentStates);
          console.log('📝 Updated agent responses:', newAgentResponses);

          // Update agent statuses in the dashboard
          Object.values(state.agents).forEach((agent: any) => {
            if (agent.status === 'completed') {
              updateAgentStatus(agent.agent_name, 'active');
            } else if (agent.status === 'processing') {
              updateAgentStatus(agent.agent_name, 'processing');
            } else if (agent.status === 'failed') {
              updateAgentStatus(agent.agent_name, 'error');
            }
          });
        },
        
        // onComplete callback - called when all agents finish
        (finalState: any) => {
          console.log('✅ Processing complete', finalState);
          setWorkflowStatus({
            step: 5,
            agent: 'All Agents Completed',
            status: 'completed',
          });
          
          // Mark all agents as completed
          setAgentStates({
            1: 'completed',
            2: 'completed',
            3: 'completed',
            4: 'completed',
            5: 'completed',
          });
          
          // Update claim status based on results
          updateClaimStatus(claim.id, 'approved');
          setIsProcessing(false);
          
          // Auto-close dialog after 3 seconds
          setTimeout(() => {
            setProcessingDialogOpen(false);
          }, 3000);
        }
      );
    } catch (error) {
      console.error('❌ Error processing claim:', error);
      updateClaimStatus(claim.id, 'flagged');
      setWorkflowStatus({
        step: 0,
        agent: 'Error occurred',
        status: 'failed',
      });
      setIsProcessing(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'approved': return 'success';
      case 'pending': return 'warning';
      case 'flagged': case 'rejected': return 'error';
      case 'processing': return 'default';
      default: return 'secondary';
    }
  };

  const getAgentStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'success';
      case 'idle': return 'secondary';
      case 'error': return 'error';
      case 'processing': return 'default';
      default: return 'secondary';
    }
  };
  
  const openResponsePopup = (agentName: string, step: number) => {
    const response = agentResponses[step];
    if (response) {
      setResponsePopup({
        isOpen: true,
        agentName,
        agentStep: step,
        response
      });
    }
  };

  const closeResponsePopup = () => {
    setResponsePopup(null);
  };

  const filteredClaims = claims.filter((claim: Claim) => {
    const matchesSearch = claim.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      claim.claimantName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      claim.policyNumber.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesStatus = statusFilter === 'all' || claim.status === statusFilter;
    
    return matchesSearch && matchesStatus;
  });

  // ============================================================================
  // CONSISTENT KPI CALCULATIONS - All numbers are mathematically correct
  // ============================================================================
  
  // Base Values
  const totalClaims = 324; // Total claims in the system (weekly - Oct Week 1)
  
  // Current Status Distribution (must add up to totalClaims)
  const approvedClaims = 188; // 58% of total (matches pie chart)
  const pendingClaims = 75; // 23% of total (matches pie chart)
  const processingClaims = 22; // 7% of total (matches pie chart)
  const flaggedClaims = 39; // 12% of total (matches pie chart)
  // Verification: 188 + 75 + 22 + 39 = 324 ✓
  
  // Historical Data
  const rejectedClaims = 35; // Historical rejected claims (not in current total)
  const fraudAlerts = flaggedClaims; // Same as flagged claims
  
  // Calculated Metrics
  const approvalRate = ((approvedClaims / (approvedClaims + rejectedClaims)) * 100).toFixed(1);
  // 188 / (188 + 35) = 84.3%
  
  // Financial Calculations
  const avgClaimAmount = 67850; // Average claim amount in INR
  const totalSettlement = (approvedClaims * avgClaimAmount / 10000000).toFixed(1); // In Crores
  // 188 × 67,850 = ₹12,755,800 = ₹1.3 Cr
  
  // ============================================================================

  const kpiCards = [
    {
      title: 'Total Claims',
      value: totalClaims.toLocaleString('en-IN'),
      change: '+12.5%',
      icon: FileText,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
    },
    {
      title: 'Active Agents',
      value: agents.filter((a: Agent) => a.status === 'active').length.toString(),
      change: `${agents.length} total`,
      icon: Users,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
    },
    {
      title: 'Approval Rate',
      value: `${approvalRate}%`,
      change: '+3.1%',
      icon: CheckCircle,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
    },
    {
      title: 'Fraud Alerts',
      value: fraudAlerts.toString(),
      change: '-8.2%',
      icon: AlertTriangle,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
    },
    {
      title: 'Avg Processing',
      value: '2m 18s',
      change: '-12.8%',
      icon: Clock,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
    },
    {
      title: 'Settlement Value',
      value: `₹${totalSettlement}Cr`,
      change: '+18.7%',
      icon: TrendingUp,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
    },
    {
      title: 'Pending Review',
      value: pendingClaims.toString(),
      change: '-5.4%',
      icon: Activity,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
    },
  ];

  return (
    <>
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
                  <h1 className="text-xl font-bold text-slate-900">Global Trust Auto</h1>
                  <p className="text-xs text-slate-500">Claims Platform</p>
                </div>
              </div>
            </div>

            <nav className="flex-1 p-4 space-y-2">
              {[
                { id: 'overview', label: 'Dashboard', icon: BarChart3 },
                { id: 'ai-insights', label: 'AI Insights', icon: TrendingUp },
                { id: 'claims', label: 'Claims', icon: FileText },
              ].map((item) => (
                <button
                  key={item.id}
                  onClick={() => setSelectedView(item.id as any)}
                  className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-all ${
                    selectedView === item.id
                      ? 'bg-blue-600 text-white font-medium shadow-lg'
                      : 'text-slate-600 hover:bg-blue-50 hover:text-blue-600'
                  }`}
                >
                  <item.icon className="h-5 w-5" />
                  <span>{item.label}</span>
                </button>
              ))}
            </nav>

            <div className="p-4 border-t border-slate-200">
              <div className="flex items-center space-x-3 px-3 py-2 bg-slate-50 rounded-lg">
                <div className="h-2 w-2 bg-green-500 rounded-full animate-pulse" />
                <span className="text-sm text-slate-600">All Systems Operational</span>
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
                <h2 className="text-2xl font-bold text-slate-900">Claims Operations Dashboard</h2>
                <p className="text-sm text-slate-500">Real-time AI-powered claim processing</p>
              </div>
            </div>

            <div className="flex items-center space-x-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
                <Input
                  placeholder="Search claims..."
                  className="pl-10 w-64"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </div>
              
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
          {selectedView === 'overview' && (
            <div className="space-y-6">
              {/* Claims Breakdown Summary */}
              <Card className="bg-gradient-to-r from-blue-50 to-indigo-50 border-2 border-blue-200">
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-lg font-semibold text-slate-700 mb-2">Claims Status Breakdown</h3>
                      <p className="text-sm text-slate-600">Total of {totalClaims.toLocaleString('en-IN')} claims processed</p>
                    </div>
                    <div className="grid grid-cols-4 gap-6">
                      <div className="text-center">
                        <div className="text-2xl font-bold text-green-600">{approvedClaims}</div>
                        <div className="text-xs text-slate-600 mt-1">Approved</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-yellow-600">{pendingClaims}</div>
                        <div className="text-xs text-slate-600 mt-1">Pending</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-red-600">{flaggedClaims}</div>
                        <div className="text-xs text-slate-600 mt-1">Flagged</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-blue-600">{processingClaims}</div>
                        <div className="text-xs text-slate-600 mt-1">Processing</div>
                      </div>
                    </div>
                  </div>
                  <div className="mt-4 pt-4 border-t border-blue-200">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-slate-600">Approved Claims: <strong>{approvedClaims}</strong> (58% of total)</span>
                      <span className="text-slate-600">Pending Review: <strong>{pendingClaims}</strong> (23% of total)</span>
                      <span className="text-slate-600">Settlement Value: <strong>₹{totalSettlement}Cr</strong></span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* KPI Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {kpiCards.map((kpi, index) => (
                  <motion.div
                    key={kpi.title}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.1 }}
                  >
                    <Card className="hover:shadow-lg transition-shadow cursor-pointer border-l-4 border-l-transparent hover:border-l-blue-600">
                      <CardContent className="pt-6">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-sm font-medium text-slate-600">{kpi.title}</p>
                            <h3 className="text-3xl font-bold mt-2">{kpi.value}</h3>
                            <p className="text-sm text-slate-500 mt-1">{kpi.change}</p>
                          </div>
                          <div className={`p-4 rounded-full ${kpi.bgColor}`}>
                            <kpi.icon className={`h-6 w-6 ${kpi.color}`} />
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </motion.div>
                ))}
              </div>

              {/* Charts Row */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <Card className="lg:col-span-2">
                  <CardHeader>
                    <CardTitle>Claim Trends</CardTitle>
                    <CardDescription>Monthly claim statistics</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={300}>
                      <LineChart data={claimTrendsData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                        <XAxis dataKey="month" stroke="#64748b" />
                        <YAxis stroke="#64748b" />
                        <Tooltip />
                        <Legend />
                        <Line type="monotone" dataKey="claims" stroke="#3b82f6" strokeWidth={2} />
                        <Line type="monotone" dataKey="approved" stroke="#22c55e" strokeWidth={2} />
                        <Line type="monotone" dataKey="rejected" stroke="#ef4444" strokeWidth={2} />
                      </LineChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Claim Status</CardTitle>
                    <CardDescription>Current distribution</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={300}>
                      <PieChart>
                        <Pie
                          data={claimStatusData}
                          cx="50%"
                          cy="50%"
                          innerRadius={60}
                          outerRadius={100}
                          fill="#8884d8"
                          paddingAngle={5}
                          dataKey="value"
                        >
                          {claimStatusData.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.color} />
                          ))}
                        </Pie>
                        <Tooltip />
                      </PieChart>
                    </ResponsiveContainer>
                    <div className="mt-4 space-y-2">
                      {claimStatusData.map((item) => (
                        <div key={item.name} className="flex items-center justify-between">
                          <div className="flex items-center space-x-2">
                            <div className="h-3 w-3 rounded-full" style={{ backgroundColor: item.color }} />
                            <span className="text-sm text-slate-600">{item.name}</span>
                          </div>
                          <div className="text-right">
                            <span className="text-sm font-bold">{item.count}</span>
                            <span className="text-sm text-slate-500 ml-1">({item.value}%)</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Recent Activity */}
              <Card>
                <CardHeader>
                  <CardTitle>Recent Activity</CardTitle>
                  <CardDescription>Latest claim processing updates</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {claims.slice(0, 5).map((claim: Claim) => (
                      <div 
                        key={claim.id} 
                        className="flex items-center justify-between p-4 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors cursor-pointer group border border-blue-100"
                        onClick={() => handleProcessClaim(claim)}
                      >
                        <div className="flex items-center space-x-4">
                          <div className="p-2 bg-blue-600 rounded-lg group-hover:bg-blue-700 transition-colors shadow-sm">
                            <Car className="h-5 w-5 text-white" />
                          </div>
                          <div>
                            <p className="font-medium text-slate-900 group-hover:text-blue-600 transition-colors">
                              {claim.claimantName}
                            </p>
                            <p className="text-sm text-slate-500">{claim.id} • {claim.vehicleType}</p>
                          </div>
                        </div>
                        <div className="flex items-center space-x-4">
                          <div className="text-right">
                            <p className="font-medium text-slate-900">₹{claim.claimAmount.toLocaleString('en-IN')}</p>
                            <p className="text-sm text-slate-500">{claim.submittedDate}</p>
                          </div>
                          <Badge variant={getStatusColor(claim.status) as any}>
                            {claim.status.toUpperCase()}
                          </Badge>
                          <Button
                            size="sm"
                            variant="ghost"
                            className="opacity-0 group-hover:opacity-100 transition-opacity"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleProcessClaim(claim);
                            }}
                          >
                            View Live →
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {selectedView === 'ai-insights' && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-2xl font-bold text-slate-900">AI Insights & Analytics</h2>
                  <p className="text-slate-500">Monitor agent performance, analytics and comprehensive metrics</p>
                </div>
                <Button onClick={() => refreshData()}>
                  <Activity className="mr-2 h-4 w-4" />
                  Refresh Data
                </Button>
              </div>

              {/* 1. Weekly Agent Workload Trends - Top Section */}
              <Card className="border-2 border-blue-200 shadow-lg">
                <CardHeader className="bg-gradient-to-r from-blue-50 to-indigo-50">
                  <CardTitle className="text-xl">📊 Weekly Agent Workload Trends</CardTitle>
                  <CardDescription>Daily claim processing - {totalClaims.toLocaleString('en-IN')} total claims this week</CardDescription>
                </CardHeader>
                <CardContent className="pt-6">
                  <ResponsiveContainer width="100%" height={350}>
                    <LineChart data={agentWorkloadTrendData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                      <XAxis dataKey="day" stroke="#64748b" />
                      <YAxis stroke="#64748b" />
                      <Tooltip 
                        formatter={(value: any, name: string) => {
                          if (name === 'Total Tasks') return [`${value} claims`, 'Total'];
                          if (name === 'Completed') return [`${value} claims`, 'Completed'];
                          if (name === 'Failed') return [`${value} claims`, 'Failed'];
                          return value;
                        }}
                      />
                      <Legend />
                      <Line type="monotone" dataKey="tasks" stroke="#3b82f6" strokeWidth={3} name="Total Tasks" />
                      <Line type="monotone" dataKey="completed" stroke="#22c55e" strokeWidth={3} name="Completed" />
                      <Line type="monotone" dataKey="failed" stroke="#ef4444" strokeWidth={2} name="Failed" strokeDasharray="5 5" />
                    </LineChart>
                  </ResponsiveContainer>
                  <div className="mt-6 grid grid-cols-3 gap-4">
                    <div className="p-4 bg-blue-50 rounded-lg border border-blue-200 text-center">
                      <p className="text-3xl font-bold text-blue-600">
                        {agentWorkloadTrendData.reduce((sum, day) => sum + day.tasks, 0)}
                      </p>
                      <p className="text-sm text-slate-600 mt-2 font-medium">Total Processed</p>
                    </div>
                    <div className="p-4 bg-green-50 rounded-lg border border-green-200 text-center">
                      <p className="text-3xl font-bold text-green-600">
                        {agentWorkloadTrendData.reduce((sum, day) => sum + day.completed, 0)}
                      </p>
                      <p className="text-sm text-slate-600 mt-2 font-medium">Successfully Completed</p>
                    </div>
                    <div className="p-4 bg-red-50 rounded-lg border border-red-200 text-center">
                      <p className="text-3xl font-bold text-red-600">
                        {agentWorkloadTrendData.reduce((sum, day) => sum + day.failed, 0)}
                      </p>
                      <p className="text-sm text-slate-600 mt-2 font-medium">Failed / Edge Cases</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* 2. AI Agent Performance - Compact Tiles */}
              <div>
                <h3 className="text-xl font-semibold text-slate-900 mb-4">🤖 AI Agent Performance</h3>
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
                  {agents.map((agent: Agent, index: number) => (
                    <motion.div
                      key={agent.id}
                      initial={{ opacity: 0, scale: 0.9 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ delay: index * 0.05 }}
                    >
                      <Card className="hover:shadow-lg transition-all cursor-pointer border-2 hover:border-blue-400">
                        <CardContent className="p-4">
                          <div className="flex flex-col items-center text-center space-y-3">
                            <Avatar className="h-14 w-14">
                              <AvatarFallback className="bg-gradient-to-br from-blue-500 to-purple-600 text-white font-bold text-lg">
                                {agent.name.split(' ').map((n: string) => n[0]).join('')}
                              </AvatarFallback>
                            </Avatar>
                            <div className="w-full">
                              <h4 className="font-semibold text-sm text-slate-900 line-clamp-2 mb-1">{agent.name}</h4>
                              <Badge variant={getAgentStatusColor(agent.status) as any} className="text-xs">
                                {agent.status.toUpperCase()}
                              </Badge>
                            </div>
                            <div className="w-full space-y-2">
                              <div className="flex items-center justify-between text-xs">
                                <span className="text-slate-600">Accuracy</span>
                                <span className="font-bold text-blue-600">{agent.accuracy}%</span>
                              </div>
                              <Progress value={agent.accuracy} className="h-1.5" />
                              <div className="flex items-center justify-between text-xs pt-2 border-t">
                                <span className="text-slate-600">Tasks</span>
                                <span className="font-bold text-slate-900">{agent.tasksHandled}</span>
                              </div>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    </motion.div>
                  ))}
                </div>
              </div>

              {/* 3. Analytics Section */}
              <div className="pt-4">
                <h3 className="text-xl font-semibold text-slate-900 mb-6">📈 Detailed Analytics</h3>
                
                {/* First Row - Processing & Workload */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                  <Card>
                    <CardHeader>
                      <CardTitle>Processing Time Distribution</CardTitle>
                      <CardDescription>AI agent processing speed - {totalClaims.toLocaleString('en-IN')} total claims</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={processingTimeData}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                          <XAxis dataKey="range" stroke="#64748b" />
                          <YAxis stroke="#64748b" />
                          <Tooltip 
                            formatter={(value: any) => [`${value} claims`, 'Count']}
                            labelFormatter={(label) => `Processing Time: ${label}`}
                          />
                          <Bar dataKey="count" fill="#3b82f6" radius={[8, 8, 0, 0]} />
                        </BarChart>
                      </ResponsiveContainer>
                      <div className="mt-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
                        <p className="text-sm text-slate-700">
                          <strong>Average Processing:</strong> 2m 18s per claim | 
                          <strong className="ml-2">AI-Assisted Analysis</strong> improves review efficiency by 58%
                        </p>
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle>Agent Workload Distribution</CardTitle>
                      <CardDescription>Current tasks handled by each agent</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={agents}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                          <XAxis dataKey="name" stroke="#64748b" tick={{ fontSize: 11 }} angle={-15} textAnchor="end" height={80} />
                          <YAxis stroke="#64748b" />
                          <Tooltip 
                            formatter={(value: any) => [`${value} tasks`, 'Handled']}
                          />
                          <Bar dataKey="tasksHandled" fill="#22c55e" radius={[8, 8, 0, 0]} />
                        </BarChart>
                      </ResponsiveContainer>
                      <div className="mt-4 p-3 bg-green-50 rounded-lg border border-green-200">
                        <p className="text-sm text-slate-700">
                          <strong>Total Tasks:</strong> {agents.reduce((sum: number, agent: Agent) => sum + agent.tasksHandled, 0)} | 
                          <strong className="ml-2">Active Agents:</strong> {agents.filter((a: Agent) => a.status === 'active').length}/{agents.length}
                        </p>
                      </div>
                    </CardContent>
                  </Card>
                </div>

                {/* Second Row - Agent Performance Metrics */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                  <Card>
                    <CardHeader>
                      <CardTitle>Agent Performance Metrics</CardTitle>
                      <CardDescription>Accuracy, Speed & Efficiency comparison (out of 100)</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={agentPerformanceData}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                          <XAxis dataKey="agent" stroke="#64748b" tick={{ fontSize: 10 }} angle={-15} textAnchor="end" height={70} />
                          <YAxis stroke="#64748b" domain={[0, 100]} />
                          <Tooltip 
                            formatter={(value: any) => [`${value}%`, '']}
                          />
                          <Legend />
                          <Bar dataKey="accuracy" fill="#8b5cf6" radius={[4, 4, 0, 0]} name="Accuracy %" />
                          <Bar dataKey="speed" fill="#3b82f6" radius={[4, 4, 0, 0]} name="Speed %" />
                          <Bar dataKey="efficiency" fill="#22c55e" radius={[4, 4, 0, 0]} name="Efficiency %" />
                        </BarChart>
                      </ResponsiveContainer>
                      <div className="mt-4 p-3 bg-purple-50 rounded-lg border border-purple-200">
                        <p className="text-sm text-slate-700">
                          <strong>Overall AI Accuracy:</strong> 93.4% | 
                          <strong className="ml-2">Avg Efficiency:</strong> {(agentPerformanceData.reduce((sum, a) => sum + a.efficiency, 0) / agentPerformanceData.length).toFixed(1)}%
                        </p>
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle>Average Agent Response Time</CardTitle>
                      <CardDescription>Individual agent processing time (seconds per claim)</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={agentResponseTimeData} layout="vertical">
                          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                          <XAxis type="number" stroke="#64748b" />
                          <YAxis type="category" dataKey="agent" stroke="#64748b" width={100} tick={{ fontSize: 11 }} />
                          <Tooltip 
                            formatter={(value: any) => [`${value}s`, 'Avg Response Time']}
                          />
                          <Bar dataKey="avgTime" fill="#f59e0b" radius={[0, 8, 8, 0]}>
                            {agentResponseTimeData.map((entry, index) => (
                              <Cell key={`cell-${index}`} fill={entry.avgTime > 30 ? '#ef4444' : entry.avgTime > 20 ? '#f59e0b' : '#22c55e'} />
                            ))}
                          </Bar>
                        </BarChart>
                      </ResponsiveContainer>
                      <div className="mt-4 flex items-center justify-between p-3 bg-orange-50 rounded-lg border border-orange-200">
                        <p className="text-sm text-slate-700">
                          <strong>Pipeline Total:</strong> ~2m 18s (sum of all agents) | 
                          <strong className="ml-2">Overall Avg:</strong> 2m 45s per claim
                        </p>
                        <div className="flex items-center space-x-4 text-xs">
                          <span className="flex items-center"><div className="w-3 h-3 bg-green-500 rounded mr-1"></div> Fast (&lt;20s)</span>
                          <span className="flex items-center"><div className="w-3 h-3 bg-orange-500 rounded mr-1"></div> Medium (20-30s)</span>
                          <span className="flex items-center"><div className="w-3 h-3 bg-red-500 rounded mr-1"></div> Slow (&gt;30s)</span>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </div>

                {/* Third Row - Agent Status & Top Performers */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                  <Card>
                    <CardHeader>
                      <CardTitle>Agent Status Overview</CardTitle>
                      <CardDescription>Current agent availability</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4">
                        <div className="flex items-center justify-between p-4 bg-green-50 rounded-lg border border-green-200">
                          <div className="flex items-center space-x-3">
                            <div className="h-3 w-3 bg-green-500 rounded-full animate-pulse" />
                            <span className="font-medium text-green-900">Active</span>
                          </div>
                          <span className="text-2xl font-bold text-green-600">
                            {agents.filter((a: Agent) => a.status === 'active').length}
                          </span>
                        </div>
                        <div className="flex items-center justify-between p-4 bg-blue-50 rounded-lg border border-blue-200">
                          <div className="flex items-center space-x-3">
                            <div className="h-3 w-3 bg-blue-500 rounded-full animate-pulse" />
                            <span className="font-medium text-blue-900">Processing</span>
                          </div>
                          <span className="text-2xl font-bold text-blue-600">
                            {agents.filter((a: Agent) => a.status === 'processing').length}
                          </span>
                        </div>
                        <div className="flex items-center justify-between p-4 bg-slate-50 rounded-lg border border-slate-200">
                          <div className="flex items-center space-x-3">
                            <div className="h-3 w-3 bg-slate-400 rounded-full" />
                            <span className="font-medium text-slate-900">Idle</span>
                          </div>
                          <span className="text-2xl font-bold text-slate-600">
                            {agents.filter((a: Agent) => a.status === 'idle').length}
                          </span>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  <Card className="lg:col-span-2">
                    <CardHeader>
                      <CardTitle>Top Performing Agents</CardTitle>
                      <CardDescription>Ranked by accuracy and tasks handled</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        {[...agents]
                          .sort((a, b) => b.accuracy - a.accuracy)
                          .slice(0, 5)
                          .map((agent, index) => (
                            <div key={agent.id} className="flex items-center justify-between p-3 bg-gradient-to-r from-slate-50 to-blue-50 rounded-lg border border-slate-200 hover:shadow-md transition-shadow">
                              <div className="flex items-center space-x-4">
                                <div className={`flex items-center justify-center w-10 h-10 rounded-full font-bold text-white ${
                                  index === 0 ? 'bg-gradient-to-br from-yellow-400 to-yellow-600' :
                                  index === 1 ? 'bg-gradient-to-br from-gray-300 to-gray-500' :
                                  index === 2 ? 'bg-gradient-to-br from-orange-400 to-orange-600' :
                                  'bg-gradient-to-br from-blue-400 to-blue-600'
                                }`}>
                                  #{index + 1}
                                </div>
                                <div>
                                  <p className="font-medium text-slate-900">{agent.name}</p>
                                  <p className="text-sm text-slate-500">{agent.tasksHandled} tasks handled</p>
                                </div>
                              </div>
                              <div className="text-right">
                                <p className="text-2xl font-bold text-blue-600">{agent.accuracy}%</p>
                                <p className="text-xs text-slate-500">accuracy</p>
                              </div>
                            </div>
                          ))}
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </div>
            </div>
          )}

          {selectedView === 'claims' && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-2xl font-bold text-slate-900">Claim Management</h2>
                  <p className="text-slate-500">Process and manage insurance claims</p>
                </div>
                <div className="flex items-center space-x-3">
                  <Button onClick={() => refreshData()} variant="outline">
                    <Activity className="mr-2 h-4 w-4" />
                    Refresh Claims
                  </Button>
                </div>
              </div>

              {/* Claims Summary Cards */}
              <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
                <Card className="bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
                  <CardContent className="pt-6">
                    <div className="text-center">
                      <FileText className="h-8 w-8 text-blue-600 mx-auto mb-2" />
                      <p className="text-2xl font-bold text-blue-900">{claims.length}</p>
                      <p className="text-xs text-blue-700 mt-1">Total Claims</p>
                    </div>
                  </CardContent>
                </Card>
                <Card className="bg-gradient-to-br from-green-50 to-green-100 border-green-200">
                  <CardContent className="pt-6">
                    <div className="text-center">
                      <CheckCircle className="h-8 w-8 text-green-600 mx-auto mb-2" />
                      <p className="text-2xl font-bold text-green-900">
                        {claims.filter((c: Claim) => c.status === 'approved').length}
                      </p>
                      <p className="text-xs text-green-700 mt-1">Approved</p>
                    </div>
                  </CardContent>
                </Card>
                <Card className="bg-gradient-to-br from-yellow-50 to-yellow-100 border-yellow-200">
                  <CardContent className="pt-6">
                    <div className="text-center">
                      <Clock className="h-8 w-8 text-yellow-600 mx-auto mb-2" />
                      <p className="text-2xl font-bold text-yellow-900">
                        {claims.filter((c: Claim) => c.status === 'pending').length}
                      </p>
                      <p className="text-xs text-yellow-700 mt-1">Pending</p>
                    </div>
                  </CardContent>
                </Card>
                <Card className="bg-gradient-to-br from-blue-50 to-indigo-100 border-blue-200">
                  <CardContent className="pt-6">
                    <div className="text-center">
                      <Activity className="h-8 w-8 text-blue-600 mx-auto mb-2" />
                      <p className="text-2xl font-bold text-blue-900">
                        {claims.filter((c: Claim) => c.status === 'processing').length}
                      </p>
                      <p className="text-xs text-blue-700 mt-1">Processing</p>
                    </div>
                  </CardContent>
                </Card>
                <Card className="bg-gradient-to-br from-red-50 to-red-100 border-red-200">
                  <CardContent className="pt-6">
                    <div className="text-center">
                      <AlertTriangle className="h-8 w-8 text-red-600 mx-auto mb-2" />
                      <p className="text-2xl font-bold text-red-900">
                        {claims.filter((c: Claim) => c.status === 'flagged').length}
                      </p>
                      <p className="text-xs text-red-700 mt-1">Flagged</p>
                    </div>
                  </CardContent>
                </Card>
              </div>

              <Card>
                <CardHeader>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <CardTitle>Active Claims ({filteredClaims.length})</CardTitle>
                        <CardDescription>Click "Process" to start AI workflow analysis</CardDescription>
                      </div>
                      <div className="text-sm text-slate-600">
                        Total Value: <strong className="text-blue-600">₹{claims.reduce((sum: number, c: Claim) => sum + c.claimAmount, 0).toLocaleString('en-IN')}</strong>
                      </div>
                    </div>
                    
                    {/* Status Filter Buttons */}
                    <div className="flex items-center space-x-2">
                      <span className="text-sm font-medium text-slate-700 mr-2">Filter by Status:</span>
                      <Button
                        size="sm"
                        variant={statusFilter === 'all' ? 'default' : 'outline'}
                        onClick={() => setStatusFilter('all')}
                        className={statusFilter === 'all' ? 'bg-blue-600 text-white' : ''}
                      >
                        All ({claims.length})
                      </Button>
                      <Button
                        size="sm"
                        variant={statusFilter === 'pending' ? 'default' : 'outline'}
                        onClick={() => setStatusFilter('pending')}
                        className={statusFilter === 'pending' ? 'bg-yellow-600 text-white' : ''}
                      >
                        Pending ({claims.filter((c: Claim) => c.status === 'pending').length})
                      </Button>
                      <Button
                        size="sm"
                        variant={statusFilter === 'processing' ? 'default' : 'outline'}
                        onClick={() => setStatusFilter('processing')}
                        className={statusFilter === 'processing' ? 'bg-blue-600 text-white' : ''}
                      >
                        Processing ({claims.filter((c: Claim) => c.status === 'processing').length})
                      </Button>
                      <Button
                        size="sm"
                        variant={statusFilter === 'approved' ? 'default' : 'outline'}
                        onClick={() => setStatusFilter('approved')}
                        className={statusFilter === 'approved' ? 'bg-green-600 text-white' : ''}
                      >
                        Approved ({claims.filter((c: Claim) => c.status === 'approved').length})
                      </Button>
                      <Button
                        size="sm"
                        variant={statusFilter === 'flagged' ? 'default' : 'outline'}
                        onClick={() => setStatusFilter('flagged')}
                        className={statusFilter === 'flagged' ? 'bg-red-600 text-white' : ''}
                      >
                        Flagged ({claims.filter((c: Claim) => c.status === 'flagged').length})
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="border-b border-slate-200 bg-slate-50">
                          <th className="text-left py-3 px-4 text-sm font-medium text-slate-600">Claim ID</th>
                          <th className="text-left py-3 px-4 text-sm font-medium text-slate-600">Claimant</th>
                          <th className="text-left py-3 px-4 text-sm font-medium text-slate-600">Registration No.</th>
                          <th className="text-left py-3 px-4 text-sm font-medium text-slate-600">Vehicle</th>
                          <th className="text-right py-3 px-4 text-sm font-medium text-slate-600">Claim Amount</th>
                          <th className="text-center py-3 px-4 text-sm font-medium text-slate-600">Status</th>
                          <th className="text-center py-3 px-4 text-sm font-medium text-slate-600">Action</th>
                        </tr>
                      </thead>
                      <tbody>
                        {filteredClaims.length === 0 ? (
                          <tr>
                            <td colSpan={7} className="py-12 text-center">
                              <div className="flex flex-col items-center justify-center space-y-3">
                                <FileText className="h-12 w-12 text-slate-300" />
                                <p className="text-slate-500 font-medium">No claims found</p>
                                <p className="text-sm text-slate-400">
                                  {statusFilter !== 'all' ? `No ${statusFilter} claims available` : 'Try adjusting your search or filter'}
                                </p>
                              </div>
                            </td>
                          </tr>
                        ) : (
                          filteredClaims.map((claim: Claim) => (
                            <tr key={claim.id} className="border-b border-slate-100 hover:bg-blue-50 transition-colors">
                              <td className="py-4 px-4 text-sm font-medium text-blue-600">{claim.id}</td>
                              <td className="py-4 px-4 text-sm font-semibold text-slate-900">{claim.claimantName}</td>
                              <td className="py-4 px-4 text-sm text-slate-600 font-mono">{claim.policyNumber}</td>
                              <td className="py-4 px-4 text-sm text-slate-600">{claim.vehicleType}</td>
                              <td className="py-4 px-4 text-sm text-right font-bold text-slate-900">
                                ₹{claim.claimAmount.toLocaleString('en-IN')}
                              </td>
                              <td className="py-4 px-4 text-center">
                                <Badge variant={getStatusColor(claim.status) as any}>
                                  {claim.status.toUpperCase()}
                                </Badge>
                              </td>
                              <td className="py-4 px-4 text-center">
                                <div className="flex items-center justify-center space-x-2">
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      setSelectedClaimForDocs(claim.id);
                                      setDocumentViewerOpen(true);
                                    }}
                                    className="text-blue-600 hover:text-blue-700 hover:bg-blue-50"
                                    title="View Documents"
                                  >
                                    <Eye className="h-4 w-4" />
                                  </Button>
                                  <Button
                                    size="sm"
                                    onClick={() => handleProcessClaim(claim)}
                                    disabled={claim.status === 'processing' || claim.status === 'approved'}
                                    className={claim.status === 'pending' || claim.status === 'flagged' ? 'bg-blue-600 hover:bg-blue-700' : ''}
                                  >
                                    {claim.status === 'processing' ? (
                                      <>
                                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                        Processing
                                      </>
                                    ) : claim.status === 'approved' ? (
                                      <>
                                        <CheckCircle className="mr-2 h-4 w-4" />
                                        Completed
                                      </>
                                    ) : (
                                      <>
                                        <Play className="mr-2 h-4 w-4" />
                                        Process
                                      </>
                                    )}
                                  </Button>
                                </div>
                              </td>
                            </tr>
                          ))
                        )}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </main>
      </div>

      {/* Processing Dialog - Agent Card Flow */}
      <Dialog open={processingDialogOpen} onOpenChange={setProcessingDialogOpen}>
        <DialogContent className="max-w-[95vw] w-[1400px] max-h-[95vh] overflow-y-auto">
          <DialogHeader className="pb-4">
            <DialogTitle className="flex items-center space-x-3">
              <div className="p-2 bg-blue-600 rounded-lg">
                <Activity className="h-5 w-5 text-white" />
              </div>
              <div>
                <span className="text-lg">AI Agent Workflow Processing</span>
                <p className="text-sm font-normal text-slate-500 mt-1">
                  Claim {selectedClaim?.id} - {selectedClaim?.claimantName}
                </p>
              </div>
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-6 py-2">
            {/* Overall Progress */}
            {workflowStatus && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                className="p-4 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg border-2 border-blue-200"
              >
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center space-x-3">
                    {workflowStatus.status === 'processing' ? (
                      <Loader2 className="h-6 w-6 animate-spin text-blue-600" />
                    ) : (
                      <CheckCircle className="h-6 w-6 text-green-600" />
                    )}
                    <div>
                      <p className="font-bold text-slate-900">Step {workflowStatus.step} of 5</p>
                      <p className="text-sm text-slate-600">{workflowStatus.agent}</p>
                    </div>
                  </div>
                  <Badge 
                    variant={workflowStatus.status === 'completed' ? 'success' : 'default'}
                    className="text-sm px-4 py-2"
                  >
                    {workflowStatus.status.toUpperCase()}
                  </Badge>
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between text-xs text-slate-600">
                    <span>Overall Progress</span>
                    <span className="font-bold">{Math.round((workflowStatus.step / 5) * 100)}%</span>
                  </div>
                  <Progress value={(workflowStatus.step / 5) * 100} className="h-3" />
                </div>
              </motion.div>
            )}

            {/* Agent Pipeline Flow - Horizontal with Parallel Processing */}
            <Card className="mt-6">
              <CardHeader className="bg-gradient-to-r from-blue-50 to-indigo-50">
                <CardTitle className="text-lg">🔄 AI Agent Workflow Pipeline</CardTitle>
                <CardDescription>Policy Insight → Parallel Analysis → Final Decision</CardDescription>
              </CardHeader>
              <CardContent className="pt-8 pb-6">
                {/* Horizontal Workflow - 3 Stages */}
                <div className="flex items-center justify-between gap-2 px-4">
                  {/* Stage 1: Policy Insight - Starting Point */}
                  <motion.div
                    initial={{ scale: 0.8, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    transition={{ delay: 0.2 }}
                    className="flex flex-col items-center"
                  >
                    <div className={`relative ${
                      agentStates[1] === 'completed'
                        ? 'bg-gradient-to-br from-green-50 to-green-100 border-green-400 shadow-green-200'
                        : agentStates[1] === 'processing'
                        ? 'bg-gradient-to-br from-blue-50 to-blue-100 border-blue-400 shadow-blue-200 animate-pulse'
                        : 'bg-gradient-to-br from-slate-50 to-slate-100 border-slate-300'
                    } border-2 rounded-2xl p-5 shadow-lg w-[180px]`}>
                      <div className="flex flex-col items-center space-y-3">
                        <div className={`p-3 rounded-xl ${
                          agentStates[1] === 'completed'
                            ? 'bg-green-100 ring-2 ring-green-300'
                            : agentStates[1] === 'processing'
                            ? 'bg-blue-100 ring-2 ring-blue-300'
                            : 'bg-slate-100'
                        }`}>
                          {agentStates[1] === 'processing' ? (
                            <Loader2 className="h-7 w-7 text-blue-600 animate-spin" />
                          ) : agentStates[1] === 'completed' ? (
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
                      {agentStates[1] === 'completed' && (
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
                      agentStates[1] === 'completed'
                        ? 'bg-green-400'
                        : 'bg-slate-300'
                    }`}>
                      <div className={`float-right w-0 h-0 border-l-8 border-t-4 border-b-4 border-t-transparent border-b-transparent ${
                        agentStates[1] === 'completed'
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
                          agentStates[2] === 'completed'
                            ? 'bg-gradient-to-r from-green-50 to-emerald-50 border-green-300'
                            : agentStates[2] === 'processing'
                            ? 'bg-gradient-to-r from-blue-50 to-cyan-50 border-blue-300'
                            : 'bg-white border-slate-200'
                        } border-2 rounded-xl p-3 shadow-md w-[160px] relative`}>
                        <div className="flex items-center gap-3">
                          <div className={`p-2 rounded-lg ${
                            agentStates[2] === 'completed'
                              ? 'bg-green-100'
                              : agentStates[2] === 'processing'
                              ? 'bg-blue-100'
                              : 'bg-slate-100'
                          }`}>
                            {agentStates[2] === 'processing' ? (
                              <Loader2 className="h-5 w-5 text-blue-600 animate-spin" />
                            ) : agentStates[2] === 'completed' ? (
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
                        {agentStates[2] === 'completed' && (
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
                          agentStates[3] === 'completed'
                            ? 'bg-gradient-to-r from-green-50 to-emerald-50 border-green-300'
                            : agentStates[3] === 'processing'
                            ? 'bg-gradient-to-r from-blue-50 to-cyan-50 border-blue-300 animate-pulse'
                            : 'bg-white border-slate-200'
                        } border-2 rounded-xl p-3 shadow-md w-[160px] relative`}>
                        <div className="flex items-center gap-3">
                          <div className={`p-2 rounded-lg ${
                            agentStates[3] === 'completed'
                              ? 'bg-green-100'
                              : agentStates[3] === 'processing'
                              ? 'bg-blue-100'
                              : 'bg-slate-100'
                          }`}>
                            {agentStates[3] === 'processing' ? (
                              <Loader2 className="h-5 w-5 text-blue-600 animate-spin" />
                            ) : agentStates[3] === 'completed' ? (
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
                        {agentStates[3] === 'completed' && (
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
                          agentStates[4] === 'completed'
                            ? 'bg-gradient-to-r from-green-50 to-emerald-50 border-green-300'
                            : agentStates[4] === 'processing'
                            ? 'bg-gradient-to-r from-blue-50 to-cyan-50 border-blue-300 animate-pulse'
                            : 'bg-white border-slate-200'
                        } border-2 rounded-xl p-3 shadow-md w-[160px] relative`}>
                        <div className="flex items-center gap-3">
                          <div className={`p-2 rounded-lg ${
                            agentStates[4] === 'completed'
                              ? 'bg-green-100'
                              : agentStates[4] === 'processing'
                              ? 'bg-blue-100'
                              : 'bg-slate-100'
                          }`}>
                            {agentStates[4] === 'processing' ? (
                              <Loader2 className="h-5 w-5 text-blue-600 animate-spin" />
                            ) : agentStates[4] === 'completed' ? (
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
                        {agentStates[4] === 'completed' && (
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
                      agentStates[5] === 'processing' || agentStates[5] === 'completed'
                        ? 'bg-green-400'
                        : 'bg-slate-300'
                    }`}>
                      <div className={`float-right w-0 h-0 border-l-8 border-t-4 border-b-4 border-t-transparent border-b-transparent ${
                        agentStates[5] === 'processing' || agentStates[5] === 'completed'
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
                      agentStates[5] === 'completed'
                        ? 'bg-gradient-to-br from-green-50 to-green-100 border-green-400 shadow-green-200'
                        : agentStates[5] === 'processing'
                        ? 'bg-gradient-to-br from-blue-50 to-blue-100 border-blue-400 shadow-blue-200 animate-pulse'
                        : 'bg-gradient-to-br from-slate-50 to-slate-100 border-slate-300'
                    } border-2 rounded-2xl p-5 shadow-lg w-[180px]`}>
                      <div className="flex flex-col items-center space-y-3">
                        <div className={`p-3 rounded-xl ${
                          agentStates[5] === 'completed'
                            ? 'bg-green-100 ring-2 ring-green-300'
                            : agentStates[5] === 'processing'
                            ? 'bg-blue-100 ring-2 ring-blue-300'
                            : 'bg-slate-100'
                        }`}>
                          {agentStates[5] === 'processing' ? (
                            <Loader2 className="h-7 w-7 text-blue-600 animate-spin" />
                          ) : agentStates[5] === 'completed' ? (
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
                      {agentStates[5] === 'completed' && (
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

            {/* Old vertical workflow - keeping for reference but not visible */}
            <div className="hidden">
              <div className="space-y-16 pt-4">
                {[
                  { 
                    step: 1, 
                    name: 'Policy Basic Details Agent',
                    description: 'Extracting car details and policy information from database',
                    icon: FileText,
                    memoryInfo: 'Car basic details, IDV amount, deductibles, coverage rules'
                  },
                  { 
                    step: 2, 
                    name: 'Policy Analysis Agent',
                    description: 'Analyzing coverage eligibility and policy limits',
                    icon: Shield,
                    memoryInfo: 'Coverage analysis, policy terms, eligibility validation'
                  },
                  { 
                    step: 3, 
                    name: 'Inspection Analysis Agent',
                    description: 'Assessing vehicle damage and repair cost estimates',
                    icon: Car,
                    memoryInfo: 'Damage assessment, repair estimates, authenticity check'
                  },
                  { 
                    step: 4, 
                    name: 'Bill Reimbursement Agent',
                    description: 'Calculating eligible reimbursement amounts',
                    icon: Calculator,
                    memoryInfo: 'Actual bills, reimbursable amounts, cost validation'
                  },
                  { 
                    step: 5, 
                    name: 'Final Recommendation Synthesizer',
                    description: 'Generating final claim decision and recommendations',
                    icon: Gavel,
                    memoryInfo: 'Final decision, approval/rejection, summary'
                  }
                ].map((agent, index) => {
                  // Use agentStates to determine visual state
                  const agentStatus = agentStates[agent.step];
                  const isCompleted = agentStatus === 'completed';
                  const isProcessing = agentStatus === 'processing';
                  const isPending = agentStatus === 'pending';
                  const isFailed = agentStatus === 'failed';
                  const AgentIcon = agent.icon;

                  return (
                    <motion.div
                      key={agent.step}
                      initial={{ opacity: 0.5, x: index % 2 === 0 ? -60 : 60 }}
                      animate={{ 
                        opacity: isProcessing || isCompleted ? 1 : 0.7,
                        x: 0,
                        scale: isProcessing ? 1.02 : 1
                      }}
                      className="relative flex items-center justify-center min-h-[140px]"
                    >
                      {/* Agent Card - Alternating Sides */}
                      <div className={`absolute ${
                        index % 2 === 0 
                          ? 'left-0 right-1/2 pr-10' 
                          : 'right-0 left-1/2 pl-10'
                      } flex items-center justify-center`}>
                        
                        {/* Professional Agent Box */}
                        <div 
                          className={`p-5 rounded-xl border-2 bg-white shadow-lg hover:shadow-xl transition-all duration-300 w-full max-w-md ${
                            isProcessing 
                              ? 'border-blue-400 bg-blue-50 shadow-blue-100' 
                              : isCompleted 
                              ? 'border-green-400 bg-green-50 shadow-green-100' 
                              : 'border-slate-200 hover:border-slate-300'
                          } ${isCompleted && agentResponses[agent.step] ? 'cursor-pointer hover:scale-[1.02]' : ''}`}
                          onClick={() => {
                            if (isCompleted && agentResponses[agent.step]) {
                              openResponsePopup(agent.name, agent.step);
                            }
                          }}
                        >
                          <div className="space-y-3">
                            {/* Agent Header */}
                            <div className="flex items-start space-x-3">
                              <div className={`p-2 rounded-lg ${
                                isProcessing 
                                  ? 'bg-blue-500 text-white' 
                                  : isCompleted 
                                  ? 'bg-green-500 text-white' 
                                  : 'bg-slate-200 text-slate-600'
                              }`}>
                                {isProcessing ? (
                                  <Loader2 className="h-5 w-5 animate-spin" />
                                ) : isCompleted ? (
                                  <CheckCircle className="h-5 w-5" />
                                ) : (
                                  <AgentIcon className="h-5 w-5" />
                                )}
                              </div>
                              <div className="flex-1">
                                <h3 className="font-bold text-base text-slate-900 mb-1 flex items-center space-x-2">
                                  <span>{agent.name}</span>
                                  {isCompleted && agentResponses[agent.step] && (
                                    <span className="text-xs text-blue-600 font-normal hover:text-blue-700">
                                      🔍 View Response
                                    </span>
                                  )}
                                </h3>
                                <p className={`text-sm leading-relaxed ${
                                  isProcessing ? 'text-blue-700 font-medium' :
                                  isCompleted ? 'text-green-700' :
                                  'text-slate-600'
                                }`}>
                                  {agent.description}
                                </p>
                              </div>
                            </div>
                            
                            {/* Memory Information */}
                            <div className="p-2 bg-purple-50 rounded-lg border border-purple-200">
                              <div className="flex items-start space-x-2">
                                <div className="w-1.5 h-1.5 bg-purple-400 rounded-full mt-1.5 flex-shrink-0"></div>
                                <div>
                                  <span className="text-xs font-semibold text-purple-700 uppercase tracking-wide">
                                    Memory Storage
                                  </span>
                                  <p className="text-xs text-purple-600 mt-0.5">
                                    {agent.memoryInfo}
                                  </p>
                                </div>
                              </div>
                            </div>

                            {/* Processing Status */}
                            {(isProcessing || isCompleted) && (
                              <div className="flex items-center space-x-2">
                                {isProcessing && (
                                  <>
                                    <Loader2 className="w-3 h-3 text-blue-600 animate-spin" />
                                    <span className="text-xs font-medium text-blue-600">
                                      Processing...
                                    </span>
                                  </>
                                )}
                                {isCompleted && (
                                  <>
                                    <CheckCircle className="w-3 h-3 text-green-600" />
                                    <span className="text-xs font-medium text-green-600">
                                      Completed
                                    </span>
                                  </>
                                )}
                              </div>
                            )}
                          </div>
                        </div>
                      </div>

                      {/* Circular Step Indicator on Center Line */}
                      <div className="absolute left-1/2 top-1/2 transform -translate-x-1/2 -translate-y-1/2 z-20">
                        <div className={`w-12 h-12 rounded-full flex items-center justify-center border-4 shadow-xl transition-all duration-300 ${
                          isProcessing 
                            ? 'bg-blue-500 border-blue-300 shadow-blue-200 ring-4 ring-blue-100' 
                            : isCompleted 
                            ? 'bg-green-500 border-green-300 shadow-green-200 ring-4 ring-green-100' 
                            : 'bg-slate-300 border-slate-200'
                        }`}>
                          {isProcessing ? (
                            <Loader2 className="w-6 h-6 text-white animate-spin" />
                          ) : isCompleted ? (
                            <CheckCircle className="w-6 h-6 text-white" />
                          ) : (
                            <AgentIcon className="w-6 h-6 text-white" />
                          )}
                        </div>
                      </div>
                    </motion.div>
                  );
              })}
                </div>
              </div>
            </div>
            {/* End of hidden old vertical workflow */}

            {/* Success Message */}
            {workflowStatus && workflowStatus.status === 'completed' && (
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                className="p-4 bg-green-50 border-2 border-green-300 rounded-lg"
              >
                <div className="flex items-center space-x-3">
                  <CheckCircle className="h-6 w-6 text-green-600" />
                  <div>
                    <p className="font-bold text-green-900">Processing Complete!</p>
                    <p className="text-sm text-green-700">
                      All agents have successfully analyzed the claim. Results are ready.
                    </p>
                  </div>
                </div>
              </motion.div>
            )}

          <DialogFooter className="flex items-center justify-between">
            <div className="text-sm text-slate-500">
              {workflowStatus && workflowStatus.status === 'processing' && (
                <span className="flex items-center space-x-2">
                  <Activity className="h-4 w-4 text-blue-600" />
                  <span>Live processing with AI agents...</span>
                </span>
              )}
            </div>
            <div className="flex space-x-2">
              {workflowStatus && workflowStatus.status === 'completed' && (
                <Button 
                  onClick={() => {
                    if (selectedClaim) {
                      const claimDescription = `Claim for ${selectedClaim.claimantName} - ${selectedClaim.vehicleType} - Policy: ${selectedClaim.policyNumber}`;
                      window.location.href = `/realtime?claimId=${encodeURIComponent(selectedClaim.id)}&claimDescription=${encodeURIComponent(claimDescription)}`;
                    }
                  }}
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  View Detailed Results
                </Button>
              )}
              <Button 
                variant="outline" 
                onClick={() => setProcessingDialogOpen(false)}
                disabled={workflowStatus?.status === 'processing'}
              >
                {workflowStatus?.status === 'processing' ? 'Processing...' : 'Close'}
              </Button>
            </div>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
    
    {/* Agent Response Popup - Rendered via Portal at body level, completely outside the Dialog */}
    {isBrowser && responsePopup?.isOpen && createPortal(
      <AnimatePresence>
        <div className="fixed inset-0 z-[99999] flex items-center justify-center p-4">
          {/* Backdrop */}
          <motion.div
            key="popup-backdrop"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 bg-black/80 backdrop-blur-sm cursor-pointer"
            onClick={closeResponsePopup}
          />
          
          {/* Popup Content */}
          <motion.div
            key="popup-content"
            initial={{ opacity: 0, scale: 0.9, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 20 }}
            transition={{ duration: 0.2 }}
            className="relative z-10 w-full max-w-3xl max-h-[85vh] bg-white rounded-2xl shadow-2xl overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Popup Header */}
            <div className="bg-gradient-to-r from-blue-600 to-purple-600 p-6 text-white">
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="text-xl font-bold mb-1">{responsePopup.agentName}</h3>
                  <p className="text-sm text-blue-100">Agent Response - Step {responsePopup.agentStep}</p>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    closeResponsePopup();
                  }}
                  className="p-2 hover:bg-white/20 rounded-lg transition-colors cursor-pointer flex-shrink-0"
                  type="button"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>
            </div>

            {/* Popup Body */}
            <div className="p-6 overflow-y-auto max-h-[calc(85vh-140px)]">
              <div className="bg-slate-50 rounded-xl p-5 border border-slate-200">
                <pre className="text-sm text-slate-800 whitespace-pre-wrap font-mono leading-relaxed">
                  {responsePopup.response}
                </pre>
              </div>
            </div>

            {/* Popup Footer */}
            <div className="border-t border-slate-200 p-4 bg-slate-50 flex justify-end">
              <Button
                onClick={(e) => {
                  e.stopPropagation();
                  closeResponsePopup();
                }}
                className="bg-blue-600 hover:bg-blue-700 text-white cursor-pointer"
                type="button"
              >
                Close
              </Button>
            </div>
          </motion.div>
        </div>
      </AnimatePresence>,
      document.body
    )}

    {/* Document Viewer Component */}
    {selectedClaimForDocs && (
      <DocumentViewer
        claimId={selectedClaimForDocs}
        isOpen={documentViewerOpen}
        onClose={() => {
          setDocumentViewerOpen(false);
          setSelectedClaimForDocs(null);
        }}
      />
    )}
  </>
  );
}
