# Setup Guide - Vehicle Insurance Claims Processing System

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.9 or higher
- Node.js 18 or higher (for frontend)
- Azure subscription with required services
- Git

### 2. Environment Configuration

#### Step 1: Copy Environment Template
```bash
cp .env.example .env
```

#### Step 2: Fill in Your Azure Credentials

Open `.env` file and update the following **REQUIRED** values:

```env
# Azure AI Project Configuration
AZURE_ENDPOINT=https://your-region.api.azureml.ms
AZURE_RESOURCE_GROUP=your-resource-group-name
AZURE_SUBSCRIPTION_ID=your-subscription-id
AZURE_PROJECT_NAME=your-project-name

# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com/
AZURE_OPENAI_API_KEY=your-openai-key

# Cosmos DB (Memory Storage)
COSMOS_DB_ENDPOINT=https://your-cosmos.documents.azure.com:443/
COSMOS_DB_KEY=your-cosmos-key

# Blob Storage (choose one option)
# Option A: Connection String (recommended)
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=...

# Option B: Account Name + Key
AZURE_STORAGE_ACCOUNT_NAME=your-storage-account
AZURE_STORAGE_ACCOUNT_KEY=your-storage-key
AZURE_STORAGE_CONTAINER_NAME=vehicle-insurance
```

### 3. Verify Configuration

Run the configuration checker:
```bash
python config.py
```

You should see:
```
✅ All required configurations are set
```

### 4. Install Dependencies

#### Backend (Python):
```bash
pip install -r requirements.txt
```

#### Frontend (Next.js):
```bash
cd frontend
npm install
```

### 5. Run the Application

#### Backend API:
```bash
# Real-time streaming API (recommended)
python api_server_realtime.py

# Or batch processing API
python api_server.py
```

Backend will run on: `http://localhost:8001`

#### Frontend UI:
```bash
cd frontend
npm run dev
```

Frontend will run on: `http://localhost:3000`

## 🔑 Required Azure Resources

### 1. Azure AI Project
- **Service**: Azure AI Studio
- **Purpose**: Orchestrates AI agents
- **Setup**: Create project in Azure AI Studio
- Get: Endpoint, Resource Group, Subscription ID, Project Name

### 2. Azure OpenAI
- **Service**: Azure OpenAI Service
- **Purpose**: Powers GPT-4 agents
- **Setup**: Deploy GPT-4o model
- Get: Endpoint, API Key

### 3. Cosmos DB
- **Service**: Azure Cosmos DB (NoSQL)
- **Purpose**: Stores agent memory and responses
- **Setup**: Create database `insurance`, container `data`
- Partition key: `/claim_id`
- Get: Endpoint, Key

### 4. Blob Storage
- **Service**: Azure Storage Account
- **Purpose**: Stores documents (PDFs, images)
- **Setup**: Create container `vehicle-insurance`
- Get: Connection String or Account Name + Key

### 5. Azure AI Search (Optional)
- **Service**: Azure Cognitive Search
- **Purpose**: Indexes policy, inspection, bill documents
- **Setup**: Create search service with indexes: `policy`, `insurance`, `bill`
- Get: Endpoint, Admin Key

## 🔒 Security Best Practices

### DO ✅
- Keep `.env` file secure and never commit it
- Use Azure Key Vault for production credentials
- Rotate keys regularly
- Use managed identities when possible
- Set appropriate RBAC permissions

### DON'T ❌
- Never hardcode credentials in code
- Never commit `.env` to version control
- Never share credentials via email/chat
- Never use production keys in development

## 🧪 Testing the Setup

### 1. Test Configuration
```bash
python config.py
```

### 2. Test Backend Health
```bash
curl http://localhost:8001/health
```

Expected response:
```json
{
  "status": "healthy",
  "orchestrator_initialized": true
}
```

### 3. Test Frontend
Open browser to `http://localhost:3000` and verify:
- API Status shows "Healthy"
- You can enter a claim ID
- Process Claim button is enabled

## 🐛 Troubleshooting

### Issue: "Missing required Azure configuration"
**Solution**: Check your `.env` file has all required variables set

### Issue: "Orchestrator not initialized"
**Solution**: 
1. Verify Azure credentials are correct
2. Check Azure services are accessible
3. Review backend terminal for error messages

### Issue: "Cosmos DB not available"
**Solution**:
1. Verify COSMOS_DB_ENDPOINT and COSMOS_DB_KEY
2. Check database and container exist
3. Verify firewall rules allow your IP

### Issue: "Blob storage connection failed"
**Solution**:
1. Use either connection string OR account name + key (not both)
2. Verify container name matches
3. Check storage account firewall settings

## 📚 Additional Resources

- [Azure AI Studio Documentation](https://learn.microsoft.com/azure/ai-studio/)
- [Azure OpenAI Service](https://learn.microsoft.com/azure/ai-services/openai/)
- [Azure Cosmos DB](https://learn.microsoft.com/azure/cosmos-db/)
- [Azure Blob Storage](https://learn.microsoft.com/azure/storage/blobs/)

## 🆘 Support

For issues or questions:
1. Check `SETUP.md` troubleshooting section
2. Review application logs in terminal
3. Verify Azure resource configurations
4. Check `.env` file for typos or missing values
