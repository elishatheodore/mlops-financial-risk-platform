# MLOps Financial Risk Platform

> **My journey into production MLOps** - This was my first attempt at building a complete, production-ready MLOps platform. I learned SO much building this - from FastAPI async patterns to Kubernetes troubleshooting!

A **production-grade, end-to-end MLOps pipeline** for financial risk scoring and fraud detection — built with MLflow, FastAPI, Kubernetes, ArgoCD, and Evidently AI. Deployed on Azure Kubernetes Service (AKS) with automated retraining, drift monitoring, and GitOps delivery.

This platform operationalizes a credit risk / fraud detection model through the full MLOps lifecycle: data ingestion, experiment tracking, model registry, containerized serving, CI/CD with quality gates, GitOps deployment, and automated drift-triggered retraining.

**Why I built this:** I wanted to understand what "production ML" really means beyond just training models. Turns out it's 90% engineering and 10% ML!

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     ML Financial Risk Scoring Platform                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                  │
│  │  Data Layer  │    │Training Layer│    │ Serving Layer│                  │
│  └──────────────┘    └──────────────┘    └──────────────┘                  │
│        │                   │                   │                          │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                  │
│  │Kaggle Dataset│    │   MLflow    │    │  FastAPI    │                  │
│  │Credit Card   │───▶│  Tracking    │───▶│   Server     │                  │
│  │Fraud        │    │  & Registry  │    │   + Helm     │                  │
│  └──────────────┘    └──────────────┘    └──────────────┘                  │
│        │                   │                   │                          │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                  │
│  │  Feature     │    │  Automated   │    │  Kubernetes  │                  │
│  │Engineering   │    │  Retraining  │    │ Deployment   │                  │
│  └──────────────┘    └──────────────┘    └──────────────┘                  │
│        │                   │                   │                          │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                  │
│  │  Drift       │    │  GitHub     │    │    ArgoCD   │                  │
│  │Detection     │───▶│  Actions     │───▶│   GitOps     │                  │
│  └──────────────┘    └──────────────┘    └──────────────┘                  │
│        │                   │                   │                          │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                  │
│  │Prometheus+   │    │   Azure     │    │  Terraform   │                  │
│  │  Grafana     │    │   AKS       │    │Infra as Code│                  │
│  └──────────────┘    └──────────────┘    └──────────────┘                  │
└─────────────────────────────────────────────────────────────────────┘
│  ┌──────────────┐    ┌──────────────┐            │                          │
│  │  CI/CD Layer │    │Monitor Layer │◄───────────┘                          │
│  │              │    │              │                                        │
│  │ • GH Actions │    │ • Evidently  │                                        │
│  │ • Quality    │    │ • Prometheus │                                        │
│  │   Gates      │    │ • Grafana    │                                        │
│  │ • ArgoCD     │    │ • Auto-      │                                        │
│  │   GitOps     │    │   Retrain    │                                        │
│  └──────────────┘    └──────────────┘                                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Tech Stack

### ML & Experiment Tracking
- **Scikit-learn** — Model training (Random Forest / XGBoost)
- **MLflow** — Experiment tracking, model registry, artifact storage
- **Evidently AI** — Data drift detection and model performance monitoring
- **Pandas / NumPy** — Feature engineering and data processing

### Model Serving
- **FastAPI** — High-performance model serving API
- **Pydantic** — Request/response validation
- **Uvicorn** — ASGI server

### Platform & Orchestration
- **Kubernetes (AKS)** — Container orchestration
- **Helm** — Kubernetes package management with environment-specific values
- **Docker** — Containerization
- **GHCR** — GitHub Container Registry for model server images

### CI/CD & GitOps
- **GitHub Actions** — Training pipeline, model evaluation, image build, deployment
- **ArgoCD** — GitOps delivery with automated sync and self-healing
- **Trivy** — Container vulnerability scanning

