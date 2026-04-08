"""
Pydantic schemas for credit card fraud detection API.
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class MerchantCategory(str, Enum):
    """Merchant category enumeration."""
    ONLINE_RETAIL = "online_retail"
    ENTERTAINMENT = "entertainment"
    TRAVEL = "travel"
    RESTAURANT = "restaurant"
    GROCERY = "grocery"
    GAS_STATION = "gas_station"
    UTILITIES = "utilities"
    HEALTHCARE = "healthcare"
    EDUCATION = "education"
    OTHER = "other"

class RiskLabel(str, Enum):
    """Risk level enumeration."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class PredictionRequest(BaseModel):
    """Request schema for fraud prediction."""
    
    # Original credit card features
    Time: float = Field(..., ge=0, description="Time in seconds from first transaction")
    V1: float = Field(..., description="PCA component V1")
    V2: float = Field(..., description="PCA component V2")
    V3: float = Field(..., description="PCA component V3")
    V4: float = Field(..., description="PCA component V4")
    V5: float = Field(..., description="PCA component V5")
    V6: float = Field(..., description="PCA component V6")
    V7: float = Field(..., description="PCA component V7")
    V8: float = Field(..., description="PCA component V8")
    V9: float = Field(..., description="PCA component V9")
    V10: float = Field(..., description="PCA component V10")
    V11: float = Field(..., description="PCA component V11")
    V12: float = Field(..., description="PCA component V12")
    V13: float = Field(..., description="PCA component V13")
    V14: float = Field(..., description="PCA component V14")
    V15: float = Field(..., description="PCA component V15")
    V16: float = Field(..., description="PCA component V16")
    V17: float = Field(..., description="PCA component V17")
    V18: float = Field(..., description="PCA component V18")
    V19: float = Field(..., description="PCA component V19")
    V20: float = Field(..., description="PCA component V20")
    V21: float = Field(..., description="PCA component V21")
    V22: float = Field(..., description="PCA component V22")
    V23: float = Field(..., description="PCA component V23")
    V24: float = Field(..., description="PCA component V24")
    V25: float = Field(..., description="PCA component V25")
    V26: float = Field(..., description="PCA component V26")
    V27: float = Field(..., description="PCA component V27")
    V28: float = Field(..., description="PCA component V28")
    Amount: float = Field(..., gt=0, description="Transaction amount in USD")
    
    @field_validator('Amount')
    @classmethod
    def validate_amount(cls, v):
        """Validate transaction amount."""
        if v <= 0:
            raise ValueError('Amount must be greater than 0')
        if v > 100000:  # Reasonable upper limit
            raise ValueError('Amount exceeds reasonable limit')
        return v
    
    
class PredictionResponse(BaseModel):
    """Response schema for fraud prediction."""
    
    risk_score: float = Field(..., ge=0, le=1, description="Fraud risk score (0-1)")
    risk_label: RiskLabel = Field(..., description="Risk level classification")
    confidence: float = Field(..., ge=0, le=1, description="Prediction confidence score")
    model_version: str = Field(..., description="Model version used for prediction")
    prediction_id: str = Field(..., description="Unique prediction identifier")
    timestamp: datetime = Field(..., description="Prediction timestamp")
    
    # Additional metadata
    processing_time_ms: float = Field(..., ge=0, description="Processing time in milliseconds")
    feature_importance: Optional[Dict[str, float]] = Field(None, description="Feature importance scores")
    
    @field_validator('risk_score')
    @classmethod
    def validate_risk_score(cls, v):
        """Validate risk score."""
        if not 0 <= v <= 1:
            raise ValueError('Risk score must be between 0 and 1')
        return v
    
    @field_validator('confidence')
    @classmethod
    def validate_confidence(cls, v):
        """Validate confidence score."""
        if not 0 <= v <= 1:
            raise ValueError('Confidence must be between 0 and 1')
        return v

class BatchPredictionRequest(BaseModel):
    """Request schema for batch predictions."""
    
    transactions: List[PredictionRequest] = Field(..., min_items=1, max_items=100, 
                                                description="List of transactions to score")
    
    @field_validator('transactions')
    @classmethod
    def validate_transactions(cls, v):
        """Validate batch size."""
        if len(v) > 100:
            raise ValueError('Batch size cannot exceed 100 transactions')
        return v

