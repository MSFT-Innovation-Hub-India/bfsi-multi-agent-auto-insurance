'use client';

import React, { useState, useEffect } from 'react';
import { 
  Activity, 
  CheckCircle, 
  Loader2,
  ArrowLeft,
  X,
  FileText,
  Shield,
  Search,
  AlertCircle,
  IndianRupee,
  Car,
  Calculator,
  Gavel,
  Zap
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { useRouter, useSearchParams } from 'next/navigation';
import { createPortal } from 'react-dom';
import { 
  processClaimRealtime, 
  RealtimeClaimState,
  calculateProgress 
} from '@/lib/api-service-realtime';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

export default function AgentWorkflowPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const claimId = searchParams.get('claimId');
  const claimantName = searchParams.get('claimantName');

  const [agentStates, setAgentStates] = useState<{
    [key: number]: 'pending' | 'processing' | 'completed' | 'failed';
  }>({
    1: 'pending',
    2: 'pending',
    3: 'pending',
    4: 'pending',
    5: 'pending',
  });

  const [responsePopup, setResponsePopup] = useState<{
    isOpen: boolean;
    agentName: string;
    agentStep: number;
    response: string;
  } | null>(null);

  const [isBrowser, setIsBrowser] = useState(false);

  useEffect(() => {
    setIsBrowser(true);
  }, []);

  const [agentResponses, setAgentResponses] = useState<{
    [key: number]: string;
  }>({});

  const [workflowStatus, setWorkflowStatus] = useState<{
    status: 'processing' | 'completed' | 'failed';
    currentStep: number;
    progress: number;
  }>({
    status: 'processing',
    currentStep: 1,
    progress: 0,
  });

  // Real-time API integration
  useEffect(() => {
    if (!claimId || !claimantName) return;

    // Construct claim description
    const claimDescription = `Vehicle insurance claim for ${claimantName} - Claim ID: ${claimId}`;

    console.log(`🚀 Starting real-time claim processing for ${claimId}`);

    // Process claim with real-time streaming
    processClaimRealtime(
      claimId,
      claimDescription,
      // onUpdate callback - called for every agent update
      (state: RealtimeClaimState) => {
        console.log('📊 State update:', state);
        
        // Update progress
        const progress = calculateProgress(state);
        setWorkflowStatus({
          status: state.overall_status === 'completed' ? 'completed' : 
                  state.overall_status === 'error' ? 'failed' : 'processing',
          currentStep: state.current_step,
          progress: progress,
        });

        // Map agent results to our state structure
        // Step 1: Policy Basic Details
        if (state.agents.policy_basic_details) {
          const agent = state.agents.policy_basic_details;
          setAgentStates(prev => ({
            ...prev,
            1: agent.status === 'completed' ? 'completed' : 
               agent.status === 'failed' ? 'failed' : 'processing'
          }));
          if (agent.response) {
            setAgentResponses(prev => ({ ...prev, 1: agent.response! }));
          }
        }

        // Step 2: Policy Analysis
        if (state.agents.policy_analysis) {
          const agent = state.agents.policy_analysis;
          setAgentStates(prev => ({
            ...prev,
            2: agent.status === 'completed' ? 'completed' : 
               agent.status === 'failed' ? 'failed' : 'processing'
          }));
          if (agent.response) {
            setAgentResponses(prev => ({ ...prev, 2: agent.response! }));
          }
        }

        // Step 3: Inspection Analysis (mapped as Damage Assessor)
        if (state.agents.inspection_analysis) {
          const agent = state.agents.inspection_analysis;
          setAgentStates(prev => ({
            ...prev,
            3: agent.status === 'completed' ? 'completed' : 
               agent.status === 'failed' ? 'failed' : 'processing'
          }));
          if (agent.response) {
            setAgentResponses(prev => ({ ...prev, 3: agent.response! }));
          }
        }

        // Step 4: Bill Analysis (mapped as Fraud Detector)
        if (state.agents.bill_analysis) {
          const agent = state.agents.bill_analysis;
          setAgentStates(prev => ({
            ...prev,
            4: agent.status === 'completed' ? 'completed' : 
               agent.status === 'failed' ? 'failed' : 'processing'
          }));
          if (agent.response) {
            setAgentResponses(prev => ({ ...prev, 4: agent.response! }));
          }
        }

        // Step 5: Final Recommendation (mapped as Settlement Calculator)
        if (state.agents.final_recommendation) {
          const agent = state.agents.final_recommendation;
          setAgentStates(prev => ({
            ...prev,
            5: agent.status === 'completed' ? 'completed' : 
               agent.status === 'failed' ? 'failed' : 'processing'
          }));
          if (agent.response) {
            setAgentResponses(prev => ({ ...prev, 5: agent.response! }));
          }
        }
      },
      // onComplete callback
      (finalState: RealtimeClaimState) => {
        console.log('✅ Processing completed:', finalState);
        setWorkflowStatus({
          status: 'completed',
          currentStep: finalState.total_steps,
          progress: 100,
        });
      },
      // onError callback
      (error: Error) => {
        console.error('❌ Processing error:', error);
        setWorkflowStatus(prev => ({
          ...prev,
          status: 'failed',
        }));
      }
    );
  }, [claimId, claimantName]);

  const openResponsePopup = (agentName: string, step: number) => {
    const response = agentResponses[step];
    if (response) {
      setResponsePopup({
        isOpen: true,
        agentName,
        agentStep: step,
        response,
      });
    }
  };

  const closeResponsePopup = () => {
    setResponsePopup(null);
  };

  const generateMockAgents = () => {
    return [
      { 
        step: 1, 
        name: 'Policy Lookup Assistant', 
        icon: FileText, 
        role: 'Extracts vehicle and policy information',
        description: 'Retrieves vehicle details (make, model, registration), policy number, coverage type, IDV amount, and validates policy authenticity from database'
      },
      { 
        step: 2, 
        name: 'Policy Coverage Assistant', 
        icon: Shield, 
        role: 'Analyzes coverage eligibility',
        description: 'Checks if the claimed damage is covered under the policy, validates coverage limits, and confirms claim eligibility based on policy terms'
      },
      { 
        step: 3, 
        name: 'Claims Evidence Evaluator', 
        icon: Search, 
        role: 'Assesses vehicle damage',
        description: 'Analyzes uploaded damage photos, estimates repair costs, verifies authenticity of damage, and checks for any pre-existing damage'
      },
      { 
        step: 4, 
        name: 'Settlement Underwriter', 
        icon: AlertCircle, 
        role: 'Validates repair bills and costs',
        description: 'Reviews submitted repair bills, verifies vendor authenticity, calculates reimbursable amount after applying deductibles and depreciation'
      },
      { 
        step: 5, 
        name: 'Decision Advisor', 
        icon: IndianRupee, 
        role: 'Generates final claim decision',
        description: 'Synthesizes all agent findings, calculates final approved amount, generates decision (approved/rejected), and provides detailed reasoning'
      },
    ];
  };

  const agents = generateMockAgents();

  return (
    <>
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-6">
        {/* Merged Header and Workflow Content */}
        <div className="max-w-7xl mx-auto">
          <div className="bg-white rounded-xl shadow-lg">
            {/* Header Section */}
            <div className="p-6 border-b border-slate-200">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <Button
                    onClick={() => router.push('/dashboard')}
                    variant="outline"
                    className="flex items-center space-x-2"
                  >
                    <ArrowLeft className="h-4 w-4" />
                    <span>Back to Dashboard</span>
                  </Button>
                  <div className="h-8 w-px bg-slate-300"></div>
                  <div className="flex items-center space-x-3">
                    <div className="p-2 bg-blue-600 rounded-lg">
                      <Activity className="h-5 w-5 text-white" />
                    </div>
                    <div>
                      <h1 className="text-xl font-bold text-slate-900">Global Trust Auto - Claim Workflow Processing</h1>
                      <p className="text-sm text-slate-500">
                        Claim {claimId} - {claimantName}
                      </p>
                    </div>
                  </div>
                </div>
                
                {workflowStatus.status === 'completed' && (
                  <div className="flex items-center space-x-2 text-green-600">
                    <CheckCircle className="h-5 w-5" />
                    <span className="font-semibold">Processing Complete</span>
                  </div>
                )}
              </div>
            </div>

            {/* Workflow Content Section */}
            <div className="p-8">
            {/* Agent Pipeline - Horizontal Workflow */}
            <div className="bg-gradient-to-br from-slate-50 to-blue-50/30 rounded-2xl p-12 border border-slate-200 shadow-lg relative">
              {/* Small Circular Progress Indicator - Top Right Corner */}
              <div className="absolute top-4 right-4 w-16 h-16">
                <svg className="w-16 h-16 transform -rotate-90">
                  <circle
                    cx="32"
                    cy="32"
                    r="28"
                    stroke="#e2e8f0"
                    strokeWidth="4"
                    fill="none"
                  />
                  <motion.circle
                    cx="32"
                    cy="32"
                    r="28"
                    stroke="url(#smallGradient)"
                    strokeWidth="4"
                    fill="none"
                    strokeLinecap="round"
                    strokeDasharray={`${2 * Math.PI * 28}`}
                    initial={{ strokeDashoffset: 2 * Math.PI * 28 }}
                    animate={{ 
                      strokeDashoffset: 2 * Math.PI * 28 * (1 - workflowStatus.progress / 100)
                    }}
                    transition={{ duration: 0.5, ease: "easeInOut" }}
                  />
                  <defs>
                    <linearGradient id="smallGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                      <stop offset="0%" stopColor="#3b82f6" />
                      <stop offset="100%" stopColor="#1d4ed8" />
                    </linearGradient>
                  </defs>
                </svg>
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="text-sm font-bold text-slate-900">
                    {Math.round(workflowStatus.progress)}%
                  </span>
                </div>
              </div>

              {/* Clean Vertical Flow Workflow */}
              <div className="relative py-8 px-4 max-w-6xl mx-auto">
                {/* Step 1: Policy Lookup and Coverage Assistants (Side by Side) */}
                <div className="flex items-start justify-center gap-20 mb-12">
                  <motion.div
                    initial={{ scale: 0.5, opacity: 0, x: -50 }}
                    animate={{ 
                      scale: agentStates[1] !== 'pending' ? 1 : 0.5,
                      opacity: agentStates[1] !== 'pending' ? 1 : 0,
                      x: agentStates[1] !== 'pending' ? 0 : -50
                    }}
                    transition={{ duration: 0.5 }}
                    className="flex flex-col items-center relative"
                  >
                    <div className={`relative ${
                      agentStates[1] === 'completed'
                        ? 'bg-white border-blue-400 shadow-lg shadow-blue-100'
                        : agentStates[1] === 'processing'
                        ? 'bg-white border-blue-400 shadow-lg shadow-blue-100'
                        : 'bg-white border-slate-300 shadow-sm'
                    } border-2 rounded-xl p-5 w-[240px] cursor-pointer hover:scale-[1.02] hover:shadow-xl transition-all duration-200`}
                      onClick={() => agentStates[1] === 'completed' && agentResponses[1] && openResponsePopup('Policy Lookup Assistant', 1)}
                    >
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
                            <FileText className="h-7 w-7 text-green-600" />
                          ) : (
                            <FileText className="h-7 w-7 text-slate-400" />
                          )}
                        </div>
                        <div className="text-center">
                          <h4 className="font-bold text-sm text-slate-900 leading-tight">Policy Lookup Assistant</h4>
                          <p className="text-xs text-slate-500 mt-1">Policy Retrieval</p>
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
                  </motion.div>

                  {/* Step 1: Policy Coverage Assistant (Top Right) */}
                  <motion.div
                    initial={{ scale: 0.5, opacity: 0, x: 50 }}
                    animate={{ 
                      scale: agentStates[2] !== 'pending' ? 1 : 0.5,
                      opacity: agentStates[2] !== 'pending' ? 1 : 0,
                      x: agentStates[2] !== 'pending' ? 0 : 50
                    }}
                    transition={{ duration: 0.5, delay: 0.1 }}
                    className="flex flex-col items-center"
                  >
                    <div className={`relative ${
                      agentStates[2] === 'completed'
                        ? 'bg-white border-blue-400 shadow-lg shadow-blue-100'
                        : agentStates[2] === 'processing'
                        ? 'bg-white border-blue-400 shadow-lg shadow-blue-100'
                        : 'bg-white border-slate-300 shadow-sm'
                    } border-2 rounded-xl p-5 w-[240px] cursor-pointer hover:scale-[1.02] hover:shadow-xl transition-all duration-200`}
                      onClick={() => agentStates[2] === 'completed' && agentResponses[2] && openResponsePopup('Policy Coverage Assistant', 2)}
                    >
                      <div className="flex flex-col items-center space-y-3">
                        <div className={`p-3 rounded-xl ${
                          agentStates[2] === 'completed'
                            ? 'bg-green-100 ring-2 ring-green-300'
                            : agentStates[2] === 'processing'
                            ? 'bg-blue-100 ring-2 ring-blue-300'
                            : 'bg-slate-100'
                        }`}>
                          {agentStates[2] === 'processing' ? (
                            <Loader2 className="h-7 w-7 text-blue-600 animate-spin" />
                          ) : agentStates[2] === 'completed' ? (
                            <Shield className="h-7 w-7 text-green-600" />
                          ) : (
                            <Shield className="h-7 w-7 text-slate-400" />
                          )}
                        </div>
                        <div className="text-center">
                          <h4 className="font-bold text-sm text-slate-900 leading-tight">Policy Coverage Assistant</h4>
                          <p className="text-xs text-slate-500 mt-1">Coverage Analysis</p>
                        </div>
                      </div>
                      {agentStates[2] === 'completed' && (
                        <motion.div
                          initial={{ scale: 0 }}
                          animate={{ scale: 1 }}
                          className="absolute -top-2 -right-2 bg-green-500 text-white rounded-full p-1.5 shadow-lg"
                        >
                          <CheckCircle className="h-4 w-4" />
                        </motion.div>
                      )}
                    </div>
                  </motion.div>
                </div>

                {/* Converging Arrows from Policy Agents to Claims Evaluator */}
                <div className="flex justify-center mb-6">
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ 
                      opacity: (agentStates[1] === 'completed' && agentStates[2] === 'completed') ? 1 : 0
                    }}
                    transition={{ duration: 0.5 }}
                    className="relative"
                  >
                    <svg width="600" height="80" className="block">
                      {/* Left arrow from Policy Lookup - curved inward */}
                      <path
                        d="M 150 0 Q 150 30, 280 65"
                        stroke={(agentStates[1] === 'completed' && agentStates[2] === 'completed') ? "#4ade80" : "#cbd5e1"}
                        strokeWidth="3"
                        fill="none"
                      />
                      {/* Right arrow from Policy Coverage - curved inward */}
                      <path
                        d="M 450 0 Q 450 30, 320 65"
                        stroke={(agentStates[1] === 'completed' && agentStates[2] === 'completed') ? "#4ade80" : "#cbd5e1"}
                        strokeWidth="3"
                        fill="none"
                      />
                      {/* Center connecting line */}
                      <line
                        x1="280"
                        y1="65"
                        x2="320"
                        y2="65"
                        stroke={(agentStates[1] === 'completed' && agentStates[2] === 'completed') ? "#4ade80" : "#cbd5e1"}
                        strokeWidth="3"
                      />
                      {/* Final downward arrow */}
                      <line
                        x1="300"
                        y1="65"
                        x2="300"
                        y2="75"
                        stroke={(agentStates[1] === 'completed' && agentStates[2] === 'completed') ? "#4ade80" : "#cbd5e1"}
                        strokeWidth="3"
                      />
                      {/* Single arrowhead pointing down */}
                      <polygon
                        points="300,80 295,70 305,70"
                        fill={(agentStates[1] === 'completed' && agentStates[2] === 'completed') ? "#4ade80" : "#cbd5e1"}
                      />
                    </svg>
                  </motion.div>
                </div>

                {/* Step 2: Claims Evidence Evaluator (Center) */}
                <div className="flex justify-center mb-12">
                  <motion.div
                    initial={{ scale: 0.5, opacity: 0, y: 20 }}
                    animate={{ 
                      scale: (agentStates[1] === 'completed' && agentStates[2] === 'completed' && agentStates[3] !== 'pending') ? 1 : 0.5,
                      opacity: (agentStates[1] === 'completed' && agentStates[2] === 'completed' && agentStates[3] !== 'pending') ? 1 : 0,
                      y: (agentStates[1] === 'completed' && agentStates[2] === 'completed' && agentStates[3] !== 'pending') ? 0 : 20
                    }}
                    transition={{ duration: 0.5 }}
                    className="flex flex-col items-center"
                  >
                    <div className={`relative ${
                      agentStates[3] === 'completed'
                        ? 'bg-white border-blue-400 shadow-lg shadow-blue-100'
                        : agentStates[3] === 'processing'
                        ? 'bg-white border-blue-400 shadow-lg shadow-blue-100'
                        : 'bg-white border-slate-300 shadow-sm'
                    } border-2 rounded-xl p-5 w-[240px] cursor-pointer hover:scale-[1.02] hover:shadow-xl transition-all duration-200`}
                      onClick={() => agentStates[3] === 'completed' && agentResponses[3] && openResponsePopup('Claims Evidence Evaluator', 3)}
                    >
                      <div className="flex flex-col items-center space-y-3">
                        <div className={`p-3 rounded-xl ${
                          agentStates[3] === 'completed'
                            ? 'bg-green-100 ring-2 ring-green-300'
                            : agentStates[3] === 'processing'
                            ? 'bg-blue-100 ring-2 ring-blue-300'
                            : 'bg-slate-100'
                        }`}>
                          {agentStates[3] === 'processing' ? (
                            <Loader2 className="h-7 w-7 text-blue-600 animate-spin" />
                          ) : agentStates[3] === 'completed' ? (
                            <Car className="h-7 w-7 text-green-600" />
                          ) : (
                            <Car className="h-7 w-7 text-slate-400" />
                          )}
                        </div>
                        <div className="text-center">
                          <h4 className="font-bold text-sm text-slate-900 leading-tight">Claims Evidence Evaluator</h4>
                          <p className="text-xs text-slate-500 mt-1">Damage Assessment</p>
                        </div>
                      </div>
                      {agentStates[3] === 'completed' && (
                        <motion.div
                          initial={{ scale: 0 }}
                          animate={{ scale: 1 }}
                          className="absolute -top-2 -right-2 bg-green-500 text-white rounded-full p-1.5 shadow-lg"
                        >
                          <CheckCircle className="h-4 w-4" />
                        </motion.div>
                      )}
                    </div>
                  </motion.div>
                </div>

                {/* Arrow down to Settlement */}
                <div className="flex justify-center mb-6">
                  <motion.div
                    initial={{ opacity: 0, scaleY: 0 }}
                    animate={{ 
                      opacity: agentStates[3] === 'completed' ? 1 : 0,
                      scaleY: agentStates[3] === 'completed' ? 1 : 0
                    }}
                    transition={{ duration: 0.5 }}
                  >
                    <svg width="50" height="40" className="block">
                      <line x1="25" y1="0" x2="25" y2="30" stroke="#4ade80" strokeWidth="3" />
                      <polygon points="25,35 20,25 30,25" fill="#4ade80" />
                    </svg>
                  </motion.div>
                </div>

                {/* Step 3: Settlement Underwriter (Center) */}
                <div className="flex justify-center mb-12">
                  <motion.div
                    initial={{ scale: 0.5, opacity: 0, y: 20 }}
                    animate={{ 
                      scale: ((agentStates[1] === 'completed' && agentStates[2] === 'completed' && agentStates[3] === 'completed') && agentStates[4] !== 'pending') ? 1 : 0.5,
                      opacity: ((agentStates[1] === 'completed' && agentStates[2] === 'completed' && agentStates[3] === 'completed') && agentStates[4] !== 'pending') ? 1 : 0,
                      y: ((agentStates[1] === 'completed' && agentStates[2] === 'completed' && agentStates[3] === 'completed') && agentStates[4] !== 'pending') ? 0 : 20
                    }}
                    transition={{ duration: 0.5 }}
                    className="flex flex-col items-center"
                  >
                    <div className={`relative ${
                      agentStates[4] === 'completed'
                        ? 'bg-white border-blue-400 shadow-lg shadow-blue-100'
                        : agentStates[4] === 'processing'
                        ? 'bg-white border-blue-400 shadow-lg shadow-blue-100'
                        : 'bg-white border-slate-300 shadow-sm'
                    } border-2 rounded-xl p-5 w-[240px] cursor-pointer hover:scale-[1.02] hover:shadow-xl transition-all duration-200`}
                      onClick={() => agentStates[4] === 'completed' && agentResponses[4] && openResponsePopup('Settlement Underwriter', 4)}
                    >
                      <div className="flex flex-col items-center space-y-3">
                        <div className={`p-3 rounded-xl ${
                          agentStates[4] === 'completed'
                            ? 'bg-green-100 ring-2 ring-green-300'
                            : agentStates[4] === 'processing'
                            ? 'bg-blue-100 ring-2 ring-blue-300'
                            : 'bg-slate-100'
                        }`}>
                          {agentStates[4] === 'processing' ? (
                            <Loader2 className="h-7 w-7 text-blue-600 animate-spin" />
                          ) : agentStates[4] === 'completed' ? (
                            <Calculator className="h-7 w-7 text-green-600" />
                          ) : (
                            <Calculator className="h-7 w-7 text-slate-400" />
                          )}
                        </div>
                        <div className="text-center">
                          <h4 className="font-bold text-sm text-slate-900 leading-tight">Settlement Underwriter</h4>
                          <p className="text-xs text-slate-500 mt-1">Financial Review</p>
                        </div>
                      </div>
                      {agentStates[4] === 'completed' && (
                        <motion.div
                          initial={{ scale: 0 }}
                          animate={{ scale: 1 }}
                          className="absolute -top-2 -right-2 bg-green-500 text-white rounded-full p-1.5 shadow-lg"
                        >
                          <CheckCircle className="h-4 w-4" />
                        </motion.div>
                      )}
                    </div>
                  </motion.div>
                </div>

                {/* Arrow from Settlement to Final Decision */}
                <div className="flex justify-center mb-6">
                  <motion.div
                    initial={{ opacity: 0, scaleY: 0 }}
                    animate={{ 
                      opacity: agentStates[4] === 'completed' ? 1 : 0,
                      scaleY: agentStates[4] === 'completed' ? 1 : 0
                    }}
                    transition={{ duration: 0.5 }}
                    className="relative"
                  >
                    <svg width="50" height="40" className="block">
                      <line x1="25" y1="0" x2="25" y2="30" stroke="#4ade80" strokeWidth="3" />
                      <polygon points="25,35 20,25 30,25" fill="#4ade80" />
                    </svg>
                  </motion.div>
                </div>

                {/* Step 4: Final Decision Advisor (Bottom Center) */}
                <div className="flex justify-center">
                  <motion.div
                    initial={{ scale: 0.5, opacity: 0, y: 20 }}
                    animate={{ 
                      scale: (agentStates[4] === 'completed' && agentStates[5] !== 'pending') ? 1 : 0.5,
                      opacity: (agentStates[4] === 'completed' && agentStates[5] !== 'pending') ? 1 : 0,
                      y: (agentStates[4] === 'completed' && agentStates[5] !== 'pending') ? 0 : 20
                    }}
                    transition={{ duration: 0.5 }}
                    className="flex flex-col items-center"
                  >
                    <div className={`relative ${
                      agentStates[5] === 'completed'
                        ? 'bg-white border-blue-400 shadow-lg shadow-blue-100'
                        : agentStates[5] === 'processing'
                        ? 'bg-white border-blue-400 shadow-lg shadow-blue-100'
                        : 'bg-white border-slate-300 shadow-sm'
                    } border-2 rounded-xl p-5 w-[240px] cursor-pointer hover:scale-[1.02] hover:shadow-xl transition-all duration-200`}
                      onClick={() => agentStates[5] === 'completed' && agentResponses[5] && openResponsePopup('Final Decision Advisor', 5)}
                    >
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
                            <Gavel className="h-7 w-7 text-green-600" />
                          ) : (
                            <Gavel className="h-7 w-7 text-slate-400" />
                          )}
                        </div>
                        <div className="text-center">
                          <h4 className="font-bold text-sm text-slate-900 leading-tight">Final Decision Advisor</h4>
                          <p className="text-xs text-slate-500 mt-1">Final Recommendation</p>
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
                  </motion.div>
                </div>
              </div>
            </div>

            {/* Old Vertical Workflow - Hidden for reference */}
            <div className="hidden">
              <div className="space-y-16 py-12">
                {agents.map((agent, index) => {
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
                          ? 'left-0 right-1/2 pr-16' 
                          : 'right-0 left-1/2 pl-16'
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
                                  <Loader2 className="w-5 h-5 animate-spin" />
                                ) : isCompleted ? (
                                  <CheckCircle className="w-5 h-5" />
                                ) : (
                                  <AgentIcon className="w-5 h-5" />
                                )}
                              </div>
                              
                              <div className="flex-1 min-w-0">
                                <h3 className="font-bold text-slate-900 text-base truncate">
                                  {agent.name}
                                </h3>
                                <p className="text-xs text-slate-600 mt-0.5">
                                  {agent.role}
                                </p>
                              </div>
                            </div>

                            {/* Agent Task Description */}
                            <div className="bg-blue-50 rounded-lg p-3 border border-blue-200">
                              <div className="flex items-start space-x-2">
                                <div className="w-1.5 h-1.5 bg-blue-500 rounded-full mt-1.5 flex-shrink-0"></div>
                                <div>
                                  <span className="text-xs font-semibold text-blue-700 uppercase tracking-wide">
                                    Agent Task
                                  </span>
                                  <p className="text-xs text-slate-700 mt-1 leading-relaxed">
                                    {agent.description}
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

                            {/* View Response Indicator */}
                            {isCompleted && agentResponses[agent.step] && (
                              <div className="pt-2 border-t border-slate-200">
                                <span className="text-xs font-semibold text-blue-600 hover:text-blue-700">
                                  🔍 View Response
                                </span>
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
            {/* End of hidden old vertical workflow */}

            {/* Success Message */}
            {workflowStatus && workflowStatus.status === 'completed' && (
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                className="mt-8 p-6 bg-gradient-to-r from-green-50 to-emerald-50 border-2 border-green-400 rounded-xl shadow-lg"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <div className="p-3 bg-green-500 rounded-full">
                      <CheckCircle className="h-8 w-8 text-white" />
                    </div>
                    <div>
                      <p className="text-xl font-bold text-green-900">Processing Complete!</p>
                      <p className="text-sm text-green-700 mt-1">
                        All agents have successfully analyzed the claim. Comprehensive results are ready for review.
                      </p>
                    </div>
                  </div>
                  <Button
                    onClick={() => {
                      router.push(`/comprehensive-analysis?claimId=${claimId}&claimantName=${encodeURIComponent(claimantName || '')}`);
                    }}
                    className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white px-6 py-3 text-base font-semibold shadow-lg hover:shadow-xl transition-all"
                  >
                    📊 View Comprehensive Analysis
                  </Button>
                </div>
              </motion.div>
            )}
            </div>
          </div>
        </div>
      </div>

      {/* Agent Response Popup - Rendered via Portal */}
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
                <div className="bg-white rounded-xl p-6 border border-slate-200">
                  <div className="prose prose-slate prose-sm max-w-none">
                    <ReactMarkdown 
                      remarkPlugins={[remarkGfm]}
                      components={{
                        h1: ({...props}) => <h1 className="text-2xl font-bold text-slate-900 mt-6 mb-4 pb-2 border-b-2 border-slate-300" {...props} />,
                        h2: ({...props}) => <h2 className="text-xl font-bold text-slate-800 mt-5 mb-3" {...props} />,
                        h3: ({...props}) => <h3 className="text-lg font-semibold text-slate-700 mt-4 mb-2 uppercase tracking-wide" {...props} />,
                        h4: ({...props}) => <h4 className="text-base font-semibold text-slate-700 mt-3 mb-2" {...props} />,
                        p: ({...props}) => <p className="mb-4 text-slate-700 leading-relaxed text-[15px]" {...props} />,
                        ul: ({...props}) => <ul className="list-disc pl-6 mb-4 space-y-2 text-slate-700" {...props} />,
                        ol: ({...props}) => <ol className="list-decimal pl-6 mb-4 space-y-2 text-slate-700" {...props} />,
                        li: ({...props}) => <li className="text-slate-700 leading-relaxed pl-2" {...props} />,
                        strong: ({...props}) => <strong className="font-bold text-slate-900" {...props} />,
                        em: ({...props}) => <em className="italic text-slate-800" {...props} />,
                        code: ({inline, ...props}: any) => 
                          inline ? (
                            <code className="bg-blue-50 text-blue-700 px-2 py-0.5 rounded text-sm font-mono border border-blue-200" {...props} />
                          ) : (
                            <code className="block bg-slate-50 text-slate-800 p-4 rounded-lg text-sm font-mono overflow-x-auto border border-slate-200 my-3" {...props} />
                          ),
                        blockquote: ({...props}) => <blockquote className="border-l-4 border-blue-500 pl-4 py-2 italic text-slate-600 my-4 bg-blue-50" {...props} />,
                        table: ({...props}) => <table className="min-w-full border-collapse border border-slate-300 my-4" {...props} />,
                        thead: ({...props}) => <thead className="bg-slate-100" {...props} />,
                        tbody: ({...props}) => <tbody className="divide-y divide-slate-200" {...props} />,
                        tr: ({...props}) => <tr className="border-b border-slate-200" {...props} />,
                        th: ({...props}) => <th className="px-4 py-3 text-left font-semibold text-slate-700 border border-slate-300" {...props} />,
                        td: ({...props}) => <td className="px-4 py-3 text-slate-700 border border-slate-300" {...props} />,
                        hr: ({...props}) => <hr className="my-6 border-t-2 border-slate-300" {...props} />,
                        a: ({...props}) => <a className="text-blue-600 hover:text-blue-800 underline font-medium" target="_blank" rel="noopener noreferrer" {...props} />,
                      }}
                    >
                      {responsePopup.response}
                    </ReactMarkdown>
                  </div>
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
    </>
  );
}
