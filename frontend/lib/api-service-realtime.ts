// Real-time API service using Server-Sent Events (SSE)
// Connects to api_server_realtime.py

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

export interface AgentState {
  agent_name: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  step: number;
  response?: string;
  error?: string;
  processing_time_seconds?: number;
}

export interface ClaimProcessingState {
  claim_id: string;
  overall_status: 'processing' | 'completed' | 'failed';
  current_step: number;
  current_agent: string;
  agents: {
    [key: string]: AgentState;
  };
}

// Type alias for backward compatibility
export type RealtimeClaimState = ClaimProcessingState;

export interface SSEMessage {
  type: 'agent_start' | 'agent_complete' | 'agent_error' | 'final_complete' | 'error';
  agent_name: string;
  claim_id: string;
  timestamp: string;
  data?: {
    step?: number;
    total_steps?: number;
    status?: string;
    response?: string;
    error?: string;
    processing_time_seconds?: number;
    description?: string;
    message?: string;
  };
}

/**
 * Process a claim using real-time streaming (SSE)
 * @param claimId - The claim ID to process
 * @param claimDescription - Description of the claim
 * @param onUpdate - Callback function called on each agent update
 * @param onComplete - Callback function called when all processing is complete
 */
export async function processClaimRealtime(
  claimId: string,
  claimDescription: string,
  onUpdate: (state: ClaimProcessingState) => void,
  onComplete: (finalState: ClaimProcessingState) => void
): Promise<void> {
  const url = `${API_BASE_URL}/process-claim-stream`;
  
  // Initialize state
  const state: ClaimProcessingState = {
    claim_id: claimId,
    overall_status: 'processing',
    current_step: 0,
    current_agent: '',
    agents: {},
  };

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream',
      },
      body: JSON.stringify({
        claim_id: claimId,
        claim_description: claimDescription,
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();

    if (!reader) {
      throw new Error('No response body reader available');
    }

    let buffer = ''; // Buffer for incomplete lines

    // Read the stream
    while (true) {
      const { done, value } = await reader.read();
      
      if (done) {
        break;
      }

      // Decode the chunk and add to buffer
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      
      // Keep the last incomplete line in buffer
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const jsonData = line.substring(6); // Remove 'data: ' prefix
            const message: SSEMessage = JSON.parse(jsonData);

            console.log('SSE Message received:', message.type, message.agent_name);

            // Update state based on message type
            switch (message.type) {
              case 'agent_start':
                state.current_agent = message.agent_name;
                state.current_step = message.data?.step || 0;
                state.agents[message.agent_name] = {
                  agent_name: message.agent_name,
                  status: 'processing',
                  step: message.data?.step || 0,
                };
                onUpdate({ ...state });
                break;

              case 'agent_complete':
                if (state.agents[message.agent_name]) {
                  state.agents[message.agent_name].status = 'completed';
                  state.agents[message.agent_name].response = message.data?.response || '';
                  state.agents[message.agent_name].processing_time_seconds = message.data?.processing_time_seconds;
                }
                onUpdate({ ...state });
                break;

              case 'agent_error':
                if (state.agents[message.agent_name]) {
                  state.agents[message.agent_name].status = 'failed';
                  state.agents[message.agent_name].error = message.data?.error || 'Unknown error';
                }
                onUpdate({ ...state });
                break;

              case 'final_complete':
                state.overall_status = 'completed';
                onComplete({ ...state });
                break;

              case 'error':
                state.overall_status = 'failed';
                console.error('Processing error:', message.data?.error);
                onComplete({ ...state });
                break;
            }
          } catch (err) {
            console.error('Error parsing SSE message:', err, line);
          }
        }
      }
    }
  } catch (error) {
    console.error('Error in real-time claim processing:', error);
    state.overall_status = 'failed';
    onComplete(state);
    throw error;
  }
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
 * Calculate overall progress percentage from agent states
 */
export function calculateProgress(state: ClaimProcessingState): number {
  const agentNames = Object.keys(state.agents);
  
  if (agentNames.length === 0) {
    return 0;
  }

  const completedAgents = agentNames.filter(
    name => state.agents[name].status === 'completed'
  ).length;

  return Math.round((completedAgents / agentNames.length) * 100);
}
