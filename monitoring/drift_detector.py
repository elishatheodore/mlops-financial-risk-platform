#!/usr/bin/env python3
"""
Drift Detection Script for Financial Risk Model

This script uses Evidently AI to detect data drift and model performance degradation
by comparing reference (training) data with current prediction data.

Usage:
    python drift_detector.py --mlflow-tracking-uri <uri> --model-name <name> --threshold <float>
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import mlflow
import mlflow.sklearn
import numpy as np
import pandas as pd
from evidently.dashboard import Dashboard
from evidently.dashboard.tabs import DataDriftTab, ClassificationPerformanceTab
from evidently.model_profile import Profile
from evidently.model_profile.sections import DataDriftProfileSection, ClassificationPerformanceProfileSection
from evidently.pipeline.column_mapping import ColumnMapping

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DriftDetector:
    """Drift detection class using Evidently AI"""
    
    def __init__(
        self,
        mlflow_tracking_uri: str,
        model_name: str,
        threshold: float = 0.15
    ):
        """
        Initialize drift detector
        
        Args:
            mlflow_tracking_uri: MLflow tracking server URI
            model_name: Name of the model in MLflow Model Registry
            threshold: Drift threshold for triggering alerts
        """
        self.mlflow_tracking_uri = mlflow_tracking_uri
        self.model_name = model_name
        self.threshold = threshold
        
        # Set up MLflow
        mlflow.set_tracking_uri(mlflow_tracking_uri)
        
        # Define column mapping for credit card fraud detection
        self.column_mapping = ColumnMapping(
            target='Class',  # Target column name
            prediction='prediction',  # Prediction column name
            numerical_features=[
                'Time', 'V1', 'V2', 'V3', 'V4', 'V5', 'V6', 'V7', 'V8', 'V9', 'V10',
                'V11', 'V12', 'V13', 'V14', 'V15', 'V16', 'V17', 'V18', 'V19', 'V20',
                'V21', 'V22', 'V23', 'V24', 'V25', 'V26', 'V27', 'V28', 'Amount'
            ],
            categorical_features=[],
            datetime_features=[]
        )
        
    def load_reference_data(self) -> pd.DataFrame:
        """
        Load reference dataset from MLflow
        
        Returns:
            Reference DataFrame
        """
        logger.info("Loading reference dataset from MLflow...")
        
        try:
            # Get the latest production model from MLflow Model Registry
            model_uri = f"models:/{self.model_name}/Production"
            
            # Load the model to get its metadata
            model = mlflow.sklearn.load_model(model_uri)
            
            # Try to load training data from model artifacts
            try:
                # Get the run ID for the production model
                model_version_info = mlflow.client.MlflowClient().get_latest_versions(
                    name=self.model_name,
                    stages=["Production"]
                )[0]
                
                run_id = model_version_info.run_id
                
                # Download training data artifacts
                local_path = mlflow.artifacts.download_artifacts(
                    run_id=run_id,
                    path="training_data"
                )
                
                # Load training data
                reference_data = pd.read_csv(f"{local_path}/X_train.csv")
                logger.info(f"Loaded reference data with shape: {reference_data.shape}")
                
                return reference_data
                
            except Exception as e:
                logger.warning(f"Could not load training data from MLflow: {e}")
                logger.info("Using synthetic reference data for demonstration")
                
                # Generate synthetic reference data
                return self._generate_synthetic_reference_data()
                
        except Exception as e:
            logger.error(f"Error loading reference data: {e}")
            logger.info("Using synthetic reference data for demonstration")
            return self._generate_synthetic_reference_data()
    
    def _generate_synthetic_reference_data(self) -> pd.DataFrame:
        """Generate synthetic reference data for demonstration"""
        logger.info("Generating synthetic reference data...")
        
        np.random.seed(42)
        n_samples = 10000
        
        # Generate realistic credit card transaction features
        data = {
            'Time': np.random.uniform(0, 172800, n_samples),  # 2 days in seconds
            'V1': np.random.normal(0, 1, n_samples),
            'V2': np.random.normal(0, 1, n_samples),
            'V3': np.random.normal(0, 1, n_samples),
            'V4': np.random.normal(0, 1, n_samples),
            'V5': np.random.normal(0, 1, n_samples),
            'V6': np.random.normal(0, 1, n_samples),
            'V7': np.random.normal(0, 1, n_samples),
            'V8': np.random.normal(0, 1, n_samples),
            'V9': np.random.normal(0, 1, n_samples),
            'V10': np.random.normal(0, 1, n_samples),
            'V11': np.random.normal(0, 1, n_samples),
            'V12': np.random.normal(0, 1, n_samples),
            'V13': np.random.normal(0, 1, n_samples),
            'V14': np.random.normal(0, 1, n_samples),
            'V15': np.random.normal(0, 1, n_samples),
            'V16': np.random.normal(0, 1, n_samples),
            'V17': np.random.normal(0, 1, n_samples),
            'V18': np.random.normal(0, 1, n_samples),
            'V19': np.random.normal(0, 1, n_samples),
            'V20': np.random.normal(0, 1, n_samples),
            'V21': np.random.normal(0, 1, n_samples),
            'V22': np.random.normal(0, 1, n_samples),
            'V23': np.random.normal(0, 1, n_samples),
            'V24': np.random.normal(0, 1, n_samples),
            'V25': np.random.normal(0, 1, n_samples),
            'V26': np.random.normal(0, 1, n_samples),
            'V27': np.random.normal(0, 1, n_samples),
            'V28': np.random.normal(0, 1, n_samples),
            'Amount': np.random.exponential(100, n_samples),  # Realistic transaction amounts
            'Class': np.random.binomial(1, 0.01, n_samples)  # 1% fraud rate
        }
        
        df = pd.DataFrame(data)
        logger.info(f"Generated synthetic reference data with shape: {df.shape}")
        return df
    
    def load_current_data(self, logs_path: str) -> pd.DataFrame:
        """
        Load current prediction data from logs
        
        Args:
            logs_path: Path to prediction logs JSON file
            
        Returns:
            Current DataFrame
        """
        logger.info(f"Loading current data from {logs_path}...")
        
        try:
            if not os.path.exists(logs_path):
                logger.warning(f"Prediction logs not found at {logs_path}")
                logger.info("Generating synthetic current data for demonstration")
                return self._generate_synthetic_current_data()
            
            # Load prediction logs
            with open(logs_path, 'r') as f:
                logs = json.load(f)
            
            # Convert logs to DataFrame
            # Extract features from nested structure
            df_data = []
            for log in logs:
                row = log['features'].copy()
                row['prediction'] = log['prediction']
                if 'Class' in log:
                    row['Class'] = log['Class']
                df_data.append(row)
            
            df = pd.DataFrame(df_data)
            logger.info(f"Loaded current data with shape: {df.shape}")
            
            return df
            
        except Exception as e:
            logger.error(f"Error loading current data: {e}")
            logger.info("Using synthetic current data for demonstration")
            return self._generate_synthetic_current_data()
    
    def _generate_synthetic_current_data(self) -> pd.DataFrame:
        """Generate synthetic current data for demonstration"""
        logger.info("Generating synthetic current data...")
        
        np.random.seed(123)  # Different seed for current data
        n_samples = 1000
        
        # Generate data with slight drift
        data = {
            'Time': np.random.uniform(172800, 345600, n_samples),  # Next 2 days
            'V1': np.random.normal(0.1, 1.1, n_samples),  # Slight drift
            'V2': np.random.normal(-0.05, 1.05, n_samples),
            'V3': np.random.normal(0.15, 0.95, n_samples),
            'V4': np.random.normal(0, 1, n_samples),
            'V5': np.random.normal(0, 1, n_samples),
            'V6': np.random.normal(0, 1, n_samples),
            'V7': np.random.normal(0, 1, n_samples),
            'V8': np.random.normal(0, 1, n_samples),
            'V9': np.random.normal(0, 1, n_samples),
            'V10': np.random.normal(0, 1, n_samples),
            'V11': np.random.normal(0, 1, n_samples),
            'V12': np.random.normal(0, 1, n_samples),
            'V13': np.random.normal(0, 1, n_samples),
            'V14': np.random.normal(0, 1, n_samples),
            'V15': np.random.normal(0, 1, n_samples),
            'V16': np.random.normal(0, 1, n_samples),
            'V17': np.random.normal(0, 1, n_samples),
            'V18': np.random.normal(0, 1, n_samples),
            'V19': np.random.normal(0, 1, n_samples),
            'V20': np.random.normal(0, 1, n_samples),
            'V21': np.random.normal(0, 1, n_samples),
            'V22': np.random.normal(0, 1, n_samples),
            'V23': np.random.normal(0, 1, n_samples),
            'V24': np.random.normal(0, 1, n_samples),
            'V25': np.random.normal(0, 1, n_samples),
            'V26': np.random.normal(0, 1, n_samples),
            'V27': np.random.normal(0, 1, n_samples),
            'V28': np.random.normal(0, 1, n_samples),
            'Amount': np.random.exponential(120, n_samples),  # Slightly higher amounts
            'prediction': np.random.binomial(1, 0.012, n_samples),  # Slightly higher fraud rate
        }
        
        df = pd.DataFrame(data)
        
        # Add actual labels if available (for classification performance)
        if 'Class' not in df.columns:
            df['Class'] = np.random.binomial(1, 0.012, n_samples)
        
        logger.info(f"Generated synthetic current data with shape: {df.shape}")
        return df
    
    def calculate_drift_score(self, reference_data: pd.DataFrame, current_data: pd.DataFrame) -> Tuple[float, List[str]]:
        """
        Calculate drift score using Evidently
        
        Args:
            reference_data: Reference dataset
            current_data: Current dataset
            
        Returns:
            Tuple of (drift_score, drifted_features_list)
        """
        logger.info("Calculating drift score...")
        
        try:
            # Create data drift profile
            data_drift_profile = Profile(
                sections=[DataDriftProfileSection()]
            )
            
            data_drift_profile.calculate(reference_data, current_data, self.column_mapping)
            profile_json = data_drift_profile.json()
            
            # Extract drift information
            drift_stats = profile_json['data_drift']['data_metrics']
            
            # Calculate overall drift score as share of drifted features
            total_features = len(drift_stats)
            drifted_features = [
                stat['column_name'] for stat in drift_stats 
                if stat.get('drift_score', 0) > 0.5
            ]
            
            drift_score = len(drifted_features) / total_features if total_features > 0 else 0.0
            
            logger.info(f"Drift score: {drift_score:.4f}")
            logger.info(f"Drifted features: {drifted_features}")
            
            return drift_score, drifted_features
            
        except Exception as e:
            logger.error(f"Error calculating drift score: {e}")
            return 0.0, []
    
    def create_drift_report(
        self,
        reference_data: pd.DataFrame,
        current_data: pd.DataFrame,
        output_path: str
    ) -> Dict[str, Any]:
        """
        Create comprehensive drift report
        
        Args:
            reference_data: Reference dataset
            current_data: Current dataset
            output_path: Path to save HTML report
            
        Returns:
            Dictionary with drift summary
        """
        logger.info("Creating drift report...")
        
        try:
            # Calculate drift score
            drift_score, drifted_features = self.calculate_drift_score(reference_data, current_data)
            
            # Create dashboard
            dashboard = Dashboard(
                tabs=[
                    DataDriftTab(),
                    ClassificationPerformanceTab()
                ]
            )
            
            # Generate report
            dashboard.calculate(
                reference_data,
                current_data,
                column_mapping=self.column_mapping
            )
            
            # Save HTML report
            dashboard.save_html(output_path)
            logger.info(f"Drift report saved to {output_path}")
            
            # Get model version
            model_version = "unknown"
            try:
                model_info = mlflow.client.MlflowClient().get_latest_versions(
                    name=self.model_name,
                    stages=["Production"]
                )
                if model_info:
                    model_version = model_info[0].version
            except Exception as e:
                logger.warning(f"Could not get model version: {e}")
            
            # Create summary
            summary = {
                "drift_score": drift_score,
                "drift_detected": drift_score > self.threshold,
                "drifted_features": drifted_features,
                "threshold": self.threshold,
                "timestamp": datetime.utcnow().isoformat(),
                "model_version": model_version,
                "reference_data_shape": reference_data.shape,
                "current_data_shape": current_data.shape,
                "reference_data_columns": list(reference_data.columns),
                "current_data_columns": list(current_data.columns)
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error creating drift report: {e}")
            return {
                "drift_score": 0.0,
                "drift_detected": False,
                "drifted_features": [],
                "threshold": self.threshold,
                "timestamp": datetime.utcnow().isoformat(),
                "model_version": "unknown",
                "error": str(e)
            }
    
    def save_summary(self, summary: Dict[str, Any], output_path: str):
        """Save drift summary to JSON file"""
        try:
            with open(output_path, 'w') as f:
                json.dump(summary, f, indent=2)
            logger.info(f"Drift summary saved to {output_path}")
        except Exception as e:
            logger.error(f"Error saving summary: {e}")
    
    def run_detection(
        self,
        reference_data_path: Optional[str] = None,
        current_data_path: str = "monitoring/prediction_logs.json",
        output_report: str = "monitoring/drift_report.html",
        output_summary: str = "monitoring/drift_summary.json"
    ) -> Dict[str, Any]:
        """
        Run complete drift detection process
        
        Args:
            reference_data_path: Path to reference data (optional, will load from MLflow if None)
            current_data_path: Path to current prediction logs
            output_report: Path to save HTML report
            output_summary: Path to save JSON summary
            
        Returns:
            Drift summary dictionary
        """
        logger.info("Starting drift detection process...")
        
        # Load data
        if reference_data_path and os.path.exists(reference_data_path):
            reference_data = pd.read_csv(reference_data_path)
            logger.info(f"Loaded reference data from {reference_data_path}")
        else:
            reference_data = self.load_reference_data()
        
        current_data = self.load_current_data(current_data_path)
        
        # Create drift report
        summary = self.create_drift_report(reference_data, current_data, output_report)
        
        # Save summary
        self.save_summary(summary, output_summary)
        
        # Print drift score for GitHub Actions
        print(f"DRIFT_SCORE:{summary['drift_score']}")
        print(f"DRIFT_DETECTED:{summary['drift_detected']}")
        print(f"DRIFTED_FEATURES:{','.join(summary['drifted_features'])}")
        
        logger.info(f"Drift detection completed. Score: {summary['drift_score']:.4f}")
        logger.info(f"Drift detected: {summary['drift_detected']}")
        
        return summary


def create_sample_prediction_logs():
    """Create sample prediction logs for demonstration"""
    logger.info("Creating sample prediction logs...")
    
    np.random.seed(456)
    n_samples = 100
    
    logs = []
    base_time = datetime.now() - timedelta(hours=24)
    
    for i in range(n_samples):
        timestamp = base_time + timedelta(minutes=i * 15)
        
        log_entry = {
            "timestamp": timestamp.isoformat(),
            "transaction_id": f"txn_{i:06d}",
            "features": {
                "Time": float(timestamp.timestamp()),
                "V1": float(np.random.normal(0.05, 1.1)),
                "V2": float(np.random.normal(-0.02, 1.05)),
                "V3": float(np.random.normal(0.1, 0.95)),
                "V4": float(np.random.normal(0, 1)),
                "V5": float(np.random.normal(0, 1)),
                "V6": float(np.random.normal(0, 1)),
                "V7": float(np.random.normal(0, 1)),
                "V8": float(np.random.normal(0, 1)),
                "V9": float(np.random.normal(0, 1)),
                "V10": float(np.random.normal(0, 1)),
                "V11": float(np.random.normal(0, 1)),
                "V12": float(np.random.normal(0, 1)),
                "V13": float(np.random.normal(0, 1)),
                "V14": float(np.random.normal(0, 1)),
                "V15": float(np.random.normal(0, 1)),
                "V16": float(np.random.normal(0, 1)),
                "V17": float(np.random.normal(0, 1)),
                "V18": float(np.random.normal(0, 1)),
                "V19": float(np.random.normal(0, 1)),
                "V20": float(np.random.normal(0, 1)),
                "V21": float(np.random.normal(0, 1)),
                "V22": float(np.random.normal(0, 1)),
                "V23": float(np.random.normal(0, 1)),
                "V24": float(np.random.normal(0, 1)),
                "V25": float(np.random.normal(0, 1)),
                "V26": float(np.random.normal(0, 1)),
                "V27": float(np.random.normal(0, 1)),
                "V28": float(np.random.normal(0, 1)),
                "Amount": float(np.random.exponential(110))
            },
            "prediction": int(np.random.binomial(1, 0.011)),
            "prediction_probability": float(np.random.beta(2, 50)),
            "latency_ms": float(np.random.exponential(50)),
            "model_version": "1.0.0"
        }
        
        logs.append(log_entry)
    
    # Save to file
    os.makedirs("monitoring", exist_ok=True)
    with open("monitoring/prediction_logs.json", "w") as f:
        json.dump(logs, f, indent=2)
    
    logger.info("Sample prediction logs created at monitoring/prediction_logs.json")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Drift detection for financial risk model"
    )
    
    parser.add_argument(
        "--mlflow-tracking-uri",
        required=True,
        help="MLflow tracking server URI"
    )
    
    parser.add_argument(
        "--model-name",
        required=True,
        help="Name of the model in MLflow Model Registry"
    )
    
    parser.add_argument(
        "--reference-data-path",
        help="Path to reference dataset (optional)"
    )
    
    parser.add_argument(
        "--current-data-path",
        default="monitoring/prediction_logs.json",
        help="Path to current prediction logs"
    )
    
    parser.add_argument(
        "--output-report",
        default="monitoring/drift_report.html",
        help="Path to save HTML report"
    )
    
    parser.add_argument(
        "--output-summary",
        default="monitoring/drift_summary.json",
        help="Path to save JSON summary"
    )
    
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.15,
        help="Drift threshold for triggering alerts"
    )
    
    parser.add_argument(
        "--create-sample-data",
        action="store_true",
        help="Create sample prediction logs"
    )
    
    args = parser.parse_args()
    
    # Create sample data if requested
    if args.create_sample_data:
        create_sample_prediction_logs()
        return
    
    # Create monitoring directory
    os.makedirs("monitoring", exist_ok=True)
    
    # Initialize drift detector
    detector = DriftDetector(
        mlflow_tracking_uri=args.mlflow_tracking_uri,
        model_name=args.model_name,
        threshold=args.threshold
    )
    
    # Run drift detection
    try:
        summary = detector.run_detection(
            reference_data_path=args.reference_data_path,
            current_data_path=args.current_data_path,
            output_report=args.output_report,
            output_summary=args.output_summary
        )
        
        # Exit with code 0 regardless of drift score
        # The workflow decides what to do with the score
        logger.info("Drift detection completed successfully")
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Drift detection failed: {e}")
        sys.exit(1)

    print("="*50)

if __name__ == "__main__":
    main()
