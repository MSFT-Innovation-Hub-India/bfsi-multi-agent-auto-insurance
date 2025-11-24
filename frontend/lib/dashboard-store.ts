import { create } from 'zustand';

export interface Agent {
  id: string;
  name: string;
  status: 'active' | 'idle' | 'processing' | 'error';
  accuracy: number;
  tasksHandled: number;
}

export interface Claim {
  id: string;
  claimantName: string;
  policyNumber: string;
  vehicleType: string;
  claimAmount: number;
  status: 'pending' | 'processing' | 'approved' | 'flagged' | 'rejected';
  submittedDate: string;
}

interface DashboardState {
  agents: Agent[];
  claims: Claim[];
  selectedClaim: Claim | null;
  isProcessing: boolean;
  setSelectedClaim: (claim: Claim | null) => void;
  setIsProcessing: (processing: boolean) => void;
  updateAgentStatus: (agentName: string, status: Agent['status']) => void;
  updateClaimStatus: (claimId: string, status: Claim['status']) => void;
  refreshData: () => void;
}

// Mock data for agents
const initialAgents: Agent[] = [
  {
    id: '1',
    name: 'Policy Insight Agent',
    status: 'active',
    accuracy: 89.2,
    tasksHandled: 308,
  },
  {
    id: '2',
    name: 'Coverage Assessment Agent',
    status: 'active',
    accuracy: 86.7,
    tasksHandled: 305,
  },
  {
    id: '3',
    name: 'Inspection Agent',
    status: 'active',
    accuracy: 78.5,
    tasksHandled: 298,
  },
  {
    id: '4',
    name: 'Bill Analysis Agent',
    status: 'active',
    accuracy: 84.8,
    tasksHandled: 287,
  },
  {
    id: '5',
    name: 'Final Decision Agent',
    status: 'active',
    accuracy: 91.4,
    tasksHandled: 261,
  },
];

