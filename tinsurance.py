import os
import sys
import json
import uuid
import logging
import base64
from io import BytesIO
from pathlib import Path
from datetime import datetime, timedelta, timezone
from PIL import Image
from dotenv import load_dotenv

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from azure.core.credentials import AzureKeyCredential
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SimpleField,
    SearchableField,
    SearchFieldDataType
)

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)

# Azure endpoints and keys
AZURE_AI_ENDPOINT = os.getenv("AZURE_AI_ENDPOINT")
AZURE_AI_API_VERSION = os.getenv("AZURE_AI_API_VERSION", "2025-05-01-preview")
SEARCH_ENDPOINT = os.getenv("SEARCH_ENDPOINT")
SEARCH_KEY = os.getenv("SEARCH_KEY")

# Azure Blob Storage Configuration
STORAGE_ACCOUNT_NAME = os.getenv("STORAGE_ACCOUNT_NAME")
STORAGE_ACCOUNT_KEY = os.getenv("STORAGE_ACCOUNT_KEY")
CONTAINER_NAME = os.getenv("CONTAINER_NAME")

# Import CU client
sys.path.append(str(Path(__file__).parent.parent))
from python.content_understanding_client import AzureContentUnderstandingClient

credential = DefaultAzureCredential()
token_provider = get_bearer_token_provider(credential, "https://cognitiveservices.azure.com/.default")

client = AzureContentUnderstandingClient(
    endpoint=AZURE_AI_ENDPOINT,
    api_version=AZURE_AI_API_VERSION,
    token_provider=token_provider,
)


# === Blob Storage Helper Functions ===
def get_all_customer_documents():
    """
    Get all documents from pictures folder in vehicle-insurance container
    """
    connect_str = f"DefaultEndpointsProtocol=https;AccountName={STORAGE_ACCOUNT_NAME};AccountKey={STORAGE_ACCOUNT_KEY};EndpointSuffix=core.windows.net"
    blob_service_client = BlobServiceClient.from_connection_string(connect_str)
    container_client = blob_service_client.get_container_client(CONTAINER_NAME)

    # Get all blobs from the container
    blobs = container_client.list_blobs()
    
    vehicle_docs = {}
    for blob in blobs:
        # Skip folders (they end with '/')
        if blob.name.endswith('/'):
            continue
            
        # Process pictures folder structure: pictures/file.jpg
        path_parts = blob.name.split('/')
        
        if len(path_parts) >= 2 and path_parts[0] == 'pictures':
            # Structure: pictures/file.jpg
            doc_type = 'pictures'
            
            if 'vehicle-insurance' not in vehicle_docs:
                vehicle_docs['vehicle-insurance'] = {}
            if doc_type not in vehicle_docs['vehicle-insurance']:
                vehicle_docs['vehicle-insurance'][doc_type] = []
                
            vehicle_docs['vehicle-insurance'][doc_type].append(blob.name)
    
    return vehicle_docs


def get_blobs_from_customer_path(customer_id, document_type):
    """
    Retrieve blobs from pictures folder in vehicle-insurance container
    """
    connect_str = f"DefaultEndpointsProtocol=https;AccountName={STORAGE_ACCOUNT_NAME};AccountKey={STORAGE_ACCOUNT_KEY};EndpointSuffix=core.windows.net"
    blob_service_client = BlobServiceClient.from_connection_string(connect_str)
    container_client = blob_service_client.get_container_client(CONTAINER_NAME)

    # Get all blobs and filter for pictures folder
    blobs = container_client.list_blobs()
    blob_list = []
    
    for blob in blobs:
        # Skip folders
        if blob.name.endswith('/'):
            continue
            
        path_parts = blob.name.split('/')
        
        # Only check Structure: pictures/file.jpg
        if len(path_parts) >= 2 and path_parts[0] == 'pictures':
            blob_list.append(blob.name)
    
    return blob_list


