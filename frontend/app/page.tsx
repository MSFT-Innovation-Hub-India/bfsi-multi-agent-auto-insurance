'use client';

import React, { useState } from 'react';
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
  BarChart3,
  CheckCircle2,
  X
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { processClaimWithOrchestrator, checkApiHealth, ClaimResponse, AgentResponse, combinePolicyResponses } from '@/lib/api-service';

export default function LiveClaimProcessor() {
  const [currentPage, setCurrentPage] = useState<'input' | 'processing' | 'policy' | 'inspection' | 'bill' | 'final'>('input');
  const [claimId, setClaimId] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [claimResults, setClaimResults] = useState<ClaimResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedAgent, setSelectedAgent] = useState<AgentResponse | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [apiHealthy, setApiHealthy] = useState<boolean | null>(null);
  const [currentProcessingStep, setCurrentProcessingStep] = useState(0);
  const [processedSteps, setProcessedSteps] = useState<number[]>([]);

  const agentSteps = [
    { 
      id: 'policy_analysis', 
      name: 'Policy Coverage Assistant', 
      icon: Shield, 
      description: 'Extracting car details and analyzing coverage eligibility',
      dataPassedTo: 'Claims Evidence Evaluator',
      memoryInfo: 'Car basic details, IDV amount, deductibles, coverage rules'
    },
    { 
      id: 'inspection_analysis', 
      name: 'Claims Evidence Evaluator', 
      icon: Car, 
      description: 'Assessing damage and authenticity',
      dataPassedTo: 'Settlement Underwriter',
      memoryInfo: 'Damage assessment, repair estimates, authenticity check'
    },
    { 
      id: 'bill_analysis', 
      name: 'Settlement Underwriter', 
      icon: Calculator, 
      description: 'Validating repair costs and calculating reimbursement',
      dataPassedTo: 'Decision Advisor',
      memoryInfo: 'Actual bills, reimbursable amounts, cost validation'
    },
    { 
      id: 'final_recommendation', 
      name: 'Decision Advisor', 
      icon: Gavel, 
      description: 'Generating final claim recommendation',
      dataPassedTo: 'Complete',
      memoryInfo: 'Final decision, approval/rejection, summary'
    }
  ];

  React.useEffect(() => {
    checkHealth();
  }, []);

  const checkHealth = async () => {
    try {
      const health = await checkApiHealth();
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
    setCurrentPage('processing');
    setCurrentProcessingStep(0);
    setProcessedSteps([]);

    // Show step-by-step processing
    for (let i = 0; i < agentSteps.length; i++) {
      setCurrentProcessingStep(i);
      await new Promise(resolve => setTimeout(resolve, 2000)); // 2 second delay
      setProcessedSteps(prev => [...prev, i]);
    }

    try {
      const results = await processClaimWithOrchestrator(
        claimId.trim(),
        `Processing claim ${claimId.trim()}`, // Default description
        true // Always add delays for visualization
      );
      
      setClaimResults(results);
      // Instead of going to results, go to first agent page (policy)
      setCurrentPage('policy');
    } catch (error) {
      console.error('Error processing claim:', error);
      setError(`Failed to process claim: ${error instanceof Error ? error.message : 'Unknown error'}`);
      setCurrentPage('input');
    } finally {
      setIsProcessing(false);
      setCurrentProcessingStep(0);
      setProcessedSteps([]);
    }
  };

  const resetForm = () => {
    setCurrentPage('input');
    setClaimId('');
    setClaimResults(null);
    setError(null);
    setSelectedAgent(null);
    setShowModal(false);
    setCurrentProcessingStep(0);
    setProcessedSteps([]);
  };

  const openAgentModal = (agent: AgentResponse) => {
    setSelectedAgent(agent);
    setShowModal(true);
  };

  const getAgentIcon = (agentName: string) => {
    if (agentName.includes('Policy')) return <Shield className="w-5 h-5" />;
    if (agentName.includes('Inspection')) return <Car className="w-5 h-5" />;
    if (agentName.includes('Bill') || agentName.includes('Reimbursement')) return <Calculator className="w-5 h-5" />;
    if (agentName.includes('Final') || agentName.includes('Recommendation')) return <Gavel className="w-5 h-5" />;
    return <FileText className="w-5 h-5" />;
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'text-green-600 bg-green-50';
      case 'failed': return 'text-red-600 bg-red-50';
      case 'processing': return 'text-blue-600 bg-blue-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  const renderInputPage = () => (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="text-center">
        <div className="flex items-center justify-center mb-4">
          <div className="p-3 bg-blue-100 rounded-full">
            <Shield className="w-8 h-8 text-blue-600" />
          </div>
        </div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Live Insurance Claim Processor
        </h1>
        <p className="text-gray-600">
          Enter claim ID to process through our AI agent orchestrator and see live sequential handoffs
        </p>
        
        {/* API Health Status */}
        <div className="mt-4 flex items-center justify-center space-x-2">
          <div className={`w-3 h-3 rounded-full ${apiHealthy ? 'bg-green-500' : 'bg-red-500'}`}></div>
          <span className="text-sm text-gray-600">
            API Status: {apiHealthy ? 'Healthy' : 'Disconnected'}
          </span>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <FileText className="w-5 h-5" />
            <span>Claim Details</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Claim ID
            </label>
            <Input
              type="text"
              placeholder="e.g., CLM-2024-001"
              value={claimId}
              onChange={(e) => setClaimId(e.target.value)}
              className="w-full"
            />
          </div>

          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-md">
              <div className="flex items-center space-x-2">
                <AlertCircle className="w-4 h-4 text-red-600" />
                <span className="text-red-700 text-sm">{error}</span>
              </div>
            </div>
          )}

          <Button
            onClick={handleProcessClaim}
            disabled={!apiHealthy || isProcessing}
            className="w-full"
          >
            {isProcessing ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Processing Claim...
              </>
            ) : (
              "Process Claim"
            )}
          </Button>
        </CardContent>
      </Card>
    </div>
  );

  const renderProcessingPage = () => (
    <div className="min-h-screen">
      {/* Compact Fixed Header Section */}
      <div className="sticky top-0 z-50 bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-8xl mx-auto px-4 py-3">
          {/* Compact Header */}
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="p-2 bg-blue-100 rounded-full">
                <Loader2 className="w-6 h-6 text-blue-600 animate-spin" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">
                  Processing Claim {claimId}
                </h1>
                <p className="text-sm text-gray-600">
                  {isProcessing 
                    ? `Currently: ${agentSteps[currentProcessingStep]?.name || 'Processing'}`
                    : 'Processing Complete'
                  }
                </p>
              </div>
            </div>
            
            {/* Compact Progress Section */}
            <div className="flex items-center space-x-4">
              <div className="text-right">
                <div className="text-sm font-medium text-gray-800">
                  {processedSteps.length} out of {agentSteps.length} agents completed
                </div>
                <div className="text-xs text-gray-600">
                  {Math.round((processedSteps.length / agentSteps.length) * 100)}% Complete
                </div>
              </div>
              
              {/* Compact Progress Bar */}
              <div className="w-32 bg-gray-200 rounded-full h-2 shadow-inner">
                <div 
                  className="bg-gradient-to-r from-blue-500 to-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${(processedSteps.length / agentSteps.length) * 100}%` }}
                ></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Scrollable Agent Section - More Space for Flow */}
      <div className="max-w-8xl mx-auto px-4 py-4">
        {/* Agent Flow Visualization - Full Focus on Agents */}
        <Card className="shadow-lg">
          <CardHeader className="bg-gradient-to-r from-gray-50 to-gray-100 border-b py-3">
          </CardHeader>
        <CardContent className="px-6 py-8">
          {/* Enhanced Professional Layout with Better Spacing */}
          <div className="max-w-7xl mx-auto relative">
            {/* Single Continuous Vertical Line - Enhanced */}
            <div className="absolute left-1/2 top-8 bottom-8 w-2 bg-gradient-to-b from-gray-300 to-gray-400 rounded-full transform -translate-x-0.5 shadow-sm">
              {/* Green progress overlay - Enhanced */}
              <div 
                className="w-full bg-gradient-to-b from-green-400 to-green-600 rounded-full transition-all duration-1000 ease-out shadow-lg"
                style={{ 
                  height: `${(processedSteps.length / agentSteps.length) * 100}%` 
                }}
              ></div>
            </div>

            {/* Agent Steps - Optimized for Better Flow Visibility */}
            <div className="space-y-16 py-8">
              {agentSteps.map((step, index) => {
                const IconComponent = step.icon;
                const isActive = currentProcessingStep === index;
                const isCompleted = processedSteps.includes(index);
                
                return (
                  <motion.div
                    key={step.id}
                    initial={{ opacity: 0.5, x: index % 2 === 0 ? -60 : 60 }}
                    animate={{ 
                      opacity: isActive || isCompleted ? 1 : 0.7,
                      x: 0,
                      scale: isActive ? 1.02 : 1
                    }}
                    className="relative flex items-center"
                  >
                    {/* Enhanced Agent Content - Professional Boxes */}
                    <div className={`${
                      index % 2 === 0 
                        ? 'flex-row mr-auto pr-12' 
                        : 'flex-row-reverse ml-auto pl-12'
                    } flex items-center w-full max-w-xl`}>
                      
                      {/* Professional Agent Box - Optimized Size */}
                      <div className={`p-6 rounded-xl border-2 bg-white shadow-lg hover:shadow-xl transition-all duration-300 w-full max-w-md ${
                        isActive 
                          ? 'border-blue-400 bg-blue-50 shadow-blue-100' 
                          : isCompleted 
                          ? 'border-green-400 bg-green-50 shadow-green-100' 
                          : 'border-gray-200 hover:border-gray-300'
                      }`}>
                        <div className="space-y-3">
                          {/* Agent Header */}
                          <div className="flex items-start space-x-3">
                            <div className={`p-2 rounded-lg ${
                              isActive 
                                ? 'bg-blue-100 text-blue-600' 
                                : isCompleted 
                                ? 'bg-green-100 text-green-600' 
                                : 'bg-gray-100 text-gray-600'
                            }`}>
                              <IconComponent className="w-5 h-5" />
                            </div>
                            <div className="flex-1">
                              <h3 className="font-bold text-lg text-gray-800 mb-1">
                                {step.name}
                              </h3>
                              <p className="text-sm text-gray-600 leading-relaxed">
                                {step.description}
                              </p>
                            </div>
                          </div>
                          
                          {/* Memory Information - Compact */}
                          <div className="p-2 bg-purple-50 rounded-lg border border-purple-200">
                            <div className="flex items-start space-x-2">
                              <div className="w-1.5 h-1.5 bg-purple-400 rounded-full mt-1.5 flex-shrink-0"></div>
                              <div>
                                <span className="text-xs font-semibold text-purple-700 uppercase tracking-wide">
                                  Memory Storage
                                </span>
                                <p className="text-xs text-purple-600 mt-0.5">
                                  {step.memoryInfo}
                                </p>
                              </div>
                            </div>
                          </div>

                          {/* Processing Status */}
                          {(isActive || isCompleted) && (
                            <div className="flex items-center space-x-2">
                              {isActive && (
                                <>
                                  <Loader2 className="w-3 h-3 text-blue-600 animate-spin" />
                                  <span className="text-xs font-medium text-blue-600">
                                    Processing...
                                  </span>
                                </>
                              )}
                              {isCompleted && (
                                <>
                                  <CheckCircle2 className="w-3 h-3 text-green-600" />
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

                    {/* Enhanced Step Indicator on the Line */}
                    <div className="absolute left-1/2 transform -translate-x-1/2 z-10">
                      <div className={`w-12 h-12 rounded-full flex items-center justify-center transition-all duration-500 border-3 ${
                        isActive 
                          ? 'bg-blue-500 border-blue-300 shadow-xl shadow-blue-200 scale-110' 
                          : isCompleted 
                          ? 'bg-green-500 border-green-300 shadow-xl shadow-green-200' 
                          : 'bg-gray-300 border-gray-200 shadow-lg'
                      }`}>
                        <IconComponent className={`w-5 h-5 ${
                          isActive || isCompleted ? 'text-white' : 'text-gray-600'
                        }`} />
                      </div>
                    </div>
                  </motion.div>
                );
              })}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
    </div>
  );

  // New individual agent pages
  const renderPolicyPage = () => {
    if (!claimResults || !claimResults.policy_analysis) return null;
    
    return (
      <div className="max-w-6xl mx-auto">
        {renderCompactHeader("Policy Analysis", 1, 4)}
        
        <Card className="shadow-lg">
          <CardHeader className="bg-gradient-to-r from-green-50 to-blue-50">
            <CardTitle className="flex items-center space-x-3">
              <Shield className="w-6 h-6 text-green-600" />
              <span>Policy Analysis Results</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="p-8">
            <div className="space-y-6">
              <div className="bg-green-50 p-4 rounded-lg border border-green-200">
                <h3 className="font-semibold text-green-800 mb-2">Status: Completed</h3>
                <p className="text-green-700">Car details extracted and coverage eligibility analyzed</p>
              </div>
              
              <div className="bg-gray-50 p-6 rounded-lg">
                <h3 className="font-semibold mb-4">Full Analysis:</h3>
                <pre className="whitespace-pre-wrap text-sm text-gray-700">
                  {claimResults.policy_analysis.response}
                </pre>
              </div>
            </div>
            
            <div className="flex justify-end mt-8">
              <Button 
                onClick={() => setCurrentPage('inspection')}
                className="px-8"
              >
                Next: Inspection Analysis →
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  };

  const renderInspectionPage = () => {
    if (!claimResults || !claimResults.inspection_analysis) return null;
    
    return (
      <div className="max-w-6xl mx-auto">
        {renderCompactHeader("Inspection Analysis", 2, 4)}
        
        <Card className="shadow-lg">
          <CardHeader className="bg-gradient-to-r from-blue-50 to-indigo-50">
            <CardTitle className="flex items-center space-x-3">
              <Car className="w-6 h-6 text-blue-600" />
              <span>Inspection Analysis Results</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="p-8">
            <div className="space-y-6">
              <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                <h3 className="font-semibold text-blue-800 mb-2">Status: Completed</h3>
                <p className="text-blue-700">Damage assessment and authenticity verification complete</p>
              </div>
              
              <div className="bg-gray-50 p-6 rounded-lg">
                <h3 className="font-semibold mb-4">Full Analysis:</h3>
                <pre className="whitespace-pre-wrap text-sm text-gray-700">
                  {claimResults.inspection_analysis.response}
                </pre>
              </div>
            </div>
            
            <div className="flex justify-between mt-8">
              <Button 
                variant="outline"
                onClick={() => setCurrentPage('policy')}
              >
                ← Back: Policy Analysis
              </Button>
              <Button 
                onClick={() => setCurrentPage('bill')}
                className="px-8"
              >
                Next: Bill Analysis →
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  };

  const renderBillPage = () => {
    if (!claimResults || !claimResults.bill_analysis) return null;
    
    return (
      <div className="max-w-6xl mx-auto">
        {renderCompactHeader("Bill Reimbursement", 3, 4)}
        
        <Card className="shadow-lg">
          <CardHeader className="bg-gradient-to-r from-orange-50 to-yellow-50">
            <CardTitle className="flex items-center space-x-3">
              <Calculator className="w-6 h-6 text-orange-600" />
              <span>Bill Reimbursement Results</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="p-8">
            <div className="space-y-6">
              <div className="bg-orange-50 p-4 rounded-lg border border-orange-200">
                <h3 className="font-semibold text-orange-800 mb-2">Status: Completed</h3>
                <p className="text-orange-700">Repair costs validated and reimbursement calculated</p>
              </div>
              
              <div className="bg-gray-50 p-6 rounded-lg">
                <h3 className="font-semibold mb-4">Full Analysis:</h3>
                <pre className="whitespace-pre-wrap text-sm text-gray-700">
                  {claimResults.bill_analysis.response}
                </pre>
              </div>
            </div>
            
            <div className="flex justify-between mt-8">
              <Button 
                variant="outline"
                onClick={() => setCurrentPage('inspection')}
              >
                ← Back: Inspection Analysis
              </Button>
              <Button 
                onClick={() => setCurrentPage('final')}
                className="px-8"
              >
                Final Decision →
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  };

  const renderFinalPage = () => {
    if (!claimResults || !claimResults.final_recommendation) return null;
    
    return (
      <div className="max-w-6xl mx-auto">
        {renderCompactHeader("Final Decision", 4, 4)}
        
        <Card className="shadow-lg">
          <CardHeader className="bg-gradient-to-r from-purple-50 to-indigo-50">
            <CardTitle className="flex items-center space-x-3">
              <Gavel className="w-6 h-6 text-purple-600" />
              <span>Final Claim Decision</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="p-8">
            <div className="space-y-6">
              <div className="bg-gray-50 p-6 rounded-lg">
                <h3 className="font-semibold mb-4">Complete Analysis & Recommendation:</h3>
                <pre className="whitespace-pre-wrap text-sm text-gray-700">
                  {claimResults.final_recommendation.response}
                </pre>
              </div>
              
              {/* Approve/Reject Section */}
              <div className="bg-white border-2 border-gray-200 rounded-lg p-6">
                <h3 className="text-xl font-semibold mb-4 text-center">Claim Decision Required</h3>
                <div className="flex justify-center space-x-4">
                  <Button 
                    className="px-8 py-3 bg-green-600 hover:bg-green-700 text-white"
                    onClick={() => {
                      alert('Claim Approved! Processing payment...');
                      setCurrentPage('input');
                    }}
                  >
                    <CheckCircle className="w-5 h-5 mr-2" />
                    Approve Claim
                  </Button>
                  <Button 
                    variant="destructive"
                    className="px-8 py-3"
                    onClick={() => {
                      alert('Claim Rejected. Customer will be notified.');
                      setCurrentPage('input');
                    }}
                  >
                    <X className="w-5 h-5 mr-2" />
                    Reject Claim
                  </Button>
                </div>
              </div>
            </div>
            
            <div className="flex justify-between mt-8">
              <Button 
                variant="outline"
                onClick={() => setCurrentPage('bill')}
              >
                ← Back: Bill Analysis
              </Button>
              <Button 
                variant="outline"
                onClick={() => setCurrentPage('input')}
              >
                Process New Claim
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  };

  const renderCompactHeader = (title: string, step: number, total: number) => (
    <div className="mb-6">
      <div className="text-center mb-4">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Claim Processing Results
        </h1>
        <p className="text-gray-600">Claim ID: {claimResults?.claim_id}</p>
      </div>
      
      {/* Progress Indicator */}
      <div className="bg-white rounded-lg p-4 shadow-sm border">
        <div className="flex items-center justify-between mb-2">
          <span className="text-lg font-semibold">{title}</span>
          <span className="text-sm text-gray-600">Step {step} of {total}</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div 
            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
            style={{ width: `${(step / total) * 100}%` }}
          ></div>
        </div>
      </div>
    </div>
  );

  const renderResultsPage = () => {
    if (!claimResults) return null;

    // Combine policy basic details + policy analysis using helper function
    const combinedPolicyData = combinePolicyResponses(
      claimResults.policy_basic_details,
      claimResults.policy_analysis
    );

    const agents = [
      { key: 'policy_combined', data: combinedPolicyData, title: 'Policy Analysis', step: agentSteps[0] },
      { key: 'inspection_analysis', data: claimResults.inspection_analysis, title: 'Inspection Analysis', step: agentSteps[1] },
      { key: 'bill_analysis', data: claimResults.bill_analysis, title: 'Bill Reimbursement', step: agentSteps[2] },
      { key: 'final_recommendation', data: claimResults.final_recommendation, title: 'Final Recommendation', step: agentSteps[3] }
    ].filter(agent => agent.data);

    return (
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header */}
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Claim Processing Results
          </h1>
          <p className="text-gray-600">Claim ID: {claimResults.claim_id}</p>
          <p className="text-sm text-gray-500 mt-2">
            See how data flowed through each agent in the orchestration
          </p>
        </div>

        {/* Summary Card */}
        <Card className="bg-gradient-to-r from-green-50 to-blue-50">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <BarChart3 className="w-5 h-5" />
              <span>Processing Summary</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">
                  {claimResults.summary.successful_agents}
                </div>
                <div className="text-sm text-gray-600">Successful Agents</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-red-600">
                  {claimResults.summary.failed_agents}
                </div>
                <div className="text-sm text-gray-600">Failed Agents</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">
                  {claimResults.summary.total_agents_processed}
                </div>
                <div className="text-sm text-gray-600">Total Agents</div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Agent Flow Results - Simple Cards */}
        <div className="space-y-6">
          {agents.map((agent, index) => {
            const IconComponent = agent.step.icon;
            return (
              <motion.div
                key={agent.key}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
              >
                <Card className="border-l-4 border-l-green-500 shadow-sm">
                  <CardHeader>
                    <CardTitle className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <div className="p-3 bg-green-100 rounded-full">
                          <IconComponent className="w-6 h-6 text-green-600" />
                        </div>
                        <div>
                          <span className="text-xl font-semibold text-green-900">{agent.title}</span>
                          <div className="text-sm text-gray-600 mt-1">{agent.step.description}</div>
                        </div>
                      </div>
                      <div className="px-4 py-2 rounded-full text-sm font-medium bg-green-100 text-green-700">
                        ✅ Completed
                      </div>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid md:grid-cols-4 gap-6">
                      <div className="md:col-span-3">
                        <div className="text-gray-700 text-sm leading-relaxed">
                          {agent.data!.response.substring(0, 400)}...
                        </div>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => openAgentModal(agent.data!)}
                          className="mt-4"
                        >
                          <FileText className="w-4 h-4 mr-2" />
                          View Full Analysis
                        </Button>
                      </div>
                      
                      <div className="space-y-4">
                        <div className="bg-purple-50 p-4 rounded-lg border border-purple-200">
                          <div className="flex items-center space-x-2 mb-2">
                            <span className="text-sm font-semibold text-purple-700">Memory</span>
                          </div>
                          <div className="text-xs text-purple-600 leading-relaxed">{agent.step.memoryInfo}</div>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            );
          })}
        </div>

        {/* Actions */}
        <div className="flex justify-center space-x-4">
          <Button onClick={resetForm} variant="outline">
            Process Another Claim
          </Button>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <AnimatePresence mode="wait">
        {currentPage === 'input' && (
          <motion.div
            key="input"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
          >
            {renderInputPage()}
          </motion.div>
        )}
        
        {currentPage === 'processing' && (
          <motion.div
            key="processing"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
          >
            {renderProcessingPage()}
          </motion.div>
        )}
        
        {currentPage === 'policy' && (
          <motion.div
            key="policy"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
          >
            {renderPolicyPage()}
          </motion.div>
        )}
        
        {currentPage === 'inspection' && (
          <motion.div
            key="inspection"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
          >
            {renderInspectionPage()}
          </motion.div>
        )}
        
        {currentPage === 'bill' && (
          <motion.div
            key="bill"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
          >
            {renderBillPage()}
          </motion.div>
        )}
        
        {currentPage === 'final' && (
          <motion.div
            key="final"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
          >
            {renderFinalPage()}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
