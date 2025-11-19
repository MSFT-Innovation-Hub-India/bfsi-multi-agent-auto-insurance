# Document Viewer Feature - Setup Guide

## Overview
The document viewer feature allows users to view claim-related documents stored in Azure Blob Storage directly from the dashboard by clicking the eye icon (👁️) in the claims table.

## Azure Blob Storage Configuration

### Storage Account Details
- **Storage Account Name**: `dataexc`
- **Container Name**: `vehicle-insuarance`
- **Connection String**: Already configured in `lib/azure-blob-service.ts`

### Document Organization
Documents should be organized in the blob storage by claim ID:
```
vehicle-insuarance/
  ├── CLM-2024-001/
  │   ├── accident_report.pdf
  │   ├── vehicle_photo_front.jpg
  │   ├── vehicle_photo_damage.jpg
  │   └── repair_invoice.pdf
  ├── CLM-2024-002/
  │   ├── police_report.pdf
  │   └── damage_photos.jpg
  └── ...
```

## Features Implemented

### 1. Azure Blob Service (`lib/azure-blob-service.ts`)
- **listClaimDocuments(claimId)**: Lists all documents for a specific claim
- **getDocumentSasUrl(blobName, claimId)**: Gets a URL for document access
- **downloadDocument(blobName, claimId)**: Downloads a document as a blob
- **testConnection()**: Tests blob storage connectivity
- **Helper functions**: getDocumentIcon(), formatFileSize()

### 2. Document Viewer Component (`components/DocumentViewer.tsx`)
A modal component that provides:
- Document preview for images and PDFs
- Navigation between multiple documents (Previous/Next)
- Download functionality
- File information display (size, type, last modified)
- Loading states and error handling
- Responsive design with animations

### 3. Dashboard Integration
The eye icon (👁️) button has been added to the Action column in the claims table:
- Click to open document viewer for that claim
- Shows next to the Process button
- Opens modal overlay with document preview

## Usage

### For Users
1. Navigate to the Claims section in the dashboard
2. Find the claim you want to view documents for
3. Click the eye icon (👁️) in the Action column
4. The document viewer will open showing all documents for that claim
5. Use Previous/Next buttons to navigate between documents
6. Click Download to save a document locally
7. Click Close or X to exit the viewer

### For Developers

#### Adding Documents to Blob Storage
Upload documents to the blob storage using Azure Storage Explorer or Azure Portal:
1. Navigate to the `vehicle-insuarance` container
2. Create a folder with the claim ID (e.g., `CLM-2024-001`)
3. Upload documents into that folder

#### Testing Connectivity
```typescript
import { testConnection } from '@/lib/azure-blob-service';

const isConnected = await testConnection();
console.log('Blob storage connected:', isConnected);
```

#### Listing Documents
```typescript
import { listClaimDocuments } from '@/lib/azure-blob-service';

const documents = await listClaimDocuments('CLM-2024-001');
console.log('Found documents:', documents);
```

## Supported File Types
- **Images**: JPG, JPEG, PNG, GIF, BMP (inline preview)
- **PDFs**: PDF files (inline preview using iframe)
- **Documents**: DOC, DOCX, XLS, XLSX (download only)
- **Videos**: MP4, AVI, MOV (download only)
- **Other**: Generic file download

## Security Considerations

### Connection String
- The connection string is hardcoded in `lib/azure-blob-service.ts`
- **For Production**: Move to environment variables
  ```typescript
  const CONNECTION_STRING = process.env.AZURE_STORAGE_CONNECTION_STRING;
  ```

### SAS Tokens
- Current implementation uses direct blob URLs
- **For Production**: Generate time-limited SAS tokens
  ```typescript
  import { generateBlobSASQueryParameters, BlobSASPermissions } from '@azure/storage-blob';
  // Generate SAS token with expiration
  ```

### Access Control
- Ensure proper CORS settings on the blob storage
- Implement role-based access if needed
- Consider adding authentication checks before allowing document access

## Environment Variables (Recommended for Production)

Add to `.env.local`:
```env
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=dataexc;AccountKey=...;EndpointSuffix=core.windows.net
AZURE_STORAGE_CONTAINER_NAME=vehicle-insuarance
```

Update `lib/azure-blob-service.ts`:
```typescript
const CONNECTION_STRING = process.env.AZURE_STORAGE_CONNECTION_STRING;
const CONTAINER_NAME = process.env.AZURE_STORAGE_CONTAINER_NAME || 'vehicle-insuarance';
```

## Troubleshooting

### "Failed to list documents"
- Check that the claim ID folder exists in blob storage
- Verify blob storage connection string is correct
- Ensure the container name is `vehicle-insuarance` (note the spelling)

### "No documents found"
- Verify documents are uploaded to the correct folder (claim ID)
- Check that files are in the format: `{claimId}/{filename}`

### CORS Errors
If you see CORS errors in the browser console:
1. Go to Azure Portal → Storage Account → CORS settings
2. Add allowed origins (e.g., `http://localhost:3000`)
3. Allow methods: GET, HEAD
4. Allow headers: `*`

### Preview Not Working
- PDFs: Ensure the blob URL is accessible directly
- Images: Check image format is supported
- Other files: Download option is always available

## Future Enhancements
- [ ] Add document upload functionality from the dashboard
- [ ] Implement document versioning
- [ ] Add document annotations/comments
- [ ] Implement document sharing via email
- [ ] Add search within documents
- [ ] Support for more file types (Excel preview, Word preview)
- [ ] Implement SAS token generation for enhanced security
- [ ] Add document deletion functionality
- [ ] Implement audit logging for document access

## Files Modified/Created
1. ✅ `lib/azure-blob-service.ts` - Azure Blob Storage service
2. ✅ `components/DocumentViewer.tsx` - Document viewer modal component
3. ✅ `app/dashboard/page.tsx` - Added eye icon button and viewer integration
4. ✅ `package.json` - Added `@azure/storage-blob` dependency

## Testing Checklist
- [ ] Upload test documents to blob storage
- [ ] Test document listing for a claim
- [ ] Test image preview
- [ ] Test PDF preview
- [ ] Test document download
- [ ] Test navigation between documents
- [ ] Test error handling (no documents, invalid claim)
- [ ] Test on different browsers
- [ ] Test responsive design on mobile devices
