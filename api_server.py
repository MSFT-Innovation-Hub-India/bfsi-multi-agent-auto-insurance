"""
FastAPI Server for Auto Insurance Claim Orchestrator
Single endpoint that processes all agents and returns comprehensive results
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional
import asyncio
import json
from datetime import datetime
import uvicorn

# Import the orchestrator
from orchestrator import AutoInsuranceOrchestrator, ClaimData

app = FastAPI(title="Auto Insurance Claim API", version="1.0.0")

# Add CORS middleware to allow frontend connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # Next.js default ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response models
class ClaimRequest(BaseModel):
    claim_id: str
    claim_description: str
    add_delays: Optional[bool] = False  # Option to add delays between agents for demo

class AgentResponse(BaseModel):
    agent_name: str
    status: str
    response: str
    timestamp: str
    processing_time_seconds: Optional[float] = None

class ClaimResponse(BaseModel):
    claim_id: str
    overall_status: str
    processing_started: str
    processing_completed: str
    total_processing_time_seconds: float
    
    # Individual agent responses
    policy_basic_details: Optional[AgentResponse] = None
    policy_analysis: Optional[AgentResponse] = None
    inspection_analysis: Optional[AgentResponse] = None
    bill_analysis: Optional[AgentResponse] = None
    final_recommendation: Optional[AgentResponse] = None
    
    # Summary
    summary: Dict[str, Any]

# Global orchestrator instance
orchestrator: Optional[AutoInsuranceOrchestrator] = None

@app.on_event("startup")
async def startup_event():
    """Initialize the orchestrator on startup"""
    global orchestrator
    try:
        orchestrator = AutoInsuranceOrchestrator()
        print("✅ Orchestrator initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize orchestrator: {e}")
        raise e

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup orchestrator on shutdown"""
    global orchestrator
    if orchestrator:
        orchestrator.cleanup()

def create_agent_response(agent_name: str, response: str, status: str = "completed", processing_time: float = None) -> AgentResponse:
    """Helper function to create standardized agent response"""
    return AgentResponse(
        agent_name=agent_name,
        status=status,
        response=response,
        timestamp=datetime.now().isoformat(),
        processing_time_seconds=processing_time
    )

