# Vehicle Insurance Claims Processing System

AI-powered multi-agent insurance claims processing system built with Azure AI services. The system automates the end-to-end claims workflow — policy lookup, coverage assessment, damage inspection evaluation, bill verification, and final claim decision synthesis — using specialized AI agents coordinated by an orchestrator.

## 🚀 Features

- **Real-time Claims Processing** — Server-Sent Events (SSE) streaming for live agent updates
- **Multi-Agent Architecture** — 5 specialized AI agents working in parallel and sequential pipelines
- **Azure Managed Identity** — Secure, keyless authentication using `DefaultAzureCredential`
- **Modular Orchestrator** — Separated concerns: memory, agent factory, data extraction, synthesis
- **Container-Ready** — Docker support with Azure Container Apps deployment
- **Next.js Frontend** — Modern React-based UI with real-time progress tracking and document viewer

## 📋 Architecture

```
                         ┌─────────────────────────────┐
                         │      Next.js Frontend        │
                         │   (Real-time SSE Client)     │
                         └─────────────┬───────────────┘
                                       │
                         ┌─────────────▼───────────────┐
                         │   FastAPI (SSE Streaming)    │
                         │    api_server_realtime.py    │
                         └─────────────┬───────────────┘
                                       │
                         ┌─────────────▼───────────────┐
                         │     Orchestrator Engine      │
                         │  (Parallel + Sequential)     │
                         └──┬──────┬──────┬──────┬─────┘
                            │      │      │      │
                ┌───────────▼──┐ ┌─▼──────▼─┐ ┌──▼────────────┐
                │  Step 1      │ │ Step 2   │ │ Step 3        │
                │ (Parallel)   │ │          │ │               │
                │ Policy       │ │Inspection│ │ Bill Analysis │
                │ Insight +    │ │ Agent    │ │ Agent         │
                │ Coverage     │ │          │ │               │
                └──────────────┘ └──────────┘ └───────────────┘
                                       │
                         ┌─────────────▼───────────────┐
                         │   Step 4: Final Decision     │
                         │   (Synthesis from all data)  │
                         └─────────────────────────────┘
                                       │
                    ┌──────────────┬────┴─────┬──────────────┐
                    │ Cosmos DB    │ Blob     │ AI Search    │
                    │ (Memory)     │ Storage  │ (Optional)   │
                    └──────────────┘──────────┘──────────────┘
```

### AI Agents

| Agent | Description | Step |
|-------|-------------|------|
| **Policy Insight Agent** | Extracts car details and policy information | 1 (parallel) |
| **Coverage Assessment Agent** | Analyzes coverage eligibility and policy limits | 1 (parallel) |
| **Inspection Agent** | Evaluates vehicle damage and estimates repair costs | 2 |
| **Bill Analysis Agent** | Validates repair bills and calculates reimbursement | 3 |
| **Final Decision Agent** | Synthesizes all agent outputs into a comprehensive claim decision | 4 |

### Backend Components
- **API Server** — FastAPI with real-time SSE streaming and batch processing modes
- **Orchestrator** — Modular coordinator (agent factory, memory manager, data extractors, synthesis engine)
- **Blob Service** — Azure Blob Storage integration for claim documents
- **Config** — Centralized environment configuration with validation

### Frontend Components
- **Real-time Processor** — Live agent progress tracking via SSE
- **Document Viewer** — View and manage claim documents (PDFs, images)
- **Dashboard** — Claims analytics and insights
- **Agent Workflow** — Visualize multi-agent pipeline execution

## 🛠️ Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Backend** | Python 3.12, FastAPI, Uvicorn/Gunicorn, Semantic Kernel |
| **Frontend** | Next.js 15, React 18, TypeScript, Tailwind CSS, shadcn/ui |
| **AI** | Azure OpenAI (GPT-4o), Azure AI Projects SDK |
| **Data** | Azure Cosmos DB (NoSQL), Azure Blob Storage, Azure AI Search |
| **Auth** | Azure Managed Identity (`DefaultAzureCredential`) |
| **Infra** | Docker, Azure Container Apps, GitHub Actions CI/CD |

## 📦 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Azure subscription with required services configured

### 1. Clone the repository
```bash
git clone https://github.com/MSFT-Innovation-Hub-India/bfsi-multi-agent-auto-insurance.git
cd bfsi-multi-agent-auto-insurance
```

### 2. Set up environment variables
```bash
cp .env.example .env
# Edit .env with your Azure credentials (see Configuration section below)
```

### 3. Verify configuration
```bash
python config.py
# Should output: ✅ All required configurations are set
```

### 4. Install backend dependencies
```bash
pip install -r requirements.txt
```

### 5. Run the backend API
```bash
python api_server_realtime.py
```

### 6. Install and run the frontend
```bash
cd frontend
npm install
npm run dev
```

## ☁️ Deployment

