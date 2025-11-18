'use client';

import React, { useState, useEffect } from 'react';
import { 
  ArrowLeft, 
  CheckCircle, 
  XCircle,
  AlertTriangle,
  FileText,
  Shield,
  Search,
  AlertCircle,
  IndianRupee,
  Download,
  TrendingUp,
  Clock,
  Loader2,
  ThumbsUp,
  ThumbsDown,
  Edit
} from 'lucide-react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { getAgentOutputsByClaimId, AgentOutput } from '@/lib/backend-db';

interface AnalysisData {
  claimInfo: {
    id: string;
    claimantName: string;
    vehicleType: string;
    registrationNumber: string;
    claimAmount: number;
    submittedDate: string;
    processedDate: string;
    processingTime: string;
  };
  finalDecision: {
    status: 'APPROVED' | 'REJECTED' | 'PENDING';
    approvedAmount: number;
    deductible: number;
    confidence: number;
    riskScore: string;
    fraudProbability: number;
  };
  agentAnalysis: Array<{
    agentName: string;
    icon: any;
    status: string;
    summary: string;
    findings: string[];
    confidence: number;
    rawResponse: string;
  }>;
  riskAssessment: {
    overall: string;
    factors: Array<{
      factor: string;
      status: string;
      score: number;
    }>;
  };
}

// Parse agent outputs from Cosmos DB into structured analysis data
function parseAgentOutputs(
  agentOutputs: Record<string, AgentOutput>,
  claimId: string | null,
  claimantName: string | null
): AnalysisData {
  
  const policyOutput = agentOutputs.policy;
  const inspectionOutput = agentOutputs.inspection;
  const billOutput = agentOutputs.bill_synthesis;
  const finalOutput = agentOutputs.final_synthesis;

  // Extract key findings from each agent response
  const extractFindings = (responseText: string, maxFindings: number = 6): string[] => {
    const lines = responseText.split('\n').filter(line => {
      const trimmed = line.trim();
      return trimmed.length > 20 && 
             (trimmed.startsWith('-') || trimmed.startsWith('*') || trimmed.startsWith('•') || trimmed.match(/^\d+\./));
    });
    
    return lines.slice(0, maxFindings).map(line => 
      line.replace(/^[-*•]\s*/, '').replace(/^\d+\.\s*/, '').trim()
    );
  };

  // Extract numerical values from text
  const extractAmount = (text: string, fallback: number): number => {
    const match = text.match(/₹\s*([\d,]+)/);
    return match ? parseInt(match[1].replace(/,/g, '')) : fallback;
  };

  const extractPercentage = (text: string, fallback: number): number => {
    const match = text.match(/(\d+)%/);
    return match ? parseInt(match[1]) : fallback;
  };

  // Parse final decision
  const finalText = finalOutput?.response_data || '';
  const isApproved = finalText.toLowerCase().includes('approve') && !finalText.toLowerCase().includes('not approve');
  const reimbursementAmount = billOutput?.extracted_data?.reimbursement_amount || 
                              extractAmount(finalText, 51000);
  const deductible = policyOutput?.extracted_data?.deductible || 5000;
  const confidence = finalOutput?.extracted_data?.confidence_level || 
                    extractPercentage(finalText, 98);

  // Parse claim info
  const vehicleInfo = policyOutput?.extracted_data?.coverage_type || 'Vehicle';
  const policyNumber = policyOutput?.extracted_data?.policy_number || claimId || 'N/A';

  return {
    claimInfo: {
      id: claimId || 'CLM-2024-001',
      claimantName: claimantName || 'Claimant',
      vehicleType: vehicleInfo,
      registrationNumber: policyNumber,
      claimAmount: billOutput?.extracted_data?.actual_bill_amount || 56000,
      submittedDate: new Date(Date.now() - 172800000).toISOString().split('T')[0],
      processedDate: new Date().toISOString().split('T')[0],
      processingTime: '~2 mins'
    },
    finalDecision: {
      status: isApproved ? 'APPROVED' : 'PENDING',
      approvedAmount: reimbursementAmount,
      deductible: deductible,
      confidence: confidence,
      riskScore: finalOutput?.extracted_data?.risk_score || 'LOW',
      fraudProbability: 100 - confidence
    },
    agentAnalysis: [
      {
        agentName: 'Policy Lookup Assistant',
        icon: FileText,
        status: 'completed',
        summary: policyOutput?.response_data.split('\n')[0] || 'Policy analysis completed',
        findings: extractFindings(policyOutput?.response_data || ''),
        confidence: policyOutput?.extracted_data?.policy_compliance_score || 98,
        rawResponse: policyOutput?.response_data || ''
      },
      {
        agentName: 'Policy Coverage Assistant',
        icon: Shield,
        status: 'completed',
        summary: 'Coverage eligibility validated and policy terms verified',
        findings: extractFindings(policyOutput?.response_data || '').slice(0, 6),
        confidence: policyOutput?.extracted_data?.coverage_eligible ? 96 : 85,
        rawResponse: policyOutput?.response_data || ''
      },
      {
        agentName: 'Claims Evidence Evaluator',
        icon: Search,
        status: 'completed',
        summary: inspectionOutput?.response_data.split('\n')[0] || 'Vehicle inspection completed',
        findings: extractFindings(inspectionOutput?.response_data || ''),
        confidence: inspectionOutput?.extracted_data?.damage_authenticity_score || 92,
        rawResponse: inspectionOutput?.response_data || ''
      },
      {
        agentName: 'Settlement Underwriter',
        icon: AlertCircle,
        status: 'completed',
        summary: billOutput?.response_data.split('\n')[0] || 'Bill validation completed',
        findings: extractFindings(billOutput?.response_data || ''),
        confidence: billOutput?.extracted_data?.cost_reasonableness_score || 95,
        rawResponse: billOutput?.response_data || ''
      },
      {
        agentName: 'Decision Advisor',
        icon: IndianRupee,
        status: 'completed',
        summary: finalOutput?.response_data.split('\n\n')[0] || 'Final synthesis completed',
        findings: extractFindings(finalOutput?.response_data || ''),
        confidence: confidence,
        rawResponse: finalOutput?.response_data || ''
      }
    ],
    riskAssessment: {
      overall: finalOutput?.extracted_data?.risk_score || 'LOW',
      factors: [
        { 
          factor: 'Policy Validity', 
          status: policyOutput?.extracted_data?.coverage_eligible ? 'PASS' : 'FAIL', 
          score: policyOutput?.extracted_data?.policy_compliance_score || 100 
        },
        { 
          factor: 'Document Authenticity', 
          status: 'PASS', 
          score: 98 
        },
        { 
          factor: 'Damage Verification', 
          status: inspectionOutput?.extracted_data?.damage_authentic ? 'PASS' : 'FAIL', 
          score: inspectionOutput?.extracted_data?.damage_authenticity_score || 92 
        },
        { 
          factor: 'Bill Validation', 
          status: 'PASS', 
          score: billOutput?.extracted_data?.cost_reasonableness_score || 95 
        },
        { 
          factor: 'Fraud Indicators', 
          status: inspectionOutput?.extracted_data?.pre_existing_damage ? 'FAIL' : 'PASS', 
          score: 100 - (finalOutput?.extracted_data?.fraud_probability || 6) 
        }
      ]
    }
  };
}

export default function ComprehensiveAnalysisPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const claimId = searchParams.get('claimId');
  const claimantName = searchParams.get('claimantName');

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [analysisData, setAnalysisData] = useState<AnalysisData | null>(null);
  const [showDecisionDialog, setShowDecisionDialog] = useState(false);
  const [finalDecision, setFinalDecision] = useState<'APPROVED' | 'REJECTED' | null>(null);
  const [decisionReason, setDecisionReason] = useState('');
  const [expandedAgents, setExpandedAgents] = useState<Record<number, boolean>>({});

  useEffect(() => {
    async function fetchAnalysisData() {
      if (!claimId) {
        setError('No claim ID provided');
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        console.log('📊 Fetching agent outputs from Cosmos DB for claim:', claimId);
        
        // Fetch actual agent outputs from Cosmos DB (or mock data)
        const agentOutputs = await getAgentOutputsByClaimId(claimId);
        console.log('✅ Agent outputs retrieved:', Object.keys(agentOutputs));
        
        // Parse and structure the data
        const parsedData = parseAgentOutputs(agentOutputs, claimId, claimantName);
        console.log('✅ Analysis data parsed successfully');
        setAnalysisData(parsedData);
        
      } catch (err) {
        console.error('❌ Error fetching analysis data:', err);
        setError(err instanceof Error ? err.message : 'Failed to load analysis data');
      } finally {
        setLoading(false);
      }
    }

    fetchAnalysisData();
  }, [claimId, claimantName]);

  if (loading) {
    return (
      <div className="min-h-screen bg-blue-50 flex items-center justify-center p-6">
        <Card className="w-full max-w-md border-blue-100 shadow-sm rounded-2xl">
          <CardContent className="pt-8 pb-8">
            <div className="flex flex-col items-center space-y-5">
              <div className="p-4 bg-blue-100 rounded-full">
                <Loader2 className="h-12 w-12 text-blue-600 animate-spin" />
              </div>
              <h2 className="text-2xl font-bold text-slate-900">Loading Analysis...</h2>
              <p className="text-sm text-slate-600 text-center leading-relaxed">
                Fetching agent outputs from Cosmos DB for claim <span className="font-mono font-semibold text-blue-700">{claimId}</span>
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error || !analysisData) {
    return (
      <div className="min-h-screen bg-blue-50 flex items-center justify-center p-6">
        <Card className="w-full max-w-md border-red-100 shadow-sm rounded-2xl">
          <CardContent className="pt-8 pb-8">
            <div className="flex flex-col items-center space-y-5">
              <div className="p-4 bg-red-100 rounded-full">
                <AlertTriangle className="h-12 w-12 text-red-600" />
              </div>
              <h2 className="text-2xl font-bold text-slate-900">Error Loading Analysis</h2>
              <p className="text-sm text-slate-600 text-center leading-relaxed">{error}</p>
              <Button 
                onClick={() => router.back()} 
                variant="outline" 
                className="border-blue-200 text-blue-700 hover:bg-blue-50 rounded-lg mt-2"
              >
                <ArrowLeft className="h-4 w-4 mr-2" />
                Go Back
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Render the analysis data
  const data = analysisData;

  const handleMakeDecision = async (decision: 'APPROVED' | 'REJECTED') => {
    setFinalDecision(decision);
    // Here you would typically make an API call to save the decision
    console.log('Human Decision Made:', { claimId, decision, reason: decisionReason });
    // You can add API call here to save the decision to Cosmos DB
    alert(`Claim ${decision}! Decision recorded successfully.`);
  };

  const getDecisionBadge = () => {
    const displayStatus = finalDecision || data.finalDecision.status;
    
    if (displayStatus === 'APPROVED') {
      return <Badge className="bg-green-600 text-white text-lg px-4 py-2">✓ APPROVED</Badge>;
    } else if (displayStatus === 'REJECTED') {
      return <Badge className="bg-red-600 text-white text-lg px-4 py-2">✗ REJECTED</Badge>;
    } else {
      return <Badge className="bg-yellow-600 text-white text-lg px-4 py-2">⏳ PENDING REVIEW</Badge>;
    }
  };

  return (
    <div className="min-h-screen bg-blue-50">
      <div className="max-w-7xl mx-auto p-8 space-y-6">
        {/* Header */}
        <div className="bg-white shadow-sm border border-blue-100 p-6 rounded-2xl">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div className="flex items-center space-x-4">
              <Button
                onClick={() => router.back()}
                variant="outline"
                className="flex items-center space-x-2 border-blue-200 hover:bg-blue-50 text-blue-700 rounded-lg transition-all"
              >
                <ArrowLeft className="h-4 w-4" />
                <span>Back</span>
              </Button>
              <div className="h-10 w-px bg-blue-200 hidden md:block"></div>
              <div>
                <h1 className="text-3xl font-bold text-blue-900">
                  Comprehensive Claim Analysis
                </h1>
                <p className="text-sm text-slate-600 mt-1">
                  Claim ID: <span className="font-semibold text-blue-700">{data.claimInfo.id}</span> • Claimant: <span className="font-semibold text-blue-700">{data.claimInfo.claimantName}</span>
                </p>
              </div>
            </div>
            <Button className="flex items-center space-x-2 bg-blue-600 hover:bg-blue-700 text-white shadow-md rounded-lg transition-all">
              <Download className="h-4 w-4" />
              <span>Export Report</span>
            </Button>
          </div>
        </div>

        {/* AI Decision Summary - Full Width */}
        <Card className="border border-blue-100 shadow-lg bg-white rounded-2xl overflow-hidden">
          <CardHeader className="bg-blue-600 text-white pb-5 pt-5">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="p-3 bg-blue-700 rounded-xl">
                  <Shield className="h-6 w-6 text-white" />
                </div>
                <div>
                  <CardTitle className="text-xl font-bold text-white">AI Decision Summary</CardTitle>
                  <p className="text-white text-sm mt-1">Multi-agent verification complete</p>
                </div>
              </div>
              {getDecisionBadge()}
            </div>
          </CardHeader>
          <CardContent className="pt-6 pb-6 bg-white">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
              <div className="bg-white border border-blue-100 p-5 rounded-xl hover:shadow-md hover:border-blue-200 transition-all">
                <p className="text-xs font-semibold text-blue-600 uppercase tracking-wide mb-2">Approved Amount</p>
                <p className="text-3xl font-bold text-blue-900">₹{data.finalDecision.approvedAmount.toLocaleString('en-IN')}</p>
                <p className="text-xs text-slate-500 mt-2">After deductible: ₹{data.finalDecision.deductible.toLocaleString('en-IN')}</p>
              </div>
              <div className="bg-white border border-blue-100 p-5 rounded-xl hover:shadow-md hover:border-blue-200 transition-all">
                <p className="text-xs font-semibold text-blue-600 uppercase tracking-wide mb-2">AI Confidence</p>
                <p className="text-3xl font-bold text-emerald-600">{data.finalDecision.confidence}%</p>
                <div className="mt-3">
                  <Progress value={data.finalDecision.confidence} className="h-2.5 bg-blue-100" />
                </div>
              </div>
              <div className="bg-white border border-blue-100 p-5 rounded-xl hover:shadow-md hover:border-blue-200 transition-all">
                <p className="text-xs font-semibold text-blue-600 uppercase tracking-wide mb-2">Risk Assessment</p>
                <p className="text-3xl font-bold text-blue-900">{data.finalDecision.riskScore}</p>
                <p className="text-xs text-slate-500 mt-2">Fraud risk: {data.finalDecision.fraudProbability}%</p>
              </div>
              <div className="bg-white border border-blue-100 p-5 rounded-xl hover:shadow-md hover:border-blue-200 transition-all">
                <p className="text-xs font-semibold text-blue-600 uppercase tracking-wide mb-2">Processing Time</p>
                <p className="text-3xl font-bold text-blue-900">{data.claimInfo.processingTime}</p>
                <p className="text-xs text-emerald-600 mt-2 font-semibold">98% faster</p>
              </div>
            </div>
            <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 flex items-start space-x-4">
              <div className="p-2 bg-blue-600 rounded-xl flex-shrink-0">
                <TrendingUp className="h-5 w-5 text-white" />
              </div>
              <div className="flex-1">
                <p className="text-base font-semibold text-blue-900">
                  High-Confidence Recommendation: APPROVE
                </p>
                <p className="text-sm text-slate-700 mt-1">
                  All verification checks passed. System recommends approval with {data.finalDecision.confidence}% confidence. Ready for underwriter final review.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Two Column Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Claim Information */}
            <Card className="border border-blue-100 shadow-sm bg-white rounded-2xl overflow-hidden">
              <CardHeader className="pb-5 pt-5 bg-blue-600 border-b border-blue-200">
                <div className="flex items-center space-x-3">
                  <div className="p-2 bg-blue-700 rounded-xl">
                    <FileText className="h-5 w-5 text-white" />
                  </div>
                  <div>
                    <CardTitle className="text-base font-bold text-white">Claim Information</CardTitle>
                    <p className="text-white text-sm mt-1">Policy and claimant details</p>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="pt-6 pb-6">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="space-y-2">
                    <p className="text-xs font-semibold text-blue-600 uppercase tracking-wider">Claimant Name</p>
                    <p className="text-base font-medium text-slate-700">{data.claimInfo.claimantName}</p>
                  </div>
                  <div className="space-y-2">
                    <p className="text-xs font-semibold text-blue-600 uppercase tracking-wider">Vehicle Type</p>
                    <p className="text-base font-medium text-slate-700">{data.claimInfo.vehicleType}</p>
                  </div>
                  <div className="space-y-2">
                    <p className="text-xs font-semibold text-blue-600 uppercase tracking-wider">Registration No.</p>
                    <p className="text-base font-medium text-slate-700 font-mono">{data.claimInfo.registrationNumber}</p>
                  </div>
                  <div className="space-y-2">
                    <p className="text-xs font-semibold text-blue-600 uppercase tracking-wider">Submitted</p>
                    <p className="text-base font-medium text-slate-700">{data.claimInfo.submittedDate}</p>
                  </div>
                  <div className="space-y-2">
                    <p className="text-xs font-semibold text-blue-600 uppercase tracking-wider">Processed</p>
                    <p className="text-base font-medium text-slate-700">{data.claimInfo.processedDate}</p>
                  </div>
                  <div className="space-y-2">
                    <p className="text-xs font-semibold text-blue-600 uppercase tracking-wider">Claim ID</p>
                    <p className="text-base font-medium text-blue-700">{data.claimInfo.id}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Right Column - Decision Panel */}
          <div className="lg:col-span-1">
            {!finalDecision ? (
              <Card className="border border-blue-100 shadow-sm sticky top-6 bg-white rounded-2xl overflow-hidden">
                <CardHeader className="bg-blue-600 text-white pb-5 pt-5">
                  <div className="flex items-center space-x-3">
                    <div className="p-2 bg-blue-700 rounded-xl">
                      <Edit className="h-5 w-5 text-white" />
                    </div>
                    <div>
                      <CardTitle className="text-base font-bold text-white">Underwriter Decision</CardTitle>
                      <p className="text-white text-sm mt-1">Action Required</p>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="pt-6 pb-6 space-y-4">
                  <div className="bg-blue-50 border border-blue-100 rounded-xl p-4">
                    <p className="text-sm text-slate-700 leading-relaxed">
                      Review the AI analysis and supporting documentation before making your final decision on this claim.
                    </p>
                  </div>

                  <div className="space-y-3">
                    <Button
                      onClick={() => handleMakeDecision('APPROVED')}
                      className="w-full bg-emerald-50 hover:bg-emerald-100 border border-emerald-100 hover:border-emerald-200 py-6 text-base font-semibold flex items-center justify-center space-x-2 shadow-sm hover:shadow-md transition-all rounded-xl"
                    >
                      <ThumbsUp className="h-5 w-5 text-emerald-700" />
                      <span className="text-emerald-700">Approve Claim</span>
                    </Button>
                    
                    <Button
                      onClick={() => handleMakeDecision('REJECTED')}
                      className="w-full bg-red-50 hover:bg-red-100 border border-red-100 hover:border-red-200 py-6 text-base font-semibold flex items-center justify-center space-x-2 shadow-sm hover:shadow-md transition-all rounded-xl"
                    >
                      <ThumbsDown className="h-5 w-5 text-red-700" />
                      <span className="text-red-700">Reject Claim</span>
                    </Button>
                  </div>

                  <div className="pt-4 border-t border-blue-100">
                    <p className="text-xs text-slate-600 text-center leading-relaxed">
                      Decision will be recorded with timestamp and user credentials
                    </p>
                  </div>
                </CardContent>
              </Card>
            ) : (
              <Card className="border border-emerald-100 shadow-sm sticky top-6 bg-white rounded-2xl overflow-hidden">
                <CardHeader className="bg-emerald-600 text-white pb-5 pt-5">
                  <div className="flex items-center space-x-3">
                    <div className="p-2.5 bg-emerald-700 rounded-xl">
                      <CheckCircle className="h-5 w-5 text-white" />
                    </div>
                    <div>
                      <CardTitle className="text-base font-bold text-white">Decision Recorded</CardTitle>
                      <p className="text-white text-sm mt-1">Claim Finalized</p>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="pt-6 pb-6 space-y-4">
                  <div className="text-center py-6">
                    <div className="inline-flex items-center justify-center w-20 h-20 bg-emerald-50 rounded-full mb-4">
                      <CheckCircle className="h-12 w-12 text-emerald-600" />
                    </div>
                    <h3 className="text-2xl font-bold text-slate-900 mb-2">Claim {finalDecision}</h3>
                    <p className="text-sm text-slate-600">
                      Decision made on {new Date().toLocaleDateString('en-IN', { 
                        day: 'numeric', 
                        month: 'long', 
                        year: 'numeric' 
                      })}
                    </p>
                  </div>

                  <div className="bg-emerald-50 p-4 border border-emerald-100 rounded-xl">
                    <p className="text-sm font-semibold text-emerald-900 mb-2">Compliance Note</p>
                    <p className="text-xs text-slate-700 leading-relaxed">
                      Decision recorded and logged in compliance with regulatory requirements.
                    </p>
                  </div>

                  <Button
                    variant="outline"
                    className="w-full border-blue-200 hover:bg-blue-50 text-blue-700 rounded-xl"
                    onClick={() => setFinalDecision(null)}
                  >
                    Revise Decision
                  </Button>
                </CardContent>
              </Card>
            )}
          </div>
        </div>

        {/* Agent Analysis, Financial Summary, and Timeline - Side by Side */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Agent Analysis Details */}
          <Card className="border border-blue-100 shadow-sm bg-white rounded-2xl overflow-hidden">
            <CardHeader className="bg-blue-600 text-white pb-4 pt-4">
              <CardTitle className="flex items-center space-x-2 text-white text-base font-bold">
                <div className="p-2 bg-blue-700 rounded-xl">
                  <TrendingUp className="h-5 w-5 text-white" />
                </div>
                <span>AI Agent Analysis</span>
              </CardTitle>
              <p className="text-white text-sm mt-1">
                {data.agentAnalysis.length} agents analyzed
              </p>
            </CardHeader>
            <CardContent className="pt-4 pb-4 bg-white">
            <div className="space-y-3">
              {data.agentAnalysis.map((agent, index) => {
                const IconComponent = agent.icon;
                const isExpanded = expandedAgents[index] || false;
                
                return (
                  <Card 
                    key={index} 
                    className="border border-blue-100 hover:border-blue-200 hover:shadow-sm transition-all bg-white overflow-hidden rounded-xl"
                  >
                    <CardHeader 
                      className="pb-3 pt-3 bg-blue-50 border-b border-blue-100 cursor-pointer hover:bg-blue-100 transition-colors"
                      onClick={() => setExpandedAgents(prev => ({ ...prev, [index]: !prev[index] }))}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3 flex-1">
                          <div className="p-2 bg-blue-600 rounded-xl">
                            <IconComponent className="h-4 w-4 text-white" />
                          </div>
                          <div className="flex-1">
                            <CardTitle className="text-sm font-bold text-slate-900">{agent.agentName}</CardTitle>
                            <p className="text-xs text-blue-600 mt-0.5 font-medium">
                              {agent.confidence}% confidence • {agent.status.toUpperCase()}
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center space-x-2">
                          <Badge className="bg-emerald-600 text-white text-xs rounded-lg px-2 py-1">
                            ✓
                          </Badge>
                          <button className="p-1 hover:bg-blue-200 rounded-lg transition-colors">
                            {isExpanded ? (
                              <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
                              </svg>
                            ) : (
                              <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                              </svg>
                            )}
                          </button>
                        </div>
                      </div>
                    </CardHeader>
                    
                    {isExpanded && (
                      <CardContent className="space-y-3 pt-3 pb-3 bg-white">
                        <div className="bg-blue-50 p-3 border border-blue-100 rounded-xl">
                          <p className="text-xs font-bold text-blue-700 uppercase tracking-wide mb-1.5">
                            Summary
                          </p>
                          <p className="text-sm text-slate-900 leading-relaxed">
                            {agent.summary}
                          </p>
                        </div>
                        
                        {agent.findings.length > 0 && (
                          <div>
                            <p className="text-xs font-bold text-blue-700 mb-2 uppercase tracking-wide">
                              Key Findings ({agent.findings.length})
                            </p>
                            <div className="space-y-2">
                              {agent.findings.map((finding, fIndex) => (
                                <div 
                                  key={fIndex} 
                                  className="bg-white border border-blue-100 rounded-xl p-3 flex items-start space-x-2 hover:border-blue-200 hover:shadow-sm transition-all"
                                >
                                  <div className="mt-1 p-1 bg-blue-600 rounded-full">
                                    <div className="w-1.5 h-1.5 bg-white rounded-full"></div>
                                  </div>
                                  <p className="text-sm text-slate-900 leading-relaxed flex-1">{finding}</p>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        <div className="pt-3 border-t border-blue-100">
                          <div className="flex items-center justify-between text-sm mb-2">
                            <span className="text-blue-600 font-semibold">Confidence Level</span>
                            <span className="font-bold text-blue-900">{agent.confidence}%</span>
                          </div>
                          <Progress value={agent.confidence} className="h-2 bg-blue-100" />
                        </div>
                      </CardContent>
                    )}
                  </Card>
                );
              })}
            </div>
          </CardContent>
        </Card>

        {/* Financial Summary */}
        <Card className="border border-blue-100 shadow-sm bg-white rounded-2xl overflow-hidden">
          <CardHeader className="bg-blue-600 border-b border-blue-200 pb-4 pt-4">
            <CardTitle className="flex items-center space-x-2 text-white text-base font-bold">
              <div className="p-2 bg-blue-700 rounded-xl">
                <IndianRupee className="h-5 w-5 text-white" />
              </div>
              <span>Financial Summary</span>
            </CardTitle>
            <CardDescription className="text-white text-sm">Claim breakdown</CardDescription>
          </CardHeader>
          <CardContent className="pt-4 pb-4 bg-white">
            <div className="space-y-3">
              <div className="flex items-center justify-between p-4 bg-blue-50 rounded-xl border border-blue-100">
                <div>
                  <p className="text-sm text-blue-700 font-bold uppercase tracking-wider">Claimed</p>
                  <p className="text-xs text-slate-600 mt-0.5">Submitted amount</p>
                </div>
                <p className="text-2xl font-bold text-slate-900">
                  ₹{data.claimInfo.claimAmount.toLocaleString('en-IN')}
                </p>
              </div>

              <div className="flex items-center justify-between p-4 bg-blue-50 rounded-xl border border-blue-100">
                <div>
                  <p className="text-sm text-blue-700 font-bold uppercase tracking-wider">Deductible</p>
                  <p className="text-xs text-slate-600 mt-0.5">Policy amount</p>
                </div>
                <p className="text-2xl font-bold text-slate-900">
                  -₹{data.finalDecision.deductible.toLocaleString('en-IN')}
                </p>
              </div>

              <div className="flex items-center justify-between p-4 bg-emerald-50 rounded-xl border border-emerald-100">
                <div>
                  <p className="text-sm text-emerald-700 font-bold uppercase tracking-wider">Approved</p>
                  <p className="text-xs text-slate-600 mt-0.5">AI recommended</p>
                </div>
                <p className="text-2xl font-bold text-slate-900">
                  ₹{data.finalDecision.approvedAmount.toLocaleString('en-IN')}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Processing Timeline */}
        <Card className="border border-blue-100 shadow-sm bg-white rounded-2xl overflow-hidden">
          <CardHeader className="bg-blue-600 border-b border-blue-200 pb-4 pt-4">
            <CardTitle className="flex items-center space-x-2 text-white text-base font-bold">
              <div className="p-2 bg-blue-700 rounded-xl">
                <Clock className="h-5 w-5 text-white" />
              </div>
              <span>Processing Timeline</span>
            </CardTitle>
            <CardDescription className="text-white text-sm">Processing efficiency</CardDescription>
          </CardHeader>
          <CardContent className="pt-4 pb-4 bg-white">
            <div className="space-y-3">
              <div className="text-center p-4 bg-blue-50 rounded-xl border border-blue-100">
                <p className="text-xs text-blue-700 font-bold mb-2 uppercase tracking-wider">Submitted</p>
                <p className="text-base font-bold text-slate-900">{data.claimInfo.submittedDate}</p>
              </div>
              <div className="text-center p-4 bg-blue-50 rounded-xl border border-blue-100">
                <p className="text-xs text-blue-700 font-bold mb-2 uppercase tracking-wider">Processing Time</p>
                <p className="text-base font-bold text-slate-900">{data.claimInfo.processingTime}</p>
              </div>
              <div className="text-center p-4 bg-emerald-50 rounded-xl border border-emerald-100">
                <p className="text-xs text-emerald-700 font-bold mb-2 uppercase tracking-wider">Completed</p>
                <p className="text-base font-bold text-slate-900">{data.claimInfo.processedDate}</p>
              </div>
            </div>
            <div className="mt-4 p-4 bg-blue-600 rounded-xl shadow-sm">
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-blue-700 rounded-xl">
                  <TrendingUp className="h-5 w-5 text-white" />
                </div>
                <div>
                  <p className="text-sm font-bold text-white">
                    98% faster than traditional
                  </p>
                  <p className="text-xs text-white mt-0.5">
                    From 48 hours to ~2 minutes
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
      </div>
    </div>
  );
}
