import os
from dotenv import load_dotenv

load_dotenv()

# Azure Blob Storage
STORAGE_ACCOUNT_NAME = os.getenv("STORAGE_ACCOUNT_NAME")
STORAGE_ACCOUNT_KEY = os.getenv("STORAGE_ACCOUNT_KEY")
CONTAINER_NAME = os.getenv("CONTAINER_NAME")

# Azure Document Intelligence
DOC_INTEL_ENDPOINT = os.getenv("DOC_INTEL_ENDPOINT")
DOC_INTEL_KEY = os.getenv("DOC_INTEL_KEY")

# Azure OpenAI
OPENAI_ENDPOINT = os.getenv("OPENAI_ENDPOINT")
OPENAI_SUBSCRIPTION_KEY = os.getenv("OPENAI_SUBSCRIPTION_KEY")
OPENAI_API_VERSION = os.getenv("OPENAI_API_VERSION")
OPENAI_DEPLOYMENT_NAME = os.getenv("OPENAI_DEPLOYMENT_NAME")
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME")

# Azure AI Search
SEARCH_SERVICE_ENDPOINT = os.getenv("SEARCH_SERVICE_ENDPOINT")
SEARCH_SERVICE_KEY = os.getenv("SEARCH_SERVICE_KEY")
SEARCH_INDEX_NAME = os.getenv("SEARCH_INDEX_NAME")

# Validate required environment variables
required_env_vars = [
    "STORAGE_ACCOUNT_NAME", "STORAGE_ACCOUNT_KEY", "CONTAINER_NAME",
    "DOC_INTEL_ENDPOINT", "DOC_INTEL_KEY",
    "OPENAI_ENDPOINT", "OPENAI_SUBSCRIPTION_KEY", "OPENAI_API_VERSION",
    "OPENAI_DEPLOYMENT_NAME", "EMBEDDING_MODEL_NAME",
    "SEARCH_SERVICE_ENDPOINT", "SEARCH_SERVICE_KEY", "SEARCH_INDEX_NAME"
]

missing_vars = [var for var in required_env_vars if not os.getenv(var)]
if missing_vars:
    import sys
    print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
    print("Please check your .env file and ensure all required variables are set.")
    print("Copy .env.example to .env and fill in your Azure credentials.")
    sys.exit(1)