def generate_sas_url(file_name):
    """Generate SAS URL for blob access"""
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


def get_file_modality(file_name):
    """
    Determine the modality of a file based on its extension
    """
    extension = file_name.lower().split('.')[-1]
    
    if extension in ['pdf', 'doc', 'docx', 'txt', 'jpg', 'jpeg', 'png', 'tiff', 'bmp']:
        return 'document'
    elif extension in ['mp3', 'wav', 'aac', 'flac', 'm4a']:
        return 'audio'
    elif extension in ['mp4', 'avi', 'mov', 'wmv', 'flv', 'mkv']:
        return 'video'
    else:
        # Default to document for unknown types
        return 'document'


def list_available_customers_and_types():
    """
    Show available vehicle insurance pictures in the container
    """
    print("\n🔍 Scanning available vehicle insurance pictures...")
    vehicle_docs = get_all_customer_documents()
    
    if not vehicle_docs:
        print("❌ No vehicle insurance pictures found in pictures/ folder.")
        return
    
    print("\n📊 Available Vehicle Insurance Pictures:")
    print("-" * 40)
    
    for folder_name, doc_types in vehicle_docs.items():
        print(f"🚗 Container: {folder_name}")
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


def save_image(image_id: str, analyze_response):
    try:
        raw_image = client.get_image_from_analyze_operation(
            analyze_response=analyze_response,
            image_id=image_id
        )
        if not raw_image:
            logging.warning(f"No image data returned for image ID {image_id}")
            return

        image = Image.open(BytesIO(raw_image))
        Path(".cache").mkdir(exist_ok=True)
        image.save(f".cache/{image_id}.jpg", "JPEG")
        logging.info(f"Saved image: .cache/{image_id}.jpg")
    except Exception as e:
        logging.warning(f"Could not fetch image {image_id}: {e}")


def create_search_index(index_name: str):
    try:
        fields = [
            # Core document fields
            SimpleField(name="id", type=SearchFieldDataType.String, key=True),
            SearchableField(name="content", type=SearchFieldDataType.String, analyzer_name="en.lucene"),
            SearchableField(name="metadata", type=SearchFieldDataType.String, analyzer_name="en.lucene"),
            SearchableField(name="segmentDescription", type=SearchFieldDataType.String, analyzer_name="en.lucene"),
            
            # Vehicle information fields
            SearchableField(name="vehicle_make", type=SearchFieldDataType.String, analyzer_name="en.lucene"),
            SearchableField(name="vehicle_type", type=SearchFieldDataType.String, analyzer_name="en.lucene"),
            SearchableField(name="vehicle_model", type=SearchFieldDataType.String, analyzer_name="en.lucene"),
            SearchableField(name="vehicle_color", type=SearchFieldDataType.String, analyzer_name="en.lucene"),
            
            # Scene and damage detection
            SearchableField(name="scene_type", type=SearchFieldDataType.String, analyzer_name="en.lucene"),
            SimpleField(name="damage_detected", type=SearchFieldDataType.Boolean),
            SearchableField(name="damage_locations", type=SearchFieldDataType.String, analyzer_name="en.lucene"),
            SearchableField(name="damage_type", type=SearchFieldDataType.String, analyzer_name="en.lucene"),
            SearchableField(name="damage_severity", type=SearchFieldDataType.String, analyzer_name="en.lucene"),
            SearchableField(name="damage_description_text", type=SearchFieldDataType.String, analyzer_name="en.lucene"),
            
            # Specific damage assessment fields
            SearchableField(name="airbag_status", type=SearchFieldDataType.String, analyzer_name="en.lucene"),
            SearchableField(name="glass_damage", type=SearchFieldDataType.String, analyzer_name="en.lucene"),
            SearchableField(name="tire_or_wheel_damage", type=SearchFieldDataType.String, analyzer_name="en.lucene"),
            SearchableField(name="impact_zone", type=SearchFieldDataType.String, analyzer_name="en.lucene"),
            SearchableField(name="tow_required", type=SearchFieldDataType.String, analyzer_name="en.lucene"),
            
            # Document processing fields
            SearchableField(name="markdown", type=SearchFieldDataType.String, analyzer_name="en.lucene"),
            SimpleField(name="file_path", type=SearchFieldDataType.String),
            SimpleField(name="folder_name", type=SearchFieldDataType.String),
            SimpleField(name="document_type", type=SearchFieldDataType.String),
            SimpleField(name="analyzer_id", type=SearchFieldDataType.String),
        ]
        index = SearchIndex(name=index_name, fields=fields)
        index_client = SearchIndexClient(endpoint=SEARCH_ENDPOINT, credential=AzureKeyCredential(SEARCH_KEY))
        index_client.create_index(index)
        print(f"Index '{index_name}' created.")
    except Exception as e:
        print(f"Index creation skipped or failed: {e}")


