// Batch API service for non-streaming requests
// Connects to api_server.py (batch mode)

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

export interface AgentResponse {
  agent_name: string;
  status: string;
  response: string;
  timestamp: string;
  processing_time_seconds?: number;
}

export interface ClaimResponse {
  claim_id: string;
  overall_status: string;
  processing_started: string;
  processing_completed: string;
  total_processing_time_seconds: number;
  
  // Individual agent responses
  policy_basic_details?: AgentResponse;
  policy_analysis?: AgentResponse;
  inspection_analysis?: AgentResponse;
  bill_analysis?: AgentResponse;
  final_recommendation?: AgentResponse;
  
  // Summary
  summary: {
    total_agents_processed: number;
    successful_agents: number;
    failed_agents: number;
    total_processing_time: string;
    claim_status: string;
  };
}

/**
 * Process a claim using batch mode (returns all results at once)
 */
export async function processClaimWithOrchestrator(
  claimId: string,
  claimDescription: string,
  addDelays: boolean = false
): Promise<ClaimResponse> {
  const response = await fetch(`${API_BASE_URL}/process-claim`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      claim_id: claimId,
      claim_description: claimDescription,
      add_delays: addDelays,
    }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
  }

  return response.json();
}

/**
 * Check API health
 */
export async function checkApiHealth(): Promise<{
  status: string;
  timestamp: string;
  orchestrator_initialized: boolean;
}> {
  const response = await fetch(`${API_BASE_URL}/health`);
  if (!response.ok) {
    throw new Error('API health check failed');
  }
  return response.json();
}

/**
 * Helper function to combine policy basic details and policy analysis
 */
export function combinePolicyResponses(
  basicDetails?: AgentResponse,
  policyAnalysis?: AgentResponse
): AgentResponse | undefined {
  if (!basicDetails && !policyAnalysis) return undefined;
  
  if (!basicDetails) return policyAnalysis;
  if (!policyAnalysis) return basicDetails;
  
  return {
    agent_name: 'Policy Analysis (Combined)',
    status: basicDetails.status === 'completed' && policyAnalysis.status === 'completed' 
      ? 'completed' 
      : 'failed',
    response: `${basicDetails.response}\n\n---\n\n${policyAnalysis.response}`,
    timestamp: policyAnalysis.timestamp,
    processing_time_seconds: 
      (basicDetails.processing_time_seconds || 0) + (policyAnalysis.processing_time_seconds || 0),
  };
}
