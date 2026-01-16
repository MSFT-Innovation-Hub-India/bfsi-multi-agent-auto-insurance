// Azure Blob Storage service for document management

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

// Storage account configuration
const STORAGE_ACCOUNT_NAME = process.env.NEXT_PUBLIC_STORAGE_ACCOUNT_NAME || 'dataexc';
const CONTAINER_NAME = process.env.NEXT_PUBLIC_CONTAINER_NAME || 'vehicle-insurance';

export interface BlobDocument {
  name: string;
  url: string;
  type: 'policy' | 'inspection' | 'bill' | 'other';
  uploadDate: string;
  size: number;
}

export interface ClaimDocument {
  name: string;
  url: string;
  contentType: string;
  size: number;
  lastModified: Date;
  type: 'policy' | 'inspection' | 'bill' | 'other';
}

/**
 * Get documents for a specific claim from Azure Blob Storage
 */
export async function getClaimDocuments(claimId: string): Promise<BlobDocument[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/blob/documents/${claimId}`);
    
    if (!response.ok) {
      throw new Error(`Failed to fetch documents: ${response.status}`);
    }
    
    return response.json();
  } catch (error) {
    console.error('Error fetching claim documents:', error);
    // Return mock data for development
    return getMockDocuments(claimId);
  }
}

/**
 * Upload a document to Azure Blob Storage
 */
export async function uploadDocument(
  claimId: string,
  file: File,
  documentType: BlobDocument['type']
): Promise<BlobDocument> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('claimId', claimId);
  formData.append('documentType', documentType);

  const response = await fetch(`${API_BASE_URL}/api/blob/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`Failed to upload document: ${response.status}`);
  }

  return response.json();
}

/**
 * Delete a document from Azure Blob Storage
 */
export async function deleteDocument(claimId: string, documentName: string): Promise<void> {
  const response = await fetch(
    `${API_BASE_URL}/api/blob/documents/${claimId}/${documentName}`,
    {
      method: 'DELETE',
    }
  );

  if (!response.ok) {
    throw new Error(`Failed to delete document: ${response.status}`);
  }
}

/**
 * Generate a SAS URL for temporary document access
 */
export async function generateSasUrl(
  claimId: string,
  documentName: string,
  expiryHours: number = 1
): Promise<string> {
  const response = await fetch(`${API_BASE_URL}/api/blob/sas-url`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      claim_id: claimId,
      document_name: documentName,
      expiry_hours: expiryHours,
    }),
  });

  if (!response.ok) {
    throw new Error(`Failed to generate SAS URL: ${response.status}`);
  }

  const data = await response.json();
  return data.url;
}

/**
 * List all documents for a claim from Azure Blob Storage
 * This function is used by DocumentViewer component
 */
export async function listClaimDocuments(claimId: string): Promise<ClaimDocument[]> {
  try {
    // Fetch all documents from the container (documents are organized by type folders, not claim_id)
    const response = await fetch(`${API_BASE_URL}/api/blob/list-all`);
    
    if (response.ok) {
      const data = await response.json();
      const documents = data.documents || [];
      return documents.map((doc: any) => ({
        name: doc.name,
        url: doc.url || '#',
        // Handle snake_case from backend (content_type, last_modified)
        contentType: doc.content_type || doc.contentType || 'application/octet-stream',
        size: doc.size || 0,
        lastModified: new Date(doc.last_modified || doc.lastModified || Date.now()),
        type: determineDocumentType(doc.name),
      }));
    }
    
    // Fallback to mock data
    return getMockClaimDocuments(claimId);
  } catch (error) {
    console.error('Error listing claim documents:', error);
    return getMockClaimDocuments(claimId);
  }
}

/**
 * Get SAS URL for a specific document
 */