def process_and_index(modality_name, analyzer_id, file_blob_name, search_client):
    print(f"\nProcessing: {file_blob_name} with analyzer: {analyzer_id}")

    # Generate SAS URL for the blob
    blob_url = generate_sas_url(file_blob_name)
    
    # Use the pre-existing analyzer instead of creating one
    response = client.begin_analyze(analyzer_id, file_location=blob_url)
    result = client.poll_result(response)

    print(json.dumps(result, indent=2))

    documents = []
    keyframe_ids = set()

    result_data = result.get("result", {})
    contents = result_data.get("contents", [])

    # Extract folder and document type from blob path
    folder_name = "vehicle-insurance"
    doc_type = "pictures"
    path_parts = file_blob_name.split('/')
    if len(path_parts) >= 2 and path_parts[0] == 'pictures':
        folder_name = "vehicle-insurance"
        doc_type = path_parts[0]

    for idx, item in enumerate(contents):
        content_text = item.get("text") or item.get("transcript") or item.get("markdown") or ""
        metadata = json.dumps(item.get("metadata", {}))
        segment_desc = ""
        
        # Extract markdown content
        markdown_content = item.get("markdown", "")

        # Extract segmentDescription from video results
        if modality_name == "video":
            fields = item.get("fields", {})
            segment_desc = fields.get("segmentDescription", {}).get("valueString", "")

            # Also collect keyframes if available
            media_info = item.get("metadata", {}).get("media", {})
            image_id = media_info.get("imageId")
            if image_id:
                keyframe_ids.add(image_id)

        # Extract vehicle insurance analysis fields
        fields = item.get("fields", {})
        
        # Helper function to extract field values safely
        def get_field_value(field_name, default=""):
            field_data = fields.get(field_name, {})
            if field_data.get("type") == "string":
                return field_data.get("valueString", default)
            elif field_data.get("type") == "boolean":
                return field_data.get("valueBoolean", False)
            elif field_data.get("type") == "array":
                array_values = field_data.get("valueArray", [])
                return ", ".join([item.get("valueString", "") for item in array_values if item.get("valueString")])
            return default

        documents.append({
            "id": f"{folder_name}-{doc_type}-{modality_name}-{uuid.uuid4()}",
            "content": content_text,
            "metadata": metadata,
            "segmentDescription": segment_desc,
            
            # Vehicle information
            "vehicle_make": get_field_value("vehicle_make"),
            "vehicle_type": get_field_value("vehicle_type"),
            "vehicle_model": get_field_value("vehicle_model"),
            "vehicle_color": get_field_value("vehicle_color"),
            
            # Scene and damage detection
            "scene_type": get_field_value("scene_type"),
            "damage_detected": get_field_value("damage_detected"),
            "damage_locations": get_field_value("damage_locations"),
            "damage_type": get_field_value("damage_type"),
            "damage_severity": get_field_value("damage_severity"),
            "damage_description_text": get_field_value("damage_description_text"),
            
            # Specific damage assessment
            "airbag_status": get_field_value("airbag_status"),
            "glass_damage": get_field_value("glass_damage"),
            "tire_or_wheel_damage": get_field_value("tire_or_wheel_damage"),
            "impact_zone": get_field_value("impact_zone"),
            "tow_required": get_field_value("tow_required"),
            
            # Document processing fields
            "markdown": markdown_content,
            "file_path": file_blob_name,
            "folder_name": folder_name,
            "document_type": doc_type,
            "analyzer_id": analyzer_id,
        })

    if documents:
        result_upload = search_client.upload_documents(documents=documents)
        print(f"Uploaded {len(documents)} documents from {modality_name} - {file_blob_name}")

    for keyframe_id in keyframe_ids:
        try:
            save_image(keyframe_id, result)
        except Exception as e:
            logging.warning(f"Failed to save keyframe image {keyframe_id}: {e}")


