# Main Auto Insurance Policy Expert Agent
# This agent serves as the authoritative source for vehicle insurance policy knowledge,
# providing definitive policy interpretations, coverage determinations, and regulatory guidance.
# It acts as the primary policy reference for all other agents in the auto insurance system.

# Step 1: Load packages
import os
import json
import re
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.projects.models import AzureAISearchTool, Tool
from azure.cosmos import CosmosClient, PartitionKey
# Load environment variables
load_dotenv()

# Azure AI Project config
ENDPOINT = os.getenv("AZURE_ENDPOINT")
RESOURCE_GROUP = os.getenv("AZURE_RESOURCE_GROUP")
SUBSCRIPTION_ID = os.getenv("AZURE_SUBSCRIPTION_ID")
PROJECT_NAME = os.getenv("AZURE_PROJECT_NAME")
INDEX_NAME = os.getenv("POLICY_INDEX_NAME", "policy")

# Step 2: Connect to your Azure AI Project
project_client = AIProjectClient(
    endpoint=ENDPOINT,
    resource_group_name=RESOURCE_GROUP,
    subscription_id=SUBSCRIPTION_ID,
    project_name=PROJECT_NAME,
    credential=DefaultAzureCredential()
)
# Step 3: Connect to Azure AI Search
conn_list = project_client.connections.list()
conn_id = ""
for conn in conn_list:
    if conn.connection_type == "CognitiveSearch":
        conn_id = conn.id
        print(f"✅ Found Azure AI Search connection: {conn_id}")

# Step 4: Define the AI Search tool
try:
    ai_search = AzureAISearchTool(
        index_connection_id=conn_id,
        index_name=INDEX_NAME,
        field_mappings={
            "content": "content",
            "title": "document_title",
            "source": "document_path",
            "claim_type": "claim_category"
        }
    )
    
except TypeError:
    print("⚠️ 'field_mappings' not supported by SDK. Proceeding without mappings.")
    ai_search = AzureAISearchTool(
        index_connection_id=conn_id,
        index_name=INDEX_NAME
    )

# Step 5: Load instructions from external file
instructions_path = Path(__file__).parent.parent / "instructions" / "policy_agent.txt"
with open(instructions_path, "r") as f:
    instructions = f.read()

# Step 6: Define the Agent with instructions from file
search_agent = project_client.agents.create_agent(
    model="gpt-4o",
    name="main-auto-insurance-policy-expert",
    instructions=instructions,
    tools=ai_search.definitions,
    tool_resources=ai_search.resources,
)

# Step 7: Create a thread and get summary
thread = project_client.agents.create_thread()

print("\n💬 Generating Main Auto Insurance Policy Expert Analysis...")

# Step 8: Create message for complete analysis
policy_expert_query = (
    "Provide a comprehensive auto insurance policy analysis including: "
    "1) Coverage types and limits (liability, collision, comprehensive) with specific amounts "
    "2) Insured Declared Value (IDV) or Sum Assured amount for the vehicle "
    "3) Key exclusions and deductibles with specific amounts "
    "4) Claims processing procedures "
    "5) Depreciation rates and calculation methods "
    "Please cite specific policy sections and include all monetary values in Indian Rupees."
)

# Add message
project_client.agents.create_message(
    thread_id=thread.id,
    role="user",
    content=policy_expert_query
)

# Run the agent
run = project_client.agents.create_and_process_run(
    thread_id=thread.id,
    agent_id=search_agent.id
)

# Display output
if run.status == "failed":
    print(f"❌ Auto insurance policy expert analysis failed: {run.last_error}")
else:
    messages = project_client.agents.list_messages(thread_id=thread.id)
    last_msg = messages.get_last_text_message_by_role("assistant")
    print("\n📋 Main Auto Insurance Policy Expert Analysis:")
    print("=" * 60)
    print(last_msg.text.value)
    print("=" * 60)

# Step 8: Clean up (optional)
project_client.agents.delete_agent(search_agent.id)
print("\n✅ Auto insurance policy expert analysis complete and agent cleaned up.")