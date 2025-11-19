'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Download, ChevronLeft, ChevronRight, FileText, Loader2, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  ClaimDocument, 
  listClaimDocuments, 
  getDocumentSasUrl,
  getDocumentIcon,
  formatFileSize 
} from '@/lib/azure-blob-service';

interface DocumentViewerProps {
  claimId: string;
  isOpen: boolean;
  onClose: () => void;
}

export function DocumentViewer({ claimId, isOpen, onClose }: DocumentViewerProps) {
  const [documents, setDocuments] = useState<ClaimDocument[]>([]);
  const [currentDocIndex, setCurrentDocIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [documentUrl, setDocumentUrl] = useState<string | null>(null);

  // Load documents when modal opens
  useEffect(() => {
    if (isOpen && claimId) {
      loadDocuments();
    }
  }, [isOpen, claimId]);

  // Load document URL when current document changes
  useEffect(() => {
    if (documents.length > 0 && currentDocIndex >= 0) {
      loadCurrentDocumentUrl();
    }
  }, [currentDocIndex, documents]);

  const loadDocuments = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const docs = await listClaimDocuments(claimId);
      
      if (docs.length === 0) {
        setError('No documents found for this claim');
      } else {
        setDocuments(docs);
        setCurrentDocIndex(0);
      }
    } catch (err) {
      console.error('Error loading documents:', err);
      setError('Failed to load documents. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const loadCurrentDocumentUrl = async () => {
    if (documents.length === 0) return;
    
    try {
      const currentDoc = documents[currentDocIndex];
      const url = await getDocumentSasUrl(currentDoc.name, claimId);
      setDocumentUrl(url);
    } catch (err) {
      console.error('Error loading document URL:', err);
      setError('Failed to load document preview');
    }
  };

  const handlePrevious = () => {
    if (currentDocIndex > 0) {
      setCurrentDocIndex(currentDocIndex - 1);
    }
  };

  const handleNext = () => {
    if (currentDocIndex < documents.length - 1) {
      setCurrentDocIndex(currentDocIndex + 1);
    }
  };

  const handleDownload = async () => {
    if (!documentUrl) return;
    
    try {
      const response = await fetch(documentUrl);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = documents[currentDocIndex].name;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      console.error('Error downloading document:', err);
      alert('Failed to download document');
    }
  };

  const currentDoc = documents[currentDocIndex];
  const isImage = currentDoc?.contentType?.includes('image');
  const isPdf = currentDoc?.contentType?.includes('pdf') || currentDoc?.name?.endsWith('.pdf');

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-[99999] flex items-center justify-center p-4">
        {/* Backdrop */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="absolute inset-0 bg-black/90 backdrop-blur-sm"
          onClick={onClose}
        />
        
        {/* Modal Content */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 20 }}
          className="relative z-10 w-full max-w-[95vw] max-h-[90vh] bg-white rounded-2xl shadow-2xl overflow-hidden flex flex-col"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="bg-blue-600 p-6 text-white">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center space-x-3 mb-2">
                  <FileText className="h-6 w-6" />
                  <h2 className="text-2xl font-bold">Claim Documents</h2>
                </div>
                <p className="text-sm text-blue-100">
                  Claim ID: <span className="font-semibold">{claimId}</span>
                </p>
                {documents.length > 0 && (
                  <div className="mt-2 flex items-center space-x-2">
                    <Badge variant="secondary" className="bg-white/20 text-white">
                      {currentDocIndex + 1} of {documents.length}
                    </Badge>
                    {currentDoc && (
                      <span className="text-sm text-blue-100">
                        {getDocumentIcon(currentDoc.contentType, currentDoc.name)} {currentDoc.name}
                      </span>
                    )}
                  </div>
                )}
              </div>
              <Button
                variant="ghost"
                size="icon"
                onClick={onClose}
                className="text-white hover:bg-white/20 flex-shrink-0"
              >
                <X className="h-6 w-6" />
              </Button>
            </div>
          </div>

          {/* Document Viewer Area */}
          <div className="flex-1 bg-slate-50 relative" style={{ minHeight: '500px' }}>
            {/* Navigation Chevrons - Only show when there are multiple documents */}
            {!loading && !error && documents.length > 1 && (
              <>
                <button
                  onClick={handlePrevious}
                  disabled={currentDocIndex === 0}
                  title="Previous document"
                  aria-label="Previous document"
                  className="absolute left-4 top-1/2 -translate-y-1/2 z-10 bg-white/90 hover:bg-white disabled:opacity-30 disabled:cursor-not-allowed rounded-full p-3 shadow-lg transition-all"
                >
                  <ChevronLeft className="h-8 w-8 text-slate-700" />
                </button>
                <button
                  onClick={handleNext}
                  disabled={currentDocIndex === documents.length - 1}
                  title="Next document"
                  aria-label="Next document"
                  className="absolute right-4 top-1/2 -translate-y-1/2 z-10 bg-white/90 hover:bg-white disabled:opacity-30 disabled:cursor-not-allowed rounded-full p-3 shadow-lg transition-all"
                >
                  <ChevronRight className="h-8 w-8 text-slate-700" />
                </button>
              </>
            )}

            {loading ? (
              <div className="flex items-center justify-center h-full">
                <div className="text-center">
                  <Loader2 className="h-12 w-12 text-blue-600 animate-spin mx-auto mb-4" />
                  <p className="text-slate-600">Loading documents...</p>
                </div>
              </div>
            ) : error ? (
              <div className="flex items-center justify-center h-full">
                <div className="text-center max-w-md p-6">
                  <AlertCircle className="h-16 w-16 text-red-500 mx-auto mb-4" />
                  <h3 className="text-xl font-semibold text-slate-900 mb-2">Error Loading Documents</h3>
                  <p className="text-slate-600 mb-4">{error}</p>
                  <Button onClick={loadDocuments} className="bg-blue-600 hover:bg-blue-700">
                    Try Again
                  </Button>
                </div>
              </div>
            ) : documents.length === 0 ? (
              <div className="flex items-center justify-center h-full">
                <div className="text-center">
                  <FileText className="h-16 w-16 text-slate-300 mx-auto mb-4" />
                  <p className="text-slate-500">No documents available for this claim</p>
                </div>
              </div>
            ) : (
              <div className="w-full h-full p-6">
                {documentUrl && (
                  <>
                    {isImage ? (
                      <div className="absolute inset-4 flex items-center justify-center">
                        <img
                          src={documentUrl}
                          alt={currentDoc.name}
                          className="block"
                          style={{ 
                            maxWidth: 'calc(100% - 120px)',
                            maxHeight: 'calc(100% - 40px)',
                            width: 'auto',
                            height: 'auto',
                            objectFit: 'contain'
                          }}
                        />
                      </div>
                    ) : isPdf ? (
                      <iframe
                        src={documentUrl}
                        className="w-full h-full border-0 rounded-lg shadow-lg"
                        title={currentDoc.name}
                        style={{ minHeight: '600px' }}
                      />
                    ) : (
                      <div className="flex items-center justify-center h-full p-8">
                        <div className="text-center max-w-md">
                          <div className="text-6xl mb-4">
                            {getDocumentIcon(currentDoc.contentType, currentDoc.name)}
                          </div>
                          <h3 className="text-xl font-semibold text-slate-900 mb-2">
                            {currentDoc.name}
                          </h3>
                          <p className="text-slate-600 mb-4">
                            {formatFileSize(currentDoc.size)} • {currentDoc.contentType}
                          </p>
                          <p className="text-sm text-slate-500 mb-4">
                            Preview not available for this file type
                          </p>
                          <Button onClick={handleDownload} className="bg-blue-600 hover:bg-blue-700">
                            <Download className="mr-2 h-4 w-4" />
                            Download File
                          </Button>
                        </div>
                      </div>
                    )}
                  </>
                )}
              </div>
            )}
          </div>

          {/* Footer Controls */}
          {!loading && !error && documents.length > 0 && (
            <div className="border-t border-slate-200 bg-white p-4">
              <div className="flex items-center justify-between">
                {/* Navigation */}
                <div className="flex items-center space-x-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handlePrevious}
                    disabled={currentDocIndex === 0}
                  >
                    <ChevronLeft className="h-4 w-4 mr-1" />
                    Previous
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleNext}
                    disabled={currentDocIndex === documents.length - 1}
                  >
                    Next
                    <ChevronRight className="h-4 w-4 ml-1" />
                  </Button>
                </div>

                {/* Document Info */}
                {currentDoc && (
                  <div className="text-center flex-1 px-4">
                    <p className="text-sm text-slate-600">
                      {formatFileSize(currentDoc.size)} • Last modified:{' '}
                      {currentDoc.lastModified.toLocaleDateString()}
                    </p>
                  </div>
                )}

                {/* Actions */}
                <div className="flex items-center space-x-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleDownload}
                    disabled={!documentUrl}
                  >
                    <Download className="h-4 w-4 mr-1" />
                    Download
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={onClose}
                  >
                    Close
                  </Button>
                </div>
              </div>
            </div>
          )}
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
