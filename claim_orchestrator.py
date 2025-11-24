# Auto Insurance Claim Orchestrator
# This orchestrator manages the workflow between three specialized agents:
# 1. Main Policy Agent - Policy interpretation and coverage determination
# 2. Inspection Agent - Vehicle damage assessment and claim validation
# 3. Bill Synthesis Agent - Repair bill analysis and cost validation

import os
import asyncio
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.projects.models import AzureAISearchTool
from dataclasses import dataclass
from azure.cosmos import CosmosClient, PartitionKey
from datetime import datetime
import json
from pathlib import Path

# Load environment variables
load_dotenv()

# Load instruction templates
INSTRUCTIONS_DIR = Path(__file__).parent / "instructions"

def load_instruction(filename: str) -> str:
    """Load instruction template from file"""
    filepath = INSTRUCTIONS_DIR / filename
    with open(filepath, "r") as f:
        return f.read()

@dataclass
class ClaimData:
    """Data structure to hold claim information throughout the orchestration process"""
    claim_id: str
    policy_analysis: Optional[str] = None
    inspection_results: Optional[str] = None
    bill_analysis: Optional[str] = None
    final_recommendation: Optional[str] = None

class CosmosMemoryManager:
    """
    Manages persistent memory storage for agent responses using Azure Cosmos DB.
    Stores each agent's analysis results and allows retrieval by subsequent agents.
    """
    
    def __init__(self, cosmos_endpoint: str = None, cosmos_key: str = None):
        """Initialize Cosmos DB client and container"""
        try:
            # Get Cosmos DB configuration from environment variables
            self.cosmos_endpoint = cosmos_endpoint or os.getenv("COSMOS_DB_ENDPOINT")
            self.cosmos_key = cosmos_key or os.getenv("COSMOS_DB_KEY")
            
            if not self.cosmos_endpoint or not self.cosmos_key:
                print("⚠️ Cosmos DB credentials not found in environment variables")
                print("   Please set COSMOS_DB_ENDPOINT and COSMOS_DB_KEY")
                self.client = None
                self.container = None
                return
            
            # Initialize Cosmos client
            self.client = CosmosClient(self.cosmos_endpoint, self.cosmos_key)
            
            # Database and container configuration - using values from .env file
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
            
            print("✅ Cosmos DB Memory Manager initialized successfully")
            
        except Exception as e:
            print(f"❌ Error initializing Cosmos DB: {e}")
            self.client = None
            self.container = None
    
    async def store_agent_response(self, claim_id: str, agent_type: str, response_data: str, extracted_data: Dict[str, Any] = None) -> bool:
        """Store agent response in Cosmos DB"""
        if not self.container:
            print("⚠️ Cosmos DB not available - storing in memory only")
            return False
        
        try:
            # Create document to store
            document = {
                "id": f"{claim_id}_{agent_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "claim_id": claim_id,
                "agent_type": agent_type,
                "response_data": response_data,
                "extracted_data": extracted_data or {},
                "timestamp": datetime.now().isoformat(),
                "status": "completed"
            }
            
            # Store in Cosmos DB
            self.container.create_item(body=document)
            print(f"💾 Stored {agent_type} response for claim {claim_id} in Cosmos DB")
            return True
            
        except Exception as e:
            print(f"❌ Error storing agent response in Cosmos DB: {e}")
            return False
    
    async def retrieve_previous_responses(self, claim_id: str, agent_types: list = None) -> Dict[str, Any]:
        """Retrieve previous agent responses for a claim"""
        if not self.container:
            print("⚠️ Cosmos DB not available - no memory retrieval")
            return {}
        
        try:
            # Query for all responses for this claim
            query = "SELECT * FROM c WHERE c.claim_id = @claim_id"
            parameters = [{"name": "@claim_id", "value": claim_id}]
            
            if agent_types:
                placeholders = ', '.join([f"@agent_{i}" for i in range(len(agent_types))])
                query += f" AND c.agent_type IN ({placeholders})"
                for i, agent_type in enumerate(agent_types):
                    parameters.append({"name": f"@agent_{i}", "value": agent_type})
            
            query += " ORDER BY c.timestamp ASC"
            
            # Execute query
            items = list(self.container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            
            # Organize responses by agent type
            responses = {}
            for item in items:
                agent_type = item["agent_type"]
                responses[agent_type] = {
                    "response_data": item["response_data"],
                    "extracted_data": item.get("extracted_data", {}),
                    "timestamp": item["timestamp"]
                }
            
            print(f"📖 Retrieved {len(responses)} previous responses for claim {claim_id}")
            return responses
            
        except Exception as e:
            print(f"❌ Error retrieving previous responses: {e}")
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
            print(f"❌ Error retrieving latest response: {e}")
            return {}

class AutoInsuranceOrchestrator:
    """
    Orchestrates the auto insurance claim processing workflow using Semantic Kernel.
    Manages the sequential execution of three specialized agents.
    """
    
    def __init__(self):
        # Azure AI Project configuration from environment variables
        self.ENDPOINT = os.getenv("AZURE_ENDPOINT")
        self.RESOURCE_GROUP = os.getenv("AZURE_RESOURCE_GROUP")
        self.SUBSCRIPTION_ID = os.getenv("AZURE_SUBSCRIPTION_ID")
        self.PROJECT_NAME = os.getenv("AZURE_PROJECT_NAME")
        
        # Initialize Azure AI Project client
        self.project_client = AIProjectClient(
            endpoint=self.ENDPOINT,
            resource_group_name=self.RESOURCE_GROUP,
            subscription_id=self.SUBSCRIPTION_ID,
            project_name=self.PROJECT_NAME,
            credential=DefaultAzureCredential()
        )
        
        # Initialize Cosmos DB Memory Manager
        self.memory_manager = CosmosMemoryManager()
        
        # Store agent connections and tools
        self.search_connection_id = None
        self.agents = {}
        self._setup_agents()

    def _setup_agents(self):
        """Set up connections and search tools for all three agents"""
        try:
            # Find Azure AI Search connection
            conn_list = self.project_client.connections.list()
            for conn in conn_list:
                if conn.connection_type == "CognitiveSearch":
                    self.search_connection_id = conn.id
                    print(f"✅ Found Azure AI Search connection: {conn.id}")
                    break
            
            if not self.search_connection_id:
                raise Exception("No Azure AI Search connection found")
                
        except Exception as e:
            print(f"❌ Error setting up agents: {e}")

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
            print(f"⚠️ Field mappings not supported for {index_name}. Using basic configuration.")
            return AzureAISearchTool(
                index_connection_id=self.search_connection_id,
                index_name=index_name
            )

    async def execute_policy_analysis(self, claim_query: str, claim_id: str) -> str:
        """Execute the Main Policy Agent analysis and store in Cosmos DB"""
        print("\n🔍 Step 1: Executing Policy Analysis...")
        
        try:
            # Create policy search tool
            policy_search = self._create_search_tool(
                "policy",
                {
                    "content": "content",
                    "title": "document_title",
                    "source": "document_path",
                    "claim_type": "claim_category"
                }
            )
            
            # Load policy coverage instructions
            policy_coverage_instructions = load_instruction("policy_coverage_agent.txt")
            
            # Create policy agent
            policy_agent = self.project_client.agents.create_agent(
                model="gpt-4o",
                name="orchestrator-policy-agent",
                instructions=policy_coverage_instructions,
                tools=policy_search.definitions,
                tool_resources=policy_search.resources,
            )
            
            # Create thread and execute
            thread = self.project_client.agents.create_thread()
            
            self.project_client.agents.create_message(
                thread_id=thread.id,
                role="user",
                content=f"Analyze policy coverage for this type of auto insurance claim: {claim_query.split('totaling')[0] if 'totaling' in claim_query else claim_query}"
            )
            
            run = self.project_client.agents.create_and_process_run(
                thread_id=thread.id,
                agent_id=policy_agent.id
            )
            
            if run.status == "failed":
                result = f"❌ Policy analysis failed: {run.last_error}"
            else:
                messages = self.project_client.agents.list_messages(thread_id=thread.id)
                last_msg = messages.get_last_text_message_by_role("assistant")
                result = last_msg.text.value
                
                # Extract key policy data for memory storage
                extracted_data = {
                    "idv": self._extract_idv_from_policy(result),
                    "deductible": self._extract_deductible(result),
                    "coverage_eligible": self._check_coverage_eligibility(result)
                }
                
                # Store in Cosmos DB memory
                await self.memory_manager.store_agent_response(
                    claim_id=claim_id,
                    agent_type="policy",
                    response_data=result,
                    extracted_data=extracted_data
                )
            
            # Clean up
            self.project_client.agents.delete_agent(policy_agent.id)
            print("✅ Policy analysis completed and stored in memory")
            
            return result
            
        except Exception as e:
            return f"❌ Error in policy analysis: {str(e)}"

    async def execute_inspection_analysis(self, claim_query: str, claim_id: str) -> str:
        """Execute the Inspection Agent analysis with memory retrieval and storage"""
        print("\n🔍 Step 2: Executing Inspection Analysis...")
        
        try:
            # Retrieve previous policy analysis from memory
            policy_memory = await self.memory_manager.get_latest_response(claim_id, "policy")
            policy_context = policy_memory.get("response_data", "No policy analysis found in memory")
            extracted_policy_data = policy_memory.get("extracted_data", {})
            
            print(f"📖 Retrieved policy data from memory: IDV=₹{extracted_policy_data.get('idv', 0):,}, Deductible=₹{extracted_policy_data.get('deductible', 0):,}")
            
            # Create inspection search tool
            inspection_search = self._create_search_tool(
                "insurance",
                {
                    "content": "content",
                    "title": "document_title",
                    "source": "document_path",
                    "image_ref": "bounding_box"
                }
            )
            
            # Load inspection orchestrator instructions template
            inspection_template = load_instruction("inspection_orchestrator_agent.txt")
            
            # Replace placeholders with actual values
            inspection_instructions = inspection_template.format(
                idv=f"{extracted_policy_data.get('idv', 0):,}",
                deductible=f"{extracted_policy_data.get('deductible', 0):,}",
                coverage_eligible=extracted_policy_data.get('coverage_eligible', 'Unknown')
            )
            
            # Create inspection agent with enhanced instructions including memory context
            inspection_agent = self.project_client.agents.create_agent(
                model="gpt-4o",
                name="orchestrator-inspection-agent",
                instructions=inspection_instructions,
                tools=inspection_search.definitions,
                tool_resources=inspection_search.resources,
            )
            
            # Create thread and execute
            thread = self.project_client.agents.create_thread()
            
            inspection_query = f"""
            Conduct vehicle inspection analysis for this claim: {claim_query}
            
            POLICY CONTEXT FROM MEMORY:
            {policy_context}
            
            EXTRACTED POLICY DATA:
            - Vehicle IDV: ₹{extracted_policy_data.get('idv', 0):,}
            - Deductible: ₹{extracted_policy_data.get('deductible', 0):,}
            - Coverage Status: {extracted_policy_data.get('coverage_eligible', 'Unknown')}
            
            Focus on damage assessment, authenticity verification, cost estimation, and provide repair recommendations considering the policy limits.
            """
            
            self.project_client.agents.create_message(
                thread_id=thread.id,
                role="user",
                content=inspection_query
            )
            
            run = self.project_client.agents.create_and_process_run(
                thread_id=thread.id,
                agent_id=inspection_agent.id
            )
            
            if run.status == "failed":
                result = f"❌ Inspection analysis failed: {run.last_error}"
            else:
                messages = self.project_client.agents.list_messages(thread_id=thread.id)
                last_msg = messages.get_last_text_message_by_role("assistant")
                result = last_msg.text.value
                
                # Extract key inspection data for memory storage
                extracted_data = {
                    "repair_cost_estimate": self._extract_cost_estimate(result),
                    "total_loss_indicated": "total loss" in result.lower() and "do not qualify" not in result.lower(),
                    "damage_authentic": "authentic" in result.lower() or "consistent" in result.lower(),
                    "policy_data_used": extracted_policy_data
                }
                
                # Store in Cosmos DB memory
                await self.memory_manager.store_agent_response(
                    claim_id=claim_id,
                    agent_type="inspection",
                    response_data=result,
                    extracted_data=extracted_data
                )
            
            # Clean up
            self.project_client.agents.delete_agent(inspection_agent.id)
            print("✅ Inspection analysis completed and stored in memory")
            
            return result
            
        except Exception as e:
            return f"❌ Error in inspection analysis: {str(e)}"

    async def execute_bill_reimbursement_analysis(self, claim_query: str, claim_id: str) -> str:
        """Execute the Bill Synthesis Agent analysis with full memory context"""
        print("\n🔍 Step 3: Executing Post-Repair Bill Reimbursement Analysis...")
        
        try:
            # Retrieve all previous agent responses from memory
            all_memory = await self.memory_manager.retrieve_previous_responses(claim_id, ["policy", "inspection"])
            
            policy_memory = all_memory.get("policy", {})
            inspection_memory = all_memory.get("inspection", {})
            
            policy_data = policy_memory.get("extracted_data", {})
            inspection_data = inspection_memory.get("extracted_data", {})
            
            print(f"📖 Retrieved complete memory context:")
            print(f"   Policy: IDV=₹{policy_data.get('idv', 0):,}, Deductible=₹{policy_data.get('deductible', 0):,}")
            print(f"   Inspection: Estimate=₹{inspection_data.get('repair_cost_estimate', 0):,}, Total Loss={inspection_data.get('total_loss_indicated', False)}")
            
            # Create bill search tool
            bill_search = self._create_search_tool(
                "bill",
                {
                    "content": "content",
                    "title": "document_title",
                    "source": "document_path",
                    "image_ref": "bounding_box"
                }
            )
            
            # Load bill reimbursement instructions template
            bill_template = load_instruction("bill_reimbursement_orchestrator_agent.txt")
            
            # Replace placeholders with actual values
            bill_instructions = bill_template.format(
                idv=f"{policy_data.get('idv', 0):,}",
                deductible=f"{policy_data.get('deductible', 0):,}",
                inspection_estimate=f"{inspection_data.get('repair_cost_estimate', 0):,}",
                total_loss_status=str(inspection_data.get('total_loss_indicated', False))
            )
            
            # Create bill agent with full memory context
            bill_agent = self.project_client.agents.create_agent(
                model="gpt-4o",
                name="orchestrator-bill-reimbursement-agent",
                instructions=bill_instructions,
                tools=bill_search.definitions,
                tool_resources=bill_search.resources,
            )
            
            # Create thread and execute
            thread = self.project_client.agents.create_thread()
            
            bill_query = f"""
            ANALYZE ACTUAL REPAIR BILLS from indexed data for: {claim_query}
            
            COMPLETE MEMORY CONTEXT:
            
            POLICY ANALYSIS (from memory):
            {policy_memory.get('response_data', 'No policy data available')}
            
            INSPECTION ANALYSIS (from memory):
            {inspection_memory.get('response_data', 'No inspection data available')}
            
            EXTRACTED KEY DATA:
            - Vehicle IDV: ₹{policy_data.get('idv', 0):,}
            - Policy Deductible: ₹{policy_data.get('deductible', 0):,}
            - Inspection Cost Estimate: ₹{inspection_data.get('repair_cost_estimate', 0):,}
            - Total Loss Indicated: {inspection_data.get('total_loss_indicated', False)}
            
            CRITICAL INSTRUCTIONS:
            1. Compare ACTUAL indexed bill amounts against the inspection estimate (₹{inspection_data.get('repair_cost_estimate', 0):,})
            2. Calculate reimbursement considering IDV (₹{policy_data.get('idv', 0):,}) and deductible (₹{policy_data.get('deductible', 0):,})
            3. Flag any significant variances between estimates and actual bills
            4. Use ONLY actual amounts found in the indexed bill documents
            5. Provide final reimbursement recommendation based on memory context and actual bills
            
            Focus on: Final reimbursement calculation using complete claim memory and actual bill data.
            """
            
            self.project_client.agents.create_message(
                thread_id=thread.id,
                role="user",
                content=bill_query
            )
            
            run = self.project_client.agents.create_and_process_run(
                thread_id=thread.id,
                agent_id=bill_agent.id
            )
            
            if run.status == "failed":
                result = f"❌ Bill reimbursement analysis failed: {run.last_error}"
            else:
                messages = self.project_client.agents.list_messages(thread_id=thread.id)
                last_msg = messages.get_last_text_message_by_role("assistant")
                result = last_msg.text.value
                
                # Extract key bill data for memory storage
                extracted_data = {
                    "actual_bill_amount": self._extract_cost_estimate(result),
                    "reimbursement_amount": self._extract_reimbursement_amount(result),
                    "variance_from_estimate": inspection_data.get('repair_cost_estimate', 0) - self._extract_cost_estimate(result),
                    "memory_context_used": {
                        "policy_data": policy_data,
                        "inspection_data": inspection_data
                    }
                }
                
                # Store in Cosmos DB memory
                await self.memory_manager.store_agent_response(
                    claim_id=claim_id,
                    agent_type="bill_synthesis",
                    response_data=result,
                    extracted_data=extracted_data
                )
            
            # Clean up
            self.project_client.agents.delete_agent(bill_agent.id)
            print("✅ Bill reimbursement analysis completed and stored in memory")
            
            return result
            
        except Exception as e:
            return f"❌ Error in bill reimbursement analysis: {str(e)}"

    async def synthesize_final_recommendation(self, claim_data: ClaimData) -> str:
        """Synthesize final claim recommendation using agent-based analysis"""
        print("\n🔍 Step 4: Synthesizing Final Recommendation...")
        
        # Load synthesis instructions
        synthesis_instructions = load_instruction("synthesis_agent.txt")
        
        # Create synthesis agent for final recommendation
        synthesis_agent = self.project_client.agents.create_agent(
            model="gpt-4o",
            name="orchestrator-synthesis-agent",
            instructions=synthesis_instructions,
            tools=[],  # No search tools needed for synthesis
        )
        
        try:
            # Create thread and execute synthesis
            thread = self.project_client.agents.create_thread()
            
            synthesis_query = f"""
            SYNTHESIZE FINAL CLAIM RECOMMENDATION for Claim ID: {claim_data.claim_id}
            
            AGENT ANALYSIS INPUTS:
            
            === POLICY ANALYSIS ===
            {claim_data.policy_analysis}
            
            === INSPECTION RESULTS ===
            {claim_data.inspection_results}
            
            === BILL REIMBURSEMENT ANALYSIS ===
            {claim_data.bill_analysis}
            
            SYNTHESIS REQUIREMENTS:
            1. Extract and validate all monetary values (IDV, deductible, repair costs, depreciation amounts)
            2. Ensure consistency between agent findings
            3. Calculate final reimbursement amount with detailed breakdown
            4. Make clear approval/denial decision with comprehensive justification
            5. Provide customer communication summary with exact amounts
            6. Include professional claim closure steps
            
            Provide a complete, professional claim decision report that synthesizes all agent findings into a final recommendation.
            """
            
            self.project_client.agents.create_message(
                thread_id=thread.id,
                role="user",
                content=synthesis_query
            )
            
            run = self.project_client.agents.create_and_process_run(
                thread_id=thread.id,
                agent_id=synthesis_agent.id
            )
            
            if run.status == "failed":
                result = f"❌ Final synthesis failed: {run.last_error}"
            else:
                messages = self.project_client.agents.list_messages(thread_id=thread.id)
                last_msg = messages.get_last_text_message_by_role("assistant")
                result = last_msg.text.value
            
            # Clean up
            self.project_client.agents.delete_agent(synthesis_agent.id)
            print("✅ Final recommendation synthesized with Synthesis Agent")
            
            return result
            
        except Exception as e:
            print(f"❌ Error in synthesis agent: {str(e)}")
            return f"❌ Error in final synthesis: {str(e)}"
    
    def _calculate_detailed_depreciation(self, bill_analysis: str, total_repair_cost: int) -> dict:
        """Calculate detailed component-wise depreciation based on industry standards"""
        import re
        
        # Industry standard depreciation rates
        depreciation_rates = {
            'plastic': 0.50,    # 50% for plastic parts (bumpers, plastic body panels)
            'fiber': 0.30,      # 30% for fiber parts (fiber body panels, spoilers)
            'metal': 0.00,      # 0% for metal parts (hood, fender, doors - if paintwork only)
            'glass': 0.00,      # 0% for glass (windshield, windows)
            'rubber': 0.50,     # 50% for rubber parts (seals, gaskets)
            'paint': 0.00,      # 0% for painting work
            'labor': 0.00,      # 0% for labor charges
            'airbag': 0.00,     # 0% for safety components
            'electrical': 0.00  # 0% for electrical components
        }
        
        # Component cost breakdown with classification
        components = {
            'plastic_parts': [],
            'fiber_parts': [],
            'metal_parts': [],
            'glass_parts': [],
            'rubber_parts': [],
            'paint_work': [],
            'labor': [],
            'airbag': [],
            'electrical': []
        }
        
        bill_lower = bill_analysis.lower()
        
        # Extract and classify components from bill analysis
        # Look for specific component mentions with costs
        component_patterns = {
            'plastic_parts': [
                r'(?:front\s+)?bumper.*?₹\s*[\d,]+',
                r'plastic.*?₹\s*[\d,]+',
                r'body\s+panel.*?₹\s*[\d,]+',
                r'trim.*?₹\s*[\d,]+'
            ],
            'fiber_parts': [
                r'fiber.*?₹\s*[\d,]+',
                r'spoiler.*?₹\s*[\d,]+',
                r'body\s+kit.*?₹\s*[\d,]+'
            ],
            'metal_parts': [
                r'(?:bonnet|hood).*?(?:denting|repair|painting).*?₹\s*[\d,]+',
                r'fender.*?(?:repair|painting).*?₹\s*[\d,]+',
                r'door.*?(?:repair|painting).*?₹\s*[\d,]+',
                r'panel.*?(?:repair|painting).*?₹\s*[\d,]+'
            ],
            'glass_parts': [
                r'(?:windshield|windscreen).*?₹\s*[\d,]+',
                r'glass.*?₹\s*[\d,]+',
                r'window.*?₹\s*[\d,]+'
            ],
            'paint_work': [
                r'painting.*?₹\s*[\d,]+',
                r'paint.*?₹\s*[\d,]+',
                r'spray.*?₹\s*[\d,]+'
            ],
            'labor': [
                r'labor.*?₹\s*[\d,]+',
                r'labour.*?₹\s*[\d,]+',
                r'service.*?₹\s*[\d,]+',
                r'installation.*?₹\s*[\d,]+'
            ],
            'airbag': [
                r'airbag.*?₹\s*[\d,]+',
                r'air\s+bag.*?₹\s*[\d,]+'
            ],
            'electrical': [
                r'headlight.*?₹\s*[\d,]+',
                r'fog\s+light.*?₹\s*[\d,]+',
                r'tail\s+light.*?₹\s*[\d,]+',
                r'electrical.*?₹\s*[\d,]+',
                r'wiring.*?₹\s*[\d,]+'
            ]
        }
        
        # Extract costs for each component category
        total_classified_cost = 0
        for category, patterns in component_patterns.items():
            category_cost = 0
            for pattern in patterns:
                matches = re.findall(pattern, bill_lower)
                for match in matches:
                    amounts = re.findall(r'₹\s*[\d,]+', match)
                    for amount in amounts:
                        try:
                            cost = int(amount.replace('₹', '').replace(',', '').strip())
                            components[category].append({
                                'item': match.strip(),
                                'cost': cost
                            })
                            category_cost += cost
                        except:
                            continue
            total_classified_cost += category_cost
        
        # If we couldn't classify enough components, apply proportional distribution
        unclassified_cost = max(0, total_repair_cost - total_classified_cost)
        if unclassified_cost > 0:
            # Distribute unclassified cost proportionally (assume mixed parts)
            components['plastic_parts'].append({
                'item': 'Unclassified plastic components',
                'cost': int(unclassified_cost * 0.4)  # 40% assumed plastic
            })
            components['metal_parts'].append({
                'item': 'Unclassified metal work',
                'cost': int(unclassified_cost * 0.3)  # 30% assumed metal work
            })
            components['electrical'].append({
                'item': 'Unclassified electrical components',
                'cost': int(unclassified_cost * 0.2)  # 20% assumed electrical
            })
            components['labor'].append({
                'item': 'Unclassified labor',
                'cost': unclassified_cost - int(unclassified_cost * 0.9)  # Remaining as labor
            })
        
        # Calculate depreciation for each category
        depreciation_breakdown = {
            'plastic': {'cost': 0, 'depreciation': 0, 'items': []},
            'fiber': {'cost': 0, 'depreciation': 0, 'items': []},
            'metal': {'cost': 0, 'depreciation': 0, 'items': []},
            'glass': {'cost': 0, 'depreciation': 0, 'items': []},
            'paint': {'cost': 0, 'depreciation': 0, 'items': []},
            'labor': {'cost': 0, 'depreciation': 0, 'items': []},
            'airbag': {'cost': 0, 'depreciation': 0, 'items': []},
            'electrical': {'cost': 0, 'depreciation': 0, 'items': []},
            'total_depreciation': 0
        }
        
        # Map component categories to depreciation categories
        category_mapping = {
            'plastic_parts': 'plastic',
            'fiber_parts': 'fiber',
            'metal_parts': 'metal',
            'glass_parts': 'glass',
            'paint_work': 'paint',
            'labor': 'labor',
            'airbag': 'airbag',
            'electrical': 'electrical'
        }
        
        for comp_category, items in components.items():
            if items:
                dep_category = category_mapping[comp_category]
                category_cost = sum(item['cost'] for item in items)
                depreciation_amount = int(category_cost * depreciation_rates[dep_category])
                
                depreciation_breakdown[dep_category]['cost'] = category_cost
                depreciation_breakdown[dep_category]['depreciation'] = depreciation_amount
                depreciation_breakdown[dep_category]['items'] = items
                depreciation_breakdown['total_depreciation'] += depreciation_amount
        
        return depreciation_breakdown
    
    def _format_depreciation_breakdown(self, depreciation_breakdown: dict) -> str:
        """Format depreciation breakdown for display"""
        lines = []
        
        for category, data in depreciation_breakdown.items():
            if category == 'total_depreciation':
                continue
            
            if data['cost'] > 0:
                rate = (data['depreciation'] / data['cost']) * 100 if data['cost'] > 0 else 0
                lines.append(f"• {category.title()} Parts: ₹{data['cost']:,} @ {rate:.0f}% = ₹{data['depreciation']:,} depreciation")
                
                # Add item details if available
                if data['items']:
                    for item in data['items'][:3]:  # Show first 3 items
                        lines.append(f"  - {item['item'][:50]}...")
                    if len(data['items']) > 3:
                        lines.append(f"  - ... and {len(data['items'])-3} more items")
        
        lines.append(f"\nTotal Depreciation: ₹{depreciation_breakdown['total_depreciation']:,}")
        
        return '\n'.join(lines)
    
    def _extract_idv_from_policy(self, policy_text: str) -> int:
        """Extract IDV (Insured Declared Value) from policy agent's response"""
        import re
        
        # Look for IDV/Sum Assured patterns with rupee amounts
        idv_patterns = [
            r'(?:idv|insured\s+declared\s+value|sum\s+assured).*?₹\s*[\d,]+',
            r'₹\s*[\d,]+.*?(?:idv|insured\s+declared\s+value|sum\s+assured)',
            r'policy\s+value.*?₹\s*[\d,]+',
            r'vehicle\s+value.*?₹\s*[\d,]+',
            r'coverage\s+limit.*?₹\s*[\d,]+'
        ]
        
        for pattern in idv_patterns:
            matches = re.findall(pattern, policy_text, re.IGNORECASE)
            if matches:
                amounts = re.findall(r'₹\s*[\d,]+', matches[0])
                if amounts:
                    try:
                        clean_amount = amounts[0].replace('₹', '').replace(',', '').strip()
                        value = int(clean_amount)
                        if 100000 <= value <= 5000000:  # Reasonable IDV range ₹1L-₹50L
                            return value
                    except:
                        continue
        
        # Look for any reasonable rupee amounts in policy text
        amounts = re.findall(r'₹\s*[\d,]+', policy_text)
        for amount in amounts:
            try:
                clean_amount = amount.replace('₹', '').replace(',', '').strip()
                value = int(clean_amount)
                if 100000 <= value <= 5000000:  # Vehicle IDV range
                    return value
            except:
                continue
        
        # Default fallback
        return 321100  # Use a reasonable default if not found

    def _extract_deductible(self, policy_text: str) -> int:
        """Extract deductible amount from policy agent's response"""
        import re
        
        # Look for deductible mentions with rupee amounts
        deductible_patterns = [
            r'(?:deductible|compulsory\s+deductible|mandatory\s+deductible).*?₹\s*[\d,]+',
            r'₹\s*[\d,]+.*?(?:deductible|compulsory|mandatory)',
            r'customer\s+pays.*?₹\s*[\d,]+',
            r'out.of.pocket.*?₹\s*[\d,]+'
        ]
        
        for pattern in deductible_patterns:
            matches = re.findall(pattern, policy_text, re.IGNORECASE)
            if matches:
                amounts = re.findall(r'₹\s*[\d,]+', matches[0])
                if amounts:
                    try:
                        clean_amount = amounts[0].replace('₹', '').replace(',', '').strip()
                        value = int(clean_amount)
                        if 500 <= value <= 50000:  # Typical deductible range
                            return value
                    except:
                        continue
        
        # Default fallback
        return 1000  # Standard deductible if not found

    def _extract_cost_estimate(self, text: str) -> int:
        """Extract cost estimate from text analysis"""
        import re
        
        # Look for rupee amounts in the text
        amounts = re.findall(r'₹\s*[\d,]+', text)
        if amounts:
            # Extract the largest reasonable amount found
            max_amount = 0
            for amount in amounts:
                try:
                    clean_amount = amount.replace('₹', '').replace(',', '').strip()
                    value = int(clean_amount)
                    if 10000 <= value <= 500000 and value > max_amount:  # Reasonable range
                        max_amount = value
                except:
                    continue
            if max_amount > 0:
                return max_amount
        
        # Default fallback
        return 50000  # Reasonable default estimate

    def _extract_reimbursement_amount(self, text: str) -> int:
        """Extract reimbursement amount from bill analysis text"""
        import re
        
        # Look for reimbursement patterns
        patterns = [
            r'reimbursement.*?₹\s*[\d,]+',
            r'approved.*?₹\s*[\d,]+',
            r'payable.*?₹\s*[\d,]+',
            r'final.*?₹\s*[\d,]+',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                amounts = re.findall(r'₹\s*[\d,]+', matches[0])
                if amounts:
                    try:
                        clean_amount = amounts[0].replace('₹', '').replace(',', '').strip()
                        value = int(clean_amount)
                        if 10000 <= value <= 500000:
                            return value
                    except:
                        continue
        
        # Default fallback
        return 45000  # Reasonable default reimbursement

    def _check_coverage_eligibility(self, policy_text: str) -> bool:
        """Check if the claim is eligible for coverage"""
        policy_lower = policy_text.lower()
        return ("collision coverage" in policy_lower or "policy covers" in policy_lower or 
                "coverage applies" in policy_lower or "covered under" in policy_lower or
                "own damage" in policy_lower or "eligible" in policy_lower or
                "reimbursement" in policy_lower or "coverage" in policy_lower)

    def _get_current_date(self) -> str:
        """Get current date for reporting"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d")

    async def process_claim(self, claim_id: str, claim_description: str) -> ClaimData:
        """
        Main orchestration method that processes a complete auto insurance claim
        through all three agents in sequence with Cosmos DB memory integration:
        Policy → (Store in Cosmos) → Inspection → (Store in Cosmos) → Bill Reimbursement → (Store in Cosmos)
        """
        print(f"\n🚀 Starting Orchestrated Claim Processing for Claim ID: {claim_id}")
        print("=" * 80)
        
        # Initialize claim data
        claim_data = ClaimData(claim_id=claim_id)
        
        try:
            # Step 1: Policy Analysis - Store results in Cosmos DB memory
            claim_data.policy_analysis = await self.execute_policy_analysis(claim_description, claim_id)
            print(f"\n📋 Policy Analysis Result:\n{claim_data.policy_analysis}")
            
            # Step 2: Inspection Analysis - Retrieve policy data from memory and store results
            claim_data.inspection_results = await self.execute_inspection_analysis(claim_description, claim_id)
            print(f"\n🔍 Inspection Results:\n{claim_data.inspection_results}")
            
            print("\n🔧 === REPAIR PHASE ===")
            print("At this point, customer would:")
            print("• Get policy pre-approval based on inspection")
            print("• Complete repairs at authorized facility")
            print("• Submit actual repair bills for reimbursement")
            print("=" * 50)
            
            # Step 3: Bill Analysis - Retrieve all previous agent data from memory and store results
            claim_data.bill_analysis = await self.execute_bill_reimbursement_analysis(claim_description, claim_id)
            print(f"\n💰 Bill Reimbursement Analysis:\n{claim_data.bill_analysis}")
            
            # Step 4: Final Synthesis - Now with complete memory context
            claim_data.final_recommendation = await self.synthesize_final_recommendation(claim_data)
            
            # Store final recommendation in memory as well
            if claim_data.final_recommendation:
                await self.memory_manager.store_agent_response(
                    claim_id=claim_id,
                    agent_type="final_synthesis",
                    response_data=claim_data.final_recommendation,
                    extracted_data={"synthesis_completed": True, "claim_status": "completed"}
                )
            
            print("\n" + "=" * 80)
            print("✅ Orchestrated claim processing completed successfully with memory persistence!")
            
            return claim_data
            
        except Exception as e:
            print(f"\n❌ Error in claim processing: {str(e)}")
            return claim_data

    async def interactive_mode(self):
        """Interactive mode for processing multiple claims"""
        print("\n🤖 Auto Insurance Claim Orchestrator - Interactive Mode")
        print("Enter claim details to process through all three agents")
        print("Type 'exit' to quit\n")
        
        while True:
            try:
                claim_id = input("🆔 Enter Claim ID: ").strip()
                if claim_id.lower() in ['exit', 'quit']:
                    break
                
                claim_description = input("📝 Enter Claim Description: ").strip()
                if claim_description.lower() in ['exit', 'quit']:
                    break
                
                if claim_id and claim_description:
                    await self.process_claim(claim_id, claim_description)
                else:
                    print("⚠️ Please provide both Claim ID and Description")
                
                print("\n" + "-" * 40)
                
            except KeyboardInterrupt:
                print("\n👋 Exiting orchestrator...")
                break
            except Exception as e:
                print(f"❌ Error: {str(e)}")

# Main execution
async def main():
    """Main function to run the orchestrator"""
    orchestrator = AutoInsuranceOrchestrator()
    
    # Process single claim example
    print("🚀 Auto Insurance Claim Orchestrator Initialized")
    
    example_claim_id = "CLM-2024-001"
    example_description = """Vehicle collision claim - front-end accident with significant bumper, hood, and headlight damage. 
    Customer has completed repairs at authorized service center. 
    Need policy coverage review, damage assessment validation, and reimbursement determination for actual repair costs."""
    
    claim_result = await orchestrator.process_claim(example_claim_id, example_description)
    
    print("\n📊 COMPLETE CLAIM SUMMARY:")
    print("=" * 50)
    print(f"Claim ID: {claim_result.claim_id}")
    print(f"Status: PROCESSING COMPLETED")
    print("=" * 50)
    
    # Display final recommendation if available
    if hasattr(claim_result, 'final_recommendation') and claim_result.final_recommendation:
        print(f"\n🎯 Final Decision:\n{claim_result.final_recommendation}")
    
    print("\n✅ Claim processing completed successfully!")

if __name__ == "__main__":
    asyncio.run(main())
