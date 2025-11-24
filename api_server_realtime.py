"""
Real-Time FastAPI Server for Auto Insurance Claim Orchestrator
Uses Server-Sent Events (SSE) to stream agent results as they complete
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional, AsyncGenerator
import asyncio
import json
from datetime import datetime
import uvicorn

# Import the orchestrator and blob service
from orchestrator import AutoInsuranceOrchestrator, ClaimData
from blob_service import get_blob_service

# ============================================================
# STANDARDIZED AGENT NAME MAPPING
# This ensures consistency between backend and frontend
# ============================================================
AGENT_NAMES = {
    "POLICY_INSIGHT": "Policy Insight Agent",
    "COVERAGE_ASSESSMENT": "Coverage Assessment Agent", 
    "INSPECTION": "Inspection Agent",
    "BILL_ANALYSIS": "Bill Analysis Agent",
    "FINAL_DECISION": "Final Decision Agent"
}

app = FastAPI(title="Auto Insurance Claim API - Real-Time", version="2.0.0")

# Add CORS middleware to allow frontend connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response models
class ClaimRequest(BaseModel):
    claim_id: str
    claim_description: str

class StreamMessage(BaseModel):
    """Message structure for SSE streaming"""
    type: str  # "agent_start" | "agent_complete" | "agent_error" | "final_complete" | "error"
    agent_name: str
    claim_id: str
    timestamp: str
    data: Optional[Dict[str, Any]] = None

# Global orchestrator instance
orchestrator: Optional[AutoInsuranceOrchestrator] = None

@app.on_event("startup")
async def startup_event():
    """Initialize the orchestrator on startup"""
    global orchestrator
    try:
        orchestrator = AutoInsuranceOrchestrator()
        print("✅ Real-Time Orchestrator initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize orchestrator: {e}")
        raise e

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup orchestrator on shutdown"""
    global orchestrator
    if orchestrator:
        orchestrator.cleanup()

def create_sse_message(message: StreamMessage) -> str:
    """Format message for Server-Sent Events"""
    return f"data: {json.dumps(message.dict())}\n\n"

