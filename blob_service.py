"""
Azure Blob Storage Service for Vehicle Insurance Claims
Provides document management functionality for claim processing
Uses Managed Identity (DefaultAzureCredential) for authentication
"""

import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient, BlobSasPermissions
from azure.identity import DefaultAzureCredential

# Load environment variables
load_dotenv()

# Azure Blob Storage Configuration
STORAGE_ACCOUNT_NAME = os.getenv("AZURE_STORAGE_ACCOUNT_NAME") or os.getenv("STORAGE_ACCOUNT_NAME")
CONTAINER_NAME = os.getenv("AZURE_STORAGE_CONTAINER_NAME") or os.getenv("CONTAINER_NAME", "vehicle-insurance")


class BlobStorageService:
    """Service for managing documents in Azure Blob Storage using Managed Identity"""
    
    def __init__(self):
        """Initialize the blob storage service with Managed Identity"""
        if not STORAGE_ACCOUNT_NAME:
            raise ValueError("AZURE_STORAGE_ACCOUNT_NAME not found in environment variables")
        
        self.account_name = STORAGE_ACCOUNT_NAME
        self.container_name = CONTAINER_NAME
        self.account_url = f"https://{STORAGE_ACCOUNT_NAME}.blob.core.windows.net"
        
        # Use DefaultAzureCredential for Managed Identity authentication
        self.credential = DefaultAzureCredential()
        self.blob_service_client = BlobServiceClient(
            account_url=self.account_url,
            credential=self.credential
        )
        self.container_client = self.blob_service_client.get_container_client(self.container_name)
        print(f"[OK] Blob Storage initialized with Managed Identity for account: {STORAGE_ACCOUNT_NAME}")
    
    def list_all_documents(self) -> List[Dict[str, Any]]:
        """
        List all documents in the container
        
        Returns:
            List of document metadata dictionaries
        """
        documents = []
        try:
            blobs = self.container_client.list_blobs()
            
            for blob in blobs:
                # Skip folders (they end with '/')
                if blob.name.endswith('/'):
                    continue
                
                # Parse document information
                path_parts = blob.name.split('/')
                
                doc_info = {
                    "name": blob.name,
                    "size": blob.size,
                    "last_modified": blob.last_modified.isoformat() if blob.last_modified else None,
                    "content_type": blob.content_settings.content_type if blob.content_settings else None,
                }
                
                # Try to extract claim_id from path if available
                # Assuming structure like: claim_id/document_type/file.ext
                if len(path_parts) >= 2:
                    doc_info["claim_id"] = path_parts[0]
                    doc_info["document_type"] = path_parts[1] if len(path_parts) > 2 else "unknown"
                
                documents.append(doc_info)
                
        except Exception as e:
            print(f"Error listing documents: {e}")
            raise
        
        return documents
    
    def list_claim_documents(self, claim_id: str) -> Dict[str, Any]:
        """
        List all documents for a specific claim
        
        Args:
            claim_id: The claim identifier
            
        Returns:
            Dictionary containing claim documents organized by type
        """
        try:
            blobs = self.container_client.list_blobs(name_starts_with=f"{claim_id}/")
            
            claim_docs = {
                "claim_id": claim_id,
                "documents": []
            }
            
            for blob in blobs:
                # Skip folders
                if blob.name.endswith('/'):
                    continue
                
                path_parts = blob.name.split('/')
                
                doc_info = {
                    "name": blob.name,
                    "filename": path_parts[-1] if path_parts else blob.name,
                    "size": blob.size,
                    "last_modified": blob.last_modified.isoformat() if blob.last_modified else None,
                    "content_type": blob.content_settings.content_type if blob.content_settings else None,
                }
                
                # Extract document type from path
                if len(path_parts) >= 2:
                    doc_info["document_type"] = path_parts[1] if len(path_parts) > 2 else "general"
                
                claim_docs["documents"].append(doc_info)
            
            claim_docs["count"] = len(claim_docs["documents"])
            return claim_docs
            
        except Exception as e:
            print(f"Error listing documents for claim {claim_id}: {e}")
            raise
    
    def get_document_sas_url(
        self, 
        document_name: str, 
        claim_id: str = None, 
        expiry_hours: int = 24
    ) -> str:
        """
        Generate a SAS URL for accessing a document using User Delegation Key
        
        Args:
            document_name: Name/path of the document (can be full path like 'bills/file.pdf')
            claim_id: The claim identifier (optional, used only if document_name is not a full path)
            expiry_hours: Number of hours until the SAS URL expires (default: 24)
            
        Returns:
            SAS URL string
        """
        from azure.storage.blob import generate_blob_sas, UserDelegationKey
        
        try:
            # If document_name already contains a path (has '/'), use it directly
            # Otherwise, construct path with claim_id
            if '/' in document_name:
                blob_name = document_name
            elif claim_id:
                blob_name = f"{claim_id}/{document_name}"
            else:
                blob_name = document_name
            
            # Get user delegation key for SAS token generation with Managed Identity
            start_time = datetime.now(timezone.utc)
            expiry_time = start_time + timedelta(hours=expiry_hours)
            
            user_delegation_key = self.blob_service_client.get_user_delegation_key(
                key_start_time=start_time,
                key_expiry_time=expiry_time
            )
            
            # Generate SAS token using user delegation key
            sas_token = generate_blob_sas(
                account_name=self.account_name,
                container_name=self.container_name,
                blob_name=blob_name,
                user_delegation_key=user_delegation_key,
                permission=BlobSasPermissions(read=True),
                expiry=expiry_time,
                start=start_time
            )
            
            # Construct the full URL
            blob_url = (
                f"https://{self.account_name}.blob.core.windows.net/"
                f"{self.container_name}/{blob_name}?{sas_token}"
            )
            
            return blob_url
            
        except Exception as e:
            print(f"Error generating SAS URL for {document_name}: {e}")
            raise
    
    def upload_document(
        self, 
        claim_id: str, 
        document_name: str, 
        data: bytes,
        content_type: Optional[str] = None
    ) -> str:
        """
        Upload a document to blob storage
        
        Args:
            claim_id: The claim identifier
            document_name: Name of the document
            data: Binary data to upload
            content_type: MIME type of the content
            
        Returns:
            Blob name (path in container)
        """
        try:
            blob_name = f"{claim_id}/{document_name}"
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            
            # Upload with content type if provided
            content_settings = None
            if content_type:
                from azure.storage.blob import ContentSettings
                content_settings = ContentSettings(content_type=content_type)
            
            blob_client.upload_blob(
                data,
                overwrite=True,
                content_settings=content_settings
            )
            
            return blob_name
            
        except Exception as e:
            print(f"Error uploading document {document_name}: {e}")
            raise
    
    def delete_document(self, claim_id: str, document_name: str) -> bool:
        """
        Delete a document from blob storage
        
        Args:
            claim_id: The claim identifier
            document_name: Name of the document
            
        Returns:
            True if successful
        """
        try:
            blob_name = f"{claim_id}/{document_name}"
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            blob_client.delete_blob()
            return True
            
        except Exception as e:
            print(f"Error deleting document {document_name}: {e}")
            raise


# Global instance for singleton pattern
_blob_service_instance: Optional[BlobStorageService] = None


def get_blob_service() -> BlobStorageService:
    """
    Get or create the singleton blob storage service instance
    
    Returns:
        BlobStorageService instance
    """
    global _blob_service_instance
    
    if _blob_service_instance is None:
        _blob_service_instance = BlobStorageService()
    
    return _blob_service_instance
