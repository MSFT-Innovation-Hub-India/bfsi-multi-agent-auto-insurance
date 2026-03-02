# Azure AI Search Index Creation — Portal Guide

## Overview

This guide explains how to create Azure AI Search indexes using the Azure Portal for the **Vehicle Insurance Claims Processing System** — an AI-powered multi-agent solution that automates end-to-end claims workflows including policy lookup, coverage assessment, damage inspection, bill verification, and final claim decision synthesis.

### Integrated Services

- **Azure AI Search** — Core search and indexing engine
- **Azure Blob Storage** — Document source for indexing
- **Azure OpenAI** — Embedding model for semantic search
- **Azure AI Multi-Service Account** — Enrichment and AI capabilities (OCR, document extraction)

### Indexes to Create

Three separate indexes are required for this solution. The index creation process must be repeated for each:

| Index | Purpose |
|---|---|
| **Bills Index** (`bill`) | Repair bills, garage invoices, and towing charges |
| **Policy Index** (`policy`) | Vehicle insurance policies, coverage details, and terms |
| **Inspection Reports Index** (`insurance`) | Vehicle damage inspection reports and accident images |

> **Prerequisites:** Blob Storage must be configured correctly before creating any index.

---

## Step 1 — Configure Blob Storage Structure

Documents must be stored in the Azure Blob Storage container (`vehicle-insurance`) with three subdirectories corresponding to the three indexes.

### Required Folder Structure

```
vehicle-insurance/   ← Blob container
│
├── bills/
├── policy/
└── inspection-reports/
```

### Directory Descriptions

| Directory | Contents |
|---|---|
| `bills/` | Repair bills, garage invoices, towing bills, and payment records |
| `policy/` | Vehicle insurance policy documents, coverage terms, and rider details |
| `inspection-reports/` | Vehicle damage photos, inspection reports, and accident analysis documents |

---

## Step 2 — Create the Azure AI Search Resource

1. Open the [Azure Portal](https://portal.azure.com).
2. Navigate to your existing **Azure AI Search** resource (e.g., `fsisearchindex`) or create a new one and wait for deployment to complete.
3. Once deployed, navigate to the resource **Overview** page.
4. Click **Import data (new)**.

---

## Step 3 — Choose the Scenario

1. On the import wizard, select **RAG** as the scenario.

   > **RAG** ingests text and simple images containing text (via OCR) to enable AI-powered answers — ideal for vehicle policy documents, repair bills, and inspection reports.

---

## Step 4 — Configure the Data Source

1. Select **Azure Blob Storage** as the data source.
2. Fill in the following details:

   - **Subscription** — Your Azure subscription
   - **Storage Account** — The account containing your vehicle insurance documents (e.g., `fsidemo`)
   - **Blob Container** — `vehicle-insurance`
   - **Blob Folder** — Point to the specific folder for the index being created:
     - `bills` for the Bills Index
     - `policy` for the Policy Index
     - `inspection-reports` for the Inspection Reports Index
   - **Parsing mode** — Default
   - **Authentication** — Enable **Authenticate using managed identity** (System-assigned)

---

## Step 5 — Configure Azure OpenAI Embeddings

1. Select your **Azure OpenAI** account (e.g., `gtartifacts-openai`).
2. Choose the desired embedding model deployment (e.g., `text-embedding-ada-002` or any supported model).
3. Set **Authentication type** to **System assigned identity**.

> **Notes:**
> - Any supported embedding model can be used.
> - Use the **same embedding model** consistently across all three indexes and in `doc_index_config.py` if also using the programmatic approach.
> - API key authentication can be used if required.

---

## Step 6 — Vectorize and Enrich Images

1. Check **Extract text from images** to enable OCR on vehicle damage photos and scanned documents.
2. Select your **Azure AI Multi-Service account** (e.g., `fsi-multi`).
3. Set **Authentication type** to **System assigned identity**.

> This is important for processing vehicle inspection photos and scanned policy documents.

---

## Step 7 — Advanced Settings

1. Enable **Semantic ranker** for improved relevance ranking on natural language queries.
2. Leave the **Schedule** as **Once** (or set a recurring schedule if documents update regularly).

---

## Step 8 — Review and Create

1. Set the **Objects name prefix** to match the index name:
   - `bills` for the Bills Index
   - `policy` for the Policy Index
   - `inspection` for the Inspection Reports Index
2. Review all configuration settings.
3. Click **Create**.

The wizard will automatically:
- Connect to Blob Storage (`vehicle-insurance` container)
- Process and parse the source documents (PDF, images, Word files)
- Extract text from images via OCR
- Generate vector embeddings via Azure OpenAI
- Create and populate the Azure AI Search index

---

> **Reminder:** Repeat Steps 2–8 for each of the three indexes, pointing to the corresponding Blob folder (`bills/`, `policy/`, `inspection-reports/`) and using the corresponding name prefix each time.

---

## Index Summary

After completing all three runs, you will have:

| Index Name | Blob Folder | Used By |
|---|---|---|
| `bills` | `bills/` | Bill Analysis Agent — validates repair costs |
| `policy` | `policy/` | Policy Insight Agent + Coverage Assessment Agent |
| `inspection` | `inspection-reports/` | Inspection Agent — evaluates damage reports |

These index names must match the `SEARCH_INDEX_NAME` values configured in the application's environment variables or `doc_index_config.py`.

