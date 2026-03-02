# === Imports ===
import os
import time
import base64
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

import numpy as np

# Load environment variables
load_dotenv()

from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential
from openai import AzureOpenAI
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SimpleField,
    SearchFieldDataType,
    SearchField,
)

# Import configuration from doc_index_config
from doc_index_config import (
    STORAGE_ACCOUNT_NAME,
    STORAGE_ACCOUNT_KEY,
    CONTAINER_NAME,
    DOC_INTEL_ENDPOINT,
    DOC_INTEL_KEY,
    OPENAI_ENDPOINT,
    OPENAI_SUBSCRIPTION_KEY,
    OPENAI_API_VERSION,
    OPENAI_DEPLOYMENT_NAME,
    EMBEDDING_MODEL_NAME,
    SEARCH_SERVICE_ENDPOINT,
    SEARCH_SERVICE_KEY,
    SEARCH_INDEX_NAME
)

# === Initialize Clients ===
document_client = DocumentIntelligenceClient(
    endpoint=DOC_INTEL_ENDPOINT,
    credential=AzureKeyCredential(DOC_INTEL_KEY)
)

openai_client = AzureOpenAI(
    api_version=OPENAI_API_VERSION,
    azure_endpoint=OPENAI_ENDPOINT,
    api_key=OPENAI_SUBSCRIPTION_KEY,
)

search_credential = AzureKeyCredential(SEARCH_SERVICE_KEY)
search_index_client = SearchIndexClient(endpoint=SEARCH_SERVICE_ENDPOINT, credential=search_credential)
search_client = SearchClient(endpoint=SEARCH_SERVICE_ENDPOINT, index_name=SEARCH_INDEX_NAME, credential=search_credential)

# === Helper Functions ===
def clean_filename_for_key(filename):
    clean = filename.replace('.', '_').replace('-', '_').replace(' ', '_')
    if any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-=' for c in clean):
        clean = base64.urlsafe_b64encode(filename.encode()).decode()
    return clean

def get_all_blobs_from_container():
    connect_str = f"DefaultEndpointsProtocol=https;AccountName={STORAGE_ACCOUNT_NAME};AccountKey={STORAGE_ACCOUNT_KEY};EndpointSuffix=core.windows.net"
    blob_service_client = BlobServiceClient.from_connection_string(connect_str)
    container_client = blob_service_client.get_container_client(CONTAINER_NAME)

    blobs = container_client.list_blobs()
    return [blob.name for blob in blobs]

def get_blobs_from_customer_path(customer_id, document_type):
    """
    Retrieve blobs from specific customer and document type
    Only processes CUST*/DocumentType/ structure, ignores Documents/ folder
    """
    connect_str = f"DefaultEndpointsProtocol=https;AccountName={STORAGE_ACCOUNT_NAME};AccountKey={STORAGE_ACCOUNT_KEY};EndpointSuffix=core.windows.net"
    blob_service_client = BlobServiceClient.from_connection_string(connect_str)
    container_client = blob_service_client.get_container_client(CONTAINER_NAME)

    # Get all blobs and filter for the specific customer and document type
    blobs = container_client.list_blobs()
    blob_list = []
    
    for blob in blobs:
        # Skip folders
        if blob.name.endswith('/'):
            continue
            
        path_parts = blob.name.split('/')
        
        # Only check Structure 1: CUST0001/Identity/file.jpg
        # Ignore Documents/ folder structure
        if len(path_parts) >= 3 and path_parts[0] == customer_id and path_parts[1] == document_type:
            blob_list.append(blob.name)
    
    return blob_list