class BatchPredictionResponse(BaseModel):
    """Response schema for batch predictions."""
    
    predictions: List[PredictionResponse] = Field(..., description="List of prediction results")
    batch_id: str = Field(..., description="Unique batch identifier")
    total_predictions: int = Field(..., description="Total number of predictions")
    processing_time_ms: float = Field(..., ge=0, description="Total processing time in milliseconds")
    
    # Summary statistics
    risk_distribution: Dict[str, int] = Field(..., description="Distribution of risk labels")
    avg_risk_score: float = Field(..., ge=0, le=1, description="Average risk score across batch")
    
class HealthResponse(BaseModel):
    """Response schema for health check."""
    
    status: str = Field(..., description="Service health status")
    timestamp: datetime = Field(..., description="Health check timestamp")
    uptime_seconds: float = Field(..., ge=0, description="Service uptime in seconds")
    model_loaded: bool = Field(..., description="Whether model is loaded")
    model_version: Optional[str] = Field(None, description="Current model version")
    
    # Additional health indicators
    memory_usage_mb: float = Field(..., ge=0, description="Memory usage in MB")
    cpu_usage_percent: float = Field(..., ge=0, le=100, description="CPU usage percentage")
    
class ModelInfoResponse(BaseModel):
    """Response schema for model information."""
    
    model_name: str = Field(..., description="Model name")
    model_version: str = Field(..., description="Model version")
    model_stage: str = Field(..., description="Model stage in registry")
    run_id: str = Field(..., description="MLflow run ID")
    
    # Model metadata
    model_type: str = Field(..., description="Model type (e.g., random_forest, xgboost)")
    creation_timestamp: datetime = Field(..., description="Model creation timestamp")
    last_updated_timestamp: datetime = Field(..., description="Model last updated timestamp")
    
    # Performance metrics
    accuracy: Optional[float] = Field(None, ge=0, le=1, description="Model accuracy")
    precision: Optional[float] = Field(None, ge=0, le=1, description="Model precision")
    recall: Optional[float] = Field(None, ge=0, le=1, description="Model recall")
    f1_score: Optional[float] = Field(None, ge=0, le=1, description="Model F1 score")
    roc_auc: Optional[float] = Field(None, ge=0, le=1, description="Model ROC AUC score")
    
    # Feature information
    feature_count: int = Field(..., ge=0, description="Number of features")
    feature_names: List[str] = Field(..., description="List of feature names")
    
class DriftReportResponse(BaseModel):
    """Response schema for drift report."""
    
    report_id: str = Field(..., description="Drift report identifier")
    timestamp: datetime = Field(..., description="Report generation timestamp")
    drift_score: float = Field(..., ge=0, description="Overall drift score")
    
    # Drift details
    feature_drift: Dict[str, float] = Field(..., description="Drift scores by feature")
    prediction_drift: float = Field(..., ge=0, description="Prediction distribution drift")
    
    # Status indicators
    drift_detected: bool = Field(..., description="Whether significant drift was detected")
    alert_threshold: float = Field(..., ge=0, description="Alert threshold for drift")
    
    # Recommendations
    recommendations: List[str] = Field(..., description="Actionable recommendations")
    
class ErrorResponse(BaseModel):
    """Standard error response schema."""
    
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    timestamp: datetime = Field(..., description="Error timestamp")
    request_id: Optional[str] = Field(None, description="Request identifier")
    
class ValidationErrorResponse(BaseModel):
    """Validation error response schema."""
    
    error: str = Field(default="validation_error", description="Error type")
    message: str = Field(..., description="Error message")
    timestamp: datetime = Field(..., description="Error timestamp")
    validation_errors: List[Dict[str, Any]] = Field(..., description="Detailed validation errors")
    request_id: Optional[str] = Field(None, description="Request identifier")

# Utility schemas
class FeatureImportance(BaseModel):
    """Feature importance information."""
    
    feature_name: str = Field(..., description="Feature name")
    importance: float = Field(..., ge=0, description="Feature importance score")
    rank: int = Field(..., ge=1, description="Feature rank by importance")

class ModelMetrics(BaseModel):
    """Model performance metrics."""
    
    accuracy: float = Field(..., ge=0, le=1, description="Accuracy")
    precision: float = Field(..., ge=0, le=1, description="Precision")
    recall: float = Field(..., ge=0, le=1, description="Recall")
    f1_score: float = Field(..., ge=0, le=1, description="F1 score")
    roc_auc: float = Field(..., ge=0, le=1, description="ROC AUC")
    
    # Additional metrics
    confusion_matrix: Optional[List[List[int]]] = Field(None, description="Confusion matrix")
    classification_report: Optional[Dict[str, Any]] = Field(None, description="Classification report")
