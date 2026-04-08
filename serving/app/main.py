"""
FastAPI application for credit card fraud detection model serving.

This module provides a REST API for fraud detection predictions with
comprehensive monitoring, health checks, and drift detection capabilities.

Author: Elisha Theodore
Created: 2024
Note: This was my first production MLOps project - learned a ton about FastAPI async patterns!
"""

import os
import logging
import uuid
import time
import json
import asyncio
from datetime import datetime
from typing import Dict, Any, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import uvicorn

from .model import get_model_loader, initialize_model
from .schemas import (
    PredictionRequest, PredictionResponse, BatchPredictionRequest, BatchPredictionResponse,
    HealthResponse, ModelInfoResponse, DriftReportResponse, ErrorResponse, ValidationErrorResponse
)
from .metrics import get_metrics_collector, track_api_metrics, track_prediction_metrics, metrics_app

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Environment variables
MLFLOW_TRACKING_URI = os.getenv('MLFLOW_TRACKING_URI', 'http://localhost:5000')
MODEL_NAME = os.getenv('MODEL_NAME', 'financial-risk-model')
PORT = int(os.getenv('PORT', 8000))
HOST = os.getenv('HOST', '0.0.0.0')

# Global variables
model_loader = None
metrics_collector = get_metrics_collector()
drift_task = None

# Background task for drift detection
# TODO: Make this configurable - 6 hours felt right for testing but prod might need different timing
async def run_drift_detection_periodically():
    """Run drift detection every 6 hours.
    
    Note: Initially tried 1 hour intervals but it was too noisy for our use case.
    6 hours seems to be a good balance between detection latency and resource usage.
    """
    while True:
        try:
            logger.info("Starting scheduled drift detection...")
            
            # Run drift detector
            import subprocess
            result = subprocess.run([
                "python", 
                "monitoring/drift_detector.py",
                "--mlflow-tracking-uri", MLFLOW_TRACKING_URI,
                "--model-name", MODEL_NAME
            ], capture_output=True, text=True, cwd="../../")
            
            if result.returncode == 0:
                logger.info("Drift detection completed successfully")
                drift_score = result.stdout.strip()
                logger.info(f"Drift score: {drift_score}")
            else:
                logger.error(f"Drift detection failed: {result.stderr}")
                
        except Exception as e:
            logger.error(f"Error in scheduled drift detection: {e}")
        
        # Wait for 6 hours
        await asyncio.sleep(6 * 60 * 60)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global drift_task
    
    # Startup
    logger.info("Starting FastAPI application...")
    
    # Initialize model
    success = initialize_model()
    if not success:
        logger.error("Failed to initialize model - application will not function properly")
    
    # Log startup info
    logger.info(f"MLflow Tracking URI: {MLFLOW_TRACKING_URI}")
    logger.info(f"Model Name: {MODEL_NAME}")
    logger.info(f"Port: {PORT}")
    logger.info(f"Host: {HOST}")
    
    # Log model version if loaded
    if model_loader and model_loader.is_model_loaded():
        model_info = model_loader.get_model_info()
        logger.info(f"Model version loaded: {model_info.get('model_version', 'unknown')}")
        logger.info(f"Model stage: {model_info.get('model_stage', 'unknown')}")
        logger.info(f"Model run ID: {model_info.get('run_id', 'unknown')}")
    else:
        logger.warning("No model loaded at startup")
    
    # Start background drift detection task
    try:
        drift_task = asyncio.create_task(run_drift_detection_periodically())
        logger.info("Background drift detection task started (runs every 6 hours)")
    except Exception as e:
        logger.error(f"Failed to start drift detection task: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down FastAPI application...")
    
    # Cancel drift detection task
    if drift_task:
        drift_task.cancel()
        try:
            await drift_task
        except asyncio.CancelledError:
            logger.info("Drift detection task cancelled")

# Create FastAPI application
app = FastAPI(
    title="Financial Risk Prediction API",
    description="Credit card fraud detection model serving API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Configure appropriately for production
)

# Mount metrics app
app.mount("/metrics", metrics_app)