def get_files_from_blob_storage():
    """
    Get files from blob storage - specifically from pictures folder in vehicle-insurance container
    """
    print("\n" + "="*50)
    print("📋 VEHICLE INSURANCE PICTURES PROCESSING")
    print("="*50)
    
    choice = input("\nChoose processing mode:\n1. Process vehicle insurance pictures\n2. Process all files in pictures folder\nEnter choice (1 or 2): ").strip()
    
    files_with_modalities = []
    
    if choice == "1" or choice == "2":
        print("\n🚗 Processing vehicle insurance pictures from pictures folder...")
        
        # Get files from pictures folder
        file_names = get_blobs_from_customer_path("vehicle-insurance", "pictures")
        
        if not file_names:
            print(f"❌ No files found in pictures folder.")
            return []
        
        print(f"\n✅ Found {len(file_names)} files:")
        for file_name in file_names:
            modality = get_file_modality(file_name)
            files_with_modalities.append((modality, file_name))
            print(f"   📄 {file_name} (modality: {modality})")
    
    else:
        print("❌ Invalid choice! Please enter 1 or 2.")
        return get_files_from_blob_storage()
    
    return files_with_modalities


def get_files_interactively():
    """
    Legacy function - now redirects to blob storage
    """
    print("⚠️  This function now uses blob storage instead of local files.")
    return get_files_from_blob_storage()


if __name__ == "__main__":
    # Show debug information first
    debug_container_contents()
    
    # Show available options
    list_available_customers_and_types()
    
    index_name = input("\nEnter the Azure AI Search index name to create/use: ").strip()
    if not index_name:
        print("Index name cannot be empty. Exiting.")
        sys.exit(1)

    create_search_index(index_name)

    search_client = SearchClient(endpoint=SEARCH_ENDPOINT, index_name=index_name, credential=AzureKeyCredential(SEARCH_KEY))

    # Get files from pictures folder in vehicle-insurance container
    files_to_process = get_files_from_blob_storage()
    
    if not files_to_process:
        print("❌ No vehicle insurance pictures to process. Exiting.")
        sys.exit(1)

    # Use pre-existing analyzer IDs instead of creating them dynamically
    analyzer_ids = {
        "document": "accidentanalysis",  # Use the same analyzer ID as ttins.py
        "audio": "call_recording_analytics",  # Assuming this analyzer exists
        "video": "content_video"  # Assuming this analyzer exists
    }

    print(f"\n🚀 Starting to process {len(files_to_process)} vehicle insurance pictures...")
    
    for modality, file_blob_name in files_to_process:
        if modality not in analyzer_ids:
            print(f"No analyzer ID found for modality '{modality}'. Skipping file {file_blob_name}.")
            continue
        analyzer_id = analyzer_ids[modality]
        process_and_index(modality, analyzer_id, file_blob_name, search_client)

    print("🎯 All vehicle insurance pictures extracted and indexed successfully from blob storage.")
