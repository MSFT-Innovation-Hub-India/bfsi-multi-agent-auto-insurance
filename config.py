"""
Configuration module for Azure Auto Insurance Claims System
Centralizes all environment variable loading and validation
"""
import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Central configuration class for the application"""
    
    # ============================================================
    # Azure AI Project Configuration
    # ============================================================
    AZURE_ENDPOINT: str = os.getenv("AZURE_ENDPOINT", "")
    AZURE_RESOURCE_GROUP: str = os.getenv("AZURE_RESOURCE_GROUP", "")
    AZURE_SUBSCRIPTION_ID: str = os.getenv("AZURE_SUBSCRIPTION_ID", "")
    AZURE_PROJECT_NAME: str = os.getenv("AZURE_PROJECT_NAME", "")
    
    # ============================================================
    # Azure OpenAI Configuration
    # ============================================================
    AZURE_OPENAI_DEPLOYMENT_NAME: str = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")
    AZURE_OPENAI_ENDPOINT: str = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    AZURE_OPENAI_API_KEY: str = os.getenv("AZURE_OPENAI_API_KEY", "")
    
    # ============================================================
    # Cosmos DB Configuration
    # ============================================================
    COSMOS_DB_ENDPOINT: str = os.getenv("COSMOS_DB_ENDPOINT", "")
    COSMOS_DB_DATABASE_NAME: str = os.getenv("COSMOS_DB_DATABASE_NAME", "insurance")
    COSMOS_DB_CONTAINER_NAME: str = os.getenv("COSMOS_DB_CONTAINER_NAME", "data")
    
    # ============================================================
    # Azure AI Search Configuration
    # ============================================================
    SEARCH_ENDPOINT: str = os.getenv("SEARCH_ENDPOINT", "")
    SEARCH_KEY: str = os.getenv("SEARCH_KEY", "")
    POLICY_INDEX_NAME: str = os.getenv("POLICY_INDEX_NAME", "policy")
    INSURANCE_INDEX_NAME: str = os.getenv("INSURANCE_INDEX_NAME", "insurance")
    BILL_INDEX_NAME: str = os.getenv("BILL_INDEX_NAME", "bill")
    
    # ============================================================
    # Azure Blob Storage Configuration (uses Managed Identity)
    # ============================================================
    AZURE_STORAGE_ACCOUNT_NAME: str = os.getenv("AZURE_STORAGE_ACCOUNT_NAME", "")
    AZURE_STORAGE_CONTAINER_NAME: str = os.getenv("AZURE_STORAGE_CONTAINER_NAME", "vehicle-insurance")
    
    # ============================================================
    # Audit API Configuration
    # ============================================================
    AUDIT_API_BASE_URL: str = os.getenv("AUDIT_API_BASE_URL", "https://cosmosaudit.azurewebsites.net")
    
    # ============================================================
    # Azure AI Content Understanding (Optional)
    # ============================================================
    AZURE_AI_ENDPOINT: str = os.getenv("AZURE_AI_ENDPOINT", "")
    AZURE_AI_API_VERSION: str = os.getenv("AZURE_AI_API_VERSION", "2025-05-01-preview")
    
    @classmethod
    def validate_required_config(cls) -> list[str]:
        """
        Validate that all required configuration values are set.
        Uses Managed Identity for authentication - only endpoints are required.
        Returns a list of missing configuration keys.
        """
        missing_configs = []
        
        # Required Azure AI Project configs
        required_azure_configs = [
            ("AZURE_ENDPOINT", cls.AZURE_ENDPOINT),
            ("AZURE_RESOURCE_GROUP", cls.AZURE_RESOURCE_GROUP),
            ("AZURE_SUBSCRIPTION_ID", cls.AZURE_SUBSCRIPTION_ID),
            ("AZURE_PROJECT_NAME", cls.AZURE_PROJECT_NAME),
        ]
        
        # Required Cosmos DB configs (endpoint only - uses Managed Identity)
        required_cosmos_configs = [
            ("COSMOS_DB_ENDPOINT", cls.COSMOS_DB_ENDPOINT),
        ]
        
        # Required Storage configs (account name only - uses Managed Identity)
        required_storage_configs = [
            ("AZURE_STORAGE_ACCOUNT_NAME", cls.AZURE_STORAGE_ACCOUNT_NAME),
        ]
        
        for config_name, config_value in required_azure_configs + required_cosmos_configs + required_storage_configs:
            if not config_value:
                missing_configs.append(config_name)
        
        return missing_configs
    
    @classmethod
    def print_config_status(cls):
        """Print configuration status for debugging"""
        print("\n" + "="*60)
        print("Configuration Status")
        print("="*60)
        
        missing = cls.validate_required_config()
        
        if not missing:
            print("✅ All required configurations are set")
        else:
            print("❌ Missing required configurations:")
            for config in missing:
                print(f"   - {config}")
        
        print("\n📋 Loaded Configurations (using Managed Identity):")
        print(f"   Azure Endpoint: {'✅' if cls.AZURE_ENDPOINT else '❌'}")
        print(f"   Azure Resource Group: {'✅' if cls.AZURE_RESOURCE_GROUP else '❌'}")
        print(f"   Cosmos DB Endpoint: {'✅' if cls.COSMOS_DB_ENDPOINT else '❌'}")
        print(f"   Blob Storage Account: {'✅' if cls.AZURE_STORAGE_ACCOUNT_NAME else '❌'}")
        print(f"   AI Search: {'✅' if cls.SEARCH_ENDPOINT else '⚠️ Optional'}")
        print(f"   🔐 Authentication: Managed Identity (DefaultAzureCredential)")
        print("="*60 + "\n")


# Create a singleton instance
config = Config()


def get_config() -> Config:
    """Get the configuration instance"""
    return config


if __name__ == "__main__":
    # Test configuration loading
    Config.print_config_status()
    
    missing = Config.validate_required_config()
    if missing:
        print("\n⚠️ Warning: Some required configurations are missing.")
        print("Please update your .env file with the following variables:")
        for config_name in missing:
            print(f"  - {config_name}")
    else:
        print("\n✅ Configuration is complete and ready to use!")
