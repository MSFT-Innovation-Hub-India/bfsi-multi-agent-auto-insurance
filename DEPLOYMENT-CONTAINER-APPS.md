# 🚀 Azure Container Apps Deployment Guide

## For Complete Beginners!

This guide will help you deploy your Vehicle Insurance Claims Processing API to Azure Container Apps.

---

## 📋 What You Need Before Starting

1. **Azure Account** with an active subscription
2. **Azure CLI** installed on your computer
3. **Your Azure credentials** (you should already have these from your App Service setup)

### Install Azure CLI (if you haven't already)

**Windows:**
1. Download from: https://docs.microsoft.com/cli/azure/install-azure-cli-windows
2. Or run in PowerShell: `winget install Microsoft.AzureCLI`

---

## 🎯 Choose Your Deployment Method

### Option A: One-Click PowerShell Script (Easiest!)
### Option B: GitHub Actions (Automatic deployments)
### Option C: Step-by-Step Manual (Learn what's happening)

---

## Option A: PowerShell Script Deployment

### Step 1: Open the Script
Open `scripts/deploy-container-apps.ps1` in VS Code

### Step 2: Fill in Your Credentials
Look for the section that says "YOUR AZURE CREDENTIALS" and fill in your values:

```powershell
# Azure AI Project (from Azure AI Studio)
$AZURE_ENDPOINT = "https://eastus2.api.azureml.ms"
$AZURE_RESOURCE_GROUP = "your-ai-resource-group"
$AZURE_SUBSCRIPTION_ID = "your-subscription-id"
$AZURE_PROJECT_NAME = "your-project-name"

# Azure OpenAI
$AZURE_OPENAI_ENDPOINT = "https://your-openai.openai.azure.com/"
$AZURE_OPENAI_API_KEY = "your-openai-api-key"

# Cosmos DB
$COSMOS_DB_ENDPOINT = "https://your-cosmos.documents.azure.com:443/"
$COSMOS_DB_KEY = "your-cosmos-key"

# Blob Storage
$AZURE_STORAGE_ACCOUNT_NAME = "your-storage-account"
$AZURE_STORAGE_ACCOUNT_KEY = "your-storage-key"
```

### Step 3: Run the Script

1. Open PowerShell (or Terminal in VS Code)
2. Navigate to the scripts folder:
   ```powershell
   cd "c:\Users\t-kushik\OneDrive - Microsoft\proj\vehicle-final\vehicleinsurance-claimsprocessing\scripts"
   ```
3. Run the deployment:
   ```powershell
   .\deploy-container-apps.ps1
   ```

The script will:
- ✅ Create a Resource Group
- ✅ Create a Container Registry
- ✅ Create a Container Apps Environment
- ✅ Build your Docker image
- ✅ Deploy your app
- ✅ Give you the URL!

### Step 4: Update Your App (After Making Changes)

```powershell
.\update-container-app.ps1
```

---

## Option B: GitHub Actions (Automatic Deployments)

This deploys automatically whenever you push code to GitHub!

### Step 1: First Deploy Using PowerShell
Run `deploy-container-apps.ps1` once to create the Azure resources.

### Step 2: Create Azure Service Principal

Open PowerShell and run:

```powershell
# Replace with YOUR subscription ID and resource group
az ad sp create-for-rbac `
  --name "vehicle-claims-github" `
  --role contributor `
  --scopes /subscriptions/YOUR-SUBSCRIPTION-ID/resourceGroups/vehicle-claims-rg `
  --sdk-auth
```

📋 **Copy the entire JSON output** - you'll need it!

### Step 3: Add GitHub Secrets

1. Go to your GitHub repository
2. Click **Settings** > **Secrets and variables** > **Actions**
3. Click **New repository secret**
4. Add these secrets:

| Secret Name | Value |
|-------------|-------|
| `AZURE_CREDENTIALS` | The full JSON from Step 2 |
| `ACR_NAME` | Your container registry name (e.g., `vehicleclaimsacr1234`) |
| `RESOURCE_GROUP` | Your resource group (e.g., `vehicle-claims-rg`) |

### Step 4: Push Your Code!

```bash
git add .
git commit -m "Add Container Apps deployment"
git push
```

GitHub will automatically build and deploy your app!

---

## Option C: Manual Step-by-Step

If you want to understand each step:

### Step 1: Login to Azure
```powershell
az login
```

### Step 2: Install Container Apps Extension
```powershell
az extension add --name containerapp --upgrade
```

### Step 3: Create Resource Group
```powershell
az group create --name vehicle-claims-rg --location eastus
```

### Step 4: Create Container Registry
```powershell
az acr create --resource-group vehicle-claims-rg --name vehicleclaimsacr --sku Basic --admin-enabled true
```

### Step 5: Create Container Apps Environment
```powershell
az containerapp env create --name vehicle-claims-env --resource-group vehicle-claims-rg --location eastus
```

### Step 6: Build Docker Image
```powershell
cd "c:\Users\t-kushik\OneDrive - Microsoft\proj\vehicle-final\vehicleinsurance-claimsprocessing"
az acr build --registry vehicleclaimsacr --image vehicle-claims-api:latest .
```

### Step 7: Deploy Container App
```powershell
az containerapp create `
  --name vehicle-claims-api `
  --resource-group vehicle-claims-rg `
  --environment vehicle-claims-env `
  --image vehicleclaimsacr.azurecr.io/vehicle-claims-api:latest `
  --target-port 8000 `
  --ingress external `
  --registry-server vehicleclaimsacr.azurecr.io `
  --cpu 1.0 `
  --memory 2.0Gi
```

---

## 🔍 Useful Commands

### View Logs
```powershell
az containerapp logs show --name vehicle-claims-api --resource-group vehicle-claims-rg --follow
```

### Check App Status
```powershell
az containerapp show --name vehicle-claims-api --resource-group vehicle-claims-rg
```

### Get App URL
```powershell
az containerapp show --name vehicle-claims-api --resource-group vehicle-claims-rg --query properties.configuration.ingress.fqdn -o tsv
```

### Restart App
```powershell
az containerapp revision restart --name vehicle-claims-api --resource-group vehicle-claims-rg
```

### Delete Everything (cleanup)
```powershell
az group delete --name vehicle-claims-rg --yes
```

---

## ❓ Troubleshooting

### "az: command not found"
→ Install Azure CLI: https://docs.microsoft.com/cli/azure/install-azure-cli

### "Not logged in"
→ Run: `az login`

### "Container app failed to start"
→ Check logs: `az containerapp logs show --name vehicle-claims-api --resource-group vehicle-claims-rg`

### "Missing environment variables"
→ Make sure you filled in all credentials in the deployment script

### "Image build failed"
→ Check the Dockerfile exists in your project root
→ Make sure requirements.txt is correct

---

## 💰 Cost Comparison

| Feature | App Service (B1) | Container Apps |
|---------|------------------|----------------|
| Monthly Cost | ~$13 fixed | Pay per use (can be $0 when idle) |
| Scaling | Manual | Automatic (0 to 10+ replicas) |
| Cold Start | None | 5-10 seconds if scaled to 0 |
| Best For | Consistent traffic | Variable/burst traffic |

---

## 📚 More Resources

- [Azure Container Apps Documentation](https://learn.microsoft.com/azure/container-apps/)
- [Azure CLI Reference](https://learn.microsoft.com/cli/azure/)
- [Docker Documentation](https://docs.docker.com/)