### Observability
- **Prometheus** — Metrics collection (prediction volume, latency, drift score, accuracy)
- **Grafana** — Real-time dashboards for model health and business metrics
- **Azure Monitor** — Infrastructure-level observability

### Infrastructure
- **Terraform** — Azure infrastructure provisioning (AKS, ACR, networking)
- **Azure Kubernetes Service** — Managed Kubernetes cluster

---

## 📁 Project Structure

```
mlops-financial-risk-platform/
│
├── 📊 Data & Training
│   ├── data/
│   │   ├── raw/                        # Raw dataset (Kaggle Credit Card Fraud)
│   │   └── processed/                  # Feature-engineered dataset
│   ├── training/
│   │   ├── train.py                    # Model training script
│   │   ├── evaluate.py                 # Model evaluation and comparison
│   │   ├── feature_engineering.py      # Feature pipeline
│   │   └── requirements.txt           # Training dependencies
│
├── 🤖 Model Serving
│   ├── serving/
│   │   ├── app/
│   │   │   ├── main.py                # FastAPI application
│   │   │   ├── model.py               # Model loading and inference
│   │   │   ├── schemas.py             # Request/response schemas
│   │   │   └── metrics.py             # Prometheus metrics
│   │   ├── Dockerfile                 # Model server container
│   │   ├── requirements.txt           # Serving dependencies
│   │   └── .env                       # Environment configuration
│
├── ☸️ Kubernetes & Helm
│   ├── helm/
│   │   ├── risk-platform/
│   │   │   ├── Chart.yaml             # Chart metadata
│   │   │   ├── values.yaml            # Default values
│   │   │   ├── values-dev.yaml        # Development values
│   │   │   ├── values-prod.yaml       # Production values
│   │   │   └── templates/
│   │   │       ├── deployment.yaml    # Model server deployment
│   │   │       ├── service.yaml       # Service definition
│   │   │       ├── ingress.yaml       # Ingress configuration
│   │   │       ├── hpa.yaml           # Horizontal pod autoscaler
│   │   │       ├── configmap.yaml     # Configuration
│   │   │       ├── secret.yaml        # Secrets
│   │   │       └── servicemonitor.yaml # Prometheus scraping
│   │   └── deploy-helm.sh             # Helm deployment script
│   └── k8s/
│       ├── namespace.yaml             # Namespace
│       └── monitoring.yaml            # Prometheus + Grafana setup
│
├── 🔄 CI/CD
│   └── .github/
│       └── workflows/
│           ├── train-and-evaluate.yml # Training pipeline
│           ├── build-and-deploy.yml   # Build, scan, deploy
│           └── retrain-trigger.yml    # Drift-triggered retraining
│
├── 🚀 GitOps
│   └── gitops/
│       └── argocd/
│           ├── application-dev.yaml   # Dev environment
│           └── application-prod.yaml  # Production environment
│
├── 📡 Monitoring
│   ├── monitoring/
│   │   ├── drift_detector.py          # Evidently AI drift reports
│   │   ├── grafana-dashboard.json     # Pre-built Grafana dashboard
│   │   └── alerts.yaml                # Prometheus alert rules
│
├── 🏗️ Infrastructure
│   └── terraform/
│       ├── main.tf                    # AKS cluster + networking
│       ├── variables.tf               # Input variables
│       └── outputs.tf                 # Output values
│
└── 📚 Documentation
    ├── README.md                      # This file
    ├── MLFLOW_SETUP.md               # MLflow configuration guide
    ├── DEPLOYMENT.md                  # Deployment instructions
    └── MONITORING.md                  # Monitoring and alerting guide
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Docker
- kubectl + Helm 3.x
- Azure CLI
- Terraform
- MLflow

### 1. Train the Model
```bash
cd training
pip install -r requirements.txt

# Run training with MLflow tracking
python train.py --experiment-name "credit-risk-v1" --model-type "random_forest"

