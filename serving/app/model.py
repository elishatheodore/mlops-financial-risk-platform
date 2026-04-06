"""
Model loader class for credit card fraud detection with MLflow integration.
"""

import os
import logging
import numpy as np
import pandas as pd
import mlflow
import mlflow.sklearn
from mlflow.tracking import MlflowClient
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
import joblib
from pathlib import Path
import uuid
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ModelLoader:
    """Model loader with MLflow integration for fraud detection."""
    
    def __init__(self):
        self.model = None
        self.model_info = {}
        self.scaler = None
        self.feature_names = []
        self.startup_time = time.time()
        
        # Environment variables
        self.mlflow_tracking_uri = os.getenv('MLFLOW_TRACKING_URI', 'http://localhost:5000')
        self.model_name = os.getenv('MODEL_NAME', 'financial-risk-model')
        
        # Configure MLflow
        mlflow.set_tracking_uri(self.mlflow_tracking_uri)
        self.client = MlflowClient()
        
        logger.info(f" ModelLoader initialized")
        logger.info(f"   • MLflow Tracking URI: {self.mlflow_tracking_uri}")
        logger.info(f"   • Model Name: {self.model_name}")
    
    def load_production_model(self) -> bool:
        """Load the Production model from MLflow Model Registry."""
        logger.info(" Loading Production model from MLflow Registry...")
        
        try:
            # Get the latest Production model version
            model_versions = self.client.search_model_versions(
                filter_string=f"name='{self.model_name}' and stage='Production'"
            )
            
            if not model_versions:
                logger.error(f" No Production model found for '{self.model_name}'")
                return False
            
            # Get the latest Production version
            latest_version = max(model_versions, key=lambda x: int(x.version))
            model_version = latest_version.version
            run_id = latest_version.run_id
            
            logger.info(f" Found Production model version {model_version} from run {run_id}")
            
            # Load model from MLflow
            model_uri = f"models:/{self.model_name}/{model_version}"
            self.model = mlflow.sklearn.load_model(model_uri)
            
            # Load model metadata
            run = self.client.get_run(run_id)
            
            self.model_info = {
                'model_name': self.model_name,
                'model_version': model_version,
                'model_stage': 'Production',
                'run_id': run_id,
                'model_type': run.data.params.get('model_type', 'unknown'),
                'creation_timestamp': datetime.fromtimestamp(run.info.start_time / 1000),
                'last_updated_timestamp': datetime.now(),
                'accuracy': run.data.metrics.get('accuracy'),
                'precision': run.data.metrics.get('precision'),
                'recall': run.data.metrics.get('recall'),
                'f1_score': run.data.metrics.get('f1_score'),
                'roc_auc': run.data.metrics.get('roc_auc'),
                'feature_count': run.data.params.get('features', 'unknown'),
                'n_estimators': run.data.params.get('n_estimators', 'unknown'),
                'max_depth': run.data.params.get('max_depth', 'unknown')
            }
            
            # Load scaler if available
            try:
                # Try to load scaler from the same run
                scaler_artifact_path = self.client.download_artifacts(
                    run_id, 'scaler.pkl', dst_path='/tmp'
                )
                self.scaler = joblib.load('/tmp/scaler.pkl')
                logger.info(" Scaler loaded successfully")
            except Exception as e:
                logger.warning(f" Could not load scaler: {e}")
                # Create a dummy scaler for compatibility
                from sklearn.preprocessing import StandardScaler
                self.scaler = StandardScaler()
            
            # Set feature names (assuming V1-V28 + Amount for credit card fraud)
            self.feature_names = [f'V{i}' for i in range(1, 29)] + ['Amount']
            
            logger.info(" Production model loaded successfully!")
            logger.info(f"   • Model: {self.model_name} v{model_version}")
            logger.info(f"   • Type: {self.model_info['model_type']}")
            logger.info(f"   • ROC AUC: {self.model_info['roc_auc']:.4f}" if self.model_info['roc_auc'] else "   • ROC AUC: N/A")
            
            return True
            
        except Exception as e:
            logger.error(f" Failed to load Production model: {e}")
            return False
    
    def preprocess_input(self, transaction_data: Dict[str, Any]) -> np.ndarray:
        """Preprocess input transaction data for model inference."""
        try:
            # Create feature vector from transaction data
            features = []
            
            # Map merchant category to numeric
            merchant_mapping = {
                'online_retail': 1, 'entertainment': 2, 'travel': 3,
                'restaurant': 4, 'grocery': 5, 'gas_station': 6,
                'utilities': 7, 'healthcare': 8, 'education': 9, 'other': 10
            }
            
            # Core features (V1-V28 would be engineered from the transaction data)
            # For now, we'll use the available features to create a simplified feature set
            
            # Time-based features
            features.append(transaction_data.get('hour_of_day', 0) / 24.0)  # Normalized hour
            features.append(transaction_data.get('day_of_week', 0) / 6.0)   # Normalized day
            
            # Amount features
            amount = transaction_data.get('amount', 0)
            features.append(amount)  # Amount (will be scaled)
            
            # Behavioral features
            features.append(transaction_data.get('transaction_count_24h', 0))
            features.append(transaction_data.get('avg_amount_30d', 0))
            
            # Location features
            features.append(transaction_data.get('distance_from_home', 0))
            features.append(transaction_data.get('distance_from_last_transaction', 0))
            
            # Ratio features
            features.append(transaction_data.get('ratio_to_median_purchase_price', 1.0))
            
            # Binary features
            features.append(1 if transaction_data.get('repeat_retailer', False) else 0)
            features.append(1 if transaction_data.get('used_chip', False) else 0)
            features.append(1 if transaction_data.get('used_pin_number', False) else 0)
            features.append(1 if transaction_data.get('online_order', False) else 0)
            features.append(1 if transaction_data.get('foreign_transaction', False) else 0)
            
            # Merchant category
            merchant_category = transaction_data.get('merchant_category', 'other')
            features.append(merchant_mapping.get(merchant_category, 10))
            
            # Pad or truncate to match expected feature count (30 features: V1-V28 + Amount)
            while len(features) < 30:
                features.append(0.0)  # Pad with zeros
            
            features = features[:30]  # Truncate if too long
            
            # Convert to numpy array and reshape
            feature_vector = np.array(features).reshape(1, -1)
            
            # Scale features if scaler is available
            if self.scaler is not None:
                feature_vector = self.scaler.transform(feature_vector)
            
            logger.debug(f" Preprocessed feature vector shape: {feature_vector.shape}")
            
            return feature_vector
            
        except Exception as e:
            logger.error(f" Failed to preprocess input: {e}")
            raise
    
    def predict(self, transaction_data: Dict[str, Any]) -> Tuple[float, Dict[str, float]]:
        """
        Make prediction on transaction data.
        
        Args:
            transaction_data: Dictionary containing transaction features
            
        Returns:
            Tuple of (risk_score, feature_importance_dict)
        """
        if self.model is None:
            raise ValueError("Model not loaded. Call load_production_model() first.")
        
        try:
            # Preprocess input
            features = self.preprocess_input(transaction_data)
            
            # Make prediction
            prediction_proba = self.model.predict_proba(features)[0]
            risk_score = float(prediction_proba[1])  # Probability of fraud
            
            # Get feature importance if available
            feature_importance = {}
            if hasattr(self.model, 'feature_importances_'):
                importance_scores = self.model.feature_importances_
                for i, (name, score) in enumerate(zip(self.feature_names, importance_scores)):
                    feature_importance[name] = float(score)
            
            logger.debug(f" Prediction completed: risk_score={risk_score:.4f}")
            
            return risk_score, feature_importance
            
        except Exception as e:
            logger.error(f"❌ Prediction failed: {e}")
            raise
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get current model information."""
        if not self.model_info:
            return {
                'model_loaded': False,
                'message': 'No model loaded'
            }
        
        return {
            'model_loaded': True,
            'model_name': self.model_info['model_name'],
            'model_version': self.model_info['model_version'],
            'model_stage': self.model_info['model_stage'],
            'run_id': self.model_info['run_id'],
            'model_type': self.model_info['model_type'],
            'creation_timestamp': self.model_info['creation_timestamp'],
            'last_updated_timestamp': self.model_info['last_updated_timestamp'],
            'accuracy': self.model_info['accuracy'],
            'precision': self.model_info['precision'],
            'recall': self.model_info['recall'],
            'f1_score': self.model_info['f1_score'],
            'roc_auc': self.model_info['roc_auc'],
            'feature_count': len(self.feature_names),
            'feature_names': self.feature_names,
            'startup_time': datetime.fromtimestamp(self.startup_time),
            'uptime_seconds': time.time() - self.startup_time
        }
    
    def classify_risk(self, risk_score: float) -> str:
        """Classify risk score into risk categories."""
        if risk_score < 0.3:
            return "LOW"
        elif risk_score < 0.7:
            return "MEDIUM"
        else:
            return "HIGH"
    
    def is_model_loaded(self) -> bool:
        """Check if model is loaded."""
        return self.model is not None
    
    def reload_model(self) -> bool:
        """Reload the production model."""
        logger.info("🔄 Reloading Production model...")
        self.model = None
        self.model_info = {}
        return self.load_production_model()
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of the model loader."""
        return {
            'model_loaded': self.is_model_loaded(),
            'model_version': self.model_info.get('model_version', 'N/A'),
            'model_stage': self.model_info.get('model_stage', 'N/A'),
            'uptime_seconds': time.time() - self.startup_time,
            'mlflow_tracking_uri': self.mlflow_tracking_uri,
            'model_name': self.model_name,
            'feature_count': len(self.feature_names),
            'last_check': datetime.now()
        }

# Global model loader instance
model_loader = ModelLoader()

def get_model_loader() -> ModelLoader:
    """Get the global model loader instance."""
    return model_loader

def initialize_model() -> bool:
    """Initialize the model loader (called on startup)."""
    logger.info("🚀 Initializing model loader...")
    success = model_loader.load_production_model()
    
    if success:
        logger.info("✅ Model initialization successful")
    else:
        logger.error("❌ Model initialization failed")
    
    return success
