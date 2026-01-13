# Vehicle Insurance Claims Processing System

AI-powered insurance claims processing system using Azure AI services for automated policy analysis, inspection evaluation, bill verification, and claim decision synthesis.

## 🚀 Features

- **Real-time Claims Processing**: Server-Sent Events (SSE) streaming for live agent updates
- **Multi-Agent Architecture**: Specialized AI agents for policy, inspection, and billing analysis
- **Azure Integration**: Leverages Azure AI, Cosmos DB, Blob Storage, and OpenAI
- **RESTful API**: FastAPI-based backend with comprehensive documentation
- **Next.js Frontend**: Modern React-based UI for claims management

## 📋 Architecture

### Backend Components
- **API Servers**: FastAPI with real-time streaming and batch processing modes
- **Orchestrator**: Manages multi-agent workflow coordination
- **AI Agents**:
  - Policy Insight Agent - Extracts car and policy details
  - Coverage Assessment Agent - Analyzes policy coverage eligibility
  - Inspection Agent - Evaluates vehicle damage and repair costs
  - Bill Analysis Agent - Validates repair bills and calculates reimbursement
  - Final Decision Agent - Synthesizes comprehensive claim decisions

### Frontend Components
- **Next.js Application**: Modern React-based UI
- **Real-time Updates**: Live agent progress tracking
- **Document Viewer**: View and manage claim documents
- **Dashboard**: Claims analytics and insights

## 🛠️ Tech Stack

**Backend:**
- Python 3.11
- FastAPI
- Uvicorn/Gunicorn
- Azure AI Projects SDK
- Azure Cosmos DB
- Azure Blob Storage
- Semantic Kernel

**Frontend:**
- Next.js 15
- React 18
- TypeScript
- Tailwind CSS
- Radix UI

## 📦 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Azure subscription with required services

### Local Development

1. **Clone the repository**
```bash
git clone https://github.com/YOUR-USERNAME/vehicleinsurance-claimsprocessing.git
cd vehicleinsurance-claimsprocessing
```

2. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your Azure credentials
```

3. **Install backend dependencies**
```bash
pip install -r requirements.txt
```

4. **Run the backend API**
```bash
# Real-time streaming API (recommended)
python api_server_realtime.py

# Or batch processing API
python api_server.py
```

5. **Install and run frontend**
```bash
cd frontend
npm install
npm run dev
```

6. **Access the application**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8001
- API Docs: http://localhost:8001/docs

## 🚀 Azure Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for complete Azure App Service deployment instructions.

### Quick Deploy Steps

1. **Create Azure App Service**
```bash
az webapp create \
  --name vehicle-claims-api \
  --resource-group your-rg \
  --plan your-plan \
  --runtime "PYTHON:3.11"
```

2. **Configure environment variables**
```bash
# See azure-config-template.txt for complete list
az webapp config appsettings set --name vehicle-claims-api --settings @azure-config-template.txt
```

3. **Deploy code**
```bash
# Using GitHub Actions (recommended - see .github/workflows/azure-deploy.yml)
# Or use Azure CLI
az webapp up --name vehicle-claims-api --resource-group your-rg
```

## 🔧 Configuration

### Required Azure Resources

1. **Azure AI Project** - AI agent orchestration
2. **Azure OpenAI** - GPT-4 model deployment
3. **Cosmos DB** - Agent memory and response storage
4. **Blob Storage** - Document storage
5. **Azure AI Search** (Optional) - Policy and document indexing

### Environment Variables

See [.env.example](.env.example) for complete configuration template.

Critical settings:
- `AZURE_ENDPOINT` - Azure AI Studio endpoint
- `AZURE_OPENAI_ENDPOINT` - OpenAI service endpoint
- `COSMOS_DB_ENDPOINT` - Cosmos DB connection
- `AZURE_STORAGE_ACCOUNT_NAME` - Blob storage account
- `CORS_ORIGINS` - Allowed frontend URLs

## 📖 API Documentation

### Endpoints

**Real-time Streaming API:**
- `POST /process-claim-stream` - Stream agent results via SSE
- `GET /api/blob/list-all` - List all documents
- `GET /api/blob/list/{claim_id}` - List claim documents
- `POST /api/blob/sas-url` - Generate document SAS URL
- `GET /api/claims/{claim_id}/outputs` - Get agent outputs
- `GET /health` - Health check

**Batch Processing API:**
- `POST /process-claim` - Process claim (all results at once)
- `GET /health` - Health check

Interactive documentation: `/docs` (Swagger UI)

## 🏗️ Project Structure

```
vehicleinsurance-claimsprocessing/
├── api_server.py                 # Batch API server
├── api_server_realtime.py        # Real-time streaming API server
├── orchestrator.py               # Main orchestrator
├── config.py                     # Configuration management
├── blob_service.py               # Blob storage service
├── requirements.txt              # Python dependencies
├── startup.sh                    # Azure startup script
├── .gitignore                    # Git ignore rules
├── DEPLOYMENT.md                 # Deployment guide
├── agents/                       # AI agent implementations
│   ├── mainpolicy.py
│   ├── inspectionagent.py
│   ├── billsynthesis.py
│   └── auditagent.py
├── orchestrator/                 # Orchestrator components
│   ├── orchestrator.py
│   ├── agent_factory.py
│   ├── memory_manager.py
│   ├── synthesis_engine.py
│   └── models.py
├── instructions/                 # Agent instruction templates
├── frontend/                     # Next.js frontend application
└── .github/
    └── workflows/
        └── azure-deploy.yml      # CI/CD pipeline
```

## 🔒 Security

- Environment variables stored in Azure App Service Configuration
- Use Azure Key Vault for production secrets
- Enable managed identity for Azure resource access
- HTTPS-only communication
- CORS properly configured

## 📊 Monitoring

- Application Insights for telemetry
- Azure Monitor for infrastructure metrics
- Real-time log streaming via Azure CLI
- Health check endpoint for availability monitoring

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License.

## 🆘 Support

For issues and questions:
- Check [DEPLOYMENT.md](DEPLOYMENT.md) for deployment troubleshooting
- Review [SETUP.md](SETUP.md) for local development setup
- Open an issue on GitHub

## 🙏 Acknowledgments

- Built with Azure AI services
- Uses GPT-4 for intelligent claim analysis
- Powered by FastAPI and Next.js

## 🛠️ Tech Stack

- **Backend**: Python, FastAPI, Azure OpenAI (GPT-4o)
- **Frontend**: Next.js 15, TypeScript, Tailwind CSS, shadcn/ui
- **Azure Services**: OpenAI, Cosmos DB, Blob Storage, AI Search

## 📄 License

MIT License - see [LICENSE](LICENSE) for details
