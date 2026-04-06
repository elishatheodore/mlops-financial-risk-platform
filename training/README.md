# Training Module - Credit Card Fraud Detection

This module contains the complete training pipeline for credit card fraud detection using the Kaggle Credit Card Fraud dataset.

## 📁 Files Overview

### Core Scripts
- **`feature_engineering.py`** - Complete data preprocessing pipeline with SMOTE, scaling, and visualization
- **`train.py`** - Model training script with MLflow tracking and command-line arguments
- **`evaluate.py`** - Model evaluation and comparison script

### Configuration
- **`requirements.txt`** - All required Python dependencies
- **`config.yaml`** - Configuration file for model parameters and settings

## 🚀 Quick Start

### 1. Install Dependencies
```bash
cd training
pip install -r requirements.txt
```

### 2. Download Dataset
Download the Kaggle Credit Card Fraud dataset and place it in `data/raw/creditcard.csv`:
```bash
# Download from: https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud
# Place the file in: data/raw/creditcard.csv
```

### 3. Run Feature Engineering
```bash
python feature_engineering.py
```
This will:
- Load the raw creditcard.csv dataset
- Handle class imbalance using SMOTE
- Scale the Amount column with StandardScaler
- Drop the Time column
- Split into train/test sets (80/20) with stratification
- Save processed files to `data/processed/`
- Generate visualization plots

### 4. Train Models

#### Random Forest
```bash
python train.py --experiment-name "fraud-detection-rf" --model-type "random_forest" --n-estimators 100 --max-depth 10
```

#### XGBoost
```bash
python train.py --experiment-name "fraud-detection-xgb" --model-type "xgboost" --n-estimators 100 --max-depth 6
```

### 5. View Results in MLflow
```bash
mlflow ui
# Open http://localhost:5000
```

## 📊 Command Line Arguments

### `train.py` Arguments
- `--experiment-name` (required) - Name of the MLflow experiment
- `--model-type` (choices: random_forest, xgboost, default: random_forest) - Model type to train
- `--n-estimators` (default: 100) - Number of estimators
- `--max-depth` (default: None) - Maximum depth of trees

### Examples
```bash
# Train Random Forest with custom parameters
python train.py --experiment-name "rf-experiment-1" --model-type "random_forest" --n-estimators 200 --max-depth 15

# Train XGBoost with default parameters
python train.py --experiment-name "xgb-experiment-1" --model-type "xgboost"

# Quick test run with smaller model
python train.py --experiment-name "test-run" --model-type "random_forest" --n-estimators 50 --max-depth 5
```

## 📁 Output Files

### Processed Data (in `data/processed/`)
- `X_train.npy` - Training features (after SMOTE)
- `X_test.npy` - Test features
- `y_train.npy` - Training labels (after SMOTE)
- `y_test.npy` - Test labels
- `scaler.pkl` - Fitted StandardScaler for Amount column

### Visualizations (in `data/processed/plots/`)
- `class_distribution.png` - Class distribution chart
- `amount_distribution.png` - Amount distribution plots
- `amount_by_class.png` - Amount distribution by fraud/legitimate

### Evaluation Results (in `data/processed/evaluation_plots/`)
- `confusion_matrix.png` - Confusion matrix heatmap
- `roc_curve.png` - ROC curve plot
- `feature_importance.png` - Top 20 feature importances

### Model Artifacts
- `trained_model.pkl` - Local copy of trained model
- MLflow artifacts logged automatically

## 📊 MLflow Tracking

The training script automatically logs:
- **Parameters**: Model type, hyperparameters, dataset info
- **Metrics**: Accuracy, Precision, Recall, F1 Score, ROC AUC
- **Artifacts**: Model file, evaluation plots, confusion matrix
- **Model**: Logged with signature and input example

## 🎯 Model Performance

Expected performance metrics on the test set:
- **Random Forest**: ROC AUC ~0.95+, F1 Score ~0.85+
- **XGBoost**: ROC AUC ~0.96+, F1 Score ~0.87+

*Note: Actual performance may vary based on random seed and data split*

## 🔧 Advanced Usage

### Custom Configuration
Edit `config.yaml` to modify:
- Model hyperparameters
- Data processing parameters
- MLflow settings
- File paths

### Batch Training
```bash
# Train multiple models with different parameters
for estimators in 50 100 200; do
    python train.py --experiment-name "batch-rf-$estimators" \
                   --model-type "random_forest" \
                   --n-estimators $estimators \
                   --max-depth 10
done
```

### Hyperparameter Tuning
```bash
# Grid search example
for depth in 5 10 15; do
    for estimators in 100 200; do
        python train.py --experiment-name "grid-search" \
                       --model-type "random_forest" \
                       --n-estimators $estimators \
                       --max-depth $depth
    done
done
```

## 🐛 Troubleshooting

### Common Issues

1. **FileNotFoundError: creditcard.csv not found**
   - Download the dataset from Kaggle
   - Place it in `data/raw/creditcard.csv`

2. **ModuleNotFoundError: No module named 'xgboost'**
   - Install with: `pip install xgboost>=1.6.0`

3. **MLflow connection error**
   - Start MLflow server: `mlflow ui`
   - Default runs on http://localhost:5000

4. **Memory issues with large dataset**
   - Reduce dataset size for testing
   - Use smaller `n_estimators` parameter

### Debug Mode
Add logging for debugging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📚 Next Steps

1. **Model Evaluation**: Use `evaluate.py` to compare different models
2. **Hyperparameter Tuning**: Implement automated hyperparameter optimization
3. **Model Deployment**: Deploy best model using the serving module
4. **Monitoring**: Set up drift detection and performance monitoring

## 📖 Additional Resources

- [Kaggle Credit Card Fraud Dataset](https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud)
- [MLflow Documentation](https://mlflow.org/docs/latest/index.html)
- [Scikit-learn Documentation](https://scikit-learn.org/stable/)
- [XGBoost Documentation](https://xgboost.readthedocs.io/)
- [Imbalanced-learn Documentation](https://imbalanced-learn.org/stable/)
