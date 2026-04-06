"""
Model evaluation and registry promotion script for credit card fraud detection.
"""

import argparse
import json
import sys
import logging
from pathlib import Path
import pandas as pd
import mlflow
import mlflow.sklearn
from mlflow.tracking import MlflowClient
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ModelEvaluator:
    """Model evaluator with MLflow integration and registry promotion."""
    
    def __init__(self):
        self.client = MlflowClient()
        self.processed_data_dir = Path('../data/processed')
        self.model_name = "financial-risk-model"
        
    def load_test_data(self):
        """Load test data for evaluation."""
        logger.info("📂 Loading test data...")
        
        try:
            X_test = np.load(self.processed_data_dir / 'X_test.npy')
            y_test = np.load(self.processed_data_dir / 'y_test.npy')
            
            logger.info(f"✅ Test data loaded: X_test {X_test.shape}, y_test {y_test.shape}")
            return X_test, y_test
            
        except FileNotFoundError as e:
            logger.error(f"❌ Test data not found: {e}")
            logger.info("📝 Please run feature_engineering.py first to generate processed data")
            raise
        except Exception as e:
            logger.error(f"❌ Error loading test data: {e}")
            raise
    
    def get_experiment_runs(self, experiment_name: str):
        """Get all runs for a given experiment."""
        logger.info(f"🔍 Querying MLflow for experiment: {experiment_name}")
        
        try:
            # Get experiment
            experiment = mlflow.get_experiment_by_name(experiment_name)
            if not experiment:
                raise ValueError(f"Experiment '{experiment_name}' not found")
            
            # Get all runs for the experiment
            runs = self.client.search_runs(
                experiment_ids=[experiment.experiment_id],
                order_by=["metrics.roc_auc DESC"]
            )
            
            logger.info(f"✅ Found {len(runs)} runs in experiment")
            return runs
            
        except Exception as e:
            logger.error(f"❌ Error querying MLflow: {e}")
            raise
    
    def evaluate_single_run(self, run, X_test, y_test):
        """Evaluate a single MLflow run."""
        logger.info(f"📊 Evaluating run: {run.info.run_id}")
        
        try:
            # Load model from run
            model_uri = f"runs:/{run.info.run_id}/fraud_detection_model"
            model = mlflow.sklearn.load_model(model_uri)
            
            # Make predictions
            y_pred = model.predict(X_test)
            y_pred_proba = model.predict_proba(X_test)[:, 1]
            
            # Calculate metrics
            from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
            
            metrics = {
                'accuracy': accuracy_score(y_test, y_pred),
                'precision': precision_score(y_test, y_pred),
                'recall': recall_score(y_test, y_pred),
                'f1_score': f1_score(y_test, y_pred),
                'roc_auc': roc_auc_score(y_test, y_pred_proba)
            }
            
            # Get run parameters
            params = run.data.params or {}
            
            return {
                'run_id': run.info.run_id,
                'run_name': run.info.run_name,
                'status': run.info.status,
                'start_time': run.info.start_time,
                'end_time': run.info.end_time,
                'metrics': metrics,
                'logged_metrics': run.data.metrics or {},
                'params': params
            }
            
        except Exception as e:
            logger.error(f"❌ Error evaluating run {run.info.run_id}: {e}")
            return None
    
    def find_best_run(self, runs, X_test, y_test):
        """Find the best run based on ROC AUC score."""
        logger.info("🏆 Finding best run based on ROC AUC...")
        
        evaluated_runs = []
        
        for run in runs:
            evaluation = self.evaluate_single_run(run, X_test, y_test)
            if evaluation:
                evaluated_runs.append(evaluation)
        
        if not evaluated_runs:
            raise ValueError("No valid runs found for evaluation")
        
        # Sort by ROC AUC (descending)
        best_run = max(evaluated_runs, key=lambda x: x['metrics']['roc_auc'])
        
        logger.info(f"✅ Best run found: {best_run['run_id']} with ROC AUC: {best_run['metrics']['roc_auc']:.4f}")
        
        return best_run, evaluated_runs
    
    def check_thresholds(self, best_run, accuracy_threshold: float, auc_threshold: float):
        """Check if best run meets quality thresholds."""
        logger.info("🎯 Checking quality thresholds...")
        
        accuracy = best_run['metrics']['accuracy']
        roc_auc = best_run['metrics']['roc_auc']
        
        logger.info(f"   • Model Accuracy: {accuracy:.4f} (threshold: {accuracy_threshold:.4f})")
        logger.info(f"   • Model ROC AUC: {roc_auc:.4f} (threshold: {auc_threshold:.4f})")
        
        accuracy_pass = accuracy >= accuracy_threshold
        auc_pass = roc_auc >= auc_threshold
        
        logger.info(f"   • Accuracy threshold: {'✅ PASS' if accuracy_pass else '❌ FAIL'}")
        logger.info(f"   • ROC AUC threshold: {'✅ PASS' if auc_pass else '❌ FAIL'}")
        
        return accuracy_pass and auc_pass
    
    def promote_model_to_registry(self, run_id: str, version: str):
        """Promote model to MLflow Model Registry."""
        logger.info(f"🚀 Promoting model {run_id} to registry...")
        
        try:
            # Register model version
            model_version = mlflow.register_model(
                model_uri=f"runs:/{run_id}/fraud_detection_model",
                name=self.model_name,
                tags={"environment": "production", "promoted_by": "evaluate_script"}
            )
            
            # Transition to Production stage
            self.client.transition_model_version_stage(
                name=self.model_name,
                version=version,
                stage="Production",
                archive_existing_versions=True
            )
            
            logger.info(f"✅ Model promoted to Production! Version: {version}")
            return version
            
        except Exception as e:
            logger.error(f"❌ Error promoting model: {e}")
            raise
    
    def archive_previous_production_models(self, current_version: str):
        """Archive previous Production models."""
        logger.info("📦 Archiving previous Production models...")
        
        try:
            # Get all versions of the model
            model_versions = self.client.search_model_versions(f"name='{self.model_name}'")
            
            for model_version in model_versions:
                if (model_version.version != int(current_version) and 
                    model_version.current_stage == "Production"):
                    
                    # Archive old production version
                    self.client.transition_model_version_stage(
                        name=self.model_name,
                        version=model_version.version,
                        stage="Archived"
                    )
                    logger.info(f"   • Archived version {model_version.version}")
                    
        except Exception as e:
            logger.warning(f"⚠️ Could not archive previous models: {e}")
    
    def save_comparison_report(self, evaluated_runs: list, best_run: dict, output_path: str):
        """Save detailed comparison report as JSON."""
        logger.info("💾 Saving comparison report...")
        
        report = {
            'evaluation_timestamp': datetime.utcnow().isoformat(),
            'total_runs_evaluated': len(evaluated_runs),
            'model_name': self.model_name,
            'best_run': {
                'run_id': best_run['run_id'],
                'run_name': best_run['run_name'],
                'metrics': best_run['metrics'],
                'params': best_run['params']
            },
            'all_runs': evaluated_runs,
            'ranking': sorted(
                evaluated_runs, 
                key=lambda x: x['metrics']['roc_auc'], 
                reverse=True
            )
        }
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"✅ Comparison report saved to {output_path}")
        return report
    
    def print_promotion_summary(self, best_run: dict, version: str):
        """Print promotion summary."""
        logger.info("=" * 80)
        logger.info("🎉 MODEL PROMOTION SUCCESSFUL!")
        logger.info("=" * 80)
        logger.info(f"📝 MLflow Run ID: {best_run['run_id']}")
        logger.info(f"📝 Model Version: {version}")
        logger.info(f"📝 Model Name: {self.model_name}")
        logger.info(f"📝 Stage: Production")
        logger.info(f"📊 Final Metrics:")
        logger.info(f"   • Accuracy: {best_run['metrics']['accuracy']:.4f}")
        logger.info(f"   • Precision: {best_run['metrics']['precision']:.4f}")
        logger.info(f"   • Recall: {best_run['metrics']['recall']:.4f}")
        logger.info(f"   • F1 Score: {best_run['metrics']['f1_score']:.4f}")
        logger.info(f"   • ROC AUC: {best_run['metrics']['roc_auc']:.4f}")
        logger.info("=" * 80)
    
    def print_rejection_summary(self, best_run: dict, accuracy_threshold: float, auc_threshold: float):
        """Print rejection summary and exit with code 1."""
        logger.info("=" * 80)
        logger.info("❌ MODEL REJECTED!")
        logger.info("=" * 80)
        logger.info(f"📝 Best Run ID: {best_run['run_id']}")
        logger.info(f"📊 Best Metrics:")
        logger.info(f"   • Accuracy: {best_run['metrics']['accuracy']:.4f} (threshold: {accuracy_threshold:.4f})")
        logger.info(f"   • ROC AUC: {best_run['metrics']['roc_auc']:.4f} (threshold: {auc_threshold:.4f})")
        logger.info(f"📋 Thresholds Not Met:")
        if best_run['metrics']['accuracy'] < accuracy_threshold:
            logger.info(f"   • Accuracy: {best_run['metrics']['accuracy']:.4f} < {accuracy_threshold:.4f}")
        if best_run['metrics']['roc_auc'] < auc_threshold:
            logger.info(f"   • ROC AUC: {best_run['metrics']['roc_auc']:.4f} < {auc_threshold:.4f}")
        logger.info("=" * 80)
    
    def run_evaluation_pipeline(self, experiment_name: str, accuracy_threshold: float, auc_threshold: float):
        """Run complete evaluation pipeline."""
        logger.info("🚀 Starting model evaluation pipeline...")
        
        try:
            # Load test data
            X_test, y_test = self.load_test_data()
            
            # Get experiment runs
            runs = self.get_experiment_runs(experiment_name)
            
            if not runs:
                logger.error(f"❌ No runs found for experiment: {experiment_name}")
                return False
            
            # Find best run
            best_run, evaluated_runs = self.find_best_run(runs, X_test, y_test)
            
            # Check thresholds
            thresholds_met = self.check_thresholds(best_run, accuracy_threshold, auc_threshold)
            
            # Save comparison report
            report_path = self.processed_data_dir / 'evaluation_report.json'
            self.save_comparison_report(evaluated_runs, best_run, report_path)
            
            if thresholds_met:
                # Promote model to registry
                version = self.promote_model_to_registry(best_run['run_id'], "1")
                
                # Archive previous production models
                self.archive_previous_production_models(version)
                
                # Print success summary
                self.print_promotion_summary(best_run, version)
                return True
            else:
                # Print rejection summary and exit with code 1
                self.print_rejection_summary(best_run, accuracy_threshold, auc_threshold)
                return False
                
        except Exception as e:
            logger.error(f"❌ Evaluation pipeline failed: {e}")
            raise

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Evaluate and promote credit card fraud detection model')
    
    parser.add_argument(
        '--experiment-name',
        type=str,
        required=True,
        help='Name of the MLflow experiment to evaluate'
    )
    
    parser.add_argument(
        '--accuracy-threshold',
        type=float,
        default=0.95,
        help='Minimum accuracy threshold for model promotion (default: 0.95)'
    )
    
    parser.add_argument(
        '--auc-threshold',
        type=float,
        default=0.98,
        help='Minimum ROC AUC threshold for model promotion (default: 0.98)'
    )
    
    return parser.parse_args()

def main():
    """Main evaluation function."""
    # Parse arguments
    args = parse_arguments()
    
    logger.info("🚀 Starting Credit Card Fraud Model Evaluation")
    logger.info(f"📝 Experiment: {args.experiment_name}")
    logger.info(f"🎯 Thresholds: Accuracy >= {args.accuracy_threshold:.3f}, ROC AUC >= {args.auc_threshold:.3f}")
    
    # Initialize evaluator
    evaluator = ModelEvaluator()
    
    try:
        # Run evaluation pipeline
        promotion_success = evaluator.run_evaluation_pipeline(
            experiment_name=args.experiment_name,
            accuracy_threshold=args.accuracy_threshold,
            auc_threshold=args.auc_threshold
        )
        
        if promotion_success:
            logger.info("✅ Evaluation pipeline completed successfully!")
            sys.exit(0)
        else:
            logger.error("❌ Model did not meet quality thresholds")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"❌ Evaluation pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
