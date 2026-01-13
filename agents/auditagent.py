import os
import requests
import json
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.projects.models import OpenApiTool, OpenApiAnonymousAuthDetails, ToolSet
from jsonref import loads

# Load environment variables
load_dotenv()

class AuditAgent:
    """Insurance Audit Agent for logging and tracking claim processing activities"""
    
    def __init__(self):
        # Azure AI Project config from environment variables
        self.ENDPOINT = os.getenv("AZURE_ENDPOINT")
        self.RESOURCE_GROUP = os.getenv("AZURE_RESOURCE_GROUP")
        self.SUBSCRIPTION_ID = os.getenv("AZURE_SUBSCRIPTION_ID")
        self.PROJECT_NAME = os.getenv("AZURE_PROJECT_NAME")
        
        # Initialize project client
        self.project_client = AIProjectClient(
            endpoint=self.ENDPOINT,
            resource_group_name=self.RESOURCE_GROUP,
            subscription_id=self.SUBSCRIPTION_ID,
            project_name=self.PROJECT_NAME,
            credential=DefaultAzureCredential()
        )
        
        # Audit API base URL from environment variable
        self.audit_api_base = os.getenv("AUDIT_API_BASE_URL", "https://cosmosaudit.azurewebsites.net")
        
        # Agent configuration
        self.agent_name = "insurance-audit-agent"
        self.agent = None
        self.thread = None
        
    def _setup_agent(self):
        """Create the audit agent if not already created"""
        if self.agent is None:
            try:
                # Load swagger.json from the project root
                swagger_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "swagger.json")
                with open(swagger_path, "r") as f:
                    audit_api_spec = loads(f.read())
                
                toolset = ToolSet()
                toolset.add(OpenApiTool(
                    name="insurance_audit_api",
                    spec=audit_api_spec,
                    description="Insurance audit logging API for tracking claim processing activities and compliance",
                    auth=OpenApiAnonymousAuthDetails(),
                ))
                
                self.agent = self.project_client.agents.create_agent(
                    model="gpt-4o-mini",
                    name=self.agent_name,
                    instructions="""
                    You are an INSURANCE AUDIT AGENT responsible for logging insurance claim processing activities.
                    
                    Your responsibilities:
                    1. Create audit records using POST /audit endpoint for all claim processing events
                    2. Track process statuses: "started", "completed", "failed", "review_required"
                    3. Log detailed process information for compliance tracking
                    4. Generate audit reports when requested
                    
                    Always create detailed audit records with:
                    - claim_id: The unique claim identifier
                    - customer_name: Customer associated with the claim
                    - process_name: Name of the process (e.g., "policy_analysis", "inspection_assessment", "bill_reimbursement")
                    - process_status: Current status of the process
                    - process_details: Detailed description of what occurred
                    - agent_name: Name of the agent that performed the process
                    """,
                    tools=toolset.definitions,
                )
                
                # Create a thread for this agent
                self.thread = self.project_client.agents.create_thread()
                
                print(f"✅ Audit agent initialized: {self.agent.name} (ID: {self.agent.id})")
                
            except Exception as e:
                print(f"❌ Error setting up audit agent: {str(e)}")
                self.agent = None
                self.thread = None
    
    def log_process_start(self, claim_id: str, customer_name: str, process_name: str, agent_name: str, process_details: str = "") -> bool:
        """Log the start of a process"""
        return self._create_audit_record(
            claim_id=claim_id,
            customer_name=customer_name,
            process_name=process_name,
            process_status="started",
            process_details=process_details or f"Started {process_name} process",
            agent_name=agent_name
        )
    
    def log_process_completion(self, claim_id: str, customer_name: str, process_name: str, agent_name: str, process_details: str = "", success: bool = True) -> bool:
        """Log the completion of a process"""
        status = "completed" if success else "failed"
        return self._create_audit_record(
            claim_id=claim_id,
            customer_name=customer_name,
            process_name=process_name,
            process_status=status,
            process_details=process_details or f"{'Completed' if success else 'Failed'} {process_name} process",
            agent_name=agent_name
        )
    
    def _create_audit_record(self, claim_id: str, customer_name: str, process_name: str, 
                           process_status: str, process_details: str, agent_name: str) -> bool:
        """Create an audit record via direct API call (optional - fails silently if unavailable)"""
        try:
            # Skip if audit API is not configured or uses default placeholder
            if not self.audit_api_base or "cosmosaudit.azurewebsites.net" in self.audit_api_base:
                # Audit API not configured - skip silently
                return True
            
            audit_data = {
                "claim_id": claim_id,
                "customer_name": customer_name,
                "process_name": process_name,
                "process_status": process_status,
                "process_details": process_details,
                "agent_name": agent_name
            }
            
            response = requests.post(
                f"{self.audit_api_base}/audit",
                json=audit_data,
                headers={"Content-Type": "application/json"},
                timeout=5
            )
            
            if response.status_code == 200:
                print(f"📝 Audit logged: {process_name} - {process_status} for claim {claim_id}")
                return True
            else:
                # Fail silently for audit logging
                return False
                
        except Exception as e:
            # Fail silently - audit is optional
            return False
    
    def get_audit_history(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve audit history for a customer"""
        try:
            response = requests.get(
                f"{self.audit_api_base}/audit/{customer_id}",
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"⚠️ Failed to retrieve audit history: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error retrieving audit history: {str(e)}")
            return None
    
    def analyze_with_agent(self, query: str) -> str:
        """Use the AI agent for complex audit analysis"""
        self._setup_agent()
        
        if not self.agent or not self.thread:
            return "❌ Audit agent not available for analysis"
        
        try:
            # Add user message
            self.project_client.agents.create_message(
                thread_id=self.thread.id,
                role="user",
                content=query
            )
            
            # Run the agent
            run = self.project_client.agents.create_and_process_run(
                thread_id=self.thread.id,
                agent_id=self.agent.id
            )
            
            # Get response
            if run.status == "failed":
                return f"❌ Audit agent analysis failed: {run.last_error}"
            else:
                messages = self.project_client.agents.list_messages(thread_id=self.thread.id)
                last_msg = messages.get_last_text_message_by_role("assistant")
                return last_msg.text.value
                
        except Exception as e:
            return f"❌ Error in audit agent analysis: {str(e)}"
    
    def cleanup(self):
        """Clean up the agent resources"""
        if self.agent:
            try:
                self.project_client.agents.delete_agent(self.agent.id)
                print("🧹 Audit agent cleaned up")
            except Exception as e:
                print(f"⚠️ Error cleaning up audit agent: {str(e)}")


# Standalone functions for backwards compatibility
def create_audit_agent(project_client):
    """Legacy function - creates audit agent using old pattern"""
    audit_agent_instance = AuditAgent()
    audit_agent_instance._setup_agent()
    return audit_agent_instance.agent

def main():
    """
    Main function to demonstrate the audit agent functionality.
    """
    audit_agent = AuditAgent()
    
    print("💬 Audit agent is ready for logging and analysis.")
    
    # Interactive loop
    while True:
        user_input = input("\n🔍 Your Question (or 'exit' to quit): ")
        if user_input.lower() in ["exit", "quit"]:
            break
        
        result = audit_agent.analyze_with_agent(user_input)
        print(f"\n🤖 Audit Agent: {result}")
    
    # Cleanup
    audit_agent.cleanup()

if __name__ == "__main__":
    main()