async def process_claim_stream(claim_id: str, claim_description: str) -> AsyncGenerator[str, None]:
    """
    Stream claim processing results in real-time as each agent completes
    Uses Server-Sent Events (SSE) format
    """
    if not orchestrator:
        error_msg = StreamMessage(
            type="error",
            agent_name="system",
            claim_id=claim_id,
            timestamp=datetime.now().isoformat(),
            data={"error": "Orchestrator not initialized"}
        )
        yield create_sse_message(error_msg)
        return
    
    try:
        print(f"\n🚀 Real-Time API: Starting claim processing stream for {claim_id}")
        
        # ============================================================
        # STEP 1: PARALLEL - Policy Lookup + Policy Coverage
        # ============================================================
        print("\n⚡ Starting PARALLEL processing of Policy Lookup + Policy Coverage...")
        
        # Send start messages for both agents simultaneously
        yield create_sse_message(StreamMessage(
            type="agent_start",
            agent_name=AGENT_NAMES["POLICY_INSIGHT"],
            claim_id=claim_id,
            timestamp=datetime.now().isoformat(),
            data={"step": 1, "total_steps": 4, "description": "Extracting car details and policy information"}
        ))
        
        yield create_sse_message(StreamMessage(
            type="agent_start",
            agent_name=AGENT_NAMES["COVERAGE_ASSESSMENT"],
            claim_id=claim_id,
            timestamp=datetime.now().isoformat(),
            data={"step": 1, "total_steps": 4, "description": "Analyzing coverage eligibility and policy limits"}
        ))
        
        # Define async tasks for parallel execution
        async def run_policy_lookup():
            start_time = datetime.now()
            try:
                result = await orchestrator.get_policy_basic_details(claim_id)
                processing_time = (datetime.now() - start_time).total_seconds()
                return (AGENT_NAMES["POLICY_INSIGHT"], "completed", result, processing_time, None)
            except Exception as e:
                return (AGENT_NAMES["POLICY_INSIGHT"], "error", None, 0, str(e))
        
        async def run_coverage_assessment():
            start_time = datetime.now()
            try:
                result = await orchestrator.execute_policy_analysis(claim_description, claim_id)
                processing_time = (datetime.now() - start_time).total_seconds()
                return (AGENT_NAMES["COVERAGE_ASSESSMENT"], "completed", result, processing_time, None)
            except Exception as e:
                return (AGENT_NAMES["COVERAGE_ASSESSMENT"], "error", None, 0, str(e))
        
        # Run both agents in parallel
        parallel_start = datetime.now()
        results = await asyncio.gather(
            run_policy_lookup(),
            run_coverage_assessment(),
            return_exceptions=True
        )
        parallel_time = (datetime.now() - parallel_start).total_seconds()
        print(f"✅ Both policy agents completed in parallel in {parallel_time:.2f}s")
        
        # Process results and send completion messages
        for result in results:
            if isinstance(result, Exception):
                print(f"❌ Agent failed with exception: {result}")
                continue
                
            agent_name, status, response, processing_time, error = result
            
            if status == "completed":
                yield create_sse_message(StreamMessage(
                    type="agent_complete",
                    agent_name=agent_name,
                    claim_id=claim_id,
                    timestamp=datetime.now().isoformat(),
                    data={
                        "step": 1,
                        "status": "completed",
                        "response": response,
                        "processing_time_seconds": processing_time
                    }
                ))
                print(f"✅ {agent_name} completed in {processing_time:.2f}s")
            else:
                yield create_sse_message(StreamMessage(
                    type="agent_error",
                    agent_name=agent_name,
                    claim_id=claim_id,
                    timestamp=datetime.now().isoformat(),
                    data={"step": 1, "error": error}
                ))
                print(f"❌ {agent_name} failed: {error}")
        
        # Small delay for visual effect
        await asyncio.sleep(0.5)
        
        # ============================================================
        # STEP 2: Claims Evidence Evaluator
        # ============================================================
        yield create_sse_message(StreamMessage(
            type="agent_start",
            agent_name=AGENT_NAMES["INSPECTION"],
            claim_id=claim_id,
            timestamp=datetime.now().isoformat(),
            data={"step": 2, "total_steps": 4, "description": "Assessing vehicle damage and repair costs"}
        ))
        
        start_time = datetime.now()
        try:
            inspection_result = await orchestrator.execute_inspection_analysis(claim_description, claim_id)
            processing_time = (datetime.now() - start_time).total_seconds()
            
            yield create_sse_message(StreamMessage(
                type="agent_complete",
                agent_name=AGENT_NAMES["INSPECTION"],
                claim_id=claim_id,
                timestamp=datetime.now().isoformat(),
                data={
                    "step": 2,
                    "status": "completed",
                    "response": inspection_result,
                    "processing_time_seconds": processing_time
                }
            ))
            print(f"✅ {AGENT_NAMES['INSPECTION']} completed in {processing_time:.2f}s")
            
        except Exception as e:
            yield create_sse_message(StreamMessage(
                type="agent_error",
                agent_name=AGENT_NAMES["INSPECTION"],
                claim_id=claim_id,
                timestamp=datetime.now().isoformat(),
                data={"step": 2, "error": str(e)}
            ))
            print(f"❌ {AGENT_NAMES['INSPECTION']} failed: {e}")
        
        await asyncio.sleep(0.5)
        
        # ============================================================
        # STEP 3: Settlement Underwriter
        # ============================================================
        yield create_sse_message(StreamMessage(
            type="agent_start",
            agent_name=AGENT_NAMES["BILL_ANALYSIS"],
            claim_id=claim_id,
            timestamp=datetime.now().isoformat(),
            data={"step": 3, "total_steps": 4, "description": "Validating repair bills and calculating reimbursement"}
        ))
        
        start_time = datetime.now()
        try:
            bill_result = await orchestrator.execute_bill_reimbursement_analysis(claim_description, claim_id)
            processing_time = (datetime.now() - start_time).total_seconds()
            
            yield create_sse_message(StreamMessage(
                type="agent_complete",
                agent_name=AGENT_NAMES["BILL_ANALYSIS"],
                claim_id=claim_id,
                timestamp=datetime.now().isoformat(),
                data={
                    "step": 3,
                    "status": "completed",
                    "response": bill_result,
                    "processing_time_seconds": processing_time
                }
            ))
            print(f"✅ {AGENT_NAMES['BILL_ANALYSIS']} completed in {processing_time:.2f}s")
            
        except Exception as e:
            yield create_sse_message(StreamMessage(
                type="agent_error",
                agent_name=AGENT_NAMES["BILL_ANALYSIS"],
                claim_id=claim_id,
                timestamp=datetime.now().isoformat(),
                data={"step": 3, "error": str(e)}
            ))
            print(f"❌ {AGENT_NAMES['BILL_ANALYSIS']} failed: {e}")
        
        await asyncio.sleep(0.5)
        
        # ============================================================
        # STEP 4: Final Decision (Convergence Point)
        # ============================================================
        yield create_sse_message(StreamMessage(
            type="agent_start",
            agent_name=AGENT_NAMES["FINAL_DECISION"],
            claim_id=claim_id,
            timestamp=datetime.now().isoformat(),
            data={"step": 4, "total_steps": 4, "description": "Generating final claim decision"}
        ))
        
        start_time = datetime.now()
        try:
            # Retrieve all agent data from memory to synthesize
            all_memory = await orchestrator.memory_manager.retrieve_previous_responses(
                claim_id, 
                ["policy", "inspection", "bill_synthesis"]
            )
            
            # Create claim data object
            claim_data = ClaimData(claim_id=claim_id)
            if "policy" in all_memory:
                claim_data.policy_analysis = all_memory["policy"]["response_data"]
            if "inspection" in all_memory:
                claim_data.inspection_results = all_memory["inspection"]["response_data"]
            if "bill_synthesis" in all_memory:
                claim_data.bill_analysis = all_memory["bill_synthesis"]["response_data"]
            
            # Synthesize final recommendation
            final_result = await orchestrator.synthesize_final_recommendation(claim_data)
            processing_time = (datetime.now() - start_time).total_seconds()
            
            yield create_sse_message(StreamMessage(
                type="agent_complete",
                agent_name=AGENT_NAMES["FINAL_DECISION"],
                claim_id=claim_id,
                timestamp=datetime.now().isoformat(),
                data={
                    "step": 4,
                    "status": "completed",
                    "response": final_result,
                    "processing_time_seconds": processing_time
                }
            ))
            print(f"✅ Step 4 ({AGENT_NAMES['FINAL_DECISION']}) completed in {processing_time:.2f}s")
            
        except Exception as e:
            yield create_sse_message(StreamMessage(
                type="agent_error",
                agent_name=AGENT_NAMES["FINAL_DECISION"],
                claim_id=claim_id,
                timestamp=datetime.now().isoformat(),
                data={"step": 4, "error": str(e)}
            ))
            print(f"❌ Step 4 failed: {e}")
        
        # ============================================================
        # FINAL COMPLETION MESSAGE
        # ============================================================
        yield create_sse_message(StreamMessage(
            type="final_complete",
            agent_name="system",
            claim_id=claim_id,
            timestamp=datetime.now().isoformat(),
            data={
                "message": "All agents completed processing",
                "total_steps": 4,
                "status": "completed"
            }
        ))
        
        print(f"✅ Real-Time processing completed for claim {claim_id}")
        
    except Exception as e:
        print(f"❌ Real-Time processing error: {e}")
        yield create_sse_message(StreamMessage(
            type="error",
            agent_name="system",
            claim_id=claim_id,
            timestamp=datetime.now().isoformat(),
            data={"error": str(e)}
        ))

