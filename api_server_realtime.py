"""
Real-Time FastAPI Server for Auto Insurance Claim Orchestrator
Uses Server-Sent Events (SSE) to stream agent results as they complete
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional, AsyncGenerator
import asyncio
import json
import os
from datetime import datetime
import uvicorn

# LAZY IMPORTS - these will be imported only when needed
# from orchestrator import AutoInsuranceOrchestrator, ClaimData
# from blob_service import get_blob_service

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

# Global orchestrator instance (lazy initialization)
# Type hint uses Any to avoid importing the heavy module at startup
orchestrator: Optional[Any] = None
orchestrator_lock = asyncio.Lock()

async def get_orchestrator():
    """Lazy initialization of orchestrator - only initialize when first needed"""
    global orchestrator
    if orchestrator is None:
        async with orchestrator_lock:
            if orchestrator is None:  # Double-check after acquiring lock
                print("🔄 Importing and initializing orchestrator on first request...")
                from orchestrator import AutoInsuranceOrchestrator
                orchestrator = AutoInsuranceOrchestrator()
                print("✅ Real-Time Orchestrator initialized successfully")
    return orchestrator

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    global orchestrator
    # Startup - just log, don't initialize orchestrator yet
    print("🚀 App starting up - orchestrator will be initialized on first request")
    
    yield  # Application runs here
    
    # Shutdown
    if orchestrator:
        orchestrator.cleanup()

app = FastAPI(
    title="Auto Insurance Claim API - Real-Time",
    version="2.0.0",
    lifespan=lifespan
)

# Add CORS middleware to allow frontend connections
# Read allowed origins from environment variable (comma-separated)
allowed_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in allowed_origins],
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


def create_sse_message(message: StreamMessage) -> str:
    """Format message for Server-Sent Events"""
    return f"data: {json.dumps(message.dict())}\n\n"

def create_keepalive() -> str:
    """Create SSE keep-alive comment to prevent connection timeout"""
    return ": keepalive\n\n"

async def run_with_keepalive(coro, claim_id: str):
    """
    Run a coroutine while yielding keepalive messages every 10 seconds.
    Returns (result, keepalive_messages_list) where keepalive_messages_list 
    contains any keepalive messages that should have been sent.
    """
    task = asyncio.create_task(coro)
    keepalives = []
    while not task.done():
        try:
            await asyncio.wait_for(asyncio.shield(task), timeout=10.0)
        except asyncio.TimeoutError:
            # Task still running, add keepalive
            keepalives.append(create_keepalive())
            print(f"💓 Sending keepalive for {claim_id}")
    return task.result(), keepalives

async def process_claim_stream(claim_id: str, claim_description: str) -> AsyncGenerator[str, None]:
    """
    Stream claim processing results in real-time as each agent completes
    Uses Server-Sent Events (SSE) format
    """
    try:
        orch = await get_orchestrator()
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
                result = await orch.get_policy_basic_details(claim_id)
                processing_time = (datetime.now() - start_time).total_seconds()
                return (AGENT_NAMES["POLICY_INSIGHT"], "completed", result, processing_time, None)
            except Exception as e:
                return (AGENT_NAMES["POLICY_INSIGHT"], "error", None, 0, str(e))
        
        async def run_coverage_assessment():
            start_time = datetime.now()
            try:
                result = await orch.execute_policy_analysis(claim_description, claim_id)
                processing_time = (datetime.now() - start_time).total_seconds()
                return (AGENT_NAMES["COVERAGE_ASSESSMENT"], "completed", result, processing_time, None)
            except Exception as e:
                return (AGENT_NAMES["COVERAGE_ASSESSMENT"], "error", None, 0, str(e))
        
        # Run both agents in parallel with keepalive
        parallel_start = datetime.now()
        
        # Create tasks
        task1 = asyncio.create_task(run_policy_lookup())
        task2 = asyncio.create_task(run_coverage_assessment())
        all_tasks = [task1, task2]
        
        # Wait for tasks while sending keepalives
        while not all(t.done() for t in all_tasks):
            await asyncio.sleep(8)  # Send keepalive every 8 seconds
            if not all(t.done() for t in all_tasks):
                yield create_keepalive()
                print(f"💓 Keepalive sent for parallel agents")
        
        # Gather results
        results = [task1.result(), task2.result()]
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
            # Run with keepalive to prevent timeout
            task = asyncio.create_task(orch.execute_inspection_analysis(claim_description, claim_id))
            while not task.done():
                try:
                    inspection_result = await asyncio.wait_for(asyncio.shield(task), timeout=8.0)
                    break
                except asyncio.TimeoutError:
                    yield create_keepalive()
                    print(f"💓 Keepalive sent for inspection agent")
            
            if task.done():
                inspection_result = task.result()
            
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
            # Run with keepalive to prevent timeout
            task = asyncio.create_task(orch.execute_bill_reimbursement_analysis(claim_description, claim_id))
            while not task.done():
                try:
                    bill_result = await asyncio.wait_for(asyncio.shield(task), timeout=8.0)
                    break
                except asyncio.TimeoutError:
                    yield create_keepalive()
                    print(f"💓 Keepalive sent for bill agent")
            
            if task.done():
                bill_result = task.result()
            
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
            # Import ClaimData here to avoid import at module load time
            from orchestrator import ClaimData
            
            # Retrieve all agent data from memory to synthesize
            all_memory = await orch.memory_manager.retrieve_previous_responses(
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
            
            # Synthesize final recommendation with keepalive
            task = asyncio.create_task(orch.synthesize_final_recommendation(claim_data))
            while not task.done():
                try:
                    final_result = await asyncio.wait_for(asyncio.shield(task), timeout=8.0)
                    break
                except asyncio.TimeoutError:
                    yield create_keepalive()
                    print(f"💓 Keepalive sent for final decision agent")
            
            if task.done():
                final_result = task.result()
            
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
    orch = await get_orchestrator()
    
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
            basic_details = await orch.get_policy_basic_details(request.claim_id)
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
            policy_result = await orch.execute_policy_analysis(request.claim_description, request.claim_id)
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
            inspection_result = await orch.execute_inspection_analysis(request.claim_description, request.claim_id)
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
            bill_result = await orch.execute_bill_reimbursement_analysis(request.claim_description, request.claim_id)
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
            from orchestrator import ClaimData
            final_start = datetime.now()
            claim_data = ClaimData(claim_id=request.claim_id)
            if response.policy_analysis:
                claim_data.policy_analysis = response.policy_analysis.response
            if response.inspection_analysis:
                claim_data.inspection_results = response.inspection_analysis.response
            if response.bill_analysis:
                claim_data.bill_analysis = response.bill_analysis.response
            
            final_result = await orch.synthesize_final_recommendation(claim_data)
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
        from blob_service import get_blob_service
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
        from blob_service import get_blob_service
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
        from blob_service import get_blob_service
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
        orch = await get_orchestrator()
        
        # Get all agent responses from Cosmos DB
        agent_responses = await orch.memory_manager.get_all_agent_responses(claim_id)
        
        # Format the responses for frontend
        outputs = []
        for response in agent_responses:
            outputs.append({
                "claim_id": claim_id,
                "agent_name": response.get("agent_type", ""),
                "response": response.get("response_data", ""),
                "extracted_data": response.get("extracted_data", {}),
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
    port = int(os.getenv("PORT", 8001))  # Azure App Service sets PORT env var
    uvicorn.run(
        "api_server_realtime:app",
        host="0.0.0.0",
        port=port,
        reload=False,  # Disable reload in production
        log_level="info"
    )
