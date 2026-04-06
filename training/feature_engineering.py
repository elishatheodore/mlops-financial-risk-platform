"""
Feature engineering pipeline for credit card fraud detection using Kaggle Credit Card Fraud dataset.
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from imblearn.over_sampling import SMOTE
import joblib
import logging
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CreditCardFraudFeatureEngineer:
    """Feature engineering pipeline for credit card fraud detection."""
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.processed_data_dir = Path('../data/processed')
        self.raw_data_dir = Path('../data/raw')
        
        # Create processed data directory if it doesn't exist
        self.processed_data_dir.mkdir(parents=True, exist_ok=True)
        
    def load_raw_data(self, file_path: str = None) -> pd.DataFrame:
        """Load the raw credit card fraud dataset."""
        if file_path is None:
            file_path = self.raw_data_dir / 'creditcard.csv'
        
        logger.info(f"Loading raw data from {file_path}")
        
        try:
            df = pd.read_csv(file_path)
            logger.info(f"✅ Data loaded successfully. Shape: {df.shape}")
            return df
        except FileNotFoundError:
            logger.error(f"❌ Data file not found: {file_path}")
            logger.info("📝 Please ensure the Kaggle Credit Card Fraud dataset (creditcard.csv) is placed in data/raw/")
            raise
        except Exception as e:
            logger.error(f"❌ Error loading data: {e}")
            raise
    
    def analyze_dataset(self, df: pd.DataFrame):
        """Analyze and log dataset statistics."""
        logger.info("📊 Dataset Analysis:")
        logger.info(f"   • Total samples: {len(df):,}")
        logger.info(f"   • Total features: {df.shape[1]}")
        logger.info(f"   • Missing values: {df.isnull().sum().sum()}")
        logger.info(f"   • Data types: {df.dtypes.value_counts().to_dict()}")
        
        # Class distribution
        class_counts = df['Class'].value_counts()
        total_samples = len(df)
        fraud_percentage = (class_counts[1] / total_samples) * 100
        
        logger.info("🎯 Class Distribution:")
        logger.info(f"   • Legitimate (0): {class_counts[0]:,} ({100-fraud_percentage:.4f}%)")
        logger.info(f"   • Fraudulent (1): {class_counts[1]:,} ({fraud_percentage:.4f}%)")
        logger.info(f"   • Fraud ratio: 1:{int((class_counts[0]/class_counts[1]))}")
        
        # Amount statistics
        logger.info("💰 Amount Statistics:")
        logger.info(f"   • Mean: ${df['Amount'].mean():.2f}")
        logger.info(f"   • Median: ${df['Amount'].median():.2f}")
        logger.info(f"   • Std: ${df['Amount'].std():.2f}")
        logger.info(f"   • Min: ${df['Amount'].min():.2f}")
        logger.info(f"   • Max: ${df['Amount'].max():.2f}")
        
        return {
            'total_samples': total_samples,
            'features': df.shape[1],
            'missing_values': df.isnull().sum().sum(),
            'class_distribution': class_counts.to_dict(),
            'fraud_percentage': fraud_percentage,
            'amount_stats': {
                'mean': df['Amount'].mean(),
                'median': df['Amount'].median(),
                'std': df['Amount'].std(),
                'min': df['Amount'].min(),
                'max': df['Amount'].max()
            }
        }
    
    def preprocess_data(self, df: pd.DataFrame) -> tuple:
        """Preprocess the data for training."""
        logger.info("🔧 Preprocessing data...")
        
        # Make a copy to avoid modifying original data
        df_processed = df.copy()
        
        # Drop the Time column as specified
        if 'Time' in df_processed.columns:
            df_processed = df_processed.drop('Time', axis=1)
            logger.info("   • Dropped 'Time' column")
        
        # Check for missing values
        missing_values = df_processed.isnull().sum().sum()
        if missing_values > 0:
            logger.warning(f"   • Found {missing_values} missing values. Filling with median.")
            df_processed = df_processed.fillna(df_processed.median())
        else:
            logger.info("   • No missing values found")
        
        # Separate features and target
        X = df_processed.drop('Class', axis=1)
        y = df_processed['Class']
        
        logger.info(f"   • Features shape: {X.shape}")
        logger.info(f"   • Target shape: {y.shape}")
        
        return X, y
    
    def scale_amount_column(self, X: pd.DataFrame) -> pd.DataFrame:
        """Scale the Amount column using StandardScaler."""
        logger.info("📏 Scaling Amount column...")
        
        X_scaled = X.copy()
        
        # Scale the Amount column
        if 'Amount' in X_scaled.columns:
            # Fit scaler on Amount column and transform
            amount_values = X_scaled['Amount'].values.reshape(-1, 1)
            X_scaled['Amount'] = self.scaler.fit_transform(amount_values).flatten()
            logger.info("   • Amount column scaled using StandardScaler")
        else:
            logger.warning("   • Amount column not found in dataset")
        
        return X_scaled
    
    def split_data(self, X: pd.DataFrame, y: pd.Series, test_size: float = 0.2, random_state: int = 42) -> tuple:
        """Split data into train and test sets with stratification."""
        logger.info(f"📂 Splitting data (test_size={test_size}, stratified)...")
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, 
            test_size=test_size, 
            random_state=random_state, 
            stratify=y
        )
        
        logger.info(f"   • Training set: {X_train.shape} (Fraud: {y_train.sum()}, Legitimate: {len(y_train)-y_train.sum()})")
        logger.info(f"   • Test set: {X_test.shape} (Fraud: {y_test.sum()}, Legitimate: {len(y_test)-y_test.sum()})")
        
        return X_train, X_test, y_train, y_test
    
    def handle_class_imbalance(self, X_train: pd.DataFrame, y_train: pd.Series, random_state: int = 42) -> tuple:
        """Handle class imbalance using SMOTE."""
        logger.info("⚖️  Handling class imbalance with SMOTE...")
        
        # Check original class distribution
        original_fraud = y_train.sum()
        original_legitimate = len(y_train) - original_fraud
        logger.info(f"   • Original training distribution - Fraud: {original_fraud}, Legitimate: {original_legitimate}")
        
        # Apply SMOTE
        smote = SMOTE(random_state=random_state)
        X_train_resampled, y_train_resampled = smote.fit_resample(X_train, y_train)
        
        # Check new class distribution
        resampled_fraud = y_train_resampled.sum()
        resampled_legitimate = len(y_train_resampled) - resampled_fraud
        logger.info(f"   • After SMOTE distribution - Fraud: {resampled_fraud}, Legitimate: {resampled_legitimate}")
        logger.info(f"   • Training set size increased from {len(X_train):,} to {len(X_train_resampled):,}")
        
        return X_train_resampled, y_train_resampled
    
    def save_processed_data(self, X_train, X_test, y_train, y_test):
        """Save processed data to files."""
        logger.info("💾 Saving processed data...")
        
        # Save numpy arrays
        np.save(self.processed_data_dir / 'X_train.npy', X_train)
        np.save(self.processed_data_dir / 'X_test.npy', X_test)
        np.save(self.processed_data_dir / 'y_train.npy', y_train)
        np.save(self.processed_data_dir / 'y_test.npy', y_test)
        
        # Save the fitted scaler
        joblib.dump(self.scaler, self.processed_data_dir / 'scaler.pkl')
        
        logger.info(f"   • Saved X_train.npy: {X_train.shape}")
        logger.info(f"   • Saved X_test.npy: {X_test.shape}")
        logger.info(f"   • Saved y_train.npy: {y_train.shape}")
        logger.info(f"   • Saved y_test.npy: {y_test.shape}")
        logger.info(f"   • Saved scaler.pkl")
    
    def create_visualizations(self, df: pd.DataFrame):
        """Create and save visualization plots."""
        logger.info("📊 Creating visualizations...")
        
        # Create plots directory
        plots_dir = self.processed_data_dir / 'plots'
        plots_dir.mkdir(exist_ok=True)
        
        # Class distribution plot
        plt.figure(figsize=(8, 6))
        class_counts = df['Class'].value_counts()
        plt.bar(['Legitimate (0)', 'Fraudulent (1)'], class_counts.values, color=['green', 'red'])
        plt.title('Class Distribution')
        plt.ylabel('Count')
        plt.yscale('log')
        for i, count in enumerate(class_counts.values):
            plt.text(i, count, f'{count:,}', ha='center', va='bottom')
        plt.tight_layout()
        plt.savefig(plots_dir / 'class_distribution.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # Amount distribution plot
        plt.figure(figsize=(12, 6))
        plt.subplot(1, 2, 1)
        plt.hist(df['Amount'], bins=50, alpha=0.7, color='blue')
        plt.title('Amount Distribution (All)')
        plt.xlabel('Amount ($)')
        plt.ylabel('Frequency')
        
        plt.subplot(1, 2, 2)
        # Log scale for better visualization
        plt.hist(np.log1p(df['Amount']), bins=50, alpha=0.7, color='orange')
        plt.title('Amount Distribution (Log Scale)')
        plt.xlabel('log(Amount + 1)')
        plt.ylabel('Frequency')
        
        plt.tight_layout()
        plt.savefig(plots_dir / 'amount_distribution.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # Amount by class
        plt.figure(figsize=(10, 6))
        fraud_amounts = df[df['Class'] == 1]['Amount']
        legit_amounts = df[df['Class'] == 0]['Amount']
        
        plt.hist([legit_amounts, fraud_amounts], bins=50, alpha=0.7, 
                 label=['Legitimate', 'Fraudulent'], color=['green', 'red'])
        plt.title('Amount Distribution by Class')
        plt.xlabel('Amount ($)')
        plt.ylabel('Frequency')
        plt.legend()
        plt.yscale('log')
        plt.tight_layout()
        plt.savefig(plots_dir / 'amount_by_class.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"   • Visualizations saved to {plots_dir}")
    
    def run_complete_pipeline(self):
        """Run the complete feature engineering pipeline."""
        logger.info("🚀 Starting complete feature engineering pipeline...")
        
        try:
            # Load raw data
            df = self.load_raw_data()
            
            # Analyze dataset
            stats = self.analyze_dataset(df)
            
            # Create visualizations
            self.create_visualizations(df)
            
            # Preprocess data
            X, y = self.preprocess_data(df)
            
            # Scale Amount column
            X_scaled = self.scale_amount_column(X)
            
            # Split data
            X_train, X_test, y_train, y_test = self.split_data(X_scaled, y)
            
            # Handle class imbalance (only on training data)
            X_train_balanced, y_train_balanced = self.handle_class_imbalance(X_train, y_train)
            
            # Save processed data
            self.save_processed_data(X_train_balanced, X_test, y_train_balanced, y_test)
            
            logger.info("✅ Feature engineering pipeline completed successfully!")
            logger.info(f"📁 Processed data saved to: {self.processed_data_dir}")
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Pipeline failed: {e}")
            raise

def main():
    """Main function to run the feature engineering pipeline."""
    # Initialize the feature engineer
    fe = CreditCardFraudFeatureEngineer()
    
    # Run the complete pipeline
    stats = fe.run_complete_pipeline()
    
    # Print final summary
    logger.info("=" * 60)
    logger.info("📋 FEATURE ENGINEERING SUMMARY")
    logger.info("=" * 60)
    logger.info(f"✅ Total samples processed: {stats['total_samples']:,}")
    logger.info(f"✅ Features created: {stats['features'] - 1}")  # -1 for target
    logger.info(f"✅ Fraud cases: {stats['class_distribution'][1]:,} ({stats['fraud_percentage']:.4f}%)")
    logger.info(f"✅ Legitimate cases: {stats['class_distribution'][0]:,} ({100-stats['fraud_percentage']:.4f}%)")
    logger.info(f"✅ Class imbalance handled with SMOTE")
    logger.info(f"✅ Amount column scaled with StandardScaler")
    logger.info(f"✅ Data split: 80% train, 20% test (stratified)")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()
