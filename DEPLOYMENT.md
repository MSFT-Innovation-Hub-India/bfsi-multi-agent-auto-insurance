# Azure App Service Deployment Guide

## 🚀 Quick Deployment Steps

### Prerequisites
- Azure subscription with appropriate permissions
- Azure CLI installed or access to Azure Portal
- All Azure resources created (see Required Resources section)

---

## 📋 Deployment Checklist

### Step 1: Create Azure App Service

#### Using Azure Portal:
1. Navigate to **Azure Portal** → **App Services** → **Create**
2. Configure:
   - **Resource Group**: Choose or create new
   - **Name**: `your-app-name` (e.g., `vehicle-claims-api`)
   - **Runtime stack**: `Python 3.11` or `Python 3.10`
   - **Operating System**: `Linux`
   - **Region**: Choose closest to your users
   - **Pricing tier**: `B1` (Basic) minimum, `P1V2` (Premium) recommended

#### Using Azure CLI:
```bash
# Create resource group
az group create --name vehicle-claims-rg --location eastus

# Create App Service Plan
az appservice plan create \
  --name vehicle-claims-plan \
  --resource-group vehicle-claims-rg \
  --sku B1 \
  --is-linux

# Create Web App
az webapp create \
  --name vehicle-claims-api \
  --resource-group vehicle-claims-rg \
  --plan vehicle-claims-plan \
  --runtime "PYTHON:3.11"
```

---

### Step 2: Configure Application Settings

Navigate to **App Service → Configuration → Application Settings** and add these environment variables:

#### Required Azure Configuration
```
AZURE_ENDPOINT=https://eastus2.api.azureml.ms
AZURE_RESOURCE_GROUP=your-resource-group-name
AZURE_SUBSCRIPTION_ID=your-subscription-id
AZURE_PROJECT_NAME=your-project-name
```

#### Required Azure OpenAI
```
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o
AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com/
AZURE_OPENAI_API_KEY=your-openai-api-key
```

#### Required Cosmos DB
```
COSMOS_DB_ENDPOINT=https://your-cosmos.documents.azure.com:443/
COSMOS_DB_KEY=your-cosmos-key
COSMOS_DB_DATABASE_NAME=insurance
COSMOS_DB_CONTAINER_NAME=data
```

#### Required Blob Storage
```
AZURE_STORAGE_ACCOUNT_NAME=yourstorageaccount
AZURE_STORAGE_ACCOUNT_KEY=your-storage-key
AZURE_STORAGE_CONTAINER_NAME=vehicle-insurance
```

#### Optional: Azure AI Search
```
SEARCH_ENDPOINT=https://your-search.search.windows.net/
SEARCH_KEY=your-search-key
POLICY_INDEX_NAME=policy
INSURANCE_INDEX_NAME=insurance
BILL_INDEX_NAME=bill
```

#### CORS Configuration
```
CORS_ORIGINS=https://your-frontend.azurewebsites.net,https://custom-domain.com
```

**Using Azure CLI:**
```bash
az webapp config appsettings set \
  --name vehicle-claims-api \
  --resource-group vehicle-claims-rg \
  --settings \
    AZURE_ENDPOINT="https://eastus2.api.azureml.ms" \
    AZURE_RESOURCE_GROUP="your-rg" \
    AZURE_SUBSCRIPTION_ID="your-sub-id" \
    COSMOS_DB_ENDPOINT="https://your-cosmos.documents.azure.com:443/" \
    COSMOS_DB_KEY="your-key" \
    CORS_ORIGINS="https://your-frontend.azurewebsites.net"
```

---

### Step 3: Configure Startup Command

Navigate to **App Service → Configuration → General Settings**

**Startup Command:**
```bash
/home/site/wwwroot/startup.sh
```

Or if using batch API:
```bash
/home/site/wwwroot/startup-batch.sh
```

**Using Azure CLI:**
```bash
az webapp config set \
  --name vehicle-claims-api \
  --resource-group vehicle-claims-rg \
  --startup-file "/home/site/wwwroot/startup.sh"
```

---

### Step 4: Deploy Code

#### Option A: GitHub Actions (Recommended)
1. In Azure Portal → **App Service → Deployment Center**
2. Select **GitHub** as source
3. Authenticate and select repository
4. Select branch (main/master)
5. Azure will create a workflow file
6. Push to trigger deployment

#### Option B: Local Git
```bash
# Get deployment credentials
az webapp deployment list-publishing-credentials \
  --name vehicle-claims-api \
  --resource-group vehicle-claims-rg

# Add Azure remote
git remote add azure https://<username>:<password>@vehicle-claims-api.scm.azurewebsites.net/vehicle-claims-api.git

# Deploy
git push azure main:master
```

#### Option C: ZIP Deployment
```bash
# Create deployment package
zip -r deploy.zip . -x "*.git*" "*.env" "node_modules/*" "frontend/*"

# Deploy
az webapp deployment source config-zip \
  --name vehicle-claims-api \
  --resource-group vehicle-claims-rg \
  --src deploy.zip
```

#### Option D: VS Code Extension
1. Install **Azure App Service** extension
2. Right-click on App Service
3. Select **Deploy to Web App**
4. Select your workspace folder

---

### Step 5: Enable Logging

```bash
# Enable application logging
az webapp log config \
  --name vehicle-claims-api \
  --resource-group vehicle-claims-rg \
  --application-logging filesystem \
  --level information

# Stream logs
az webapp log tail \
  --name vehicle-claims-api \
  --resource-group vehicle-claims-rg
```

In Azure Portal:
**App Service → Monitoring → Log stream**

---

### Step 6: Configure Networking (Optional)

#### Enable HTTPS Only
```bash
az webapp update \
  --name vehicle-claims-api \
  --resource-group vehicle-claims-rg \
  --https-only true
```