def get_all_customer_documents():
    """
    Get all documents organized by customer ID and document type
    Only processes CUST*/DocumentType/ structure, ignores Documents/ folder
    """
    connect_str = f"DefaultEndpointsProtocol=https;AccountName={STORAGE_ACCOUNT_NAME};AccountKey={STORAGE_ACCOUNT_KEY};EndpointSuffix=core.windows.net"
    blob_service_client = BlobServiceClient.from_connection_string(connect_str)
    container_client = blob_service_client.get_container_client(CONTAINER_NAME)

    # Get all blobs from the container
    blobs = container_client.list_blobs()
    
    customer_docs = {}
    for blob in blobs:
        # Skip folders (they end with '/')
        if blob.name.endswith('/'):
            continue
            
        # Only process Structure 1: CUST0001/Identity/file.jpg
        # Ignore Documents/ folder structure
        path_parts = blob.name.split('/')
        
        if len(path_parts) >= 3 and path_parts[0].startswith('CUST'):
            # Structure 1: CUST0001/Identity/file.jpg
            customer_id = path_parts[0]
            doc_type = path_parts[1]
            
            if customer_id not in customer_docs:
                customer_docs[customer_id] = {}
            if doc_type not in customer_docs[customer_id]:
                customer_docs[customer_id][doc_type] = []
                
            customer_docs[customer_id][doc_type].append(blob.name)
    
    return customer_docs

def generate_sas_url(file_name):
    sas_token = generate_blob_sas(
        account_name=STORAGE_ACCOUNT_NAME,
        container_name=CONTAINER_NAME,
        blob_name=file_name,
        account_key=STORAGE_ACCOUNT_KEY,
        permission=BlobSasPermissions(read=True),
        expiry=datetime.now(timezone.utc) + timedelta(hours=1)
    )
    blob_url = f"https://{STORAGE_ACCOUNT_NAME}.blob.core.windows.net/{CONTAINER_NAME}/{file_name}?{sas_token}"
    return blob_url

def analyze_document_from_url(blob_url):
    try:
        poller = document_client.begin_analyze_document("prebuilt-layout", {"urlSource": blob_url})
        result = poller.result()
        return result
    except Exception as e:
        print(f"❌ Error analyzing document: {e}")
        return None

def extract_text_from_result(result):
    all_text = ""
    if result and hasattr(result, 'pages'):
        for page in result.pages:
            if hasattr(page, 'lines'):
                for line in page.lines:
                    all_text += line.content + " "
    return all_text.strip()

def chunk_text(text, max_tokens=500):
    sentences = text.split('. ')
    chunks, chunk = [], ""
    for sentence in sentences:
        if len(chunk) + len(sentence) < max_tokens:
            chunk += sentence + '. '
        else:
            chunks.append(chunk.strip())
            chunk = sentence + '. '
    if chunk:
        chunks.append(chunk.strip())
    return chunks

def get_embedding(text):
    response = openai_client.embeddings.create(
        input=[text],
        model=EMBEDDING_MODEL_NAME
    )
    return np.array(response.data[0].embedding)

def create_search_index():
    try:
        search_index_client.get_index(SEARCH_INDEX_NAME)
        print(f"✅ Search index '{SEARCH_INDEX_NAME}' already exists. Deleting to recreate...")
        search_index_client.delete_index(SEARCH_INDEX_NAME)
        print("🗑️ Old index deleted.")
    except:
        print(f"ℹ️ Creating new search index '{SEARCH_INDEX_NAME}'...")

    fields = [
        SimpleField(name="id", type=SearchFieldDataType.String, key=True),
        SearchField(name="content", type=SearchFieldDataType.String, searchable=True),
        SearchField(name="file_name", type=SearchFieldDataType.String, filterable=True, searchable=True),
        SearchField(name="customer_id", type=SearchFieldDataType.String, filterable=True, searchable=True),
        SearchField(name="document_type", type=SearchFieldDataType.String, filterable=True, searchable=True),
        SimpleField(name="embedding_str", type=SearchFieldDataType.String)
    ]
    
    index = SearchIndex(name=SEARCH_INDEX_NAME, fields=fields)
    search_index_client.create_or_update_index(index)
    print(f"✅ Index '{SEARCH_INDEX_NAME}' created.")