@app.post("/process-claim-stream")
async def process_claim_stream_endpoint(request: ClaimRequest):
    """
    Real-time streaming endpoint using Server-Sent Events (SSE)
    Returns agent results as they complete, not all at once
    """
    return StreamingResponse(
        process_claim_stream(request.claim_id, request.claim_description),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable buffering for nginx
        }
    )

@app.post("/process-claim")
async def process_claim_batch(request: ClaimRequest):
    """
    Batch processing endpoint (for backward compatibility)
    Returns all results at once after all agents complete
    Note: This is the same as the original api_server.py behavior
    """
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator not initialized")
    
    from pydantic import BaseModel
    from typing import Optional
    
    class AgentResponse(BaseModel):
        agent_name: str
        status: str
        response: str
        timestamp: str
        processing_time_seconds: Optional[float] = None
    
    class BatchClaimResponse(BaseModel):
        claim_id: str
        overall_status: str
        processing_started: str
        processing_completed: str
        total_processing_time_seconds: float
        policy_basic_details: Optional[AgentResponse] = None
        policy_analysis: Optional[AgentResponse] = None
        inspection_analysis: Optional[AgentResponse] = None
        bill_analysis: Optional[AgentResponse] = None
        final_recommendation: Optional[AgentResponse] = None
        summary: Dict[str, Any]
    
    start_time = datetime.now()
    print(f"\n🚀 Batch API: Processing claim {request.claim_id}")
    
    try:
        response = BatchClaimResponse(
            claim_id=request.claim_id,
            overall_status="processing",
            processing_started=start_time.isoformat(),
            processing_completed="",
            total_processing_time_seconds=0.0,
            summary={}
        )
        
        # Agent 1: Policy Basic Details
        try:
            policy_start = datetime.now()
            basic_details = await orchestrator.get_policy_basic_details(request.claim_id)
            policy_time = (datetime.now() - policy_start).total_seconds()
            response.policy_basic_details = AgentResponse(
                agent_name="Policy Lookup Assistant",
                status="completed",
                response=basic_details,
                timestamp=datetime.now().isoformat(),
                processing_time_seconds=policy_time
            )
        except Exception as e:
            response.policy_basic_details = AgentResponse(
                agent_name="Policy Lookup Assistant",
                status="failed",
                response=f"Error: {str(e)}",
                timestamp=datetime.now().isoformat()
            )
        
        # Agent 2: Policy Analysis
        try:
            policy_start = datetime.now()
            policy_result = await orchestrator.execute_policy_analysis(request.claim_description, request.claim_id)
            policy_time = (datetime.now() - policy_start).total_seconds()
            response.policy_analysis = AgentResponse(
                agent_name="Policy Coverage Assistant",
                status="completed",
                response=policy_result,
                timestamp=datetime.now().isoformat(),
                processing_time_seconds=policy_time
            )
        except Exception as e:
            response.policy_analysis = AgentResponse(
                agent_name="Policy Coverage Assistant",
                status="failed",
                response=f"Error: {str(e)}",
                timestamp=datetime.now().isoformat()
            )
        
        # Agent 3: Inspection Analysis
        try:
            inspection_start = datetime.now()
            inspection_result = await orchestrator.execute_inspection_analysis(request.claim_description, request.claim_id)
            inspection_time = (datetime.now() - inspection_start).total_seconds()
            response.inspection_analysis = AgentResponse(
                agent_name="Claims Evidence Evaluator",
                status="completed",
                response=inspection_result,
                timestamp=datetime.now().isoformat(),
                processing_time_seconds=inspection_time
            )
        except Exception as e:
            response.inspection_analysis = AgentResponse(
                agent_name="Claims Evidence Evaluator",
                status="failed",
                response=f"Error: {str(e)}",
                timestamp=datetime.now().isoformat()
            )
        
        # Agent 4: Bill Analysis
        try:
            bill_start = datetime.now()
            bill_result = await orchestrator.execute_bill_reimbursement_analysis(request.claim_description, request.claim_id)
            bill_time = (datetime.now() - bill_start).total_seconds()
            response.bill_analysis = AgentResponse(
                agent_name="Settlement Underwriter",
                status="completed",
                response=bill_result,
                timestamp=datetime.now().isoformat(),
                processing_time_seconds=bill_time
            )
        except Exception as e:
            response.bill_analysis = AgentResponse(
                agent_name="Settlement Underwriter",
                status="failed",
                response=f"Error: {str(e)}",
                timestamp=datetime.now().isoformat()
            )
        
        # Agent 5: Final Recommendation
        try:
            final_start = datetime.now()
            claim_data = ClaimData(claim_id=request.claim_id)
            if response.policy_analysis:
                claim_data.policy_analysis = response.policy_analysis.response
            if response.inspection_analysis:
                claim_data.inspection_results = response.inspection_analysis.response
            if response.bill_analysis:
                claim_data.bill_analysis = response.bill_analysis.response
            
            final_result = await orchestrator.synthesize_final_recommendation(claim_data)
            final_time = (datetime.now() - final_start).total_seconds()
            response.final_recommendation = AgentResponse(
                agent_name="Decision Advisor",
                status="completed",
                response=final_result,
                timestamp=datetime.now().isoformat(),
                processing_time_seconds=final_time
            )
        except Exception as e:
            response.final_recommendation = AgentResponse(
                agent_name="Decision Advisor",
                status="failed",
                response=f"Error: {str(e)}",
                timestamp=datetime.now().isoformat()
            )
        
        # Complete processing
        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()
        
        response.overall_status = "completed"
        response.processing_completed = end_time.isoformat()
        response.total_processing_time_seconds = total_time
        
        response.summary = {
            "total_agents_processed": 5,
            "successful_agents": sum(1 for agent in [
                response.policy_basic_details,
                response.policy_analysis,
                response.inspection_analysis,
                response.bill_analysis,
                response.final_recommendation
            ] if agent and agent.status == "completed"),
            "failed_agents": sum(1 for agent in [
                response.policy_basic_details,
                response.policy_analysis,
                response.inspection_analysis,
                response.bill_analysis,
                response.final_recommendation
            ] if agent and agent.status == "failed"),
            "total_processing_time": f"{total_time:.2f} seconds",
            "claim_status": "processed"
        }
        
        print(f"✅ Batch processing completed in {total_time:.2f}s")
        return response
        
    except Exception as e:
        print(f"❌ Batch processing error: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing claim: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "orchestrator_initialized": orchestrator is not None,
        "mode": "real-time-streaming"
    }

