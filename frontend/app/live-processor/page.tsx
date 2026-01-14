'use client';

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ArrowLeft, Activity } from 'lucide-react';
import { useRouter } from 'next/navigation';

export default function LiveProcessorPage() {
  const router = useRouter();

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-6">
      <div className="max-w-4xl mx-auto">
        <Button 
          variant="ghost" 
          onClick={() => router.push('/dashboard')}
          className="mb-6"
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Dashboard
        </Button>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-6 w-6 text-blue-600" />
              Live Claim Processor
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-slate-600">
              This page is under development. Please use the main dashboard or agent workflow pages for claim processing.
            </p>
            <div className="mt-4 flex gap-4">
              <Button onClick={() => router.push('/dashboard')}>
                Go to Dashboard
              </Button>
              <Button variant="outline" onClick={() => router.push('/agent-workflow')}>
                Agent Workflow
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}