def upload_to_search_index(chunks, embeddings, file_name):
    clean_file_name = clean_filename_for_key(file_name)
    documents = []
    
    # Extract customer ID and document type from file path
    customer_id = "unknown"
    doc_type = "unknown"
    
    path_parts = file_name.split('/')
    
    # Only handle Structure 1: CUST0001/Identity/file.jpg
    # Ignore Documents/ folder structure
    if len(path_parts) >= 3 and path_parts[0].startswith('CUST'):
        customer_id = path_parts[0]
        doc_type = path_parts[1]
    
    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        embedding_str = ','.join(map(str, embedding.tolist()))
        doc = {
            "id": f"{clean_file_name}_{i}",
            "content": chunk,
            "file_name": file_name,
            "customer_id": customer_id,
            "document_type": doc_type,
            "embedding_str": embedding_str
        }
        documents.append(doc)

    try:
        batch_size = 10
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i+batch_size]
            search_client.upload_documents(batch)
        print(f"📥 Uploaded {len(documents)} chunks from '{file_name}' to search index.")
    except Exception as e:
        print(f"❌ Upload failed: {e}")

# === Main Functions ===
def process_specific_customer_documents(customer_id, document_type):
    """
    Process documents for a specific customer and document type
    """
    print(f"📦 Fetching documents for Customer: {customer_id}, Document Type: {document_type}")
    file_names = get_blobs_from_customer_path(customer_id, document_type)
    
    if not file_names:
        print(f"❌ No files found for customer {customer_id} with document type {document_type}.")
        return
    
    create_search_index()
    
    for file_name in file_names:
        print(f"\n📄 Processing: {file_name}")
        blob_url = generate_sas_url(file_name)
        result = analyze_document_from_url(blob_url)
        extracted_text = extract_text_from_result(result)

        if not extracted_text.strip():
            print(f"⚠️ No text extracted from '{file_name}'. Skipping.")
            continue

        chunks = chunk_text(extracted_text)
        embeddings = [get_embedding(chunk) for chunk in chunks]
        tagged_chunks = [f"[{customer_id}/{document_type}] {file_name.split('/')[-1]}\n{chunk}" for chunk in chunks]

        upload_to_search_index(tagged_chunks, embeddings, file_name)

    print(f"\n✅ Document processing complete for {customer_id}/{document_type}.")

def process_all_customer_documents():
    """
    Process all documents organized by customer structure
    """
    print("📦 Fetching all documents from customer folders...")
    customer_docs = get_all_customer_documents()
    
    if not customer_docs:
        print("❌ No customer documents found in data/ structure.")
        return
    
    create_search_index()
    
    total_processed = 0
    for customer_id, doc_types in customer_docs.items():
        print(f"\n👤 Processing Customer: {customer_id}")
        
        for doc_type, file_names in doc_types.items():
            print(f"  📂 Document Type: {doc_type}")
            
            for file_name in file_names:
                print(f"    📄 Processing: {file_name}")
                blob_url = generate_sas_url(file_name)
                result = analyze_document_from_url(blob_url)
                extracted_text = extract_text_from_result(result)

                if not extracted_text.strip():
                    print(f"    ⚠️ No text extracted from '{file_name}'. Skipping.")
                    continue

                chunks = chunk_text(extracted_text)
                embeddings = [get_embedding(chunk) for chunk in chunks]
                tagged_chunks = [f"[{customer_id}/{doc_type}] {file_name.split('/')[-1]}\n{chunk}" for chunk in chunks]

                upload_to_search_index(tagged_chunks, embeddings, file_name)
                total_processed += 1

    print(f"\n✅ Document processing complete. Processed {total_processed} documents.")

def get_user_input_for_processing():
    """
    Interactive function to get customer ID and document type from user
    """
    print("\n" + "="*50)
    print("📋 DOCUMENT PROCESSING OPTIONS")
    print("="*50)
    
    choice = input("\nChoose processing mode:\n1. Process specific customer and document type\n2. Process all customer documents\nEnter choice (1 or 2): ").strip()
    
    if choice == "1":
        print("\n📝 Enter Customer and Document Details:")
        customer_id = input("Customer ID (e.g., CUST0001): ").strip()
        
        if not customer_id:
            print("❌ Customer ID cannot be empty!")
            return None, None
        
        print("\n📂 Available document types typically include:")
        print("   - Identity")
        print("   - Income") 
        print("   - Collateral")
        print("   - Guarantor")
        print("   - Others...")
        
        document_type = input("\nDocument Type (e.g., Identity): ").strip()
        
        if not document_type:
            print("❌ Document type cannot be empty!")
            return None, None
            
        return customer_id, document_type
    
    elif choice == "2":
        return "ALL", "ALL"
    
    else:
        print("❌ Invalid choice! Please enter 1 or 2.")
        return get_user_input_for_processing()

