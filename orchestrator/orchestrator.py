"""
Main Orchestrator Module
Coordinates the insurance claim processing workflow
"""

import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv

from .models import ClaimData
from .memory_manager import CosmosMemoryManager
from .agent_factory import AgentFactory
from .data_extractors import DataExtractor
from .synthesis_engine import SynthesisEngine

# Import audit agent from parent directory
import sys
sys.path.append(str(Path(__file__).parent.parent))
from agents.auditagent import AuditAgent

load_dotenv()


class AutoInsuranceOrchestrator:
    """
    Main orchestrator for auto insurance claim processing.
    Coordinates all agents in sequence with memory persistence.
    """
    
    def __init__(self):
        """Initialize orchestrator components"""
        self.memory_manager = CosmosMemoryManager()
        self.agent_factory = AgentFactory()
        self.data_extractor = DataExtractor()
        self.synthesis_engine = SynthesisEngine()
        self.audit_agent = AuditAgent()
        
        self.instructions_dir = Path(__file__).parent.parent / "instructions"
        
        print("[OK] Auto Insurance Orchestrator initialized")
    
    def _load_instruction(self, filename: str) -> str:
        """Load instruction template from file"""
        filepath = self.instructions_dir / filename
        with open(filepath, "r") as f:
            return f.read()
    
    async def get_policy_basic_details(self, claim_id: str) -> str:
        """Step 0: Get basic policy details"""
        print("\n🔍 Step 0: Getting Car Policy Basic Details...")
        
        try:
            # Load instructions and create agent
            instructions = self._load_instruction("policy_lookup_agent.txt")
            agent = self.agent_factory.project_client.agents.create_agent(
                model="gpt-4o",
                name="main-auto-insurance-policy-expert",
                instructions=instructions,
                tools=self.agent_factory._create_search_tool(
                    "policy",
                    {"content": "content", "title": "document_title", 
                     "source": "document_path", "claim_type": "claim_category"}
                ).definitions,
                tool_resources=self.agent_factory._create_search_tool(
                    "policy",
                    {"content": "content", "title": "document_title", 
                     "source": "document_path", "claim_type": "claim_category"}
                ).resources,
            )
            
            # Create thread and query
            thread = self.agent_factory.project_client.agents.create_thread()
            
            policy_query = (
                "Search the policy index and retrieve complete vehicle insurance policy information. "
                "Extract all available details about the insured vehicle and policy coverage. "
                "Use search terms: 'vehicle insurance policy', 'car details', 'IDV', 'coverage', 'premium'. "
                "Provide the response in the mandatory structured format with all sections, "
                "filling in available information or stating 'Not specified in policy' for missing fields. "
                "Include: Car basic details (make, model, year, registration), policy coverage (IDV, premium, deductible), "
                "coverage types (own damage, third party), and key exclusions."
            )
            
            self.agent_factory.project_client.agents.create_message(
                thread_id=thread.id, role="user", content=policy_query
            )
            
            run = self.agent_factory.project_client.agents.create_and_process_run(
                thread_id=thread.id, agent_id=agent.id
            )
            
            if run.status == "failed":
                result = f"❌ Policy analysis failed: {run.last_error}"
            else:
                messages = self.agent_factory.project_client.agents.list_messages(thread_id=thread.id)
                result = messages.get_last_text_message_by_role("assistant").text.value
                
                # Store in memory
                await self.memory_manager.store_agent_response(
                    claim_id, "main_policy_basic", result,
                    {"car_details_extracted": True, "structured_response": True}
                )
            
            self.agent_factory.delete_agent(agent.id)
            print("✅ Policy basic details retrieved")
            return result
            
        except Exception as e:
            return f"❌ Error getting policy details: {str(e)}"
    
    async def execute_policy_analysis(self, claim_query: str, claim_id: str) -> str:
        """Step 1: Execute policy coverage analysis"""
        print("\n🔍 Step 1: Executing Policy Analysis...")
        
        customer_name = f"Customer-{claim_id.split('-')[-1]}"
        self.audit_agent.log_process_start(
            claim_id, customer_name, "policy_analysis",
            "orchestrator-policy-agent", f"Starting policy analysis: {claim_query[:100]}..."
        )
        
        try:
            agent = self.agent_factory.create_policy_agent()
            thread = self.agent_factory.project_client.agents.create_thread()
            
            self.agent_factory.project_client.agents.create_message(
                thread_id=thread.id, role="user",
                content=f"Analyze policy coverage for: {claim_query.split('totaling')[0] if 'totaling' in claim_query else claim_query}"
            )
            
            run = self.agent_factory.project_client.agents.create_and_process_run(
                thread_id=thread.id, agent_id=agent.id
            )
            
            if run.status == "failed":
                result = f"❌ Policy analysis failed: {run.last_error}"
                self.audit_agent.log_process_completion(
                    claim_id, customer_name, "policy_analysis",
                    "orchestrator-policy-agent", f"Failed: {run.last_error}", False
                )
            else:
                messages = self.agent_factory.project_client.agents.list_messages(thread_id=thread.id)
                result = messages.get_last_text_message_by_role("assistant").text.value
                
                # Extract and store
                extracted_data = {
                    "idv": self.data_extractor.extract_idv_from_policy(result),
                    "deductible": self.data_extractor.extract_deductible(result),
                    "coverage_eligible": self.data_extractor.check_coverage_eligibility(result)
                }
                
                await self.memory_manager.store_agent_response(
                    claim_id, "policy", result, extracted_data
                )
                
                self.audit_agent.log_process_completion(
                    claim_id, customer_name, "policy_analysis",
                    "orchestrator-policy-agent",
                    f"Completed. IDV: ₹{extracted_data['idv']:,}", True
                )
            
            self.agent_factory.delete_agent(agent.id)
            print("✅ Policy analysis completed")
            return result
            
        except Exception as e:
            error_msg = f"❌ Error: {str(e)}"
            self.audit_agent.log_process_completion(
                claim_id, customer_name, "policy_analysis",
                "orchestrator-policy-agent", f"Exception: {str(e)}", False
            )
            return error_msg
    
    async def execute_inspection_analysis(self, claim_query: str, claim_id: str) -> str:
        """Step 2: Execute inspection analysis with memory context"""
        print("\n🔍 Step 2: Executing Inspection Analysis...")
        
        customer_name = f"Customer-{claim_id.split('-')[-1]}"
        self.audit_agent.log_process_start(
            claim_id, customer_name, "inspection_assessment",
            "orchestrator-inspection-agent", f"Starting inspection: {claim_query[:100]}..."
        )
        
        try:
            # Retrieve policy data from memory
            policy_memory = await self.memory_manager.get_latest_response(claim_id, "policy")
            policy_context = policy_memory.get("response_data", "No policy data")
            policy_data = policy_memory.get("extracted_data", {})
            
            print(f"📖 Using policy context: IDV=₹{policy_data.get('idv', 0):,}")
            
            # Load and customize instructions
            template = self._load_instruction("inspection_orchestrator_agent.txt")
            instructions = template.format(
                idv=f"{policy_data.get('idv', 0):,}",
                deductible=f"{policy_data.get('deductible', 0):,}",
                coverage_eligible=policy_data.get('coverage_eligible', 'Unknown')
            )
            
            agent = self.agent_factory.create_inspection_agent(instructions)
            thread = self.agent_factory.project_client.agents.create_thread()
            
            query = f"""
            Conduct inspection for: {claim_query}
            
            POLICY CONTEXT: {policy_context}
            IDV: ₹{policy_data.get('idv', 0):,}
            Deductible: ₹{policy_data.get('deductible', 0):,}
            
            Assess damage, authenticity, cost estimation.
            """
            
            self.agent_factory.project_client.agents.create_message(
                thread_id=thread.id, role="user", content=query
            )
            
            run = self.agent_factory.project_client.agents.create_and_process_run(
                thread_id=thread.id, agent_id=agent.id
            )
            
            if run.status == "failed":
                result = f"❌ Inspection failed: {run.last_error}"
                self.audit_agent.log_process_completion(
                    claim_id, customer_name, "inspection_assessment",
                    "orchestrator-inspection-agent", f"Failed: {run.last_error}", False
                )
            else:
                messages = self.agent_factory.project_client.agents.list_messages(thread_id=thread.id)
                result = messages.get_last_text_message_by_role("assistant").text.value
                
                extracted_data = {
                    "repair_cost_estimate": self.data_extractor.extract_cost_estimate(result),
                    "total_loss_indicated": self.data_extractor.check_total_loss(result),
                    "damage_authentic": self.data_extractor.check_damage_authentic(result),
                    "policy_data_used": policy_data
                }
                
                await self.memory_manager.store_agent_response(
                    claim_id, "inspection", result, extracted_data
                )
                
                self.audit_agent.log_process_completion(
                    claim_id, customer_name, "inspection_assessment",
                    "orchestrator-inspection-agent",
                    f"Completed. Estimate: ₹{extracted_data['repair_cost_estimate']:,}", True
                )
            
            self.agent_factory.delete_agent(agent.id)
            print("✅ Inspection analysis completed")
            return result
            
        except Exception as e:
            error_msg = f"❌ Error: {str(e)}"
            self.audit_agent.log_process_completion(
                claim_id, customer_name, "inspection_assessment",
                "orchestrator-inspection-agent", f"Exception: {str(e)}", False
            )
            return error_msg
    
    async def execute_bill_reimbursement_analysis(self, claim_query: str, claim_id: str) -> str:
        """Step 3: Execute bill analysis with full memory context"""
        print("\n🔍 Step 3: Executing Bill Reimbursement Analysis...")
        
        customer_name = f"Customer-{claim_id.split('-')[-1]}"
        self.audit_agent.log_process_start(
            claim_id, customer_name, "bill_reimbursement",
            "orchestrator-bill-agent", f"Starting bill analysis: {claim_query[:100]}..."
        )
        
        try:
            # Retrieve all memory
            all_memory = await self.memory_manager.retrieve_previous_responses(
                claim_id, ["policy", "inspection"]
            )
            
            policy_data = all_memory.get("policy", {}).get("extracted_data", {})
            inspection_data = all_memory.get("inspection", {}).get("extracted_data", {})
            
            print(f"📖 Using complete context: IDV=₹{policy_data.get('idv', 0):,}, "
                  f"Estimate=₹{inspection_data.get('repair_cost_estimate', 0):,}")
            
            # Load and customize instructions
            template = self._load_instruction("bill_reimbursement_orchestrator_agent.txt")
            instructions = template.format(
                idv=f"{policy_data.get('idv', 0):,}",
                deductible=f"{policy_data.get('deductible', 0):,}",
                inspection_estimate=f"{inspection_data.get('repair_cost_estimate', 0):,}",
                total_loss_status=str(inspection_data.get('total_loss_indicated', False))
            )
            
            agent = self.agent_factory.create_bill_agent(instructions)
            thread = self.agent_factory.project_client.agents.create_thread()
            
            query = f"""
            Analyze actual repair bills for: {claim_query}
            
            COMPLETE CONTEXT:
            - IDV: ₹{policy_data.get('idv', 0):,}
            - Deductible: ₹{policy_data.get('deductible', 0):,}
            - Inspection Estimate: ₹{inspection_data.get('repair_cost_estimate', 0):,}
            
            Compare actual bills vs estimates, calculate reimbursement.
            """
            
            self.agent_factory.project_client.agents.create_message(
                thread_id=thread.id, role="user", content=query
            )
            
            run = self.agent_factory.project_client.agents.create_and_process_run(
                thread_id=thread.id, agent_id=agent.id
            )
            
            if run.status == "failed":
                result = f"❌ Bill analysis failed: {run.last_error}"
                self.audit_agent.log_process_completion(
                    claim_id, customer_name, "bill_reimbursement",
                    "orchestrator-bill-agent", f"Failed: {run.last_error}", False
                )
            else:
                messages = self.agent_factory.project_client.agents.list_messages(thread_id=thread.id)
                result = messages.get_last_text_message_by_role("assistant").text.value
                
                extracted_data = {
                    "actual_bill_amount": self.data_extractor.extract_cost_estimate(result),
                    "reimbursement_amount": self.data_extractor.extract_reimbursement_amount(result),
                    "memory_context_used": {"policy_data": policy_data, "inspection_data": inspection_data}
                }
                
                await self.memory_manager.store_agent_response(
                    claim_id, "bill_synthesis", result, extracted_data
                )
                
                self.audit_agent.log_process_completion(
                    claim_id, customer_name, "bill_reimbursement",
                    "orchestrator-bill-agent",
                    f"Completed. Reimbursement: ₹{extracted_data['reimbursement_amount']:,}", True
                )
            
            self.agent_factory.delete_agent(agent.id)
            print("✅ Bill analysis completed")
            return result
            
        except Exception as e:
            error_msg = f"❌ Error: {str(e)}"
            self.audit_agent.log_process_completion(
                claim_id, customer_name, "bill_reimbursement",
                "orchestrator-bill-agent", f"Exception: {str(e)}", False
            )
            return error_msg
    
    async def synthesize_final_recommendation(self, claim_data: ClaimData) -> str:
        """Step 4: Generate final recommendation"""
        print("\n🔍 Step 4: Synthesizing Final Recommendation...")
        
        customer_name = f"Customer-{claim_data.claim_id.split('-')[-1]}"
        self.audit_agent.log_process_start(
            claim_data.claim_id, customer_name, "final_synthesis",
            "claim-orchestrator", "Starting final synthesis"
        )
        
        try:
            result = await self.synthesis_engine.synthesize_final_recommendation(claim_data)
            
            # Store in memory
            await self.memory_manager.store_agent_response(
                claim_data.claim_id, "final_synthesis", result,
                {"synthesis_completed": True, "claim_status": "completed"}
            )
            
            self.audit_agent.log_process_completion(
                claim_data.claim_id, customer_name, "final_synthesis",
                "claim-orchestrator", "Final synthesis completed", True
            )
            
            return result
            
        except Exception as e:
            error_msg = f"❌ Error: {str(e)}"
            self.audit_agent.log_process_completion(
                claim_data.claim_id, customer_name, "final_synthesis",
                "claim-orchestrator", f"Exception: {str(e)}", False
            )
            return error_msg
    
    async def process_claim(self, claim_id: str, claim_description: str) -> ClaimData:
        """
        Main orchestration: processes complete claim through all agents
        """
        print(f"\n🚀 Starting Claim Processing: {claim_id}")
        print("=" * 80)
        
        claim_data = ClaimData(claim_id=claim_id)
        customer_name = f"Customer-{claim_id.split('-')[-1]}"
        
        self.audit_agent.log_process_start(
            claim_id, customer_name, "claim_processing",
            "claim-orchestrator", f"Starting workflow: {claim_description[:100]}..."
        )
        
        try:
            # Execute agent pipeline
            claim_data.basic_policy_details = await self.get_policy_basic_details(claim_id)
            claim_data.policy_analysis = await self.execute_policy_analysis(claim_description, claim_id)
            claim_data.inspection_results = await self.execute_inspection_analysis(claim_description, claim_id)
            
            print("\n🔧 === REPAIR PHASE ===")
            print("Customer completes repairs and submits bills...")
            print("=" * 50)
            
            claim_data.bill_analysis = await self.execute_bill_reimbursement_analysis(claim_description, claim_id)
            claim_data.final_recommendation = await self.synthesize_final_recommendation(claim_data)
            
            self.audit_agent.log_process_completion(
                claim_id, customer_name, "claim_processing",
                "claim-orchestrator", "Complete workflow finished successfully", True
            )
            
            print("\n" + "=" * 80)
            print("✅ Claim processing completed successfully!")
            
            return claim_data
            
        except Exception as e:
            print(f"\n❌ Error in claim processing: {str(e)}")
            self.audit_agent.log_process_completion(
                claim_id, customer_name, "claim_processing",
                "claim-orchestrator", f"Failed: {str(e)}", False
            )
            return claim_data
    
    def cleanup(self):
        """Clean up resources"""
        try:
            if self.audit_agent:
                self.audit_agent.cleanup()
            print("🧹 Orchestrator cleanup completed")
        except Exception as e:
            print(f"⚠️ Error during cleanup: {str(e)}")


# Main execution
async def main():
    """Main function to run the orchestrator"""
    orchestrator = AutoInsuranceOrchestrator()
    
    try:
        print("🚀 Auto Insurance Claim Orchestrator Initialized")
        
        example_claim_id = "CLM-2024-001"
        example_description = """Vehicle collision - front-end accident with bumper, hood damage. 
        Customer completed repairs. Need policy review and reimbursement determination."""
        
        claim_result = await orchestrator.process_claim(example_claim_id, example_description)
        
        print("\n📊 COMPLETE CLAIM SUMMARY:")
        print("=" * 50)
        print(f"Claim ID: {claim_result.claim_id}")
        print(f"Status: COMPLETED")
        print("=" * 50)
        
        if claim_result.final_recommendation:
            print(f"\n🎯 Final Decision:\n{claim_result.final_recommendation}")
        
        print("\n✅ Processing completed!")
        
    finally:
        orchestrator.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