@app.post("/process-claim", response_model=ClaimResponse)
async def process_claim(request: ClaimRequest):
    """
    Main endpoint to process an insurance claim through all agents
    Returns comprehensive results from all 4 agents
    """
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator not initialized")
    
    start_time = datetime.now()
    print(f"\n🚀 API: Processing claim {request.claim_id}")
    
    try:
        # Initialize response structure
        response = ClaimResponse(
            claim_id=request.claim_id,
            overall_status="processing",
            processing_started=start_time.isoformat(),
            processing_completed="",
            total_processing_time_seconds=0.0,
            summary={}
        )
        
        # Step 1: Get Policy Basic Details
        print("📋 API: Getting policy basic details...")
        policy_start = datetime.now()
        
        try:
            basic_details = await orchestrator.get_policy_basic_details(request.claim_id)
            policy_time = (datetime.now() - policy_start).total_seconds()
            
            response.policy_basic_details = create_agent_response(
                "Policy Basic Details Agent",
                basic_details,
                "completed",
                policy_time
            )
            print(f"✅ API: Policy basic details completed in {policy_time:.2f}s")
            
        except Exception as e:
            response.policy_basic_details = create_agent_response(
                "Policy Basic Details Agent",
                f"Error: {str(e)}",
                "failed"
            )
            print(f"❌ API: Policy basic details failed: {e}")
        
        # Optional delay for demo purposes
        if request.add_delays:
            await asyncio.sleep(2)
        
        # Step 2: Policy Analysis
        print("🔍 API: Running policy analysis...")
        policy_analysis_start = datetime.now()
        
        try:
            policy_result = await orchestrator.execute_policy_analysis(
                request.claim_description, 
                request.claim_id
            )
            policy_analysis_time = (datetime.now() - policy_analysis_start).total_seconds()
            
            response.policy_analysis = create_agent_response(
                "Policy Analysis Agent",
                policy_result,
                "completed",
                policy_analysis_time
            )
            print(f"✅ API: Policy analysis completed in {policy_analysis_time:.2f}s")
            
        except Exception as e:
            response.policy_analysis = create_agent_response(
                "Policy Analysis Agent",
                f"Error: {str(e)}",
                "failed"
            )
            print(f"❌ API: Policy analysis failed: {e}")
        
        # Optional delay for demo purposes
        if request.add_delays:
            await asyncio.sleep(2)
        
        # Step 3: Inspection Analysis
        print("🔧 API: Running inspection analysis...")
        inspection_start = datetime.now()
        
        try:
            inspection_result = await orchestrator.execute_inspection_analysis(
                request.claim_description,
                request.claim_id
            )
            inspection_time = (datetime.now() - inspection_start).total_seconds()
            
            response.inspection_analysis = create_agent_response(
                "Inspection Analysis Agent",
                inspection_result,
                "completed",
                inspection_time
            )
            print(f"✅ API: Inspection analysis completed in {inspection_time:.2f}s")
            
        except Exception as e:
            response.inspection_analysis = create_agent_response(
                "Inspection Analysis Agent",
                f"Error: {str(e)}",
                "failed"
            )
            print(f"❌ API: Inspection analysis failed: {e}")
        
        # Optional delay for demo purposes
        if request.add_delays:
            await asyncio.sleep(2)
        
        # Step 4: Bill Reimbursement Analysis
        print("💰 API: Running bill reimbursement analysis...")
        bill_start = datetime.now()
        
        try:
            bill_result = await orchestrator.execute_bill_reimbursement_analysis(
                request.claim_description,
                request.claim_id
            )
            bill_time = (datetime.now() - bill_start).total_seconds()
            
            response.bill_analysis = create_agent_response(
                "Bill Reimbursement Agent",
                bill_result,
                "completed",
                bill_time
            )
            print(f"✅ API: Bill analysis completed in {bill_time:.2f}s")
            
        except Exception as e:
            response.bill_analysis = create_agent_response(
                "Bill Reimbursement Agent",
                f"Error: {str(e)}",
                "failed"
            )
            print(f"❌ API: Bill analysis failed: {e}")
        
        # Optional delay for demo purposes
        if request.add_delays:
            await asyncio.sleep(1)
        
        # Step 5: Final Recommendation Synthesis
        print("📊 API: Generating final recommendation...")
        final_start = datetime.now()
        
        try:
            # Create claim data object for synthesis
            claim_data = ClaimData(claim_id=request.claim_id)
            if response.policy_basic_details:
                claim_data.basic_policy_details = response.policy_basic_details.response
            if response.policy_analysis:
                claim_data.policy_analysis = response.policy_analysis.response
            if response.inspection_analysis:
                claim_data.inspection_results = response.inspection_analysis.response
            if response.bill_analysis:
                claim_data.bill_analysis = response.bill_analysis.response
            
            final_result = await orchestrator.synthesize_final_recommendation(claim_data)
            final_time = (datetime.now() - final_start).total_seconds()
            
            response.final_recommendation = create_agent_response(
                "Final Recommendation Synthesizer",
                final_result,
                "completed",
                final_time
            )
            print(f"✅ API: Final recommendation completed in {final_time:.2f}s")
            
        except Exception as e:
            response.final_recommendation = create_agent_response(
                "Final Recommendation Synthesizer",
                f"Error: {str(e)}",
                "failed"
            )
            print(f"❌ API: Final recommendation failed: {e}")
        
        # Complete processing
        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()
        
        response.overall_status = "completed"
        response.processing_completed = end_time.isoformat()
        response.total_processing_time_seconds = total_time
        
        # Create summary
        response.summary = {
            "total_agents_processed": 5,
            "successful_agents": sum(1 for agent_resp in [
                response.policy_basic_details,
                response.policy_analysis,
                response.inspection_analysis,
                response.bill_analysis,
                response.final_recommendation
            ] if agent_resp and agent_resp.status == "completed"),
            "failed_agents": sum(1 for agent_resp in [
                response.policy_basic_details,
                response.policy_analysis,
                response.inspection_analysis,
                response.bill_analysis,
                response.final_recommendation
            ] if agent_resp and agent_resp.status == "failed"),
            "total_processing_time": f"{total_time:.2f} seconds",
            "claim_status": "processed"
        }
        
        print(f"✅ API: Claim {request.claim_id} processing completed in {total_time:.2f}s")
        return response
        
    except Exception as e:
        print(f"❌ API: Unexpected error processing claim: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing claim: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "orchestrator_initialized": orchestrator is not None
    }

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Auto Insurance Claim Orchestrator API",
        "version": "1.0.0",
        "endpoints": {
            "process_claim": "/process-claim",
            "health": "/health",
            "docs": "/docs"
        }
    }

if __name__ == "__main__":
    print("🚀 Starting Auto Insurance Claim API Server...")
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
