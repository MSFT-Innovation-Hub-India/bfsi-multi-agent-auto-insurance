"""
Cosmos DB Memory Manager
Handles persistent storage and retrieval of agent responses
Supports both Key-based and Managed Identity authentication
"""

import os
from typing import Dict, Any, Optional, List
from azure.cosmos import CosmosClient, PartitionKey
from azure.identity import ManagedIdentityCredential, AzureCliCredential
from datetime import datetime


class CosmosMemoryManager:
    """
    Manages persistent memory storage for agent responses using Azure Cosmos DB.
    Stores each agent's analysis results and allows retrieval by subsequent agents.
    Supports Managed Identity (production) or Azure CLI (local development).
    """
    
    def __init__(self, cosmos_endpoint: str = None):
        """Initialize Cosmos DB client with Managed Identity or Azure CLI credential"""
        try:
            # Get Cosmos DB configuration from environment variables
            self.cosmos_endpoint = cosmos_endpoint or os.getenv("COSMOS_DB_ENDPOINT")
            self.cosmos_key = os.getenv("COSMOS_DB_KEY")
            
            if not self.cosmos_endpoint:
                print("⚠️ COSMOS_DB_ENDPOINT not found in environment variables")
                self.client = None
                self.container = None
                return
            
            # Database and container configuration
            self.database_name = os.getenv("COSMOS_DB_DATABASE_NAME", "insurance")
            self.container_name = os.getenv("COSMOS_DB_CONTAINER_NAME", "data")
            
            # Choose credential based on environment
            auth_method = None
            try:
                print("🔐 Trying Azure authentication...")
                # Check if running in Azure (has WEBSITE_INSTANCE_ID env var)
                if os.getenv("WEBSITE_INSTANCE_ID"):
                    # In Azure - use ManagedIdentity
                    print("   (Running in Azure - using Managed Identity)")
                    credential = ManagedIdentityCredential()
                else:
                    # Local - use AzureCLI (faster)
                    print("   (Running locally - using Azure CLI)")
                    credential = AzureCliCredential()
                
                self.client = CosmosClient(self.cosmos_endpoint, credential=credential)
                # Test the connection by getting database
                self.database = self.client.get_database_client(self.database_name)
                self.container = self.database.get_container_client(self.container_name)
                # Verify access by reading container properties
                self.container.read()
                auth_method = "Entra ID (Managed Identity / CLI)"
                print(f"[OK] Cosmos DB connected with {auth_method}")
            except Exception as mi_error:
                print(f"⚠️ Entra ID auth failed: {mi_error}")
                # Fall back to Key-based auth if available
                if self.cosmos_key:
                    try:
                        print("🔑 Trying Key-based authentication...")
                        self.client = CosmosClient(self.cosmos_endpoint, credential=self.cosmos_key)
                        self.database = self.client.get_database_client(self.database_name)
                        self.container = self.database.get_container_client(self.container_name)
                        self.container.read()
                        auth_method = "Key-based"
                        print(f"[OK] Cosmos DB connected with Key-based auth")
                    except Exception as key_error:
                        print(f"❌ Key-based auth also failed: {key_error}")
                        raise key_error
                else:
                    raise mi_error
            
            print(f"[OK] Cosmos DB Memory Manager initialized with {auth_method}")
            print(f"     Database: {self.database_name}, Container: {self.container_name}")
            
        except Exception as e:
            print(f"[ERROR] Error initializing Cosmos DB: {e}")
            self.client = None
            self.container = None
    
    async def store_agent_response(
        self, 
        claim_id: str, 
        agent_type: str, 
        response_data: str, 
        extracted_data: Dict[str, Any] = None
    ) -> bool:
        """Store agent response in Cosmos DB"""
        if not self.container:
            print("[WARNING] Cosmos DB not available - storing in memory only")
            return False
        
        try:
            document = {
                "id": f"{claim_id}_{agent_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "claim_id": claim_id,
                "agent_type": agent_type,
                "response_data": response_data,
                "extracted_data": extracted_data or {},
                "timestamp": datetime.now().isoformat(),
                "status": "completed"
            }
            
            self.container.create_item(body=document)
            print(f"[SAVED] Stored {agent_type} response for claim {claim_id} in Cosmos DB")
            return True
            
        except Exception as e:
            print(f"[ERROR] Error storing agent response in Cosmos DB: {e}")
            return False
    
    async def retrieve_previous_responses(
        self, 
        claim_id: str, 
        agent_types: List[str] = None
    ) -> Dict[str, Any]:
        """Retrieve previous agent responses for a claim"""
        if not self.container:
            print("[WARNING] Cosmos DB not available - no memory retrieval")
            return {}
        
        try:
            query = "SELECT * FROM c WHERE c.claim_id = @claim_id"
            parameters = [{"name": "@claim_id", "value": claim_id}]
            
            if agent_types:
                placeholders = ', '.join([f"@agent_{i}" for i in range(len(agent_types))])
                query += f" AND c.agent_type IN ({placeholders})"
                for i, agent_type in enumerate(agent_types):
                    parameters.append({"name": f"@agent_{i}", "value": agent_type})
            
            query += " ORDER BY c.timestamp ASC"
            
            items = list(self.container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            
            responses = {}
            for item in items:
                agent_type = item["agent_type"]
                responses[agent_type] = {
                    "response_data": item["response_data"],
                    "extracted_data": item.get("extracted_data", {}),
                    "timestamp": item["timestamp"]
                }
            
            print(f"[LOADED] Retrieved {len(responses)} previous responses for claim {claim_id}")
            return responses
            
        except Exception as e:
            print(f"[ERROR] Error retrieving previous responses: {e}")
            return {}
    
    async def get_latest_response(self, claim_id: str, agent_type: str) -> Dict[str, Any]:
        """Get the latest response from a specific agent for a claim"""
        if not self.container:
            return {}
        
        try:
            query = """
            SELECT TOP 1 * FROM c 
            WHERE c.claim_id = @claim_id AND c.agent_type = @agent_type 
            ORDER BY c.timestamp DESC
            """
            
            items = list(self.container.query_items(
                query=query,
                parameters=[
                    {"name": "@claim_id", "value": claim_id},
                    {"name": "@agent_type", "value": agent_type}
                ],
                enable_cross_partition_query=True
            ))
            
            if items:
                return {
                    "response_data": items[0]["response_data"],
                    "extracted_data": items[0].get("extracted_data", {}),
                    "timestamp": items[0]["timestamp"]
                }
            return {}
            
        except Exception as e:
            print(f"[ERROR] Error retrieving latest response: {e}")
            return {}
    
    async def get_all_agent_responses(self, claim_id: str) -> List[Dict[str, Any]]:
        """Get all agent responses for a specific claim"""
        if not self.container:
            return []
        
        try:
            query = """
            SELECT c.agent_type, c.response_data, c.extracted_data, c.timestamp, c.status
            FROM c 
            WHERE c.claim_id = @claim_id 
            ORDER BY c.timestamp ASC
            """
            
            items = list(self.container.query_items(
                query=query,
                parameters=[{"name": "@claim_id", "value": claim_id}],
                enable_cross_partition_query=True
            ))
            
            return items
            
        except Exception as e:
            print(f"[ERROR] Error retrieving all agent responses: {e}")
            return []
