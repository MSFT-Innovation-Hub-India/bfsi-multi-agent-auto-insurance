"""
Cosmos DB Memory Manager
Handles persistent storage and retrieval of agent responses
Uses Managed Identity (DefaultAzureCredential) for authentication
"""

import os
from typing import Dict, Any, Optional, List
from azure.cosmos import CosmosClient, PartitionKey
from azure.identity import DefaultAzureCredential
from datetime import datetime


class CosmosMemoryManager:
    """
    Manages persistent memory storage for agent responses using Azure Cosmos DB.
    Stores each agent's analysis results and allows retrieval by subsequent agents.
    Uses Managed Identity for authentication.
    """
    
    def __init__(self, cosmos_endpoint: str = None):
        """Initialize Cosmos DB client with Managed Identity"""
        try:
            # Get Cosmos DB configuration from environment variables
            self.cosmos_endpoint = cosmos_endpoint or os.getenv("COSMOS_DB_ENDPOINT")
            
            if not self.cosmos_endpoint:
                print("⚠️ COSMOS_DB_ENDPOINT not found in environment variables")
                self.client = None
                self.container = None
                return
            
            # Initialize Cosmos client with Managed Identity
            credential = DefaultAzureCredential()
            self.client = CosmosClient(self.cosmos_endpoint, credential=credential)
            
            # Database and container configuration
            self.database_name = os.getenv("COSMOS_DB_DATABASE_NAME", "insurance")
            self.container_name = os.getenv("COSMOS_DB_CONTAINER_NAME", "data")
            
            # Create database if it doesn't exist
            self.database = self.client.create_database_if_not_exists(id=self.database_name)
            
            # Create container if it doesn't exist (partition key is claim_id)
            self.container = self.database.create_container_if_not_exists(
                id=self.container_name,
                partition_key=PartitionKey(path="/claim_id"),
                offer_throughput=400
            )
            
            print("[OK] Cosmos DB Memory Manager initialized with Managed Identity")
            
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