### Option 1: Azure Container Apps (Recommended)

Container Apps provides automatic scaling, pay-per-use pricing, and built-in HTTPS.

#### Prerequisites
- Azure CLI installed (`az --version`)
- Docker (for local builds) or use ACR build

#### Quick Deploy (Manual)

```bash
# 1. Login to Azure
az login

# 2. Install Container Apps extension
az extension add --name containerapp --upgrade

# 3. Create resource group
az group create --name vehicle-claims-rg --location eastus

# 4. Create container registry
az acr create --resource-group vehicle-claims-rg \
  --name vehicleclaimsacr --sku Basic --admin-enabled true

# 5. Create Container Apps environment
az containerapp env create \
  --name vehicle-claims-env \
  --resource-group vehicle-claims-rg \
  --location eastus

# 6. Build and push image via ACR
az acr build --registry vehicleclaimsacr \
  --image vehicle-claims-api:latest .

# 7. Deploy the backend container app
az containerapp create \
  --name vehicle-claims-api \
  --resource-group vehicle-claims-rg \
  --environment vehicle-claims-env \
  --image vehicleclaimsacr.azurecr.io/vehicle-claims-api:latest \
  --target-port 8000 \
  --ingress external \
  --registry-server vehicleclaimsacr.azurecr.io \
  --cpu 1.0 --memory 2.0Gi

# 8. Set environment variables
az containerapp update \
  --name vehicle-claims-api \
  --resource-group vehicle-claims-rg \
  --set-env-vars \
    AZURE_ENDPOINT="https://eastus2.api.azureml.ms" \
    AZURE_RESOURCE_GROUP="your-rg" \
    AZURE_SUBSCRIPTION_ID="your-sub-id" \
    AZURE_PROJECT_NAME="your-project" \
    AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4o" \
    AZURE_OPENAI_ENDPOINT="https://your-openai.openai.azure.com/" \
    COSMOS_DB_ENDPOINT="https://your-cosmos.documents.azure.com:443/" \
    AZURE_STORAGE_ACCOUNT_NAME="yourstorageaccount" \
    AZURE_STORAGE_CONTAINER_NAME="vehicle-insurance"

# 9. Get the app URL
az containerapp show --name vehicle-claims-api \
  --resource-group vehicle-claims-rg \
  --query properties.configuration.ingress.fqdn -o tsv
```

#### Frontend Container App

```bash
# Build frontend image
cd frontend
az acr build --registry vehicleclaimsacr \
  --image vehicle-claims-frontend:latest \
  --build-arg NEXT_PUBLIC_API_URL=https://<your-backend-url> .

# Deploy frontend
az containerapp create \
  --name vehicle-claims-frontend \
  --resource-group vehicle-claims-rg \
  --environment vehicle-claims-env \
  --image vehicleclaimsacr.azurecr.io/vehicle-claims-frontend:latest \
  --target-port 3000 \
  --ingress external \
  --registry-server vehicleclaimsacr.azurecr.io \
  --cpu 0.5 --memory 1.0Gi
```

#### CI/CD with GitHub Actions

The repository includes a GitHub Actions workflow (`.github/workflows/deploy-container-apps.yml`) that automatically builds and deploys on push to `master`.

**Setup:**
1. Create an Azure Service Principal:
   ```bash
   az ad sp create-for-rbac --name "vehicle-claims-github" \
     --role contributor \
     --scopes /subscriptions/<SUBSCRIPTION_ID>/resourceGroups/vehicle-claims-rg \
     --sdk-auth
   ```
2. Add GitHub repository secrets:
   - `AZURE_CREDENTIALS` — Full JSON output from step 1
   - `ACR_NAME` — Your container registry name
   - `RESOURCE_GROUP` — Your resource group name

3. Push to `master` — deployment runs automatically.

#### Useful Container Apps Commands

```bash
# View logs
az containerapp logs show --name vehicle-claims-api --resource-group vehicle-claims-rg --follow

# Check status
az containerapp show --name vehicle-claims-api --resource-group vehicle-claims-rg

# Restart
az containerapp revision restart --name vehicle-claims-api --resource-group vehicle-claims-rg

# Cleanup all resources
az group delete --name vehicle-claims-rg --yes
```

### Option 2: Azure App Service

```bash
# Create App Service
az webapp create \
  --name vehicle-claims-api \
  --resource-group your-rg \
  --plan your-plan \
  --runtime "PYTHON:3.11"

# Configure environment variables
az webapp config appsettings set \
  --name vehicle-claims-api \
  --resource-group your-rg \
  --settings @azure-config-template.txt

# Deploy
az webapp up --name vehicle-claims-api --resource-group your-rg
```

## 🔧 Configuration

### Required Azure Resources