# Exception handlers
@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle ValueError exceptions."""
    logger.error(f"ValueError: {exc}")
    return JSONResponse(
        status_code=400,
        content=ErrorResponse(
            error="validation_error",
            message=str(exc),
            timestamp=datetime.now(),
            request_id=str(uuid.uuid4())
        ).dict()
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unexpected error: {exc}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="internal_server_error",
            message="An unexpected error occurred",
            timestamp=datetime.now(),
            request_id=str(uuid.uuid4())
        ).dict()
    )

# Health check endpoint
@app.get("/health", response_model=HealthResponse, tags=["Health"])
@track_api_metrics(method="GET")
async def health_check():
    """Health check endpoint."""
    try:
        health_status = model_loader.get_health_status() if model_loader else {
            'model_loaded': False,
            'model_version': 'N/A',
            'model_stage': 'N/A',
            'uptime_seconds': 0,
            'mlflow_tracking_uri': MLFLOW_TRACKING_URI,
            'model_name': MODEL_NAME,
            'feature_count': 0,
            'last_check': datetime.now()
        }
        
        # Update service metrics
        metrics_collector.update_service_metrics()
        
        return HealthResponse(
            status="healthy" if health_status['model_loaded'] else "unhealthy",
            timestamp=datetime.now(),
            uptime_seconds=health_status['uptime_seconds'],
            model_loaded=health_status['model_loaded'],
            model_version=health_status.get('model_version'),
            memory_usage_mb=health_status.get('memory_usage_mb', 0),
            cpu_usage_percent=health_status.get('cpu_usage_percent', 0)
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")

# Model info endpoint
@app.get("/model/info", response_model=ModelInfoResponse, tags=["Model"])
@track_api_metrics(method="GET")
async def get_model_info():
    """Get current model information."""
    try:
        if not model_loader or not model_loader.is_model_loaded():
            raise HTTPException(status_code=503, detail="Model not loaded")
        
        model_info = model_loader.get_model_info()
        
        return ModelInfoResponse(
            model_name=model_info['model_name'],
            model_version=model_info['model_version'],
            model_stage=model_info['model_stage'],
            run_id=model_info['run_id'],
            model_type=model_info['model_type'],
            creation_timestamp=model_info['creation_timestamp'],
            last_updated_timestamp=model_info['last_updated_timestamp'],
            accuracy=model_info.get('accuracy'),
            precision=model_info.get('precision'),
            recall=model_info.get('recall'),
            f1_score=model_info.get('f1_score'),
            roc_auc=model_info.get('roc_auc'),
            feature_count=model_info['feature_count'],
            feature_names=model_info['feature_names']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get model info: {e}")
        raise HTTPException(status_code=500, detail="Failed to get model information")

# Single prediction endpoint
@app.post("/predict", response_model=PredictionResponse, tags=["Prediction"])
@track_api_metrics(method="POST")
@track_prediction_metrics(endpoint="predict")
async def predict_fraud(request: PredictionRequest):
    """Predict fraud risk for a single transaction."""
    try:
        if not model_loader or not model_loader.is_model_loaded():
            raise HTTPException(status_code=503, detail="Model not loaded")
        
        start_time = time.time()
        
        # Convert request to dict
        transaction_data = request.dict()
        
        # Make prediction
        risk_score, feature_importance = model_loader.predict(transaction_data)
        
        # Classify risk
        risk_label = model_loader.classify_risk(risk_score)
        
        # Calculate confidence (simplified - would be based on model's probability distribution)
        confidence = max(risk_score, 1 - risk_score)
        
        # Generate prediction ID
        prediction_id = str(uuid.uuid4())
        
        # Calculate processing time
        processing_time_ms = (time.time() - start_time) * 1000
        
        # Record metrics
        model_version = model_loader.model_info.get('model_version', 'unknown')
        metrics_collector.record_prediction(risk_score, risk_label, model_version)
        
        # Update feature importance metrics
        if feature_importance:
            metrics_collector.update_feature_importance(feature_importance, model_version)
        
        return PredictionResponse(
            risk_score=risk_score,
            risk_label=risk_label,
            confidence=confidence,
            model_version=model_version,
            prediction_id=prediction_id,
            timestamp=datetime.now(),
            processing_time_ms=processing_time_ms,
            feature_importance=feature_importance
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise HTTPException(status_code=500, detail="Prediction failed")

# Batch prediction endpoint
@app.post("/predict/batch", response_model=BatchPredictionResponse, tags=["Prediction"])
@track_api_metrics(method="POST")
@track_prediction_metrics(endpoint="predict/batch")
async def predict_fraud_batch(request: BatchPredictionRequest):
    """Predict fraud risk for multiple transactions."""
    try:
        if not model_loader or not model_loader.is_model_loaded():
            raise HTTPException(status_code=503, detail="Model not loaded")
        
        start_time = time.time()
        predictions = []
        risk_scores = []
        risk_labels = []
        
        # Process each transaction
        for transaction in request.transactions:
            try:
                # Convert to dict
                transaction_data = transaction.dict()
                
                # Make prediction
                risk_score, feature_importance = model_loader.predict(transaction_data)
                
                # Classify risk
                risk_label = model_loader.classify_risk(risk_score)
                
                # Calculate confidence
                confidence = max(risk_score, 1 - risk_score)
                
                # Generate prediction ID
                prediction_id = str(uuid.uuid4())
                
                # Create response
                prediction = PredictionResponse(
                    risk_score=risk_score,
                    risk_label=risk_label,
                    confidence=confidence,
                    model_version=model_loader.model_info.get('model_version', 'unknown'),
                    prediction_id=prediction_id,
                    timestamp=datetime.now(),
                    processing_time_ms=0,  # Will be calculated for batch
                    feature_importance=feature_importance
                )
                
                predictions.append(prediction)
                risk_scores.append(risk_score)
                risk_labels.append(risk_label)
                
            except Exception as e:
                logger.error(f"Failed to process transaction: {e}")
                # Continue processing other transactions
                continue
        
        # Calculate batch statistics
        total_processing_time_ms = (time.time() - start_time) * 1000
        avg_risk_score = sum(risk_scores) / len(risk_scores) if risk_scores else 0
        
        # Risk distribution
        risk_distribution = {'LOW': 0, 'MEDIUM': 0, 'HIGH': 0}
        for label in risk_labels:
            risk_distribution[label] += 1
        
        # Record batch metrics
        model_version = model_loader.model_info.get('model_version', 'unknown')
        metrics_collector.record_batch_prediction(
            len(request.transactions), 
            model_version, 
            total_processing_time_ms / 1000
        )
        
        # Record individual predictions
        for score, label in zip(risk_scores, risk_labels):
            metrics_collector.record_prediction(score, label, model_version)
        
        return BatchPredictionResponse(
            predictions=predictions,
            batch_id=str(uuid.uuid4()),
            total_predictions=len(predictions),
            processing_time_ms=total_processing_time_ms,
            risk_distribution=risk_distribution,
            avg_risk_score=avg_risk_score
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch prediction failed: {e}")
        raise HTTPException(status_code=500, detail="Batch prediction failed")

# Drift report endpoint
@app.get("/drift/report", response_model=DriftReportResponse, tags=["Monitoring"])
@track_api_metrics(method="GET")
async def get_drift_report():
    """Get the latest drift report."""
    try:
        # This would typically load from a drift detection system
        # For now, return a placeholder response
        
        drift_report = DriftReportResponse(
            report_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            drift_score=0.05,  # Placeholder
            feature_drift={
                'V1': 0.02, 'V2': 0.03, 'V3': 0.01, 'Amount': 0.04
            },
            prediction_drift=0.03,
            drift_detected=False,
            alert_threshold=0.15,
            recommendations=[
                "Model performance is stable",
                "Continue monitoring for drift"
            ]
        )
        
        # Update drift metrics
        if model_loader:
            model_version = model_loader.model_info.get('model_version', 'unknown')
            metrics_collector.update_model_drift_score(drift_report.drift_score, model_version)
        
        return drift_report
        
    except Exception as e:
        logger.error(f"Failed to get drift report: {e}")
        raise HTTPException(status_code=500, detail="Failed to get drift report")

# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    return {
        "message": "Financial Risk Prediction API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "metrics": "/metrics"
    }

# Model reload endpoint (for admin use)
@app.post("/model/reload", tags=["Admin"])
@track_api_metrics(method="POST")
async def reload_model():
    """Reload the model from MLflow registry."""
    try:
        if not model_loader:
            raise HTTPException(status_code=503, detail="Model loader not initialized")
        
        # Reload model
        success = model_loader.reload_model()
        
        if success:
            return {
                "message": "Model reloaded successfully",
                "timestamp": datetime.now(),
                "model_version": model_loader.model_info.get('model_version', 'unknown')
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to reload model")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Model reload failed: {e}")
        raise HTTPException(status_code=500, detail="Model reload failed")

# Configuration endpoint
@app.get("/config", tags=["System"])
@track_api_metrics(method="GET")
async def get_config():
    """Get application configuration."""
    return {
        "mlflow_tracking_uri": MLFLOW_TRACKING_URI,
        "model_name": MODEL_NAME,
        "port": PORT,
        "host": HOST,
        "model_loaded": model_loader.is_model_loaded() if model_loader else False,
        "model_version": model_loader.model_info.get('model_version') if model_loader else None
    }

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    return app

if __name__ == "__main__":
    # Run the application
    uvicorn.run(
        "main:app",
        host=HOST,
        port=PORT,
        reload=True,
        log_level="info",
        access_log=True
    )
