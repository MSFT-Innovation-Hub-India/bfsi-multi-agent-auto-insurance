// Backend database service for fetching agent outputs from Cosmos DB
// This connects to the backend API to retrieve stored agent responses

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

export interface AgentOutput {
  id?: string;
  claim_id: string;
  agent_name?: string;
  agent_type?: string;
  response?: string;
  response_data?: string;
  extracted_data?: Record<string, unknown>;
  processing_time_seconds?: number;
  timestamp?: string;
  status?: 'completed' | 'failed' | 'pending';
  step?: number;
}

export type AgentOutputMap = Record<string, AgentOutput>;

/**
 * Fetch all agent outputs for a specific claim ID from Cosmos DB
 * @param claimId - The claim ID to fetch outputs for
 * @returns Array of agent outputs
 */
export async function getAgentOutputsByClaimId(claimId: string): Promise<AgentOutputMap> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/claims/${claimId}/outputs`);
    
    if (!response.ok) {
      console.warn(`Backend API not available (${response.status}), using mock data`);
      return getMockAgentOutputs(claimId);
    }
    
    const data = await response.json();
    return normalizeOutputs(data.outputs || []);
  } catch (error) {
    console.warn('Error fetching agent outputs, using mock data:', error);
    // Return mock data for development
    return normalizeOutputs(getMockAgentOutputs(claimId));
  }
}

/**
 * Fetch a specific agent's output for a claim
 * @param claimId - The claim ID
 * @param agentName - The name of the agent
 * @returns Agent output or null
 */
export async function getAgentOutput(claimId: string, agentName: string): Promise<AgentOutput | null> {
  try {
    const outputs = await getAgentOutputsByClaimId(claimId);
    return outputs[agentName] || null;
  } catch (error) {
    console.error('Error fetching agent output:', error);
    return null;
  }
}

/**
 * Normalize array payloads into a lookup keyed by agent type/name.
 */
function normalizeOutputs(outputs: AgentOutput[]): AgentOutputMap {
  const map: AgentOutputMap = {};

  outputs.forEach((o) => {
    const key = (o.agent_name || o.agent_type || '').trim();
    if (!key) return;
    map[key] = {
      ...o,
      // Prefer response_data when present; fallback to response
      response_data: o.response_data ?? o.response,
    };
  });

  return map;
}

/**
 * Mock data for development when backend is unavailable
 */
function getMockAgentOutputs(claimId: string): AgentOutput[] {
  return [
    {
      claim_id: claimId,
      agent_name: 'policy',
      response_data: JSON.stringify({
        policy_active: true,
        coverage_type: 'Comprehensive',
        policy_holder: 'John Doe',
        vehicle_details: {
          make: 'Hyundai',
          model: 'Grand i10 Sportz AT',
          year: 2018,
          registration: 'KA11MM1111'
        },
        premium_status: 'Paid',
        coverage_limits: {
          own_damage: 500000,
          third_party: 'Unlimited'
        },
        deductible: 2000
      }),
      extracted_data: { deductible: 2000, coverage_eligible: true },
      processing_time_seconds: 2.5,
      timestamp: new Date().toISOString(),
      status: 'completed',
      step: 1
    },
    {
      claim_id: claimId,
      agent_name: 'inspection',
      response_data: JSON.stringify({
        damage_severity: 'Moderate',
        affected_parts: ['Front bumper', 'Hood', 'Left fender', 'Headlight'],
        estimated_repair_cost: 45000,
        images_analyzed: 5,
        authenticity_score: 0.92,
        recommendations: 'Approve claim for repair work at authorized service center',
        red_flags: []
      }),
      extracted_data: { repair_cost_estimate: 45000, damage_authentic: true },
      processing_time_seconds: 5.8,
      timestamp: new Date().toISOString(),
      status: 'completed',
      step: 3
    },
    {
      claim_id: claimId,
      agent_name: 'bill_synthesis',
      response_data: JSON.stringify({
        total_amount: 60000,
        approved_amount: 58000,
        items: [
          { description: 'Front bumper replacement', amount: 12000, approved: true },
          { description: 'Hood repair and paint', amount: 18000, approved: true },
          { description: 'Left fender replacement', amount: 15000, approved: true },
          { description: 'Headlight assembly', amount: 8000, approved: true },
          { description: 'Labor charges', amount: 5000, approved: true },
          { description: 'Additional accessories', amount: 2000, approved: false }
        ],
        discrepancies: ['Additional accessories not covered under claim'],
        verification_status: 'Verified'
      }),
      extracted_data: { reimbursement_amount: 58000, actual_bill_amount: 60000 },
      processing_time_seconds: 4.1,
      timestamp: new Date().toISOString(),
      status: 'completed',
      step: 4
    },
    {
      claim_id: claimId,
      agent_name: 'final_synthesis',
      response_data: JSON.stringify({
        decision: 'APPROVED',
        approved_amount: 58000,
        confidence: 0.95,
        reasoning: 'All documentation verified. Damage assessment matches bill items. Policy covers comprehensive damage. No red flags detected.',
        conditions: ['Repairs must be done at authorized service center', 'Submit final repair invoice within 30 days'],
        next_steps: ['Send approval notification to claimant', 'Process payment to service center', 'Schedule quality check post-repair']
      }),
      extracted_data: { confidence_level: 95, risk_score: 'LOW' },
      processing_time_seconds: 3.5,
      timestamp: new Date().toISOString(),
      status: 'completed',
      step: 5
    }
  ];
}

/**
 * Get claim summary statistics
 */
export async function getClaimStats(claimId: string): Promise<{
  totalAgents: number;
  completedAgents: number;
  totalProcessingTime: number;
  status: string;
}> {
  try {
    const outputs = await getAgentOutputsByClaimId(claimId);
    const completedOutputs = outputs.filter(o => o.status === 'completed');
    const totalTime = completedOutputs.reduce((sum, o) => sum + (o.processing_time_seconds || 0), 0);
    
    return {
      totalAgents: 5, // Expected number of agents
      completedAgents: completedOutputs.length,
      totalProcessingTime: totalTime,
      status: completedOutputs.length === 5 ? 'completed' : 'processing'
    };
  } catch (error) {
    console.error('Error fetching claim stats:', error);
    return {
      totalAgents: 5,
      completedAgents: 0,
      totalProcessingTime: 0,
      status: 'unknown'
    };
  }
}
