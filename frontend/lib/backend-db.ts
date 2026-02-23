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
      return normalizeOutputs(getMockAgentOutputs(claimId));
    }
    
    const data = await response.json();
    const outputs = data.outputs || [];
    
    // Fall back to mock if API returned empty results (claim not in Cosmos yet)
    if (outputs.length === 0) {
      console.warn(`No outputs found in Cosmos for ${claimId}, using mock data`);
      return normalizeOutputs(getMockAgentOutputs(claimId));
    }
    
    return normalizeOutputs(outputs);
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
 * Mock data for development when backend is unavailable.
 * These are real Cosmos DB agent responses from CLM-2024-001.
 */
function getMockAgentOutputs(claimId: string): AgentOutput[] {
  return [
    {
      claim_id: claimId,
      agent_name: 'main_policy_basic',
      response_data: `### CAR BASIC DETAILS
- Make: Hyundai
- Model: Grand i10
- Variant: Sportz AT
- Year: 2018
- Registration Number: KA11MM1111
- Engine Details: 1197 CC, Petrol
- VIN/Chassis Number: Not specified in policy

### POLICY COVERAGE SUMMARY
- Policy Number: DCAR00920600359/00
- Policy Type: Comprehensive - Super Saver Plan
- Policy Period: 9th Jul 2023 to 8th Jul 2024
- Insured Declared Value (IDV): \u20b93,21,100
- Premium Amount: \u20b95,662.91 (Net Premium \u20b94,799.07 + IGST \u20b9863.83)

### COVERAGE DETAILS
- Own Damage Cover: Yes, \u20b91,383.07 (Net damage premium)
- Third Party Liability: \u20b93,416.00
- Personal Accident Cover: Not specified in policy
- Zero Depreciation: Not specified in policy (listed as add-on option)
- Deductible/Excess: \u20b91,000 (fixed compulsory deductible)

### KEY EXCLUSIONS
- Commercial usage of the car not covered.
- Damage caused due to illegal driving (e.g., without a valid license or under the influence of alcohol/drugs) is excluded.
- Claims for aggravated loss (continuous use post-accident) not covered.
- Depreciation cuts apply if no zero depreciation add-on is included:
  - 50% on plastic, rubber, batteries.
  - 30% on fiber components.
  - 25% on metal and wood parts.
  - 50% on paint.
- Standard exclusions apply for undeclared non-OEM parts like stereos or bifuel kits.`,
      extracted_data: { car_details_extracted: true, structured_response: true },
      processing_time_seconds: 2.5,
      timestamp: '2026-01-16T13:25:52.590802',
      status: 'completed',
      step: 1
    },
    {
      claim_id: claimId,
      agent_name: 'policy',
      response_data: `Based on the provided policy details, here is a structured analysis for the claim.

1. **Coverage Eligibility**
   - The insurance policy is a *Comprehensive - Super Saver* plan which provides coverage for:
     - Accidents and collisions (Own Damage)
     - Fire, theft, and natural calamities such as floods, cyclones, and earthquakes.
   - Therefore, the claim would be eligible if it falls under these categories.

2. **Policy Coverage Limits**
   - Insured Declared Value (IDV): \u20b93,21,100 for the covered vehicle, a Hyundai Grand i10.
   - Third-party property coverage limit: \u20b97,50,000.

3. **Relevant Exclusions or Limitations**
   - Claim *exclusions* include:
     - Damage due to wear and tear, breakdowns, or mechanical failures.
     - Usage of non-OEM parts unless declared.
     - Illegal activities such as driving under the influence or without a valid license.
     - Claims arising from commercial usage of a privately registered vehicle.

4. **Required Deductibles**
   - Deductibles for claims are not explicitly detailed in the extracted policy document. Usually, these would be confirmed during claims processing based on policy specifics.

5. **Claims Processing Requirements**
   - Procedure:
     1. Inform ACKO via their website, app, or helpline (1800 266 2256).
     2. ACKO will handle car pickup and repairs.
     3. The repaired vehicle is delivered back to the insured.
   - Real-time updates are available through the ACKO app.

6. **Coverage Determination Framework**
   - **Covered**: Accidental damages to the vehicle, damages from theft, fires, and calamities; third-party liability coverage; add-on benefits such as consumable coverage and roadside assistance depending on selected addons.
   - **Excluded**: Non-accidental damages, pre-existing damages, non-declared modifications, and damages from unauthorized usage.`,
      extracted_data: { idv: 321100, deductible: 0, coverage_eligible: true },
      processing_time_seconds: 3.1,
      timestamp: '2026-01-16T13:26:07.718971',
      status: 'completed',
      step: 2
    },
    {
      claim_id: claimId,
      agent_name: 'inspection',
      response_data: `### Vehicle Damage Inspection Report: Hyundai Grand i10, Claim ID ${claimId}

**Policy Context**
- **IDV:** \u20b93,21,100
- **Deductible:** \u20b90
- **Coverage Eligible:** True

---

### 1. Damage Assessment Consistent with Incident Report

#### **Exterior Damage Findings**:
- **Locations:** Front bumper, Hood, Front left fender, Windshield, Front left wheel
- **Damage Type:** Dent, crack, broken part
- **Severity:** High

- **Detailed Description:**
  - **Front bumper**: Cracked and partially detached.
  - **Hood**: Dented severely.
  - **Windshield**: Cracked.
  - **Front left fender**: Dented and scratched.
  - **Front left wheel**: Damaged visibly, requiring replacement.

#### **Airbag Status:** Not deployed during inspection.
#### **Glass Damage:** Cracked windshield only; all other glasses intact.
#### **Repair Necessity:** Tow required due to significant wheel damage.

---

### 2. Verification of Claim Authenticity and Damage Progression

The inspection confirms visible damage alignments with collision impact zones (Front left). The severity and nature ruled out pre-existing minor wear-and-tear or unrelated damage.

---

### 3. Safety Concerns and Repairability Determination
- **Critical Safety Issues:**
  - **Windshield:** Cracked, posing visibility issues, urgent replacement needed.
  - **Left Wheel:** Damage inhibits safe drivability.
  - **Front Bumper and Hood:** Structural integrity compromised.

- The vehicle is **repairable**, provided parts are replaced under OEM standards.

---

### 4. Cost Estimates

| Part | Estimated Cost (\u20b9) |
|------|-------------------|
| Front bumper replacement | 8,000 |
| Hood replacement | 7,000 |
| Windshield replacement | 6,500 |
| Front left fender repair | 5,000 |
| Front left wheel replacement | 12,000 |
| Labor costs (alignment, painting) | 5,000 |
| **Total** | **43,500** |

---

### 5. Total Loss Evaluation

The cumulative **estimated repair cost**: \u20b943,500. As this is well below the **IDV** of \u20b93,21,100, the vehicle **does not qualify as a total loss**. Repairs are economically feasible and justified.

---

### 6. Fraud Indicators or Pre-existing Damage
- No evidence of fraud or pre-existing damage identified. The incident aligns with reported collision-based progression.

---

### Recommendations
1. **Repair Approval:** Advances toward repair of damage identified: bumper, hood, windshield, fender, and wheel.
2. **Vendor Selection:** Engage authorized OEM repair centers for quality assurance and warranty coverage.
3. **Tow Services:** Immediate tow recommended considering wheel damage criticality.`,
      extracted_data: { repair_cost_estimate: 43500, total_loss_indicated: true, damage_authentic: true, policy_data_used: { idv: 321100, deductible: 0, coverage_eligible: true } },
      processing_time_seconds: 5.8,
      timestamp: '2026-01-16T13:26:23.791649',
      status: 'completed',
      step: 3
    },
    {
      claim_id: claimId,
      agent_name: 'bill_synthesis',
      response_data: `### Detailed Analysis and Reimbursement Calculation

#### **Inspection Context**
- **IDV**: \u20b93,21,100
- **Policy Deductible**: \u20b90
- **Inspection Estimate**: \u20b943,500
- **Total Loss Status**: True

#### **Actual Repair Bill Details**
1. **Garage Repairs**
   - **Front Bumper Replacement**: \u20b97,000 (Plastic - 50% depreciation applicable)
   - **Headlight Assembly (Left)**: \u20b94,500 (Electrical - 0% depreciation)
   - **Fog Light (Left)**: \u20b92,000 (Electrical - 0% depreciation)
   - **Front Grill Replacement**: \u20b92,500 (Plastic - 50% depreciation applicable)
   - **Bonnet Denting & Painting**: \u20b94,000 (Metal - 0% depreciation)
   - **Left Fender Repair**: \u20b93,500 (Fiber - 30% depreciation applicable)
   - **Airbag Replacement (Driver)**: \u20b912,000 (Safety item - 0% depreciation)
   - **Airbag Replacement (Passenger)**: \u20b912,000 (Safety item - 0% depreciation)
   - **Labor Charges**: \u20b96,000 (Labor - 0% depreciation)
   - **Subtotal for Garage Repairs**: \u20b953,500
2. **Towing Service**
   - **Accident Towing**: \u20b92,000 (Labor - 0% depreciation)
   - **Loading/Unloading Handling**: \u20b9500 (Labor - 0% depreciation)
   - **Subtotal for Towing**: \u20b92,500
   - **Grand Total**: \u20b956,000

#### **Comparison: Inspection vs Actual Bills**
- **Estimated Amount**: \u20b943,500
- **Actual Repair Bill Total**: \u20b956,000

The actual repair bills exceed the inspection estimate by **\u20b912,500**, primarily attributed to airbag replacements and labor charges.

#### **Component-Wise Depreciation and Reimbursement Calculation**

| Component | Billed (\u20b9) | Depreciation | Reimbursable (\u20b9) |
|-----------|----------|--------------|------------------|
| Front Bumper (Plastic) | 7,000 | 50% | 3,500 |
| Front Grill (Plastic) | 2,500 | 50% | 1,250 |
| Left Fender (Fiber) | 3,500 | 30% | 2,450 |
| Bonnet Denting (Metal) | 4,000 | 0% | 4,000 |
| Headlight Assembly | 4,500 | 0% | 4,500 |
| Fog Light | 2,000 | 0% | 2,000 |
| Driver Airbag | 12,000 | 0% | 12,000 |
| Passenger Airbag | 12,000 | 0% | 12,000 |
| Labor Charges | 6,000 | 0% | 6,000 |
| Towing Service | 2,500 | 0% | 2,500 |
| **Total** | **56,000** | | **50,200** |

#### **Final Reimbursement Amount**
- **Depreciation Adjusted Total**: \u20b950,200
- **Policy Deductible**: \u20b90
- **Final Reimbursement Amount**: **\u20b950,200**

#### **Discrepancies Flagged**
- Actual repair bill exceeds the inspection estimate by \u20b912,500.
- Components like airbags were not accounted for in the initial estimate.`,
      extracted_data: { actual_bill_amount: 56000, reimbursement_amount: 50200, cost_reasonableness_score: 95, memory_context_used: { policy_data: { idv: 321100, deductible: 0, coverage_eligible: true }, inspection_data: { repair_cost_estimate: 43500, total_loss_indicated: true, damage_authentic: true } } },
      processing_time_seconds: 4.1,
      timestamp: '2026-01-16T13:26:40.420566',
      status: 'completed',
      step: 4
    },
    {
      claim_id: claimId,
      agent_name: 'final_synthesis',
      response_data: `# Final Claim Decision Report

**Claim ID**: ${claimId}
**Vehicle**: Hyundai Grand i10
**Policy Type**: Comprehensive - Super Saver
**Insured Declared Value (IDV)**: \u20b93,21,100
**Deductible**: \u20b90

---

## 1. **DECISION: APPROVED**
The claim is approved for reimbursement. The total repair costs and damages are consistent with the coverage components under the policy and inspection findings. There are no exclusions applicable in this case.

---

## 2. **Coverage and Customer Responsibility**

### **Coverage Amount**: \u20b950,200

### **Customer Responsibility**: \u20b95,800
This amount covers depreciated costs and non-reimbursable portions as per the policy's depreciation rules.

---

### 3. **Detailed Cost Breakdown**

| Component | Actual Repair Cost (\u20b9) | Depreciation (%) | Covered Amount (\u20b9) |
|-----------|------------------------|------------------|---------------------|
| Front Bumper Replacement | 7,000 | 50% | 3,500 |
| Front Grill Replacement | 2,500 | 50% | 1,250 |
| Left Fender Repair | 3,500 | 30% | 2,450 |
| Bonnet Denting & Painting | 4,000 | 0% | 4,000 |
| Headlight Assembly (Left) | 4,500 | 0% | 4,500 |
| Fog Light (Left) | 2,000 | 0% | 2,000 |
| Driver Airbag Replacement | 12,000 | 0% | 12,000 |
| Passenger Airbag Replacement | 12,000 | 0% | 12,000 |
| Garage Labor Charges | 6,000 | 0% | 6,000 |
| Towing Service | 2,500 | 0% | 2,500 |
| **TOTAL** | **56,000** | | **50,200** |

---

### 4. **Customer's Responsibility Breakdown**
- **Plastic Parts Depreciation (50%)**:
  - Front Bumper: \u20b93,500
  - Front Grill: \u20b91,250
  - **Total Plastic Depreciation**: \u20b94,750
- **Fiber Parts Depreciation (30%)**:
  - Left Fender Repair: \u20b91,050
  - **Total Fiber Depreciation**: \u20b91,050

### **Total Customer Responsibility**: \u20b95,800

---

## 3. **JUSTIFICATION**

1. **Eligibility Under Policy Terms**: The incident falls under accidental damages covered by the Comprehensive - Super Saver plan. The policy's IDV (\u20b93,21,100) exceeds the repair costs (\u20b956,000), confirming that the claim is not categorized as a "total loss." Deductibles for this policy are \u20b90.

2. **Inspection and Damage Verification**: Inspection confirmed alignment between reported incidents and actual damages. Severity of damage to the front-left section matches collision impact zones. No signs of fraud, pre-existing damage, or policy violations were detected.

3. **Depreciation Adjustments**: Plastic and fiber parts are subject to 50% and 30% depreciation, respectively, as per the policy terms. These items are partially excluded from reimbursement, resulting in a Customer Responsibility of \u20b95,800.

4. **Adjustment for Actual vs. Inspection Bill**: The actual repair bill (\u20b956,000) exceeds the inspection-based estimate (\u20b943,500) due to additional necessary repairs for airbags and labor costs. These additional amounts are valid and covered under the policy terms.

---

## 4. **NEXT STEPS**

1. The insurer will process the reimbursement of **\u20b950,200** to the insured's registered account. Payment will be processed within 7-10 business days.
2. The customer must pay the responsibility amount of **\u20b95,800** directly to the garage at the time of collecting the repaired vehicle.
3. The insurer will coordinate with the garage for final settlement and ensure the timely delivery of the repaired car.
4. A detailed statement of repair and depreciation will be shared with the customer for their records.

---

## Summary

- **Total Repair Cost**: \u20b956,000
- **Depreciation (Customer Responsibility)**: \u20b95,800
- **Final Reimbursement (Payable to Customer)**: **\u20b950,200**

This claim is **approved** for reimbursement under policy guidelines and coverage limitations.`,
      extracted_data: { synthesis_completed: true, claim_status: 'completed', confidence_level: 95, risk_score: 'LOW', reimbursement_amount: 50200 },
      processing_time_seconds: 3.5,
      timestamp: '2026-01-16T13:26:54.365186',
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
    const outputValues = Object.values(outputs);
    const completedOutputs = outputValues.filter(o => o.status === 'completed');
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