# ============================================================
# BLOB STORAGE ENDPOINTS
# ============================================================

@app.get("/api/blob/list-all")
async def list_all_documents():
    """List all documents in the vehicle-insurance container"""
    try:
        blob_service = get_blob_service()
        documents = blob_service.list_all_documents()
        return {"documents": documents, "count": len(documents)}
    except Exception as e:
        print(f"Error listing all documents: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing documents: {str(e)}")

@app.get("/api/blob/list/{claim_id}")
async def list_claim_documents(claim_id: str):
    """List all documents for a specific claim"""
    try:
        blob_service = get_blob_service()
        documents = blob_service.list_claim_documents(claim_id)
        return documents
    except Exception as e:
        print(f"Error listing documents for claim {claim_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing claim documents: {str(e)}")

class SasUrlRequest(BaseModel):
    document_name: str
    claim_id: str
    expiry_hours: Optional[int] = 24

@app.post("/api/blob/sas-url")
async def get_sas_url(request: SasUrlRequest):
    """Generate SAS URL for a document"""
    try:
        blob_service = get_blob_service()
        url = blob_service.get_document_sas_url(
            request.document_name,
            request.claim_id,
            request.expiry_hours
        )
        return {"url": url}
    except Exception as e:
        print(f"Error generating SAS URL: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating SAS URL: {str(e)}")

