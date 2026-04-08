"""
Training script for credit card fraud detection with MLflow tracking.

This was my first attempt at building a production ML pipeline. 
I chose Random Forest because it's more interpretable than deep learning for fraud detection,
and XGBoost as an alternative to compare performance.

The hyperparameters here are starting points - in production I'd do proper hyperparameter tuning.
"""

import argparse
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, classification_report, confusion_matrix
import xgboost as xgb
import mlflow
import mlflow.sklearn
import logging
from pathlib import Path
import joblib
import matplotlib.pyplot as plt
import seaborn as sns

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CreditCardFraudTrainer:
    """Credit card fraud detection model trainer with MLflow tracking."""
    
    def __init__(self):
        self.processed_data_dir = Path('../data/processed')
        self.model = None
        self.experiment_name = None
        
    def load_processed_data(self):
        """Load processed training and test data."""
        logger.info("📂 Loading processed data...")
        
        try:
            X_train = np.load(self.processed_data_dir / 'X_train.npy')
            X_test = np.load(self.processed_data_dir / 'X_test.npy')
            y_train = np.load(self.processed_data_dir / 'y_train.npy')
            y_test = np.load(self.processed_data_dir / 'y_test.npy')
            
            logger.info(f"✅ Training data loaded: X_train {X_train.shape}, y_train {y_train.shape}")
            logger.info(f"✅ Test data loaded: X_test {X_test.shape}, y_test {y_test.shape}")
            
            return X_train, X_test, y_train, y_test
            
        except FileNotFoundError as e:
            logger.error(f"❌ Processed data not found: {e}")
            logger.info("📝 Please run feature_engineering.py first to generate processed data")
            raise
        except Exception as e:
            logger.error(f"❌ Error loading data: {e}")
            raise
    
    def create_model(self, model_type: str, n_estimators: int = 100, max_depth: int = None):
        """Create the specified model with given hyperparameters."""
        logger.info(f" Creating {model_type} model...")
        
        if model_type.lower() == 'random_forest':
            # Random Forest is great for fraud detection - handles imbalanced data well
            # and provides feature importance which is crucial for explaining decisions
            self.model = RandomForestClassifier(
                n_estimators=n_estimators,
                max_depth=max_depth,
                random_state=42,  # The answer to everything, and reproducible results!
                n_jobs=-1,  # Use all cores - training can be slow with large datasets
                class_weight='balanced'  # Critical for fraud detection due to class imbalance
            )
            logger.info(f"   Random Forest with {n_estimators} estimators")
            if max_depth:
                logger.info(f"   • Max depth: {max_depth}")
                
        elif model_type.lower() == 'xgboost':
            # XGBoost often performs better than Random Forest but is less interpretable
            # Good to have as a comparison point - sometimes the performance gain is worth it
            self.model = xgb.XGBClassifier(
                n_estimators=n_estimators,
                max_depth=max_depth if max_depth else 6,  # Default 6 seems to work well for tabular data
                random_state=42,
                n_jobs=-1,
                eval_metric='logloss',
                use_label_encoder=False  # Suppresses that annoying warning
            )
            logger.info(f"   XGBoost with {n_estimators} estimators")
            if max_depth:
                logger.info(f"   • Max depth: {max_depth}")
        else:
            raise ValueError(f"Unsupported model type: {model_type}. Use 'random_forest' or 'xgboost'")
        
        return self.model
    
    def train_model(self, X_train, y_train):
        """Train the model on training data."""
        logger.info("🎯 Training model...")
        
        # Fit the model
        self.model.fit(X_train, y_train)
        
        logger.info("✅ Model training completed")
        
        return self.model
    
    def evaluate_model(self, X_test, y_test):
        """Evaluate the model and compute metrics."""
        logger.info("📊 Evaluating model...")
        
        # Make predictions
        y_pred = self.model.predict(X_test)
        y_pred_proba = self.model.predict_proba(X_test)[:, 1]
        
        # Calculate metrics
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred)
        recall = recall_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred)
        roc_auc = roc_auc_score(y_test, y_pred_proba)
        
        # Log metrics
        logger.info(f"   • Accuracy: {accuracy:.4f}")
        logger.info(f"   • Precision: {precision:.4f}")
        logger.info(f"   • Recall: {recall:.4f}")
        logger.info(f"   • F1 Score: {f1:.4f}")
        logger.info(f"   • ROC AUC: {roc_auc:.4f}")
        
        # Create confusion matrix
        cm = confusion_matrix(y_test, y_pred)
        logger.info(f"   • Confusion Matrix:\n{cm}")
        
        # Classification report
        logger.info("   • Classification Report:")
        logger.info(f"{classification_report(y_test, y_pred)}")
        
        metrics = {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'roc_auc': roc_auc
        }
        
        return metrics, y_pred, y_pred_proba, cm
    
    def create_evaluation_plots(self, y_test, y_pred, y_pred_proba, cm):
        """Create and save evaluation plots."""
        logger.info("📊 Creating evaluation plots...")
        
        # Create plots directory
        plots_dir = self.processed_data_dir / 'evaluation_plots'
        plots_dir.mkdir(exist_ok=True)
        
        # Confusion Matrix Plot
        plt.figure(figsize=(8, 6))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                   xticklabels=['Legitimate', 'Fraud'], 
                   yticklabels=['Legitimate', 'Fraud'])
        plt.title('Confusion Matrix')
        plt.ylabel('True Label')
        plt.xlabel('Predicted Label')
        plt.tight_layout()
        plt.savefig(plots_dir / 'confusion_matrix.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # ROC Curve
        from sklearn.metrics import roc_curve
        fpr, tpr, _ = roc_curve(y_test, y_pred_proba)
        
        plt.figure(figsize=(8, 6))
        plt.plot(fpr, tpr, color='blue', lw=2, label=f'ROC Curve (AUC = {roc_auc_score(y_test, y_pred_proba):.4f})')
        plt.plot([0, 1], [0, 1], color='red', lw=2, linestyle='--', label='Random Classifier')
        plt.xlim([0.0, 1.0])
        plt.ylim([0.0, 1.05])
        plt.xlabel('False Positive Rate')
        plt.ylabel('True Positive Rate')
        plt.title('Receiver Operating Characteristic (ROC) Curve')
        plt.legend(loc="lower right")
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(plots_dir / 'roc_curve.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # Feature Importance (if available)
        if hasattr(self.model, 'feature_importances_'):
            plt.figure(figsize=(10, 8))
            feature_importance = self.model.feature_importances_
            feature_names = [f'V{i}' for i in range(len(feature_importance)-1)] + ['Amount']
            
            # Sort by importance
            indices = np.argsort(feature_importance)[::-1][:20]  # Top 20 features
            
            plt.bar(range(len(indices)), feature_importance[indices])
            plt.title('Top 20 Feature Importances')
            plt.xlabel('Features')
            plt.ylabel('Importance')
            plt.xticks(range(len(indices)), [feature_names[i] for i in indices], rotation=45)
            plt.tight_layout()
            plt.savefig(plots_dir / 'feature_importance.png', dpi=300, bbox_inches='tight')
            plt.close()
        
        logger.info(f"   • Evaluation plots saved to {plots_dir}")
        
        return plots_dir
    
    def save_model_locally(self):
        """Save the trained model locally."""
        logger.info("💾 Saving model locally...")
        
        model_path = self.processed_data_dir / 'trained_model.pkl'
        joblib.dump(self.model, model_path)
        
        logger.info(f"   • Model saved to {model_path}")
        
        return model_path
    
    def run_training_pipeline(self, experiment_name: str, model_type: str, n_estimators: int, max_depth: int):
        """Run the complete training pipeline with MLflow tracking."""
        logger.info("🚀 Starting training pipeline...")
        
        # Set experiment name
        self.experiment_name = experiment_name
        mlflow.set_experiment(experiment_name)
        
        with mlflow.start_run(run_name=f"{model_type}_{n_estimators}_estimators") as run:
            logger.info(f"📝 MLflow Run ID: {run.info.run_id}")
            logger.info(f"📝 Experiment: {experiment_name}")
            
            # Log hyperparameters
            params = {
                "model_type": model_type,
                "n_estimators": n_estimators,
                "max_depth": max_depth,
                "random_state": 42
            }
            mlflow.log_params(params)
            logger.info(f"📝 Logged parameters: {params}")
            
            # Load data
            X_train, X_test, y_train, y_test = self.load_processed_data()
            
            # Log dataset info
            dataset_info = {
                "train_samples": len(X_train),
                "test_samples": len(X_test),
                "features": X_train.shape[1],
                "train_fraud_cases": int(y_train.sum()),
                "test_fraud_cases": int(y_test.sum())
            }
            mlflow.log_params(dataset_info)
            logger.info(f"📝 Dataset info: {dataset_info}")
            
            # Create and train model
            self.create_model(model_type, n_estimators, max_depth)
            self.train_model(X_train, y_train)
            
            # Evaluate model
            metrics, y_pred, y_pred_proba, cm = self.evaluate_model(X_test, y_test)
            
            # Log metrics to MLflow
            mlflow.log_metrics(metrics)
            logger.info(f"📝 Logged metrics: {metrics}")
            
            # Create evaluation plots
            plots_dir = self.create_evaluation_plots(y_test, y_pred, y_pred_proba, cm)
            
            # Log plots as artifacts
            mlflow.log_artifacts(plots_dir, "evaluation_plots")
            
            # Save model locally and log to MLflow
            model_path = self.save_model_locally()
            mlflow.log_artifact(model_path, "model")
            
            # Log model with signature and input example
            # Create input example (first few samples)
            input_example = X_train[:5]
            
            # Log the model with signature
            mlflow.sklearn.log_model(
                self.model,
                "fraud_detection_model",
                signature=mlflow.models.infer_signature(input_example, self.model.predict(input_example)),
                input_example=input_example
            )
            
            logger.info("📝 Model logged to MLflow with signature and input example")
            
            # Print final results
            self.print_results(run.info.run_id, metrics, params)
            
            return run.info.run_id, metrics
    
    def print_results(self, run_id: str, metrics: dict, params: dict):
        """Print a summary of training results."""
        logger.info("=" * 80)
        logger.info("🎉 TRAINING COMPLETED SUCCESSFULLY!")
        logger.info("=" * 80)
        logger.info(f"📝 MLflow Run ID: {run_id}")
        logger.info(f"📝 Experiment: {self.experiment_name}")
        logger.info(f"🤖 Model Type: {params['model_type']}")
        logger.info(f"🔧 Hyperparameters:")
        logger.info(f"   • n_estimators: {params['n_estimators']}")
        logger.info(f"   • max_depth: {params['max_depth']}")
        logger.info(f"📊 Performance Metrics:")
        logger.info(f"   • Accuracy: {metrics['accuracy']:.4f}")
        logger.info(f"   • Precision: {metrics['precision']:.4f}")
        logger.info(f"   • Recall: {metrics['recall']:.4f}")
        logger.info(f"   • F1 Score: {metrics['f1_score']:.4f}")
        logger.info(f"   • ROC AUC: {metrics['roc_auc']:.4f}")
        logger.info("=" * 80)
        logger.info("📊 To view results in MLflow UI, run: mlflow ui")
        logger.info("📊 Then open: http://localhost:5000")
        logger.info("=" * 80)

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Train credit card fraud detection model')
    parser.add_argument('--experiment-name', type=str, required=True,
                       help='MLflow experiment name')
    parser.add_argument('--model-type', type=str, default='random_forest',
                       choices=['random_forest', 'xgboost'],
                       help='Model type to train')
    parser.add_argument('--n-estimators', type=int, default=100,
                       help='Number of estimators for random forest')
    parser.add_argument('--max-depth', type=int, default=None,
                       help='Maximum depth for random forest')
    parser.add_argument('--mlflow-tracking-uri', type=str, default='http://localhost:5000',
                       help='MLflow tracking server URI')
    parser.add_argument('--model-name', type=str, default='financial-risk-model',
                       help='Model name for MLflow registry')
    return parser.parse_args()

def main():
    """Main training function."""
    # Parse arguments
    args = parse_arguments()
    
    # Set MLflow tracking URI
    mlflow.set_tracking_uri(args.mlflow_tracking_uri)
    
    logger.info("🚀 Starting Credit Card Fraud Detection Training")
    logger.info(f"📝 Experiment: {args.experiment_name}")
    logger.info(f"🤖 Model: {args.model_type}")
    logger.info(f"🔧 Parameters: n_estimators={args.n_estimators}, max_depth={args.max_depth}")
    
    # Initialize trainer
    trainer = CreditCardFraudTrainer()
    
    try:
        # Run training pipeline
        run_id, metrics = trainer.run_training_pipeline(
            experiment_name=args.experiment_name,
            model_type=args.model_type,
            n_estimators=args.n_estimators,
            max_depth=args.max_depth
        )
        
        logger.info("✅ Training pipeline completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Training pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()