// Mock data for claims
const initialClaims: Claim[] = [
  {
    id: 'CLM-2024-001',
    claimantName: 'Diya S',
    policyNumber: 'KA11MM1111',
    vehicleType: 'Hyundai Grand i10 Sportz AT (2018)',
    claimAmount: 60000,
    status: 'pending',
    submittedDate: '2024-11-18',
  },
  {
    id: 'CLM-2024-002',
    claimantName: 'Arjun Mehta',
    policyNumber: 'MH12AB8890',
    vehicleType: 'Maruti Suzuki Baleno Delta CVT (2020)',
    claimAmount: 45000,
    status: 'processing',
    submittedDate: '2024-11-17',
  },
  {
    id: 'CLM-2024-003',
    claimantName: 'Amit Patel',
    policyNumber: 'MH-01-CD-5678',
    vehicleType: 'Hyundai Creta',
    claimAmount: 78000,
    status: 'approved',
    submittedDate: '2024-11-16',
  },
  {
    id: 'CLM-2024-004',
    claimantName: 'Sunita Reddy',
    policyNumber: 'TN-09-EF-9012',
    vehicleType: 'Toyota Innova',
    claimAmount: 125000,
    status: 'flagged',
    submittedDate: '2024-11-15',
  },
  {
    id: 'CLM-2024-005',
    claimantName: 'Vikram Singh',
    policyNumber: 'RJ-14-GH-3456',
    vehicleType: 'Tata Nexon',
    claimAmount: 56000,
    status: 'pending',
    submittedDate: '2024-11-14',
  },
  {
    id: 'CLM-2024-006',
    claimantName: 'Anjali Desai',
    policyNumber: 'GJ-01-IJ-7890',
    vehicleType: 'Honda Amaze',
    claimAmount: 38000,
    status: 'approved',
    submittedDate: '2024-11-13',
  },
  {
    id: 'CLM-2024-007',
    claimantName: 'Karthik Nair',
    policyNumber: 'KL-07-KL-2345',
    vehicleType: 'Kia Seltos',
    claimAmount: 92000,
    status: 'processing',
    submittedDate: '2024-11-12',
  },
  {
    id: 'CLM-2024-008',
    claimantName: 'Meera Iyer',
    policyNumber: 'TN-01-MN-6789',
    vehicleType: 'Maruti Baleno',
    claimAmount: 41000,
    status: 'approved',
    submittedDate: '2024-11-11',
  },
  {
    id: 'CLM-2024-009',
    claimantName: 'Rahul Verma',
    policyNumber: 'UP-16-OP-0123',
    vehicleType: 'Mahindra XUV500',
    claimAmount: 110000,
    status: 'pending',
    submittedDate: '2024-11-10',
  },
  {
    id: 'CLM-2024-010',
    claimantName: 'Divya Menon',
    policyNumber: 'KA-03-QR-4567',
    vehicleType: 'Volkswagen Polo',
    claimAmount: 48000,
    status: 'approved',
    submittedDate: '2024-11-09',
  },
  {
    id: 'CLM-2024-011',
    claimantName: 'Sandeep Joshi',
    policyNumber: 'MH-12-ST-8901',
    vehicleType: 'Ford EcoSport',
    claimAmount: 67000,
    status: 'processing',
    submittedDate: '2024-11-08',
  },
  {
    id: 'CLM-2024-012',
    claimantName: 'Kavya Rao',
    policyNumber: 'AP-09-UV-2345',
    vehicleType: 'Renault Duster',
    claimAmount: 73000,
    status: 'flagged',
    submittedDate: '2024-11-07',
  },
  {
    id: 'CLM-2024-013',
    claimantName: 'Arun Kumar',
    policyNumber: 'TN-11-WX-6789',
    vehicleType: 'Nissan Magnite',
    claimAmount: 52000,
    status: 'pending',
    submittedDate: '2024-11-06',
  },
  {
    id: 'CLM-2024-014',
    claimantName: 'Pooja Gupta',
    policyNumber: 'DL-08-YZ-0123',
    vehicleType: 'Skoda Rapid',
    claimAmount: 59000,
    status: 'approved',
    submittedDate: '2024-11-05',
  },
  {
    id: 'CLM-2024-015',
    claimantName: 'Suresh Babu',
    policyNumber: 'KA-01-AB-4567',
    vehicleType: 'Honda Jazz',
    claimAmount: 44000,
    status: 'processing',
    submittedDate: '2024-11-04',
  },
  {
    id: 'CLM-2024-016',
    claimantName: 'Lakshmi Krishnan',
    policyNumber: 'TN-20-CD-8901',
    vehicleType: 'Hyundai Venue',
    claimAmount: 61000,
    status: 'pending',
    submittedDate: '2024-11-03',
  },
  {
    id: 'CLM-2024-017',
    claimantName: 'Manoj Tiwari',
    policyNumber: 'MP-09-EF-2345',
    vehicleType: 'Maruti Brezza',
    claimAmount: 69000,
    status: 'processing',
    submittedDate: '2024-11-02',
  },
  {
    id: 'CLM-2024-018',
    claimantName: 'Nisha Kapoor',
    policyNumber: 'PB-01-GH-6789',
    vehicleType: 'Tata Harrier',
    claimAmount: 135000,
    status: 'pending',
    submittedDate: '2024-11-01',
  },
  {
    id: 'CLM-2024-019',
    claimantName: 'Ramesh Chandra',
    policyNumber: 'HR-26-IJ-0123',
    vehicleType: 'Mahindra Scorpio',
    claimAmount: 98000,
    status: 'processing',
    submittedDate: '2024-10-31',
  },
  {
    id: 'CLM-2024-020',
    claimantName: 'Sneha Bose',
    policyNumber: 'WB-06-KL-4567',
    vehicleType: 'Hyundai i20',
    claimAmount: 47000,
    status: 'flagged',
    submittedDate: '2024-10-30',
  },
];

export const useDashboardStore = create<DashboardState>((set) => ({
  agents: initialAgents,
  claims: initialClaims,
  selectedClaim: null,
  isProcessing: false,

  setSelectedClaim: (claim) => set({ selectedClaim: claim }),
  
  setIsProcessing: (processing) => set({ isProcessing: processing }),
  
  updateAgentStatus: (agentName, status) =>
    set((state) => ({
      agents: state.agents.map((agent) =>
        agent.name === agentName ? { ...agent, status } : agent
      ),
    })),
  
  updateClaimStatus: (claimId, status) =>
    set((state) => ({
      claims: state.claims.map((claim) =>
        claim.id === claimId ? { ...claim, status } : claim
      ),
    })),
  
  refreshData: () => {
    // In a real app, this would fetch fresh data from the API
    console.log('Refreshing dashboard data...');
  },
}));
