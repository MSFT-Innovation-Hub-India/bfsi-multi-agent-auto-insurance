"""
Synthesis Engine
Generates final claim recommendations
Uses Managed Identity for Azure OpenAI authentication
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Optional
import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.core_plugins import TextPlugin
from semantic_kernel.functions import KernelArguments
from azure.identity import DefaultAzureCredential, get_bearer_token_provider

from .models import ClaimData
from .data_extractors import DataExtractor


class SynthesisEngine:
    """Engine for synthesizing final claim recommendations"""
    
    def __init__(self):
        """Initialize synthesis engine with Semantic Kernel"""
        self.kernel = sk.Kernel()
        self.extractor = DataExtractor()
        self._setup_kernel()
        self.instructions_dir = Path(__file__).parent.parent / "instructions"
    
    def _setup_kernel(self):
        """Initialize Semantic Kernel with Managed Identity"""
        try:
            endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
            api_key = os.getenv("AZURE_OPENAI_API_KEY")
            deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")
            
            if endpoint:
                # Try Managed Identity first, fall back to API key
                if api_key and api_key != "your-azure-openai-api-key-here":
                    # Use API key if provided
                    self.kernel.add_service(
                        AzureChatCompletion(
                            service_id="azure_openai_chat",
                            endpoint=endpoint,
                            deployment_name=deployment_name,
                            api_key=api_key,
                            api_version="2024-02-01"
                        )
                    )
                    print("[OK] Semantic Kernel initialized with Azure OpenAI (API Key)")
                else:
                    # Use Managed Identity via DefaultAzureCredential
                    credential = DefaultAzureCredential()
                    token_provider = get_bearer_token_provider(
                        credential, 
                        "https://cognitiveservices.azure.com/.default"
                    )
                    self.kernel.add_service(
                        AzureChatCompletion(
                            service_id="azure_openai_chat",
                            endpoint=endpoint,
                            deployment_name=deployment_name,
                            ad_token_provider=token_provider,
                            api_version="2024-02-01"
                        )
                    )
                    print("[OK] Semantic Kernel initialized with Azure OpenAI (Managed Identity)")
            else:
                print("[WARNING] AZURE_OPENAI_ENDPOINT not found, using fallback mode")
            
            self.kernel.add_plugin(TextPlugin(), plugin_name="TextPlugin")
            
        except Exception as e:
            print(f"[WARNING] Error setting up Semantic Kernel: {e}")
    
    def _load_instruction(self, filename: str) -> str:
        """Load instruction template"""
        filepath = self.instructions_dir / filename
        with open(filepath, "r") as f:
            return f.read()
    
    async def synthesize_final_recommendation(self, claim_data: ClaimData) -> str:
        """Synthesize final claim recommendation"""
        print("\n🔍 Synthesizing Final Recommendation...")
        
        try:
            # Try Semantic Kernel first
            synthesis_instructions = self._load_instruction("synthesis_agent.txt")
            
            synthesis_prompt = f"""
            {synthesis_instructions}
            
            Based on comprehensive analysis, provide a final claim decision.
            
            CLAIM ID: {{{{$claim_id}}}}
            POLICY ANALYSIS: {{{{$policy_analysis}}}}
            INSPECTION RESULTS: {{{{$inspection_results}}}}
            BILL ANALYSIS: {{{{$bill_analysis}}}}
            
            Provide: DECISION, COVERAGE AMOUNT, CUSTOMER RESPONSIBILITY, JUSTIFICATION, NEXT STEPS
            """
            
            synthesis_function = self.kernel.add_function(
                function_name="synthesize_claim",
                plugin_name="ClaimOrchestrator",
                prompt=synthesis_prompt
            )
            
            arguments = KernelArguments(
                claim_id=claim_data.claim_id,
                policy_analysis=claim_data.policy_analysis,
                inspection_results=claim_data.inspection_results,
                bill_analysis=claim_data.bill_analysis
            )
            
            result = await self.kernel.invoke(synthesis_function, arguments)
            print("✅ Final recommendation synthesized with Semantic Kernel")
            return str(result)
            
        except Exception as e:
            print(f"⚠️ Semantic Kernel synthesis failed: {str(e)}")
            print("🔄 Using fallback synthesis method...")
            return self._fallback_synthesis(claim_data)
    
    def _fallback_synthesis(self, claim_data: ClaimData) -> str:
        """Fallback synthesis using rule-based logic"""
        try:
            # Extract key information
            policy_text = claim_data.policy_analysis.lower()
            inspection_text = claim_data.inspection_results.lower()
            bill_text = claim_data.bill_analysis.lower()
            
            # Determine coverage
            coverage_eligible = self.extractor.check_coverage_eligibility(claim_data.policy_analysis)
            
            # Extract costs
            repair_cost = self.extractor.extract_cost_estimate(inspection_text + " " + bill_text)
            idv = self.extractor.extract_idv_from_policy(claim_data.policy_analysis)
            deductible = self.extractor.extract_deductible(claim_data.policy_analysis)
            
            # Validate extracted data
            if idv == 0:
                return "❌ Error: IDV not found in policy analysis"
            if deductible == 0:
                return "❌ Error: Deductible not found in policy analysis"
            if repair_cost == 0:
                return "❌ Error: Repair cost not found in analyses"
            
            # Check total loss
            total_loss = (self.extractor.check_total_loss(inspection_text) or 
                         self.extractor.check_total_loss(bill_text) or 
                         repair_cost > idv * 0.75)
            
            # Generate decision
            decision, coverage_amount, customer_responsibility, justification = self._calculate_decision(
                coverage_eligible, total_loss, repair_cost, idv, deductible
            )
            
            # Format final report
            return self._format_final_report(
                claim_data.claim_id, decision, coverage_amount, 
                customer_responsibility, repair_cost, justification
            )
            
        except Exception as e:
            return f"❌ Error in fallback synthesis: {str(e)}"
    
    def _calculate_decision(
        self, 
        coverage_eligible: bool, 
        total_loss: bool, 
        repair_cost: int, 
        idv: int, 
        deductible: int
    ) -> tuple:
        """Calculate claim decision and amounts"""
        if not coverage_eligible:
            return (
                "DENIED",
                "₹0",
                "Full repair costs",
                "Policy coverage does not apply to this claim"
            )
        elif total_loss:
            settlement = idv - deductible
            return (
                "APPROVED - TOTAL LOSS",
                f"₹{settlement:,}",
                f"₹{deductible:,} deductible",
                f"Vehicle deemed total loss. Repair cost (₹{repair_cost:,}) exceeds 75% of IDV (₹{idv:,})"
            )
        else:
            depreciation = int(repair_cost * 0.25)
            reimbursement = max(0, repair_cost - deductible - depreciation)
            return (
                "APPROVED - REIMBURSEMENT",
                f"₹{reimbursement:,}",
                f"₹{deductible + depreciation:,} (₹{deductible:,} deductible + ₹{depreciation:,} depreciation)",
                "Coverage applies. Reimbursement calculated per policy terms"
            )
    
    def _format_final_report(
        self,
        claim_id: str,
        decision: str,
        coverage_amount: str,
        customer_responsibility: str,
        repair_cost: int,
        justification: str
    ) -> str:
        """Format final claim decision report"""
        return f"""
═══════════════════════════════════════════════════════════════════
                      FINAL CLAIM DECISION REPORT
═══════════════════════════════════════════════════════════════════

CLAIM ID: {claim_id}
PROCESSING DATE: {datetime.now().strftime("%Y-%m-%d")}

1. **CLAIM DECISION**: {decision}

2. **REIMBURSEMENT AMOUNT**: {coverage_amount}

3. **CUSTOMER RESPONSIBILITY**: {customer_responsibility}

4. **PAYMENT BREAKDOWN**:
   • Actual Repair Cost: ₹{repair_cost:,}
   • Approved Reimbursement: {coverage_amount}
   • Customer Pays: {customer_responsibility}

5. **SUPPORTING RATIONALE**:
   {justification}

6. **NEXT STEPS**:
   • Process reimbursement payment to customer
   • Update claim status to "Settled"
   • Handle any subrogation recovery if applicable
   • Issue settlement letter and close claim file

7. **TIMELINE**: 
   • Reimbursement processing: 3-5 business days
   • Payment transfer: 2-3 business days after approval
   • Claim closure: Within 7 days of settlement

RECOMMENDATION: {decision} - Proceed with processing as outlined above.

═══════════════════════════════════════════════════════════════════
        """.strip()
