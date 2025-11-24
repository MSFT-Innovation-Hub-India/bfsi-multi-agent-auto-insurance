"""
Test script to verify Azure Blob Storage connection and list documents
"""
import os
from dotenv import load_dotenv
from blob_service import get_blob_service

# Load environment variables
load_dotenv()

def test_blob_connection():
    """Test blob storage connection and list all documents"""
    print("🔍 Testing Azure Blob Storage connection...")
    print(f"Account: {os.getenv('AZURE_STORAGE_ACCOUNT_NAME')}")
    print(f"Container: {os.getenv('AZURE_STORAGE_CONTAINER_NAME')}")
    print()
    
    try:
        # Get blob service
        blob_service = get_blob_service()
        
        # List all documents
        print("📁 Listing all documents in container...")
        documents = blob_service.list_all_documents()
        
        if not documents:
            print("⚠️  No documents found in container")
            return
        
        print(f"✅ Found {len(documents)} documents:\n")
        
        # Group by type
        by_type = {}
        for doc in documents:
            doc_type = doc.get('type', 'other')
            if doc_type not in by_type:
                by_type[doc_type] = []
            by_type[doc_type].append(doc)
        
        # Display by type
        for doc_type, docs in by_type.items():
            print(f"\n{doc_type.upper()} Documents ({len(docs)}):")
            print("-" * 80)
            for doc in docs:
                size_mb = doc['size'] / (1024 * 1024)
                print(f"  📄 {doc['name']}")
                print(f"     Type: {doc['contentType']}")
                print(f"     Size: {size_mb:.2f} MB")
                print(f"     Modified: {doc['lastModified']}")
                print()
        
        # Test SAS URL generation for first document
        if documents:
            first_doc = documents[0]
            print("\n🔗 Testing SAS URL generation...")
            sas_url = blob_service.generate_blob_url(first_doc['name'], expiry_hours=1)
            print(f"Generated SAS URL for: {first_doc['name']}")
            print(f"URL: {sas_url[:100]}..." if len(sas_url) > 100 else f"URL: {sas_url}")
        
        print("\n✅ Blob storage connection test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_blob_connection()
