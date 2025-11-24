"""
Azure Blob Storage service for fetching claim documents
"""
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from azure.storage.blob import BlobServiceClient, BlobSasPermissions, generate_blob_sas
from azure.core.exceptions import ResourceNotFoundError

class BlobStorageService:
    """Service for interacting with Azure Blob Storage"""
    
    def __init__(self):
        # Get configuration from environment variables
        self.account_name = os.getenv('AZURE_STORAGE_ACCOUNT_NAME', 'dataexc')
        self.account_key = os.getenv('AZURE_STORAGE_ACCOUNT_KEY')
        self.connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
        self.container_name = os.getenv('AZURE_STORAGE_CONTAINER_NAME', 'vehicle-insuarance')
        
        # Initialize blob service client
        if self.connection_string:
            self.blob_service_client = BlobServiceClient.from_connection_string(self.connection_string)
        elif self.account_key:
            account_url = f"https://{self.account_name}.blob.core.windows.net"
            self.blob_service_client = BlobServiceClient(account_url=account_url, credential=self.account_key)
        else:
            raise ValueError("Either AZURE_STORAGE_CONNECTION_STRING or AZURE_STORAGE_ACCOUNT_KEY must be set")
        
        self.container_client = self.blob_service_client.get_container_client(self.container_name)
    
    def list_all_documents(self, prefix: Optional[str] = None) -> List[Dict]:
        """
        List all documents in the container, optionally filtered by prefix
        
        Args:
            prefix: Optional prefix to filter blobs (e.g., claim_id)
        
        Returns:
            List of document metadata dictionaries
        """
        try:
            documents = []
            blobs = self.container_client.list_blobs(name_starts_with=prefix)
            
            for blob in blobs:
                # Only include PDF and common image formats
                if self._is_valid_document(blob.name):
                    documents.append({
                        'name': blob.name,
                        'contentType': blob.content_settings.content_type if blob.content_settings else self._get_content_type(blob.name),
                        'size': blob.size,
                        'lastModified': blob.last_modified.isoformat() if blob.last_modified else None,
                        'url': self.generate_blob_url(blob.name),
                        'type': self._determine_document_type(blob.name)
                    })
            
            return documents
        except ResourceNotFoundError:
            print(f"Container '{self.container_name}' not found")
            return []
        except Exception as e:
            print(f"Error listing documents: {e}")
            return []
    
    def list_claim_documents(self, claim_id: str) -> List[Dict]:
        """
        List all documents for a specific claim
        
        Args:
            claim_id: The claim identifier
        
        Returns:
            List of document metadata dictionaries
        """
        # Use claim_id as prefix to filter documents
        return self.list_all_documents(prefix=f"{claim_id}/")
    
    def generate_blob_url(self, blob_name: str, expiry_hours: int = 24) -> str:
        """
        Generate a SAS URL for accessing a blob
        
        Args:
            blob_name: Name of the blob
            expiry_hours: Number of hours until the SAS URL expires
        
        Returns:
            SAS URL string
        """
        try:
            blob_client = self.container_client.get_blob_client(blob_name)
            
            if self.account_key:
                # Generate SAS token with read permissions
                sas_token = generate_blob_sas(
                    account_name=self.account_name,
                    container_name=self.container_name,
                    blob_name=blob_name,
                    account_key=self.account_key,
                    permission=BlobSasPermissions(read=True),
                    expiry=datetime.utcnow() + timedelta(hours=expiry_hours)
                )
                return f"{blob_client.url}?{sas_token}"
            else:
                # Return URL without SAS if no account key
                return blob_client.url
        except Exception as e:
            print(f"Error generating SAS URL for {blob_name}: {e}")
            return ""
    
    def get_document_sas_url(self, document_name: str, claim_id: str, expiry_hours: int = 24) -> str:
        """
        Get SAS URL for a specific document (with claim_id prefix handling)
        
        Args:
            document_name: Name of the document (can include folder prefix)
            claim_id: The claim identifier (optional, used if document isn't already prefixed)
            expiry_hours: Number of hours until the SAS URL expires
        
        Returns:
            SAS URL string
        """
        # Use document_name as-is since our documents are organized in folders like bill/, pictures/
        blob_name = document_name
        
        return self.generate_blob_url(blob_name, expiry_hours)
    
    def upload_document(self, file_data: bytes, blob_name: str, content_type: str = None) -> Dict:
        """
        Upload a document to blob storage
        
        Args:
            file_data: Binary file data
            blob_name: Name for the blob
            content_type: MIME type of the file
        
        Returns:
            Dictionary with upload result
        """
        try:
            blob_client = self.container_client.get_blob_client(blob_name)
            blob_client.upload_blob(
                file_data,
                overwrite=True,
                content_settings={'content_type': content_type} if content_type else None
            )
            
            return {
                'success': True,
                'name': blob_name,
                'url': self.generate_blob_url(blob_name)
            }
        except Exception as e:
            print(f"Error uploading document {blob_name}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def delete_document(self, blob_name: str) -> bool:
        """
        Delete a document from blob storage
        
        Args:
            blob_name: Name of the blob to delete
        
        Returns:
            True if successful, False otherwise
        """
        try:
            blob_client = self.container_client.get_blob_client(blob_name)
            blob_client.delete_blob()
            return True
        except Exception as e:
            print(f"Error deleting document {blob_name}: {e}")
            return False
    
    def _is_valid_document(self, filename: str) -> bool:
        """Check if file is a PDF or common image format"""
        valid_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.doc', '.docx', '.xls', '.xlsx']
        return any(filename.lower().endswith(ext) for ext in valid_extensions)
    
    def _get_content_type(self, filename: str) -> str:
        """Determine content type from file extension"""
        extension_map = {
            '.pdf': 'application/pdf',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.bmp': 'image/bmp',
            '.tiff': 'image/tiff',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.xls': 'application/vnd.ms-excel',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        }
        
        for ext, content_type in extension_map.items():
            if filename.lower().endswith(ext):
                return content_type
        
        return 'application/octet-stream'
    
    def _determine_document_type(self, filename: str) -> str:
        """Determine document category from filename"""
        lower_name = filename.lower()
        
        if 'policy' in lower_name or 'insurance' in lower_name:
            return 'policy'
        elif 'inspection' in lower_name or 'damage' in lower_name or 'photo' in lower_name or 'image' in lower_name:
            return 'inspection'
        elif 'bill' in lower_name or 'invoice' in lower_name or 'receipt' in lower_name:
            return 'bill'
        else:
            return 'other'


# Singleton instance
_blob_service = None

def get_blob_service() -> BlobStorageService:
    """Get or create blob service instance"""
    global _blob_service
    if _blob_service is None:
        _blob_service = BlobStorageService()
    return _blob_service
