"""
Agent Factory
Handles creation and configuration of AI agents
"""

import os
from pathlib import Path
from typing import Optional
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import AzureAISearchTool
from azure.identity import DefaultAzureCredential


class AgentFactory:
    """Factory for creating and configuring AI agents"""
    
    def __init__(self):
        """Initialize Azure AI Project client"""
        self.ENDPOINT = os.getenv("AZURE_ENDPOINT")
        self.RESOURCE_GROUP = os.getenv("AZURE_RESOURCE_GROUP")
        self.SUBSCRIPTION_ID = os.getenv("AZURE_SUBSCRIPTION_ID")
        self.PROJECT_NAME = os.getenv("AZURE_PROJECT_NAME")
        
        if not all([self.ENDPOINT, self.RESOURCE_GROUP, self.SUBSCRIPTION_ID, self.PROJECT_NAME]):
            raise ValueError("Missing required Azure configuration. Please check your .env file.")
        
        self.project_client = AIProjectClient(
            endpoint=self.ENDPOINT,
            resource_group_name=self.RESOURCE_GROUP,
            subscription_id=self.SUBSCRIPTION_ID,
            project_name=self.PROJECT_NAME,
            credential=DefaultAzureCredential()
        )
        
        self.search_connection_id = self._find_search_connection()
        self.instructions_dir = Path(__file__).parent.parent / "instructions"
    
    def _find_search_connection(self) -> Optional[str]:
        """Find Azure AI Search connection"""
        try:
            conn_list = self.project_client.connections.list()
            for conn in conn_list:
                if conn.connection_type == "CognitiveSearch":
                    print(f"[OK] Found Azure AI Search connection: {conn.id}")
                    return conn.id
            raise Exception("No Azure AI Search connection found")
        except Exception as e:
            print(f"[ERROR] Error finding search connection: {e}")
            return None
    
    def _load_instruction(self, filename: str) -> str:
        """Load instruction template from file"""
        filepath = self.instructions_dir / filename
        with open(filepath, "r") as f:
            return f.read()
    
    def _create_search_tool(self, index_name: str, field_mappings: dict = None):
        """Create an Azure AI Search tool for a specific index"""
        try:
            if field_mappings:
                return AzureAISearchTool(
                    index_connection_id=self.search_connection_id,
                    index_name=index_name,
                    field_mappings=field_mappings
                )
            else:
                return AzureAISearchTool(
                    index_connection_id=self.search_connection_id,
                    index_name=index_name
                )
        except TypeError:
            print(f"[WARNING] Field mappings not supported for {index_name}. Using basic configuration.")
            return AzureAISearchTool(
                index_connection_id=self.search_connection_id,
                index_name=index_name
            )
    
    def create_policy_agent(self, instructions_file: str = "policy_coverage_agent.txt"):
        """Create policy analysis agent"""
        policy_search = self._create_search_tool(
            "policy",
            {
                "content": "content",
                "title": "document_title",
                "source": "document_path",
                "claim_type": "claim_category"
            }
        )
        
        instructions = self._load_instruction(instructions_file)
        
        return self.project_client.agents.create_agent(
            model="gpt-4o",
            name="orchestrator-policy-agent",
            instructions=instructions,
            tools=policy_search.definitions,
            tool_resources=policy_search.resources,
        )
    
    def create_inspection_agent(self, instructions: str):
        """Create inspection analysis agent"""
        inspection_search = self._create_search_tool(
            "insurance",
            {
                "content": "content",
                "title": "document_title",
                "source": "document_path",
                "image_ref": "bounding_box"
            }
        )
        
        return self.project_client.agents.create_agent(
            model="gpt-4o",
            name="orchestrator-inspection-agent",
            instructions=instructions,
            tools=inspection_search.definitions,
            tool_resources=inspection_search.resources,
        )
    
    def create_bill_agent(self, instructions: str):
        """Create bill reimbursement agent"""
        bill_search = self._create_search_tool(
            "bill",
            {
                "content": "content",
                "title": "document_title",
                "source": "document_path",
                "image_ref": "bounding_box"
            }
        )
        
        return self.project_client.agents.create_agent(
            model="gpt-4o",
            name="orchestrator-bill-reimbursement-agent",
            instructions=instructions,
            tools=bill_search.definitions,
            tool_resources=bill_search.resources,
        )
    
    def delete_agent(self, agent_id: str):
        """Delete an agent to free resources"""
        try:
            self.project_client.agents.delete_agent(agent_id)
        except Exception as e:
            print(f"[WARNING] Error deleting agent: {e}")
