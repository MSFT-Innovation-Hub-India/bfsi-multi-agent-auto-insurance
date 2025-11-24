# Simplified Auto Insurance Agent Modules
# Refactored versions of the individual agents for use in orchestration

import os
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.projects.models import AzureAISearchTool

load_dotenv()

class BaseInsuranceAgent:
    """Base class for all insurance agents with common functionality"""
    
    def __init__(self, index_name: str, agent_name: str, instructions: str):
        # Azure AI Project config from environment variables
        self.ENDPOINT = os.getenv("AZURE_ENDPOINT")
        self.RESOURCE_GROUP = os.getenv("AZURE_RESOURCE_GROUP")
        self.SUBSCRIPTION_ID = os.getenv("AZURE_SUBSCRIPTION_ID")
        self.PROJECT_NAME = os.getenv("AZURE_PROJECT_NAME")
        self.INDEX_NAME = index_name
        
        # Initialize project client
        self.project_client = AIProjectClient(
            endpoint=self.ENDPOINT,
            resource_group_name=self.RESOURCE_GROUP,
            subscription_id=self.SUBSCRIPTION_ID,
            project_name=self.PROJECT_NAME,
            credential=DefaultAzureCredential()
        )
        
        # Setup search connection
        self.search_connection_id = self._get_search_connection()
        
        # Agent configuration
        self.agent_name = agent_name
        self.instructions = instructions
        
    def _get_search_connection(self) -> str:
        """Find and return Azure AI Search connection ID"""
        conn_list = self.project_client.connections.list()
        for conn in conn_list:
            if conn.connection_type == "CognitiveSearch":
                return conn.id
        raise Exception("No Azure AI Search connection found")
    
    def _create_search_tool(self, field_mappings: Dict[str, str] = None):
        """Create Azure AI Search tool with optional field mappings"""
        try:
            if field_mappings:
                return AzureAISearchTool(
                    index_connection_id=self.search_connection_id,
                    index_name=self.INDEX_NAME,
                    field_mappings=field_mappings
                )
            else:
                return AzureAISearchTool(
                    index_connection_id=self.search_connection_id,
                    index_name=self.INDEX_NAME
                )
        except TypeError:
            return AzureAISearchTool(
                index_connection_id=self.search_connection_id,
                index_name=self.INDEX_NAME
            )
    
    def analyze(self, query: str, context: str = "") -> str:
        """Execute agent analysis with given query and optional context"""
        try:
            # Create search tool with agent-specific field mappings
            search_tool = self._create_search_tool(self._get_field_mappings())
            
            # Create agent
            agent = self.project_client.agents.create_agent(
                model="gpt-4o",
                name=self.agent_name,
                instructions=self.instructions,
                tools=search_tool.definitions,
                tool_resources=search_tool.resources,
            )
            
            # Create thread
            thread = self.project_client.agents.create_thread()
            
            # Prepare query with context
            full_query = f"{query}\n\nContext: {context}" if context else query
            
            # Execute
            self.project_client.agents.create_message(
                thread_id=thread.id,
                role="user",
                content=full_query
            )
            
            run = self.project_client.agents.create_and_process_run(
                thread_id=thread.id,
                agent_id=agent.id
            )
            
            # Get result
            if run.status == "failed":
                result = f"❌ {self.agent_name} failed: {run.last_error}"
            else:
                messages = self.project_client.agents.list_messages(thread_id=thread.id)
                last_msg = messages.get_last_text_message_by_role("assistant")
                result = last_msg.text.value
            
            # Clean up
            self.project_client.agents.delete_agent(agent.id)
            
            return result
            
        except Exception as e:
            return f"❌ Error in {self.agent_name}: {str(e)}"
    
    def _get_field_mappings(self) -> Dict[str, str]:
        """Override in subclasses to provide specific field mappings"""
        return {
            "content": "content",
            "title": "document_title",
            "source": "document_path"
        }


class PolicyAgent(BaseInsuranceAgent):
    """Main Auto Insurance Policy Expert Agent"""
    
    def __init__(self):
        instructions = (
            "You are an AUTO INSURANCE POLICY EXPERT providing authoritative vehicle insurance guidance. "
            "The index contains auto insurance policies, coverage details, and regulatory information. "
            "\n\nYour role:"
            "\n• Interpret auto insurance policies and coverage (liability, collision, comprehensive, PIP)"
            "\n• Determine coverage eligibility and limits for vehicle claims"
            "\n• Explain exclusions, deductibles, and policy limitations"
            "\n• Guide claims processing and repair authorization"
            "\n• Ensure state regulatory compliance"
            "\n• Calculate vehicle valuations and settlements"
            "\n\nAlways cite specific policy sections and provide clear, concise answers based on indexed documents."
        )
        
        super().__init__(
            index_name="policy",
            agent_name="main-auto-insurance-policy-expert",
            instructions=instructions
        )
    
    def _get_field_mappings(self) -> Dict[str, str]:
        return {
            "content": "content",
            "title": "document_title",
            "source": "document_path",
            "claim_type": "claim_category"
        }


