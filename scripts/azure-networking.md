# Azure Networking Setup

Scripts to enable Azure Blob Storage and Cosmos DB public network access for the Vehicle Insurance Claims Processing system.

This is needed when Azure resources have restricted network access (e.g., via Private Endpoints or firewall rules) and you need to temporarily or persistently enable access from your current machine or a deployment environment.

---

## Files

| File | Description |
|------|-------------|
| `enable-azure-networking.ps1` | PowerShell script — enables network access on Blob Storage and Cosmos DB |
| `enable-azure-networking.cmd` | CMD launcher — double-click shortcut to run the PowerShell script with bypass policy |

---

## Usage

### Option 1 — Inline with environment variables (recommended for CI / one-liners)

Set the required resource names inline and invoke the script directly:

```powershell
powershell -ExecutionPolicy Bypass -Command {
    $env:AZURE_RESOURCE_GROUP      = "fsi-demos"
    $env:AZURE_STORAGE_ACCOUNT_NAME = "fsidemo"
    $env:COSMOS_DB_ACCOUNT_NAME    = "fsiauto"
    & ".\scripts\enable-azure-networking.ps1"
}
```

> Replace the values with your own resource names if they differ.

### Option 2 — Export environment variables first, then run

```powershell
$env:AZURE_RESOURCE_GROUP       = "fsi-demos"
$env:AZURE_STORAGE_ACCOUNT_NAME = "fsidemo"
$env:COSMOS_DB_ACCOUNT_NAME     = "fsiauto"

.\scripts\enable-azure-networking.ps1
```

### Option 3 — Pass parameters directly

```powershell
.\scripts\enable-azure-networking.ps1 `
    -ResourceGroup      "fsi-demos" `
    -StorageAccountName "fsidemo" `
    -CosmosAccountName  "fsiauto"
```

### Option 4 — Double-click launcher (Windows only)

Run `enable-azure-networking.cmd` directly from Explorer. It picks up environment variables already set in the shell session.

---

## Parameters

| Parameter / Env Var | Required | Description |
|---------------------|----------|-------------|
| `AZURE_RESOURCE_GROUP` / `-ResourceGroup` | Yes | Azure resource group containing the storage and Cosmos accounts |
| `AZURE_STORAGE_ACCOUNT_NAME` / `-StorageAccountName` | Yes | Azure Blob Storage account name |
| `COSMOS_DB_ACCOUNT_NAME` / `-CosmosAccountName` | Yes | Azure Cosmos DB account name |
| `AZURE_SUBSCRIPTION_ID` / `-SubscriptionId` | No | Subscription ID — uses the default subscription if omitted |

---

## Prerequisites

- [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli) installed and on `PATH`
- Logged in via `az login` (the script will prompt if not already logged in)
- Sufficient RBAC permissions to modify network rules on the storage account and Cosmos DB account (typically **Contributor** or a custom role with `Microsoft.Storage/storageAccounts/networkRuleSet/write` and `Microsoft.DocumentDB/databaseAccounts/write`)

---

## Notes

- Run this once per session if your Azure resources are configured to block all public access by default.
- The script exits with a non-zero code on any failure, making it safe to use in CI pipelines.
- `AZURE_SUBSCRIPTION_ID` is optional; omit it to use whichever subscription is currently active in your `az` session.
