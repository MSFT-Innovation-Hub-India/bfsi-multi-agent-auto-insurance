import { NextRequest, NextResponse } from 'next/server';

// This route proxies blob requests to the backend API
// The actual blob operations are handled by the Python backend using Managed Identity

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const claimId = searchParams.get('claimId');
    
    const endpoint = claimId 
      ? `${API_BASE_URL}/api/blob/list/${claimId}`
      : `${API_BASE_URL}/api/blob/list-all`;
    
    const response = await fetch(endpoint);
    
    if (!response.ok) {
      throw new Error(`Backend responded with status: ${response.status}`);
    }
    
    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error fetching blobs:', error);
    return NextResponse.json(
      { error: 'Failed to fetch blobs' },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { blobPath } = body;
    
    if (!blobPath) {
      return NextResponse.json(
        { error: 'blobPath is required' },
        { status: 400 }
      );
    }
    
    const response = await fetch(`${API_BASE_URL}/api/blob/sas-url`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ blob_path: blobPath }),
    });
    
    if (!response.ok) {
      throw new Error(`Backend responded with status: ${response.status}`);
    }
    
    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error getting SAS URL:', error);
    return NextResponse.json(
      { error: 'Failed to get SAS URL' },
      { status: 500 }
    );
  }
}