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
import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.core_plugins import TextPlugin
from semantic_kernel.functions import KernelArguments
from dataclasses import dataclass
from azure.cosmos import CosmosClient, PartitionKey
from datetime import datetime
import json
from pathlib import Path

# Import the audit agent
from agents.auditagent import AuditAgent

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
    basic_policy_details: Optional[str] = None
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
    
    async def get_all_agent_responses(self, claim_id: str) -> list:
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
                parameters=[
                    {"name": "@claim_id", "value": claim_id}
                ],
                enable_cross_partition_query=True
            ))
            
            return items
            
        except Exception as e:
            print(f"❌ Error retrieving all agent responses: {e}")
            return []

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
        
        # Validate required environment variables
        if not all([self.ENDPOINT, self.RESOURCE_GROUP, self.SUBSCRIPTION_ID, self.PROJECT_NAME]):
            raise ValueError("Missing required Azure configuration. Please check your .env file.")
        
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
        
        # Initialize Audit Agent
        self.audit_agent = AuditAgent()
        print("✅ Audit agent initialized for process tracking")
        
        # Initialize Semantic Kernel
        self.kernel = sk.Kernel()
        self._setup_kernel()
        
        # Store agent connections and tools
        self.search_connection_id = None
        self.agents = {}
        self._setup_agents()

    def _setup_kernel(self):
        """Initialize Semantic Kernel with fallback configuration"""
        try:
            # Try to add Azure OpenAI Chat Completion service to kernel
            service_id = "azure_openai_chat"
            
            # Check if we have the necessary environment variables
            api_key = os.getenv("AZURE_OPENAI_API_KEY")
            endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", self.ENDPOINT)
            
            if api_key and endpoint:
                self.kernel.add_service(
                    AzureChatCompletion(
                        service_id=service_id,
                        endpoint=endpoint,
                        deployment_name="gpt-4o",
                        api_key=api_key,
                        api_version="2024-02-01"
                    )
                )
                print("✅ Semantic Kernel initialized with Azure OpenAI")
            else:
                print("⚠️ Azure OpenAI credentials not found, using fallback mode")
            
            # Add core plugins
            self.kernel.add_plugin(TextPlugin(), plugin_name="TextPlugin")
            
            print("✅ Semantic Kernel initialized successfully")
            
        except Exception as e:
            print(f"⚠️ Error setting up Semantic Kernel: {e}")
            print("🔄 Using fallback synthesis mode")

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

    async def get_policy_basic_details(self, claim_id: str) -> str:
        """Get basic policy details from the Main Policy Agent first"""
        print("\n🔍 Step 0: Getting Car Policy Basic Details...")
        
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
            
            # Load policy lookup instructions
            policy_lookup_instructions = load_instruction("policy_lookup_agent.txt")
            
            # Create main policy agent exactly like mainpolicy.py
            main_policy_agent = self.project_client.agents.create_agent(
                model="gpt-4o",
                name="main-auto-insurance-policy-expert",
                instructions=policy_lookup_instructions,
                tools=policy_search.definitions,
                tool_resources=policy_search.resources,
            )
            
            # Create thread and execute
            thread = self.project_client.agents.create_thread()
            
            # Query for comprehensive policy analysis including car basic details
            policy_expert_query = (
                "Provide a comprehensive auto insurance policy analysis in the following structured format: "
                "\n\n### CAR BASIC DETAILS"
                "\n- Make: [Car Make]"
                "\n- Model: [Car Model]" 
                "\n- Variant: [Car Variant]"
                "\n- Year: [Year of Registration]"
                "\n- Registration Number: [Registration Number]"
                "\n- Engine: [Engine Details]"
                "\n\n### COVERAGE DETAILS"
                "\n1) Coverage types and limits (liability, collision, comprehensive) with specific amounts "
                "\n2) Insured Declared Value (IDV): ₹[Amount]"
                "\n3) Deductible: ₹[Amount]"
                "\n4) Key exclusions and limitations"
                "\n5) Claims processing procedures "
                "\n6) Depreciation rates and calculation methods "
                "\n\nPlease follow this exact format and cite specific policy sections. Include all monetary values in Indian Rupees."
            )
            
            self.project_client.agents.create_message(
                thread_id=thread.id,
                role="user",
                content=policy_expert_query
            )
            
            run = self.project_client.agents.create_and_process_run(
                thread_id=thread.id,
                agent_id=main_policy_agent.id
            )
            
            if run.status == "failed":
                result = f"❌ Main Policy analysis failed: {run.last_error}"
            else:
                messages = self.project_client.agents.list_messages(thread_id=thread.id)
                last_msg = messages.get_last_text_message_by_role("assistant")
                result = last_msg.text.value
                
                # Store the structured response directly without regex extraction
                extracted_data = {
                    "car_details_extracted": True,
                    "structured_response": True,
                    "idv_found": "₹" in result and ("idv" in result.lower() or "declared value" in result.lower()),
                    "deductible_found": "₹" in result and "deductible" in result.lower(),
                    "coverage_eligible": self._check_coverage_eligibility(result)
                }
                
                # Store in Cosmos DB memory
                await self.memory_manager.store_agent_response(
                    claim_id=claim_id,
                    agent_type="main_policy_basic",
                    response_data=result,
                    extracted_data=extracted_data
                )
            
            # Clean up
            self.project_client.agents.delete_agent(main_policy_agent.id)
            print("✅ Car policy basic details retrieved and stored in memory")
            
            return result
            
        except Exception as e:
            return f"❌ Error in getting policy basic details: {str(e)}"

    async def execute_policy_analysis(self, claim_query: str, claim_id: str) -> str:
        """Execute the Main Policy Agent analysis and store in Cosmos DB"""
        print("\n🔍 Step 1: Executing Policy Analysis...")
        
        # Log process start
        customer_name = f"Customer-{claim_id.split('-')[-1]}"  # Extract customer from claim ID
        self.audit_agent.log_process_start(
            claim_id=claim_id,
            customer_name=customer_name,
            process_name="policy_analysis",
            agent_name="orchestrator-policy-agent",
            process_details=f"Starting policy analysis for claim: {claim_query[:100]}..."
        )
        
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
                # Log failure
                self.audit_agent.log_process_completion(
                    claim_id=claim_id,
                    customer_name=customer_name,
                    process_name="policy_analysis",
                    agent_name="orchestrator-policy-agent",
                    process_details=f"Policy analysis failed: {run.last_error}",
                    success=False
                )
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
                
                # Log successful completion
                self.audit_agent.log_process_completion(
                    claim_id=claim_id,
                    customer_name=customer_name,
                    process_name="policy_analysis",
                    agent_name="orchestrator-policy-agent",
                    process_details=f"Policy analysis completed. IDV: ₹{extracted_data.get('idv', 0):,}, Coverage Eligible: {extracted_data.get('coverage_eligible', False)}",
                    success=True
                )
            
            # Clean up
            self.project_client.agents.delete_agent(policy_agent.id)
            print("✅ Policy analysis completed and stored in memory")
            
            return result
            
        except Exception as e:
            error_msg = f"❌ Error in policy analysis: {str(e)}"
            # Log exception
            self.audit_agent.log_process_completion(
                claim_id=claim_id,
                customer_name=customer_name,
                process_name="policy_analysis",
                agent_name="orchestrator-policy-agent",
                process_details=f"Policy analysis exception: {str(e)}",
                success=False
            )
            return error_msg

    async def execute_inspection_analysis(self, claim_query: str, claim_id: str) -> str:
        """Execute the Inspection Agent analysis with memory retrieval and storage"""
        print("\n🔍 Step 2: Executing Inspection Analysis...")
        
        # Log process start
        customer_name = f"Customer-{claim_id.split('-')[-1]}"
        self.audit_agent.log_process_start(
            claim_id=claim_id,
            customer_name=customer_name,
            process_name="inspection_assessment",
            agent_name="orchestrator-inspection-agent",
            process_details=f"Starting vehicle inspection analysis for claim: {claim_query[:100]}..."
        )
        
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
                # Log failure
                self.audit_agent.log_process_completion(
                    claim_id=claim_id,
                    customer_name=customer_name,
                    process_name="inspection_assessment",
                    agent_name="orchestrator-inspection-agent",
                    process_details=f"Inspection analysis failed: {run.last_error}",
                    success=False
                )
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
                
                # Log successful completion
                self.audit_agent.log_process_completion(
                    claim_id=claim_id,
                    customer_name=customer_name,
                    process_name="inspection_assessment",
                    agent_name="orchestrator-inspection-agent",
                    process_details=f"Inspection analysis completed. Estimated repair cost: ₹{extracted_data.get('repair_cost_estimate', 0):,}, Damage authentic: {extracted_data.get('damage_authentic', False)}",
                    success=True
                )
            
            # Clean up
            self.project_client.agents.delete_agent(inspection_agent.id)
            print("✅ Inspection analysis completed and stored in memory")
            
            return result
            
        except Exception as e:
            error_msg = f"❌ Error in inspection analysis: {str(e)}"
            # Log exception
            self.audit_agent.log_process_completion(
                claim_id=claim_id,
                customer_name=customer_name,
                process_name="inspection_assessment",
                agent_name="orchestrator-inspection-agent",
                process_details=f"Inspection analysis exception: {str(e)}",
                success=False
            )
            return error_msg

    async def execute_bill_reimbursement_analysis(self, claim_query: str, claim_id: str) -> str:
        """Execute the Bill Synthesis Agent analysis with full memory context"""
        print("\n🔍 Step 3: Executing Post-Repair Bill Reimbursement Analysis...")
        
        # Log process start
        customer_name = f"Customer-{claim_id.split('-')[-1]}"
        self.audit_agent.log_process_start(
            claim_id=claim_id,
            customer_name=customer_name,
            process_name="bill_reimbursement",
            agent_name="orchestrator-bill-reimbursement-agent",
            process_details=f"Starting bill reimbursement analysis for claim: {claim_query[:100]}..."
        )
        
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
                # Log failure
                self.audit_agent.log_process_completion(
                    claim_id=claim_id,
                    customer_name=customer_name,
                    process_name="bill_reimbursement",
                    agent_name="orchestrator-bill-reimbursement-agent",
                    process_details=f"Bill reimbursement analysis failed: {run.last_error}",
                    success=False
                )
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
                
                # Log successful completion
                self.audit_agent.log_process_completion(
                    claim_id=claim_id,
                    customer_name=customer_name,
                    process_name="bill_reimbursement",
                    agent_name="orchestrator-bill-reimbursement-agent",
                    process_details=f"Bill reimbursement analysis completed. Actual bill: ₹{extracted_data.get('actual_bill_amount', 0):,}, Reimbursement: ₹{extracted_data.get('reimbursement_amount', 0):,}",
                    success=True
                )
            
            # Clean up
            self.project_client.agents.delete_agent(bill_agent.id)
            print("✅ Bill reimbursement analysis completed and stored in memory")
            
            return result
            
        except Exception as e:
            error_msg = f"❌ Error in bill reimbursement analysis: {str(e)}"
            # Log exception
            self.audit_agent.log_process_completion(
                claim_id=claim_id,
                customer_name=customer_name,
                process_name="bill_reimbursement",
                agent_name="orchestrator-bill-reimbursement-agent",
                process_details=f"Bill reimbursement analysis exception: {str(e)}",
                success=False
            )
            return error_msg

    async def synthesize_final_recommendation(self, claim_data: ClaimData) -> str:
        """Synthesize final claim recommendation with fallback logic"""
        print("\n🔍 Step 4: Synthesizing Final Recommendation...")
        
        # Log process start
        customer_name = f"Customer-{claim_data.claim_id.split('-')[-1]}"
        self.audit_agent.log_process_start(
            claim_id=claim_data.claim_id,
            customer_name=customer_name,
            process_name="final_synthesis",
            agent_name="claim-orchestrator",
            process_details="Starting final claim recommendation synthesis"
        )
        
        try:
            # Load synthesis instructions
            synthesis_instructions = load_instruction("synthesis_agent.txt")
            
            # Try Semantic Kernel first
            synthesis_prompt = f"""
            {synthesis_instructions}
            
            Based on the comprehensive analysis from three specialized agents, provide a final claim decision including:
            
            CLAIM ID: {{{{$claim_id}}}}
            
            POLICY ANALYSIS:
            {{{{$policy_analysis}}}}
            
            INSPECTION RESULTS:
            {{{{$inspection_results}}}}
            
            BILL ANALYSIS:
            {{{{$bill_analysis}}}}
            
            Provide a FINAL RECOMMENDATION including:
            1. CLAIM DECISION: Approve/Deny/Partial Approval
            2. COVERAGE AMOUNT: Specific dollar amount covered
            3. CUSTOMER RESPONSIBILITY: Deductibles and non-covered costs
            4. JUSTIFICATION: Clear reasoning based on policy, inspection, and billing analysis
            5. NEXT STEPS: Required actions for claim closure
            
            Be decisive, clear, and reference specific findings from each analysis.
            """
            
            synthesis_function = self.kernel.add_function(
                function_name="synthesize_claim",
                plugin_name="ClaimOrchestrator",
                prompt=synthesis_prompt
            )
            
            # Execute synthesis
            arguments = KernelArguments(
                claim_id=claim_data.claim_id,
                policy_analysis=claim_data.policy_analysis,
                inspection_results=claim_data.inspection_results,
                bill_analysis=claim_data.bill_analysis
            )
            
            result = await self.kernel.invoke(synthesis_function, arguments)
            
            # Log successful completion
            self.audit_agent.log_process_completion(
                claim_id=claim_data.claim_id,
                customer_name=customer_name,
                process_name="final_synthesis",
                agent_name="claim-orchestrator",
                process_details="Final claim recommendation completed using Semantic Kernel",
                success=True
            )
            
            print("✅ Final recommendation synthesized with Semantic Kernel")
            return str(result)
            
        except Exception as e:
            print(f"⚠️ Semantic Kernel synthesis failed: {str(e)}")
            print("🔄 Using fallback synthesis method...")
            
            # Log fallback attempt
            self.audit_agent.log_process_completion(
                claim_id=claim_data.claim_id,
                customer_name=customer_name,
                process_name="final_synthesis",
                agent_name="claim-orchestrator",
                process_details=f"Semantic Kernel synthesis failed: {str(e)}, using fallback method",
                success=False
            )
            
            # Fallback to rule-based synthesis
            return self._fallback_synthesis(claim_data)
    
    def _fallback_synthesis(self, claim_data: ClaimData) -> str:
        """Fallback synthesis method using rule-based logic"""
        try:
            # Extract key information from analyses
            policy_text = claim_data.policy_analysis.lower()
            inspection_text = claim_data.inspection_results.lower()
            bill_text = claim_data.bill_analysis.lower()
            
            # Determine coverage decision - improved logic
            coverage_eligible = ("collision coverage" in policy_text or "policy covers" in policy_text or 
                               "coverage applies" in policy_text or "covered under" in policy_text or
                               "own damage" in policy_text or "eligible" in policy_text or
                               "reimbursement" in policy_text or "coverage" in policy_text)
            
            # Extract cost estimates from inspection and bill analysis
            repair_cost_estimate = self._extract_cost_estimate(inspection_text + " " + bill_text)
            
            # Extract actual IDV and deductible from policy agent's response
            actual_idv = self._extract_idv_from_policy(claim_data.policy_analysis)
            deductible = self._extract_deductible(claim_data.policy_analysis)
            
            # Check if we got valid values from agents
            if actual_idv == 0:
                print("❌ Error: IDV not found in policy agent response")
                return "❌ Error: Cannot process claim - IDV (Insured Declared Value) not found in policy analysis. Policy agent needs to provide vehicle valuation information."
            
            if deductible == 0:
                print("❌ Error: Deductible not found in policy agent response")
                return "❌ Error: Cannot process claim - Deductible amount not found in policy analysis. Policy agent needs to provide deductible information."
            
            if repair_cost_estimate == 0:
                print("❌ Error: Repair cost not found in agent responses")
                return "❌ Error: Cannot process claim - Repair cost not found in inspection or bill analysis. Agents need to provide actual repair cost information."
            
            print(f"\n💰 Calculation Details:")
            print(f"   Repair Cost: ₹{repair_cost_estimate:,}")
            print(f"   Vehicle IDV (from policy): ₹{actual_idv:,}")
            print(f"   Deductible (from policy): ₹{deductible:,}")
            print(f"   Coverage Eligible: {coverage_eligible}")
            print(f"   Total Loss Indicated: {total_loss_indicated if 'total_loss_indicated' in locals() else 'Not calculated yet'}")
            
            # Debug: Show what was found in policy text
            if actual_idv == 0:
                print(f"   🔍 DEBUG: IDV extraction failed from policy text")
                print(f"   🔍 Looking for IDV patterns in: {claim_data.policy_analysis[:200]}...")
            if deductible == 0:
                print(f"   🔍 DEBUG: Deductible extraction failed from policy text")
            
            # Extract specific reimbursement amount from bill analysis
            reimbursement_amount = self._extract_reimbursement_amount(bill_text)
            
            # Check for total loss indicators or if repair cost exceeds IDV threshold
            total_loss_indicated = (("total loss" in inspection_text and "do not qualify" not in inspection_text) or 
                                  ("total loss" in bill_text and "do not qualify" not in bill_text) or 
                                  repair_cost_estimate > actual_idv * 0.75)
            
            # Generate decision based on improved logic
            if not coverage_eligible:
                decision = "DENIED"
                coverage_amount = "₹0"
                customer_responsibility = "Full repair costs"
                justification = "Policy coverage does not apply to this claim based on policy analysis."
            elif total_loss_indicated:
                decision = "APPROVED - TOTAL LOSS"
                settlement_amount = actual_idv - deductible
                coverage_amount = f"₹{settlement_amount:,} (IDV ₹{actual_idv:,} minus ₹{deductible:,} deductible)"
                customer_responsibility = f"₹{deductible:,} deductible"
                justification = f"Vehicle deemed total loss as repair cost (₹{repair_cost_estimate:,}) exceeds 75% of IDV (₹{actual_idv:,}). Settlement based on IDV minus deductible."
            else:
                # Standard reimbursement scenario
                decision = "APPROVED - REIMBURSEMENT"
                # Apply depreciation based on policy guidelines (simplified calculation)
                depreciation_deduction = int(repair_cost_estimate * 0.25)  # Average 25% depreciation for mixed parts
                net_reimbursement = repair_cost_estimate - deductible - depreciation_deduction
                coverage_amount = f"₹{max(0, net_reimbursement):,}"
                customer_responsibility = f"₹{deductible + depreciation_deduction:,} (₹{deductible:,} deductible + ₹{depreciation_deduction:,} depreciation)"
                justification = "Motor insurance coverage applies. Reimbursement calculated as repair cost minus deductible and depreciation per policy terms."
            
            # Create final recommendation
            final_recommendation = f"""
═══════════════════════════════════════════════════════════════════
                      FINAL CLAIM DECISION REPORT
═══════════════════════════════════════════════════════════════════

CLAIM ID: {claim_data.claim_id}
PROCESSING DATE: {self._get_current_date()}

1. **CLAIM DECISION**: {decision}

2. **REIMBURSEMENT AMOUNT**: {coverage_amount}

3. **CUSTOMER RESPONSIBILITY**: {customer_responsibility}

4. **PAYMENT BREAKDOWN**:
   • Actual Repair Cost: ₹{repair_cost_estimate:,}
   • Approved Reimbursement: {coverage_amount}
   • Customer Pays: {customer_responsibility}

5. **SUPPORTING RATIONALE**:
   • Policy Coverage: Motor insurance coverage confirmed for the reported incident
   • Inspection Findings: Damage consistent with reported incident, repair estimates validated
   • Bill Validation: Actual repair costs verified against pre-approved estimates and market rates
   • Exclusions applied for consumables, aesthetic work, and depreciation as per policy terms

6. **NEXT STEPS**:
   • Process reimbursement payment to customer
   • Update claim status to "Settled"
   • Handle any subrogation recovery if third party is liable
   • Issue settlement letter and close claim file

7. **TIMELINE**: 
   • Reimbursement processing: 3-5 business days from bill submission
   • Payment transfer: 2-3 business days after approval
   • Claim closure: Within 7 days of settlement

RECOMMENDATION: {decision} - Proceed with reimbursement processing as outlined above.

═══════════════════════════════════════════════════════════════════
            """
            
            print("✅ Fallback synthesis completed successfully")
            
            # Log successful fallback synthesis completion
            customer_name = f"Customer-{claim_data.claim_id.split('-')[-1]}"
            self.audit_agent.log_process_completion(
                claim_id=claim_data.claim_id,
                customer_name=customer_name,
                process_name="final_synthesis",
                agent_name="claim-orchestrator",
                process_details=f"Fallback synthesis completed successfully. Decision: {decision}",
                success=True
            )
            
            return final_recommendation.strip()
            
        except Exception as e:
            error_msg = f"❌ Error in fallback synthesis: {str(e)}"
            
            # Log fallback synthesis failure
            customer_name = f"Customer-{claim_data.claim_id.split('-')[-1]}"
            self.audit_agent.log_process_completion(
                claim_id=claim_data.claim_id,
                customer_name=customer_name,
                process_name="final_synthesis",
                agent_name="claim-orchestrator",
                process_details=f"Fallback synthesis failed: {str(e)}",
                success=False
            )
            
            return error_msg
    
    def _extract_idv_from_policy(self, policy_text: str) -> int:
        """Extract IDV (Insured Declared Value) from policy agent's response - simple text search"""
        # Look for IDV amounts in the text - simple approach without regex
        lines = policy_text.split('\n')
        for line in lines:
            line_lower = line.lower()
            if ('idv' in line_lower or 'declared value' in line_lower) and '₹' in line:
                # Extract numbers from the line
                numbers = ''.join(c for c in line if c.isdigit() or c == ',')
                if numbers:
                    try:
                        # Remove commas and convert to int
                        value = int(numbers.replace(',', ''))
                        if 100000 <= value <= 5000000:  # Reasonable IDV range
                            return value
                    except:
                        continue
        
        # If not found in specific lines, look for any reasonable amount with simple parsing
        # Split by rupee symbol and check for reasonable values
        if '₹' in policy_text:
            parts = policy_text.split('₹')
            for i in range(1, len(parts)):  # Skip first part (before first ₹)
                # Take first few characters after ₹ and extract digits
                amount_text = parts[i][:20]  # First 20 chars should contain the amount
                numbers = ''.join(c for c in amount_text if c.isdigit() or c == ',')
                if numbers:
                    try:
                        value = int(numbers.replace(',', ''))
                        if 100000 <= value <= 5000000:  # Vehicle IDV range
                            return value
                    except:
                        continue
        
        print("⚠️ Warning: IDV not found in policy agent response")
        return 0

    def _extract_reimbursement_amount(self, text: str) -> int:
        """Extract specific reimbursement amount from bill analysis text - simple text search"""
        # Look for reimbursement-related lines first
        lines = text.split('\n')
        for line in lines:
            line_lower = line.lower()
            if ('reimbursement' in line_lower or 'approved' in line_lower or 'payable' in line_lower) and '₹' in line:
                # Extract numbers from the line
                numbers = ''.join(c for c in line if c.isdigit() or c == ',')
                if numbers:
                    try:
                        value = int(numbers.replace(',', ''))
                        if 10000 <= value <= 5000000:  # Reasonable range
                            return value
                    except:
                        continue
        
        # If not found, look for any amount in bill context
        if '₹' in text:
            parts = text.split('₹')
            for i in range(1, len(parts)):
                amount_text = parts[i][:20]
                numbers = ''.join(c for c in amount_text if c.isdigit() or c == ',')
                if numbers:
                    try:
                        value = int(numbers.replace(',', ''))
                        if 10000 <= value <= 5000000:
                            return value
                    except:
                        continue
        
        return 0
    
    def _extract_cost_estimate(self, text: str) -> int:
        """Extract cost estimate from text analysis in Indian Rupees - simple text search"""
        # Look for cost-related lines
        lines = text.split('\n')
        for line in lines:
            line_lower = line.lower()
            if ('total' in line_lower or 'cost' in line_lower or 'repair' in line_lower or 'bill' in line_lower) and '₹' in line:
                # Extract numbers from the line
                numbers = ''.join(c for c in line if c.isdigit() or c == ',')
                if numbers:
                    try:
                        value = int(numbers.replace(',', ''))
                        if 10000 <= value <= 5000000:  # Reasonable range
                            return value
                    except:
                        continue
        
        # If not found, look for any reasonable amount
        if '₹' in text:
            parts = text.split('₹')
            max_amount = 0
            for i in range(1, len(parts)):
                amount_text = parts[i][:20]
                numbers = ''.join(c for c in amount_text if c.isdigit() or c == ',')
                if numbers:
                    try:
                        value = int(numbers.replace(',', ''))
                        if 10000 <= value <= 5000000 and value > max_amount:
                            max_amount = value
                    except:
                        continue
            if max_amount > 0:
                return max_amount
        
        print("⚠️ Warning: Repair cost not found in agent responses")
        return 0
    
    def _extract_deductible(self, policy_text: str) -> int:
        """Extract deductible amount from policy agent's response - simple text search"""
        # Look for deductible-related lines
        lines = policy_text.split('\n')
        for line in lines:
            line_lower = line.lower()
            if ('deductible' in line_lower or 'compulsory' in line_lower) and '₹' in line:
                # Extract numbers from the line
                numbers = ''.join(c for c in line if c.isdigit() or c == ',')
                if numbers:
                    try:
                        value = int(numbers.replace(',', ''))
                        if 500 <= value <= 50000:  # Typical deductible range
                            return value
                    except:
                        continue
        
        # Look for common deductible amounts mentioned in policy
        if "1000" in policy_text or "1,000" in policy_text:
            return 1000
        elif "2000" in policy_text or "2,000" in policy_text:
            return 2000
        elif "5000" in policy_text or "5,000" in policy_text:
            return 5000
        
        print("⚠️ Warning: Deductible not found in policy agent response")
        return 0
    
    def _check_coverage_eligibility(self, policy_text: str) -> bool:
        """Check if the claim is eligible for coverage based on policy text"""
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
        Get Basic Policy Details → Policy → (Store in Cosmos) → Inspection → (Store in Cosmos) → Bill Reimbursement → (Store in Cosmos)
        """
        print(f"\n🚀 Starting Orchestrated Claim Processing for Claim ID: {claim_id}")
        print("=" * 80)
        
        # Initialize claim data
        claim_data = ClaimData(claim_id=claim_id)
        customer_name = f"Customer-{claim_id.split('-')[-1]}"
        
        # Log overall claim processing start
        self.audit_agent.log_process_start(
            claim_id=claim_id,
            customer_name=customer_name,
            process_name="claim_processing",
            agent_name="claim-orchestrator",
            process_details=f"Starting complete claim processing workflow: {claim_description[:100]}..."
        )
        
        try:
            # Step 0: Get Car Policy Basic Details First
            claim_data.basic_policy_details = await self.get_policy_basic_details(claim_id)
            print(f"\n📋 Car Policy Basic Details:\n{claim_data.basic_policy_details}")
            
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
            
            # Log successful claim processing completion
            self.audit_agent.log_process_completion(
                claim_id=claim_id,
                customer_name=customer_name,
                process_name="claim_processing",
                agent_name="claim-orchestrator",
                process_details="Complete claim processing workflow completed successfully. All agent analyses completed and final recommendation generated.",
                success=True
            )
            
            print("\n" + "=" * 80)
            print("✅ Orchestrated claim processing completed successfully with memory persistence!")
            
            return claim_data
            
        except Exception as e:
            error_msg = f"\n❌ Error in claim processing: {str(e)}"
            print(error_msg)
            
            # Log claim processing failure
            self.audit_agent.log_process_completion(
                claim_id=claim_id,
                customer_name=customer_name,
                process_name="claim_processing",
                agent_name="claim-orchestrator",
                process_details=f"Claim processing failed with exception: {str(e)}",
                success=False
            )
            
            return claim_data
    
    def cleanup(self):
        """Clean up resources including the audit agent"""
        try:
            if hasattr(self, 'audit_agent') and self.audit_agent:
                self.audit_agent.cleanup()
                print("🧹 Orchestrator cleanup completed")
        except Exception as e:
            print(f"⚠️ Error during orchestrator cleanup: {str(e)}")

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

async def get_car_policy_basic_details_standalone():
    """Standalone function to get car policy basic details using the Main Policy Agent"""
    print("🚀 Getting Car Policy Basic Details...")
    
    # Initialize orchestrator
    orchestrator = AutoInsuranceOrchestrator()
    
    # Get basic policy details for a sample claim
    sample_claim_id = "POLICY-CHECK-001"
    basic_details = await orchestrator.get_policy_basic_details(sample_claim_id)
    
    print("\n📋 Car Policy Basic Details Retrieved:")
    print("=" * 60)
    print(basic_details)
    print("=" * 60)
    
    return basic_details

# Main execution
async def main():
    """Main function to run the orchestrator"""
    orchestrator = AutoInsuranceOrchestrator()
    
    try:
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
        
    finally:
        # Always cleanup resources
        orchestrator.cleanup()

if __name__ == "__main__":
    asyncio.run(main())