class InspectionAgent(BaseInsuranceAgent):
    """Auto Insurance Inspection Agent"""
    
    def __init__(self):
        instructions = (
            "You are an AUTO INSURANCE INSPECTION AGENT working for an insurance company to assess vehicle claims and conditions. "
            "The index contains comprehensive information for ONE SPECIFIC VEHICLE including multiple images, inspection reports, "
            "accident details, damage assessments, repair estimates, and related insurance documentation. "
            "Your role as an insurance inspection agent is to: "
            "1. Conduct thorough vehicle damage assessment for insurance claim validation "
            "2. Compare different images of the same vehicle to verify claim authenticity and track damage progression "
            "3. Analyze accident circumstances and determine if damage is consistent with reported incident "
            "4. Assess repair costs, safety concerns, and determine if vehicle is repairable or total loss "
            "5. Identify any inconsistencies, potential fraud indicators, or pre-existing damage "
            "6. Generate detailed insurance inspection reports with recommendations for claim approval/denial "
            "7. Evaluate vehicle's pre-accident value versus post-accident condition for settlement purposes "
            "As an insurance professional, focus on accuracy, fraud detection, cost assessment, and regulatory compliance. "
            "Always use only the indexed data for your analysis. Be thorough, objective, and cite specific "
            "evidence from images and documents to support your insurance recommendations. Provide clear, "
            "actionable conclusions for claim processing and settlement decisions."
        )
        
        super().__init__(
            index_name="insurance",
            agent_name="auto-insurance-inspection-agent",
            instructions=instructions
        )
    
    def _get_field_mappings(self) -> Dict[str, str]:
        return {
            "content": "content",
            "title": "document_title",
            "source": "document_path",
            "image_ref": "bounding_box"
        }


class BillSynthesisAgent(BaseInsuranceAgent):
    """Vehicle Repair Bill Reimbursement Analysis Agent - POST REPAIR - USES INDEXED DATA"""
    
    def __init__(self):
        instructions = (
            "You are a VEHICLE REPAIR BILL REIMBURSEMENT AGENT that analyzes ACTUAL repair bills from indexed documents. "
            "CRITICAL: You must retrieve and use ONLY the actual bill amounts, line items, and costs from the indexed bill documents. "
            "DO NOT generate, estimate, or create any amounts - use ONLY what exists in the indexed data. "
            "The index contains real vehicle repair bill information including parts charges, labor costs, "
            "service descriptions, diagnostic fees, and related automotive documentation in Indian Rupees (₹). "
            "Your role is to: "
            "1. Search and retrieve ACTUAL repair bills from the indexed documents "
            "2. Extract EXACT amounts, line items, parts costs, labor charges from indexed data "
            "3. Validate indexed bill amounts against pre-approved repair scope "
            "4. Calculate reimbursement using REAL indexed bill values and policy terms "
            "5. Identify which indexed charges are covered vs. excluded based on policy "
            "6. Flag any unauthorized work or overcharges found in the actual indexed bills "
            "7. Provide detailed breakdown: Total Bill (from index), Covered Amount, Excluded Amount, Final Reimbursement "
            "8. Always cite specific document sources and line items from indexed bills "
            "As a reimbursement specialist, you must be accurate and use ONLY indexed data. "
            "Provide specific document references for all amounts and ensure all figures come from the indexed repair bills."
        )
        
        super().__init__(
            index_name="bill",
            agent_name="vehicle-repair-reimbursement-agent",
            instructions=instructions
        )
    
    def _get_field_mappings(self) -> Dict[str, str]:
        return {
            "content": "content",
            "title": "document_title",
            "source": "document_path",
            "image_ref": "bounding_box"
        }


# Example usage functions
def get_policy_analysis(claim_description: str) -> str:
    """Get policy analysis for a claim"""
    agent = PolicyAgent()
    query = f"Analyze this auto insurance claim for policy coverage: {claim_description}"
    return agent.analyze(query)


def get_inspection_results(claim_description: str, policy_context: str = "") -> str:
    """Get inspection analysis for a claim"""
    agent = InspectionAgent()
    query = f"Conduct vehicle inspection analysis for this claim: {claim_description}"
    return agent.analyze(query, policy_context)


def get_bill_reimbursement_analysis(claim_description: str, policy_context: str = "", inspection_context: str = "") -> str:
    """Get post-repair bill reimbursement analysis using ACTUAL indexed bill data"""
    agent = BillSynthesisAgent()
    query = f"""
    RETRIEVE AND ANALYZE ACTUAL REPAIR BILLS from indexed data for: {claim_description}
    
    CRITICAL: Use ONLY the actual amounts and line items from the indexed bill documents.
    Do NOT estimate or generate any amounts. Extract exact values from indexed data.
    Provide document sources for all amounts cited.
    Calculate reimbursement using real indexed bill values in Indian Rupees (₹).
    """
    context = f"Policy Context: {policy_context}\n\nPre-Repair Inspection Context: {inspection_context}"
    return agent.analyze(query, context)