# View experiments
mlflow ui
# Open http://localhost:5000
```

### 2. Promote Model to Registry
```bash
# Evaluate and promote best model
python evaluate.py --experiment-name "credit-risk-v1" --accuracy-threshold 0.95
```

### 3. Deploy Model Server (Docker)
```bash
cd serving
docker build -t risk-platform:latest .
docker run -p 8000:8000 -e MLFLOW_TRACKING_URI=<uri> risk-platform:latest

# Test prediction endpoint
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"amount": 1500.0, "merchant_category": "online", "hour": 2}'
```

### 4. Deploy to AKS (Helm)
```bash
cd helm
./deploy-helm.sh -f values-prod.yaml

# Verify deployment
kubectl get pods -n risk-platform
kubectl get ingress -n risk-platform
```

### 5. Enable GitOps (ArgoCD)
```bash
kubectl apply -f gitops/argocd/application-prod.yaml
# ArgoCD automatically syncs new model versions from Git
```

---

## 📡 API Endpoints

### Prediction
- `POST /predict` — Score a transaction for fraud/credit risk
- `POST /predict/batch` — Batch scoring for multiple transactions

### Health & Monitoring
- `GET /health` — Service health check
- `GET /metrics` — Prometheus metrics endpoint
- `GET /model/info` — Current model version and metadata
- `GET /drift/report` — Latest drift detection report

### Request Format
```json
{
  "amount": 1500.00,
  "merchant_category": "online_retail",
  "hour_of_day": 2,
  "day_of_week": 6,
  "transaction_count_24h": 15,
  "avg_amount_30d": 250.00
}
```

### Response Format
```json
{
  "risk_score": 0.87,
  "risk_label": "HIGH",
  "confidence": 0.92,
  "model_version": "v2.1.0",
  "prediction_id": "pred_abc123",
  "timestamp": "2026-04-06T14:30:00Z"
}
```

---

## 🔄 CI/CD Pipeline

### Training Pipeline (train-and-evaluate.yml)
1. **Data validation** — Check dataset integrity and schema
2. **Feature engineering** — Run feature pipeline
3. **Model training** — Train with MLflow tracking
4. **Model evaluation** — Compare against production model
5. **Quality gate** — Only promote if accuracy > 95% and AUC > 0.98
6. **Registry promotion** — Push winning model to MLflow Registry

### Deployment Pipeline (build-and-deploy.yml)
1. **Build** — Multi-architecture Docker image
2. **Security scan** — Trivy vulnerability scan
3. **Helm validation** — Chart linting and dry-run
4. **Deploy** — ArgoCD syncs new version to AKS
5. **Smoke test** — Health check and prediction test
6. **Rollback** — Automatic rollback if smoke test fails

### Retraining Pipeline (retrain-trigger.yml)
- Triggered automatically when drift score exceeds threshold
- Runs full training pipeline with latest data
- Promotes new model only if it outperforms current production model

---

## 📊 Monitoring & Observability

### Grafana Dashboard Panels
- **Prediction Volume** — Requests per second, daily totals
- **Model Accuracy** — Live accuracy against labeled feedback
- **Latency** — p50, p95, p99 prediction latency
- **Drift Score** — Feature drift and prediction drift over time
- **Risk Distribution** — HIGH / MEDIUM / LOW score distribution
- **Error Rate** — Failed predictions and API errors

### Prometheus Metrics
```
risk_platform_predictions_total          # Total predictions by label
risk_platform_prediction_latency_seconds # Prediction latency histogram
risk_platform_drift_score                # Current drift score
risk_platform_model_accuracy             # Rolling accuracy score
risk_platform_errors_total               # Error count by type
```

### Drift Detection
- **Feature drift** — Detects when incoming transaction patterns shift
- **Prediction drift** — Detects when score distribution changes
- **Auto-retraining** — GitHub Actions triggered when drift score > 0.15
- **Reports** — Daily HTML drift reports saved as MLflow artifacts

---

## 🔒 Security

- **RBAC** — Kubernetes role-based access control
- **Network Policies** — Pod-level traffic isolation
- **Secret Management** — Kubernetes secrets for API keys and MLflow credentials
- **Container Scanning** — Trivy scans on every build
- **Input Validation** — Pydantic schema validation on all prediction requests
- **Rate Limiting** — API rate limiting to prevent abuse

---

## 🌍 Multi-Environment Support

| Environment | Replicas | Resources | Monitoring | Auto-retrain |
|---|---|---|---|---|
| **Development** | 1 | Minimal | Basic | Manual |
| **Staging** | 2 | Medium | Full | Manual |
| **Production** | 3+ (HPA) | High | Full + Alerts | Automated |

---

## 🚀 Deployment Roadmap

### Phase 1: Complete ✅
- ✅ Model training with MLflow experiment tracking
- ✅ Model registry with promotion workflow
- ✅ FastAPI model serving
- ✅ Docker containerization + GHCR
- ✅ Helm chart deployment on AKS
- ✅ GitHub Actions CI/CD with quality gates
- ✅ ArgoCD GitOps delivery
- ✅ Evidently AI drift detection
- ✅ Prometheus + Grafana monitoring
- ✅ Terraform infrastructure provisioning

### Phase 2: In Progress 🔄
- 🔄 Feature store integration
- 🔄 A/B model testing framework
- 🔄 Model explainability (SHAP values)
- 🔄 Multi-region deployment

### Phase 3: Planned 📋
- 📋 Real-time streaming predictions (Kafka)
- 📋 Online learning and incremental retraining
- 📋 Model fairness and bias monitoring

---

## 📚 Documentation

| Document | Description |
|---|---|
| `README.md` | This file — project overview |
| `MLFLOW_SETUP.md` | MLflow tracking server configuration |
| `DEPLOYMENT.md` | Step-by-step deployment guide |
| `MONITORING.md` | Grafana dashboards and alerting setup |

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Test locally with Docker
5. Push to branch and open a Pull Request

---

## 📄 License

MIT License — see LICENSE file for details.

---

## 📝 Personal Learning Journey

### My Learning Journey Building This

**What I learned the hard way:**
- **FastAPI async patterns**: Spent way too much time debugging async context managers!
- **MLflow registry stages**: The API changes between versions are... painful
- **Kubernetes networking**: Why won't my pods talk to each other?! (spoiler: service mesh issues)
- **Pydantic v2 migration**: Validators are now field_validators - who knew?

**Proud moments:**
- Getting the first successful model promotion to Production stage
- Watching drift detection actually trigger a retraining pipeline
- When the Grafana dashboard finally showed real metrics

**Things I'd do differently next time:**
- Start with feature engineering earlier (spent weeks fixing data issues)
- Use a simpler monitoring setup initially (Prometheus is complex!)
- Better error handling in the FastAPI app (learned this the hard way)

**Resources that saved me:**
- MLflow documentation (actually pretty good!)
- FastAPI's excellent error messages
- The Kubernetes community on Slack
- Countless Stack Overflow answers at 2 AM

---

**Built by [Elisha Theodore](https://github.com/elishatheodore) · [elisha.app](https://www.elisha.app) · [LinkedIn](https://www.linkedin.com/in/elishatheodore)**

**Stack:** MLflow · Scikit-learn · FastAPI · Docker · Helm · Kubernetes (AKS) · ArgoCD · GitHub Actions · Evidently AI · Prometheus · Grafana · Terraform · Python

![Version](https://img.shields.io/badge/version-1.0.0-blue) ![Status](https://img.shields.io/badge/status-production--ready-green) ![MLOps](https://img.shields.io/badge/MLOps-end--to--end-orange) ![Cloud](https://img.shields.io/badge/cloud-Azure%20AKS-blue)
