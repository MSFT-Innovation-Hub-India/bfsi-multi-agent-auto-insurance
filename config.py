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
    COSMOS_DB_KEY: str = os.getenv("COSMOS_DB_KEY", "")
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
    # Azure Blob Storage Configuration
    # ============================================================
    AZURE_STORAGE_ACCOUNT_NAME: str = os.getenv("AZURE_STORAGE_ACCOUNT_NAME", "")
    AZURE_STORAGE_ACCOUNT_KEY: str = os.getenv("AZURE_STORAGE_ACCOUNT_KEY", "")
    AZURE_STORAGE_CONNECTION_STRING: str = os.getenv("AZURE_STORAGE_CONNECTION_STRING", "")
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
        
        # Required Cosmos DB configs
        required_cosmos_configs = [
            ("COSMOS_DB_ENDPOINT", cls.COSMOS_DB_ENDPOINT),
            ("COSMOS_DB_KEY", cls.COSMOS_DB_KEY),
        ]
        
        # Required Storage configs (either connection string OR account name + key)
        storage_config_valid = (
            cls.AZURE_STORAGE_CONNECTION_STRING or
            (cls.AZURE_STORAGE_ACCOUNT_NAME and cls.AZURE_STORAGE_ACCOUNT_KEY)
        )
        
        for config_name, config_value in required_azure_configs + required_cosmos_configs:
            if not config_value:
                missing_configs.append(config_name)
        
        if not storage_config_valid:
            missing_configs.append("AZURE_STORAGE_CONNECTION_STRING or (AZURE_STORAGE_ACCOUNT_NAME + AZURE_STORAGE_ACCOUNT_KEY)")
        
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
        
        print("\n📋 Loaded Configurations:")
        print(f"   Azure Endpoint: {'✅' if cls.AZURE_ENDPOINT else '❌'}")
        print(f"   Azure Resource Group: {'✅' if cls.AZURE_RESOURCE_GROUP else '❌'}")
        print(f"   Cosmos DB: {'✅' if cls.COSMOS_DB_ENDPOINT else '❌'}")
        print(f"   Blob Storage: {'✅' if (cls.AZURE_STORAGE_CONNECTION_STRING or cls.AZURE_STORAGE_ACCOUNT_NAME) else '❌'}")
        print(f"   AI Search: {'✅' if cls.SEARCH_ENDPOINT else '⚠️ Optional'}")
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