| Resource | Purpose | Setup |
|----------|---------|-------|
| **Azure AI Project** | AI agent orchestration |
| **Azure OpenAI** | GPT-4o model deployment | Deploy GPT-4o model |
| **Cosmos DB** | Agent memory & response storage | Database: `insurance`, Container: `data`, Partition Key: `/claim_id` |
| **Blob Storage** | Claim document storage | Container: `vehicle-insurance` |
| **AI Search** | Policy & document indexing | Indexes: `policy`, `insurance`, `bill` |

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `AZURE_ENDPOINT` | ✅ | Azure AI Studio endpoint |
| `AZURE_RESOURCE_GROUP` | ✅ | Azure resource group name |
| `AZURE_SUBSCRIPTION_ID` | ✅ | Azure subscription ID |
| `AZURE_PROJECT_NAME` | ✅ | Azure AI project name |
| `AZURE_OPENAI_DEPLOYMENT_NAME` | ✅ | OpenAI model deployment name (default: `gpt-4o`) |
| `AZURE_OPENAI_ENDPOINT` | ✅ | Azure OpenAI service endpoint |
| `COSMOS_DB_ENDPOINT` | ✅ | Cosmos DB endpoint |
| `AZURE_STORAGE_ACCOUNT_NAME` | ✅ | Blob storage account name |
| `AZURE_STORAGE_CONTAINER_NAME` | ✅ | Blob container name (default: `vehicle-insurance`) |
| `CORS_ORIGINS` | ✅ | Comma-separated frontend URLs |
| `SEARCH_ENDPOINT` | ⬜ | Azure AI Search endpoint |
| `AUDIT_API_BASE_URL` | ⬜ | Audit API endpoint |

## 📖 API Endpoints

### Real-time Streaming API (Recommended)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/process-claim-stream` | Stream agent results via SSE |
| `POST` | `/process-claim` | Batch process (all results at once) |
| `GET` | `/api/blob/list-all` | List all documents |
| `GET` | `/api/blob/list/{claim_id}` | List documents for a claim |
| `POST` | `/api/blob/sas-url` | Generate SAS URL for a document |
| `GET` | `/api/claims/{claim_id}/outputs` | Get agent outputs from Cosmos DB |
| `GET` | `/health` | Health check |
| `GET` | `/docs` | Interactive Swagger UI |

## 🏗️ Project Structure

```
bfsi-multi-agent-auto-insurance/
├── api_server_realtime.py        # Real-time SSE streaming API server
├── orchestrator.py               # Main orchestrator entry point
├── config.py                     # Centralized configuration
├── blob_service.py               # Azure Blob Storage service
├── requirements.txt              # Python dependencies
├── Dockerfile                    # Backend container image
├── startup.sh                    # Azure startup script
├── agents/                       # AI agent implementations
│   ├── mainpolicy.py             #   Policy analysis agent
│   ├── inspectionagent.py        #   Inspection evaluation agent
│   ├── billsynthesis.py          #   Bill verification agent
│   └── auditagent.py             #   Audit logging agent
├── orchestrator/                 # Modular orchestrator components
│   ├── orchestrator.py           #   Main coordinator
│   ├── agent_factory.py          #   Agent creation & configuration
│   ├── memory_manager.py         #   Cosmos DB memory operations
│   ├── data_extractors.py        #   Text parsing utilities
│   ├── synthesis_engine.py       #   Final decision synthesis
│   └── models.py                 #   Data models (ClaimData, etc.)
├── instructions/                 # Agent instruction prompt templates
├── frontend/                     # Next.js frontend application
│   ├── Dockerfile                #   Frontend container image
│   ├── app/                      #   Next.js app router pages
│   ├── components/               #   React UI components
│   ├── contexts/                 #   React context providers
│   └── lib/                      #   API services & utilities
└── .github/
    └── workflows/
        └── deploy-container-apps.yml  # CI/CD pipeline
```

## 🔒 Security

- **Managed Identity** — Uses `DefaultAzureCredential` for keyless Azure service authentication
- **Environment Variables** — Credentials stored in Azure App/Container configuration (never in code)
- **CORS** — Configured via `CORS_ORIGINS` environment variable
- **HTTPS** — Enforced on all Azure deployments
- **.gitignore** — Sensitive files, keys, and deployment scripts excluded from source control

## 📊 Monitoring

- **Health Check** — `GET /health` endpoint for availability monitoring
- **Structured Logging** — Console logs with emoji indicators for agent pipeline status
- **Azure Monitor** — Container Apps built-in metrics and log streaming
- **Real-time Logs** — `az containerapp logs show --follow`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📚 Additional Resources

- [Azure Container Apps Documentation](https://learn.microsoft.com/azure/container-apps/)
- [Azure AI Studio Documentation](https://learn.microsoft.com/azure/ai-studio/)
- [Azure OpenAI Service](https://learn.microsoft.com/azure/ai-services/openai/)
- [Azure Cosmos DB](https://learn.microsoft.com/azure/cosmos-db/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)

