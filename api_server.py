"""
FastAPI server for MediGuard AI Frontend
Provides REST API endpoints for the Next.js frontend
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import json
import sys
import os

# Add parent directory to path to import main
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import (
    analyze_patient,
    analyze_agent1_only,
    get_sample_patient_ids,
    fetch_patient_data
)

app = FastAPI(title="MediGuard AI API", version="1.0.0")

# CORS middleware for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PatientAnalysisRequest(BaseModel):
    patient_id: str

class AnalysisResponse(BaseModel):
    identity: Optional[dict] = None
    billing: Optional[dict] = None
    discharge: Optional[dict] = None
    final: Optional[dict] = None

@app.get("/")
async def root():
    return {"message": "MediGuard AI API", "version": "1.0.0"}

@app.get("/api/sample-ids")
async def get_sample_ids(limit: int = 10):
    """Get sample patient IDs for testing"""
    try:
        ids = get_sample_patient_ids(limit)
        return {"ids": ids}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze_patient_endpoint(request: PatientAnalysisRequest):
    """Analyze a patient through all agents"""
    try:
        # Validate patient exists
        try:
            fetch_patient_data(request.patient_id)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        
        # Run full analysis - get the full workflow state, not just final
        workflow_result = analyze_patient(request.patient_id)
        
        # Extract results from workflow state
        identity_result = workflow_result.get("identity", {})
        billing_result = workflow_result.get("billing", {})
        discharge_result = workflow_result.get("discharge", {})
        final_result = workflow_result.get("final", {})
        
        # Structure response to match frontend expectations
        response = AnalysisResponse(
            identity={
                "fraud_risk_score": identity_result.get("fraud_risk_score", 0),
                "identity_misuse_flag": identity_result.get("identity_misuse_flag", False),
                "reasons": identity_result.get("reasons", [])
            } if identity_result else None,
            billing={
                "billing_fraud_score": billing_result.get("billing_fraud_score", billing_result.get("billing_risk_score", 0)),
                "unnecessary_procedure_flag": billing_result.get("unnecessary_procedure_flag", False),
                "billing_flags": billing_result.get("billing_flags", billing_result.get("suspicious_items", [])),
                "billing_explanation": billing_result.get("billing_explanation", billing_result.get("explanations", ""))
            } if billing_result else None,
            discharge={
                "discharge_ready": discharge_result.get("discharge_ready", discharge_result.get("discharge_ready_flag", False)),
                "blockers": discharge_result.get("blockers", []),
                "delay_hours": discharge_result.get("delay_hours", 0),
                "priority_level": discharge_result.get("priority_level", "medium")
            } if discharge_result else None,
            final=final_result if final_result else {}
        )
        
        return response
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = f"Analysis error: {str(e)}\n{traceback.format_exc()}"
        raise HTTPException(status_code=500, detail=error_detail)

@app.post("/api/analyze/agent1")
async def analyze_agent1_only_endpoint(request: PatientAnalysisRequest):
    """Analyze a patient using only Agent 1"""
    try:
        result = analyze_agent1_only(request.patient_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