export async function getDocumentSasUrl(documentName: string, claimId: string): Promise<string> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/blob/sas-url`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        document_name: documentName,
        claim_id: claimId || 'default',
      }),
    });

    if (response.ok) {
      const data = await response.json();
      return data.url;
    }

    // Fallback: return the document's existing URL if available
    return getMockDocumentUrl(documentName);
  } catch (error) {
    console.error('Error getting document SAS URL:', error);
    return getMockDocumentUrl(documentName);
  }
}

/**
 * Get icon emoji for document type
 */
export function getDocumentIcon(contentType: string, fileName: string): string {
  if (contentType?.includes('pdf') || fileName?.endsWith('.pdf')) {
    return '📄';
  }
  if (contentType?.includes('image') || /\.(jpg|jpeg|png|gif|bmp)$/i.test(fileName)) {
    return '🖼️';
  }
  if (contentType?.includes('word') || /\.(doc|docx)$/i.test(fileName)) {
    return '📝';
  }
  if (contentType?.includes('excel') || /\.(xls|xlsx)$/i.test(fileName)) {
    return '📊';
  }
  return '📎';
}

/**
 * Format file size in human-readable format
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

/**
 * Determine document type from file name
 */
function determineDocumentType(fileName: string): ClaimDocument['type'] {
  const lowerName = fileName.toLowerCase();
  if (lowerName.includes('policy') || lowerName.includes('insurance')) {
    return 'policy';
  }
  if (lowerName.includes('inspection') || lowerName.includes('damage') || lowerName.includes('photo')) {
    return 'inspection';
  }
  if (lowerName.includes('bill') || lowerName.includes('invoice') || lowerName.includes('receipt')) {
    return 'bill';
  }
  return 'other';
}

/**
 * Get mock document URL for development
 */
function getMockDocumentUrl(documentName: string): string {
  // Return a placeholder image or PDF URL
  if (/\.(jpg|jpeg|png|gif)$/i.test(documentName)) {
    return `https://via.placeholder.com/800x600/4F46E5/FFFFFF?text=${encodeURIComponent(documentName)}`;
  }
  return '#';
}

/**
 * Mock data for development - simulates Azure Blob Storage response
 */
function getMockClaimDocuments(claimId: string): ClaimDocument[] {
  return [
    {
      name: 'policy_document.pdf',
      url: '#',
      contentType: 'application/pdf',
      size: 1024000,
      lastModified: new Date('2024-11-15T10:30:00Z'),
      type: 'policy',
    },
    {
      name: 'vehicle_front_damage.jpg',
      url: 'https://via.placeholder.com/800x600/4F46E5/FFFFFF?text=Front+Damage',
      contentType: 'image/jpeg',
      size: 2048000,
      lastModified: new Date('2024-11-16T14:20:00Z'),
      type: 'inspection',
    },
    {
      name: 'vehicle_rear_damage.jpg',
      url: 'https://via.placeholder.com/800x600/DC2626/FFFFFF?text=Rear+Damage',
      contentType: 'image/jpeg',
      size: 1856000,
      lastModified: new Date('2024-11-16T14:22:00Z'),
      type: 'inspection',
    },
    {
      name: 'vehicle_side_view.jpg',
      url: 'https://via.placeholder.com/800x600/059669/FFFFFF?text=Side+View',
      contentType: 'image/jpeg',
      size: 1920000,
      lastModified: new Date('2024-11-16T14:25:00Z'),
      type: 'inspection',
    },
    {
      name: 'repair_invoice.pdf',
      url: '#',
      contentType: 'application/pdf',
      size: 512000,
      lastModified: new Date('2024-11-17T09:15:00Z'),
      type: 'bill',
    },
    {
      name: 'insurance_policy_copy.pdf',
      url: '#',
      contentType: 'application/pdf',
      size: 856000,
      lastModified: new Date('2024-11-15T08:00:00Z'),
      type: 'policy',
    },
  ];
}

// Mock data for development
function getMockDocuments(claimId: string): BlobDocument[] {
  return [
    {
      name: 'policy_document.pdf',
      url: '#',
      type: 'policy',
      uploadDate: '2024-11-15T10:30:00Z',
      size: 1024000,
    },
    {
      name: 'vehicle_inspection_front.jpg',
      url: '#',
      type: 'inspection',
      uploadDate: '2024-11-16T14:20:00Z',
      size: 2048000,
    },
    {
      name: 'vehicle_inspection_rear.jpg',
      url: '#',
      type: 'inspection',
      uploadDate: '2024-11-16T14:22:00Z',
      size: 1856000,
    },
    {
      name: 'repair_bill.pdf',
      url: '#',
      type: 'bill',
      uploadDate: '2024-11-17T09:15:00Z',
      size: 512000,
    },
  ];
}