def list_available_customers_and_types():
    """
    Show available customers and document types in the container
    """
    print("\n🔍 Scanning available customers and document types...")
    customer_docs = get_all_customer_documents()
    
    if not customer_docs:
        print("❌ No customer documents found in data/ structure.")
        return
    
    print("\n📊 Available Customers and Document Types:")
    print("-" * 40)
    
    for customer_id, doc_types in customer_docs.items():
        print(f"👤 Customer: {customer_id}")
        for doc_type, files in doc_types.items():
            print(f"   📂 {doc_type} ({len(files)} files)")
        print()

def debug_container_contents():
    """
    Debug function to show ALL files in the container to understand the structure
    """
    print("\n🔧 DEBUG: Exploring container contents...")
    print("-" * 50)
    
    try:
        connect_str = f"DefaultEndpointsProtocol=https;AccountName={STORAGE_ACCOUNT_NAME};AccountKey={STORAGE_ACCOUNT_KEY};EndpointSuffix=core.windows.net"
        blob_service_client = BlobServiceClient.from_connection_string(connect_str)
        container_client = blob_service_client.get_container_client(CONTAINER_NAME)

        # List all blobs
        blobs = container_client.list_blobs()
        blob_list = []
        
        for blob in blobs:
            blob_list.append(blob.name)
        
        if not blob_list:
            print("❌ No files found in the container at all!")
            print(f"   Container name: {CONTAINER_NAME}")
            print(f"   Storage account: {STORAGE_ACCOUNT_NAME}")
        else:
            print(f"✅ Found {len(blob_list)} files in container '{CONTAINER_NAME}':")
            print("\n📂 All files in container:")
            for i, blob_name in enumerate(blob_list[:20], 1):  # Show first 20 files
                print(f"   {i:2d}. {blob_name}")
            
            if len(blob_list) > 20:
                print(f"   ... and {len(blob_list) - 20} more files")
            
            # Analyze the structure
            print(f"\n📊 File structure analysis:")
            folders = set()
            for blob_name in blob_list:
                parts = blob_name.split('/')
                if len(parts) > 1:
                    folders.add('/'.join(parts[:-1]))
            
            if folders:
                print("   Detected folder structure:")
                for folder in sorted(folders):
                    print(f"     📁 {folder}/")
            else:
                print("   All files are in the root of the container")
                
    except Exception as e:
        print(f"❌ Error accessing container: {e}")
        print(f"   Please check your storage account credentials")

def main():
    """
    Main function with interactive input and options for different processing modes
    """
    import sys
    
    customer_id = None
    document_type = None
    
    # Check if command line arguments are provided
    if len(sys.argv) > 2:
        customer_id = sys.argv[1]
        document_type = sys.argv[2]
        print(f"📋 Processing from command line: Customer={customer_id}, Type={document_type}")
    else:
        # Show debug information first
        debug_container_contents()
        
        # Show available options first
        list_available_customers_and_types()
        
        # Get user input interactively
        customer_id, document_type = get_user_input_for_processing()
        
        if customer_id is None or document_type is None:
            print("❌ Invalid input. Exiting...")
            return
    
    # Process based on the inputs
    if customer_id == "ALL" and document_type == "ALL":
        print("\n🚀 Starting processing for ALL customer documents...")
        process_all_customer_documents()
    else:
        print(f"\n🚀 Starting processing for Customer: {customer_id}, Document Type: {document_type}")
        process_specific_customer_documents(customer_id, document_type)

if __name__ == "__main__":
    main()