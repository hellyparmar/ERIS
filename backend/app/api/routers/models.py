"""
Enterprise Retail Intelligence System v3.0
MODEL MANAGEMENT ROUTER

Endpoints for model information and retraining.
"""

from fastapi import APIRouter, HTTPException
from app.api.schemas import ModelsListResponse, ModelInfo, RetrainRequest, RetrainResponse, TrainingStatus
from app.api.services.model_service import ModelService
from datetime import datetime
import uuid

router = APIRouter()
model_service = ModelService()

@router.get("/models/list", response_model=ModelsListResponse)
async def list_models():
    """
    List all available ML models with their metrics.
    """
    try:
        models_info = model_service.get_models_info()
        return ModelsListResponse(models=models_info)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/models/retrain", response_model=RetrainResponse)
async def retrain_model(request: RetrainRequest):
    """
    Initiate model retraining process.
    
    Returns a job_id for tracking training progress.
    """
    try:
        if request.model_type not in ["random_forest", "gradient_boosting"]:
            raise HTTPException(
                status_code=400,
                detail="Invalid model_type. Must be 'random_forest' or 'gradient_boosting'"
            )
        
        # Generate job ID
        job_id = str(uuid.uuid4())
        
        # In production, this would queue a background job
        # For now, return pending status
        return RetrainResponse(
            job_id=job_id,
            status="pending",
            message=f"Training job {job_id} queued for {request.model_type}"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models/status/{job_id}", response_model=TrainingStatus)
async def get_training_status(job_id: str):
    """
    Get status of a model training job.
    """
    try:
        # Simulated status (in production, query from job queue/database)
        return TrainingStatus(
            job_id=job_id,
            status="running",
            progress=0.65,
            metrics={"rmse": 0.0185, "mae": 0.0156},
            error=None
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
