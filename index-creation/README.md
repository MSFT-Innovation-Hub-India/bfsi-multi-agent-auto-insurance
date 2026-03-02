# Azure AI Search Index Creation — Programmatic Approach

This folder contains scripts for programmatically creating and populating Azure AI Search indexes for the **Vehicle Insurance Claims Processing System**. This is an alternative to the portal-based approach described in [`index-creation-portal/index_setup-portal.md`](../index-creation-portal/index_setup-portal.md).

## When to Use This Approach

Use the Python scripts here when you need to:
- Automate index creation as part of a CI/CD pipeline
- Customize index fields beyond what the portal wizard offers
- Re-index documents in bulk after document updates
- Process documents for a specific customer or document type selectively

For a quick, GUI-guided setup, use the [portal guide](../index-creation-portal/index_setup-portal.md) instead.

---

## Files

| File | Purpose |
|---|---|
| `create_index.py` | Main script — connects to Blob Storage, extracts text via Document Intelligence, generates embeddings, and uploads to AI Search |
| `doc_index_config.py` | Configuration loader — reads all Azure credentials from environment variables |

---

## Prerequisites

- Python 3.11+
- The following Azure services provisioned and accessible:
  - **Azure Blob Storage** — container `vehicle-insurance` populated with documents
  - **Azure Document Intelligence** — for text extraction from PDFs and images
  - **Azure OpenAI** — embedding model deployed (e.g., `text-embedding-ada-002`)
  - **Azure AI Search** — search service endpoint and key available

### Install dependencies

```bash
pip install -r ../requirements.txt
```

---

## Configuration

Create a `.env` file in this directory (or the project root) with the following variables:

```env
# Azure Blob Storage
STORAGE_ACCOUNT_NAME=your-storage-account-name
STORAGE_ACCOUNT_KEY=your-storage-account-key
CONTAINER_NAME=vehicle-insurance

# Azure Document Intelligence
DOC_INTEL_ENDPOINT=https://your-doc-intel.cognitiveservices.azure.com/
DOC_INTEL_KEY=your-doc-intel-key

# Azure OpenAI (for embeddings)
OPENAI_ENDPOINT=https://your-openai.openai.azure.com/
OPENAI_SUBSCRIPTION_KEY=your-openai-key
OPENAI_API_VERSION=2024-02-01
OPENAI_DEPLOYMENT_NAME=gpt-4o
EMBEDDING_MODEL_NAME=text-embedding-ada-002

# Azure AI Search
SEARCH_SERVICE_ENDPOINT=https://your-search-service.search.windows.net
SEARCH_SERVICE_KEY=your-search-service-key
SEARCH_INDEX_NAME=bills
```

> **Important:** Use the **same embedding model** (`EMBEDDING_MODEL_NAME`) here as configured in the portal-based indexes — consistency across all indexes is required for correct vector search.

---

## Blob Storage Structure

Documents must be organized in the `vehicle-insurance` container under customer-specific folders:

```
vehicle-insurance/              ← Blob container
│
└── CUST0001/
    ├── bills/                  → Repair bills, garage invoices
    ├── policy/                 → Insurance policy documents
    └── inspection-reports/     → Damage inspection reports, accident photos
```

Each `CUST*/` folder maps to one vehicle insurance claim. The `document_type` (second path segment) determines which AI Search index the documents are uploaded to.

---

## Usage

### Interactive Mode (Default)

Run the script without arguments to scan the container, list available customers and document types, then prompt for your choice:

```bash
cd index-creation
python create_index.py
```

You will see:
1. A debug scan of all files in the container
2. A list of discovered customers and their document types
3. A prompt to choose:
   - **Option 1** — Process a specific customer and document type
   - **Option 2** — Process all customer documents

### Command Line Mode

Pass the customer ID and document type directly as arguments to skip the interactive prompts:

```bash
# Process bills for customer CUST0001
python create_index.py CUST0001 bills

# Process policy documents for customer CUST0002
python create_index.py CUST0002 policy

# Process inspection reports for customer CUST0001
python create_index.py CUST0001 inspection-reports
```

---

## What the Script Does

For each document found:

1. **Generates a SAS URL** — Time-limited secure URL for the blob
2. **Extracts text** — Calls Azure Document Intelligence (`prebuilt-layout`) to parse PDFs and images
3. **Chunks the text** — Splits into ~500-token segments for optimal embedding size
4. **Generates embeddings** — Calls Azure OpenAI to produce vector representations
5. **Tags chunks** — Prefixes each chunk with `[CUST_ID/DocumentType] filename` for traceability
6. **Uploads to AI Search** — Pushes chunks + embeddings to the configured Azure AI Search index

---

## Creating Separate Indexes for Each Document Type

To create three separate indexes (matching the portal setup), run the script three times with `SEARCH_INDEX_NAME` set to a different value each time:

```bash
# Index 1: Bills
SEARCH_INDEX_NAME=bill python create_index.py ALL ALL

# Index 2: Policy documents
SEARCH_INDEX_NAME=policy python create_index.py ALL ALL

# Index 3: Inspection reports
SEARCH_INDEX_NAME=insurance python create_index.py ALL ALL
```

Or update the `.env` file between runs.

---

## Index Fields

The script creates an Azure AI Search index with the following fields:

| Field | Type | Purpose |
|---|---|---|
| `id` | String (key) | Unique chunk identifier |
| `content` | String (searchable) | Text chunk content |
| `file_name` | String (filterable) | Source file path |
| `customer_id` | String (filterable) | Claim/customer identifier |
| `document_type` | String (filterable) | Document category (bills, policy, etc.) |
| `embedding_str` | String | Vector embedding (stored as comma-separated string) |

---

## Troubleshooting

| Problem | Solution |
|---|---|
| `Missing required environment variables` | Check your `.env` file — all variables listed in the Configuration section are required |
| `No customer documents found` | Verify the blob container name and that files follow the `CUST*/DocType/file` path structure |
| `Error analyzing document` | Check Document Intelligence endpoint and key; ensure the document format is supported |
| `Upload failed` | Verify AI Search endpoint and key; check that the index name does not conflict with a read-only index |