#### Add Custom Domain (Optional)
1. Navigate to **App Service → Custom domains**
2. Add your domain
3. Configure DNS records
4. Add SSL certificate

---

## 🔍 Verification Steps

### 1. Check Deployment Status
```bash
az webapp show \
  --name vehicle-claims-api \
  --resource-group vehicle-claims-rg \
  --query state
```

### 2. Test Health Endpoint
```bash
curl https://vehicle-claims-api.azurewebsites.net/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2026-01-13T...",
  "orchestrator_initialized": true,
  "mode": "real-time-streaming"
}
```

### 3. Test API Documentation
Visit: `https://vehicle-claims-api.azurewebsites.net/docs`

### 4. Check Application Logs
```bash
az webapp log tail \
  --name vehicle-claims-api \
  --resource-group vehicle-claims-rg
```

---

## ⚠️ Common Issues & Solutions

### Issue: Application won't start
**Solution:**
- Check logs: `az webapp log tail`
- Verify startup command is correct
- Ensure all required environment variables are set
- Check Python version matches runtime stack

### Issue: "Orchestrator not initialized"
**Solution:**
- Verify all Azure credentials in Application Settings
- Check Cosmos DB and Blob Storage are accessible
- Review environment variable names (case-sensitive)

### Issue: CORS errors
**Solution:**
- Add frontend URL to `CORS_ORIGINS` setting
- Ensure URLs include protocol (https://)
- Use comma-separated list for multiple origins

### Issue: Timeout errors
**Solution:**
- Increase timeout in `startup.sh` (current: 120s)
- Scale up to higher pricing tier (more CPU/memory)
- Check Azure AI service quotas

### Issue: Dependencies not installed
**Solution:**
- Verify `requirements.txt` is in root directory
- Check `.deployment` file exists
- Enable build during deployment

---

## 🔒 Security Best Practices

### 1. Use Managed Identity (Recommended)
Instead of using keys, enable managed identity:
```bash
az webapp identity assign \
  --name vehicle-claims-api \
  --resource-group vehicle-claims-rg
```

Then grant access to Azure resources using RBAC.

### 2. Store Secrets in Key Vault
```bash
# Create Key Vault
az keyvault create \
  --name vehicle-claims-kv \
  --resource-group vehicle-claims-rg

# Add secret
az keyvault secret set \
  --vault-name vehicle-claims-kv \
  --name "CosmosDbKey" \
  --value "your-cosmos-key"

# Reference in App Settings
@Microsoft.KeyVault(SecretUri=https://vehicle-claims-kv.vault.azure.net/secrets/CosmosDbKey/)
```

### 3. Network Security
- Enable HTTPS only
- Configure IP restrictions if needed
- Use Private Endpoints for Azure services
- Enable Azure DDoS protection

### 4. Monitoring & Alerts
```bash
# Enable Application Insights
az monitor app-insights component create \
  --app vehicle-claims-insights \
  --location eastus \
  --resource-group vehicle-claims-rg

# Connect to App Service
az webapp config appsettings set \
  --name vehicle-claims-api \
  --resource-group vehicle-claims-rg \
  --settings APPLICATIONINSIGHTS_CONNECTION_STRING="InstrumentationKey=..."
```

---

## 📊 Scaling & Performance

### Manual Scaling
```bash
# Scale up (vertical)
az appservice plan update \
  --name vehicle-claims-plan \
  --resource-group vehicle-claims-rg \
  --sku P1V2

# Scale out (horizontal)
az appservice plan update \
  --name vehicle-claims-plan \
  --resource-group vehicle-claims-rg \
  --number-of-workers 3
```

### Auto-scaling Rules
In Azure Portal:
**App Service Plan → Scale out (App Service plan)** → Configure rules

---

## 🔄 CI/CD Pipeline Example

### GitHub Actions Workflow
Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Azure App Service

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Deploy to Azure
      uses: azure/webapps-deploy@v2
      with:
        app-name: 'vehicle-claims-api'
        publish-profile: ${{ secrets.AZURE_WEBAPP_PUBLISH_PROFILE }}
```

---

## 📚 Additional Resources

- [Azure App Service Documentation](https://docs.microsoft.com/azure/app-service/)
- [Python on Azure App Service](https://docs.microsoft.com/azure/app-service/quickstart-python)
- [Deploy Python Apps](https://docs.microsoft.com/azure/app-service/configure-language-python)
- [Troubleshooting Guide](https://docs.microsoft.com/azure/app-service/troubleshoot-diagnostic-logs)

---

## 💰 Cost Estimation

### Basic Setup (Development/Testing)
- **App Service (B1)**: ~$13/month
- **Cosmos DB (Serverless)**: Pay-per-use, ~$10-50/month
- **Blob Storage**: ~$2-10/month
- **Azure OpenAI**: Pay-per-token
- **Total**: ~$30-100/month

### Production Setup
- **App Service (P1V2)**: ~$96/month
- **Cosmos DB (Provisioned 400 RU/s)**: ~$24/month
- **Blob Storage**: ~$10-20/month
- **Azure OpenAI**: Variable based on usage
- **Application Insights**: ~$5-50/month
- **Total**: ~$150-250/month (excluding AI usage)

---

## 🆘 Support & Troubleshooting

### View Live Logs
```bash
az webapp log tail --name vehicle-claims-api --resource-group vehicle-claims-rg
```

### SSH into Container
```bash
az webapp ssh --name vehicle-claims-api --resource-group vehicle-claims-rg
```

### Restart Application
```bash
az webapp restart --name vehicle-claims-api --resource-group vehicle-claims-rg
```

### Check Environment Variables
```bash
az webapp config appsettings list \
  --name vehicle-claims-api \
  --resource-group vehicle-claims-rg
```
