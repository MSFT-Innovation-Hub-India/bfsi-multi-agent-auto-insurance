# Vehicle Insurance Claims System

An automated Azure-based vehicle insurance claims processing system with AI agents for policy analysis, damage inspection, and bill verification.

## 🚀 Setup Instructions

### Prerequisites
- Python 3.8+
- Node.js 16+ (for frontend)
- Azure subscription with the following services:
  - Azure OpenAI
  - Azure Cosmos DB
  - Azure AI Search
  - Azure Blob Storage
  - Azure AI Content Understanding

### Environment Configuration

1. **Copy the environment template:**
   ```bash
   cp .env.example .env
   ```

2. **Fill in your Azure credentials in `.env`:**
   - `AZURE_OPENAI_ENDPOINT` and `AZURE_OPENAI_API_KEY`
   - `COSMOS_DB_ENDPOINT` and `COSMOS_DB_KEY`
   - `AZURE_SUBSCRIPTION_ID`, `AZURE_RESOURCE_GROUP`, `AZURE_PROJECT_NAME`
   - `SEARCH_ENDPOINT` and `SEARCH_KEY`
   - `STORAGE_ACCOUNT_NAME` and `STORAGE_ACCOUNT_KEY`
   - `AZURE_AI_ENDPOINT` for Content Understanding

3. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install frontend dependencies:**
   ```bash
   cd frontend
   npm install
   ```

### Running the Application

**Backend API Server:**
```bash
# Standard API
python api_server.py

# Realtime streaming API
python api_server_realtime.py
```

**Frontend:**
```bash
cd frontend
npm run dev
```

## 🔒 Security Notes

- **Never commit `.env` file** - it contains sensitive credentials
- The `.env.example` file is provided as a template with placeholder values
- All API keys and secrets should be stored in `.env` locally
- For production, use Azure Key Vault or similar secrets management

## 📁 Project Structure

```
├── agents/              # AI agent modules
│   ├── mainpolicy.py    # Policy expert agent
│   ├── inspectionagent.py  # Inspection agent
│   └── billsynthesis.py    # Bill analysis agent
├── frontend/            # Next.js frontend
├── api_server.py        # Main API server
├── api_server_realtime.py  # Streaming API server
├── tinsurance.py        # Document processing & indexing
├── .env.example         # Environment template
└── requirements.txt     # Python dependencies
```

## 🛠️ Development

Make sure to:
1. Keep `.env` updated with your local credentials
2. Never hardcode secrets in source files
3. Use environment variables for all configuration
4. Test changes with different Azure resources

## 📝 License

[Add your license information here]