# ============================================================
# COSMOS DB / AGENT OUTPUTS ENDPOINTS
# ============================================================

@app.get("/api/claims/{claim_id}/outputs")
async def get_claim_agent_outputs(claim_id: str):
    """Get all agent outputs for a specific claim from Cosmos DB"""
    try:
        if not orchestrator or not orchestrator.memory_manager:
            raise HTTPException(status_code=503, detail="Orchestrator or memory manager not initialized")
        
        # Get all agent responses from Cosmos DB
        agent_responses = await orchestrator.memory_manager.get_all_agent_responses(claim_id)
        
        # Format the responses for frontend
        outputs = []
        for response in agent_responses:
            outputs.append({
                "claim_id": claim_id,
                "agent_name": response.get("agent_type", ""),
                "response": response.get("response_data", ""),
                "timestamp": response.get("timestamp", ""),
                "status": response.get("status", "completed")
            })
        
        return {"outputs": outputs, "count": len(outputs)}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching agent outputs for claim {claim_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching agent outputs: {str(e)}")

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Auto Insurance Claim Orchestrator API - Real-Time Version",
        "version": "2.0.0",
        "mode": "Server-Sent Events (SSE) Streaming",
        "endpoints": {
            "process_claim_stream": "/process-claim-stream (POST) - Real-time streaming",
            "list_all_documents": "/api/blob/list-all (GET) - List all documents",
            "list_claim_documents": "/api/blob/list/{claim_id} (GET) - List documents for claim",
            "get_sas_url": "/api/blob/sas-url (POST) - Generate SAS URL for document",
            "get_claim_outputs": "/api/claims/{claim_id}/outputs (GET) - Get agent outputs from Cosmos DB",
            "health": "/health",
            "docs": "/docs"
        }
    }

if __name__ == "__main__":
    print("🚀 Starting Real-Time Auto Insurance Claim API Server...")
    print("📡 Using Server-Sent Events (SSE) for live streaming")
    uvicorn.run(
        "api_server_realtime:app",
        host="0.0.0.0",
        port=8001,  # Different port to avoid conflict
        reload=True,
        log_level="info"
    )
