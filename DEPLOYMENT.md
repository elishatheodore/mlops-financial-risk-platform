# MLOps Financial Risk Platform - Deployment Guide

This guide provides step-by-step instructions for deploying the MLOps Financial Risk Platform to production environments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Dataset Setup](#dataset-setup)
4. [MLflow Tracking Server](#mlflow-tracking-server)
5. [Local Development](#local-development)
6. [Docker Deployment](#docker-deployment)
7. [Kubernetes Deployment](#kubernetes-deployment)
8. [ArgoCD GitOps Setup](#argocd-gitops-setup)
9. [GitHub Actions CI/CD](#github-actions-cicd)
10. [Monitoring and Observability](#monitoring-and-observability)
11. [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Software
- **Python 3.9+**
- **Docker** and **Docker Compose**
- **Kubernetes** (v1.20+) with **kubectl**
- **Helm 3**
- **Azure CLI** (for Azure deployment)
- **Git**

### Required Accounts
- **Kaggle Account** (for dataset download)
- **Azure Subscription** (for AKS deployment)
- **GitHub Account** (for repository and Actions)

### System Requirements
- **Minimum RAM**: 8GB (16GB recommended)
- **Minimum Storage**: 50GB (100GB recommended)
- **Network**: Stable internet connection

## Environment Setup

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/mlops-financial-risk-platform.git
cd mlops-financial-risk-platform
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
make install
# Or manually:
pip install -r requirements.txt
pip install -r serving/requirements.txt
pip install -r training/requirements.txt
pip install -r monitoring/requirements.txt
```

### 4. Setup Environment Variables
```bash
# Copy example environment file
cp .env.example .env

# Edit with your configuration
nano .env
```

## Dataset Setup

### 1. Download Kaggle Dataset
```bash
# Install Kaggle API if not already installed
pip install kaggle

# Configure Kaggle API credentials
mkdir -p ~/.kaggle
echo '{"username":"your_kaggle_username","key":"your_kaggle_api_key"}' > ~/.kaggle/kaggle.json

# Download the dataset
make download-data
# Or manually:
kaggle datasets download -d mlg-ulb/creditcardfraud --unzip
mv creditcard.csv data/
```

### 2. Verify Dataset
```bash
# Check dataset structure
head -5 data/creditcard.csv
wc -l data/creditcard.csv
```

## MLflow Tracking Server

### 1. Local MLflow Server
```bash
# Start MLflow tracking server
mlflow server --host 0.0.0.0 --port 5000 --default-artifact-root ./mlartifacts

# Access at: http://localhost:5000
```

### 2. Production MLflow Server (Docker)
```bash
docker run -d \
  --name mlflow-server \
  -p 5000:5000 \
  -v $(pwd)/mlartifacts:/mlartifacts \
  python:3.9 \
  bash -c "pip install mlflow psycopg2-binary && mlflow server --host 0.0.0.0 --port 5000 --default-artifact-root /mlartifacts --backend-store-uri postgresql://user:password@host:port/dbname"
```

### 3. Set MLflow Environment Variables
```bash
export MLFLOW_TRACKING_URI=http://localhost:5000
export MLFLOW_EXPERIMENT_NAME=financial-risk-experiment
```

## Local Development

### 1. Train the Model
```bash
# Run full training pipeline
make train

# Or manually:
cd training
python train.py \
  --mlflow-tracking-uri http://localhost:5000 \
  --experiment-name "financial-risk-experiment" \
  --model-name "financial-risk-model"
```

### 2. Start the API Server
```bash
# Start FastAPI server
make serve

# Or manually:
cd serving
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Test the API
```bash
# Health check
curl http://localhost:8000/health

# Sample prediction
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "Time": 172800.0,
    "V1": -1.3598071336738,
    "V2": -0.0727811733098497,
    "V3": 2.53634673796914,
    "V4": 1.37815522427443,
    "V5": -0.338320769942518,
    "V6": 0.462387777762292,
    "V7": 0.239598554061257,
    "V8": 0.0986979012610507,
    "V9": 0.363786969611213,
    "V10": 0.0907941719789316,
    "V11": -0.551599533260813,
    "V12": -0.617800855762348,
    "V13": -0.991389447340619,
    "V14": -0.311169353699879,
    "V15": 1.46817697209427,
    "V16": -0.470400525259478,
    "V17": 0.207971244929082,
    "V18": 0.0257905801985596,
    "V19": 0.403992960255733,
    "V20": -0.25783590189361,
    "V21": -0.018306777944153,
    "V22": 0.213800573652629,
    "V23": 0.111202476357791,
    "V24": 0.0694539228685292,
    "V25": -0.0273005534596218,
    "V26": 0.331593340106543,
    "V27": 0.095874154372954,
    "V28": 0.392196706518795,
    "Amount": 149.62
  }'
```

### 4. Run Tests
```bash
# Run all tests
make test

# Run specific test types
make test-unit
make test-integration
```

## Docker Deployment

### 1. Build Docker Image
```bash
# Build the application image
make docker-build

# Or manually:
docker build -t financial-risk-platform:latest -f serving/Dockerfile serving/
```

### 2. Run Container Locally
```bash
# Run with environment variables
docker run -d \
  --name financial-risk-api \
  -p 8000:8000 \
  -e MLFLOW_TRACKING_URI=http://host.docker.internal:5000 \
  -e MODEL_NAME=financial-risk-model \
  financial-risk-platform:latest
```

### 3. Push to Container Registry
```bash
# Tag for registry
docker tag financial-risk-platform:latest yourregistry/financial-risk-platform:latest

# Push to registry
docker push yourregistry/financial-risk-platform:latest

# Using make command (requires DOCKER_REGISTRY env var)
DOCKER_REGISTRY=yourregistry.com make docker-push
```

## Kubernetes Deployment

### 1. Setup Azure Infrastructure
```bash
# Deploy Azure infrastructure using Terraform
cd terraform

# Initialize Terraform
terraform init

# Plan deployment
terraform plan

# Apply changes
terraform apply

# Get outputs
terraform output
```

### 2. Configure kubectl
```bash
# Get AKS credentials
az aks get-credentials \
  --resource-group rg-mlops-risk-platform \
  --name aks-risk-platform \
  --overwrite-existing

# Verify cluster access
kubectl get nodes
```

### 3. Deploy with Helm
```bash
# Deploy to development
make helm-deploy-dev

# Deploy to production
make helm-deploy-prod

# Or manually:
helm upgrade --install risk-platform-prod ./helm/risk-platform \
  --namespace production \
  --create-namespace \
  --values ./helm/risk-platform/values-prod.yaml \
  --set image.repository=yourregistry/financial-risk-platform \
  --set image.tag=latest
```

### 4. Verify Deployment
```bash
# Check pods
kubectl get pods -n production

# Check services
kubectl get services -n production

# Check logs
kubectl logs -f deployment/risk-platform -n production

# Port forward for local testing
kubectl port-forward svc/risk-platform 8000:80 -n production
```

## ArgoCD GitOps Setup

### 1. Install ArgoCD
```bash
# Install ArgoCD namespace
kubectl create namespace argocd

# Install ArgoCD
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Wait for ArgoCD to be ready
kubectl wait --for=condition=available --timeout=300s deployment/argocd-server -n argocd
```

### 2. Access ArgoCD
```bash
# Get ArgoCD admin password
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d

# Port forward ArgoCD UI
kubectl port-forward svc/argocd-server -n argocd 8080:443

# Access at: https://localhost:8080
# Username: admin
# Password: (from above command)
```

### 3. Configure ArgoCD Applications
```bash
# Apply ArgoCD applications
kubectl apply -f gitops/argocd/application-prod.yaml
kubectl apply -f gitops/argocd/application-dev.yaml

# Check application status
argocd app list
argocd app get risk-platform-prod
```

### 4. ArgoCD Sync
```bash
# Manual sync
argocd app sync risk-platform-prod

# Check sync status
argocd app get risk-platform-prod --show-log
```

## GitHub Actions CI/CD

### Required GitHub Secrets

Configure these secrets in your GitHub repository settings:

1. **MLFLOW_TRACKING_URI**
   - Description: MLflow tracking server URL
   - Example: `http://your-mlflow-server:5000`

2. **AZURE_CREDENTIALS**
   - Description: Azure service principal credentials (JSON format)
   - Example: `{"appId": "...", "password": "...", "tenant": "..."}`

3. **KUBE_CONFIG**
   - Description: Base64 encoded Kubernetes configuration
   - Example: Base64 of `~/.kube/config` file

4. **DOCKER_REGISTRY**
   - Description: Container registry URL
   - Example: `yourregistry.azurecr.io`

5. **DOCKER_USERNAME**
   - Description: Container registry username
   - Example: `your-registry-username`

6. **DOCKER_PASSWORD**
   - Description: Container registry password
   - Example: `your-registry-password`

7. **KAGGLE_USERNAME**
   - Description: Kaggle API username
   - Example: `your-kaggle-username`

8. **KAGGLE_API_KEY**
   - Description: Kaggle API key
   - Example: `your-kaggle-api-key`

### GitHub Actions Workflow

The CI/CD pipeline automatically:

1. **Triggers** on push to main branch and pull requests
2. **Runs tests** to ensure code quality
3. **Builds Docker image** and pushes to registry
4. **Deploys to Kubernetes** using Helm
5. **Updates ArgoCD** for GitOps synchronization

### Manual GitHub Actions Trigger
```bash
# Trigger workflow manually
curl -X POST \
  -H "Authorization: token YOUR_GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/yourusername/mlops-financial-risk-platform/actions/workflows/deploy.yml/dispatches \
  -d '{"ref":"main"}'
```

## Monitoring and Observability

### 1. Access Metrics Dashboard
```bash
# Port forward Grafana
kubectl port-forward svc/prometheus-operator-grafana 3000:3000 -n monitoring

# Access at: http://localhost:3000
# Username: admin
# Password: admin123 (or as configured in values.yaml)
```

### 2. Access Prometheus
```bash
# Port forward Prometheus
kubectl port-forward svc/prometheus-operated 9090:9090 -n monitoring

# Access at: http://localhost:9090
```

### 3. View Application Logs
```bash
# View application logs
kubectl logs -f deployment/risk-platform -n production --tail=100

# View all logs in namespace
kubectl logs -f -n production --all-containers=true
```

### 4. Run Drift Detection
```bash
# Manual drift check
make drift-check

# Or manually:
cd monitoring
python drift_detector.py \
  --mlflow-tracking-uri http://your-mlflow-server:5000 \
  --model-name financial-risk-model \
  --threshold 0.15
```

### 5. Model Performance Monitoring
```bash
# Check model metrics
curl http://localhost:8000/model/info

# Check drift report
curl http://localhost:8000/drift/report

# Check API health
curl http://localhost:8000/health
```

## Troubleshooting

### Common Issues

#### 1. MLflow Connection Failed
```bash
# Check MLflow server status
curl http://localhost:5000

# Verify environment variables
echo $MLFLOW_TRACKING_URI

# Restart MLflow server
docker restart mlflow-server
```

#### 2. Model Loading Failed
```bash
# Check model registry
curl http://localhost:5000/api/2.0/preview/mlflow/registered-models/list

# Verify model exists
curl http://localhost:5000/api/2.0/preview/mlflow/model-versions/get-full?name=financial-risk-model

# Check API logs
kubectl logs deployment/risk-platform -n production
```

#### 3. Kubernetes Deployment Issues
```bash
# Check pod status
kubectl get pods -n production -o wide

# Describe pod for details
kubectl describe pod <pod-name> -n production

# Check events
kubectl get events -n production --sort-by=.metadata.creationTimestamp

# Check resource usage
kubectl top pods -n production
```

#### 4. ArgoCD Sync Issues
```bash
# Check ArgoCD application status
argocd app get risk-platform-prod

# Check ArgoCD server logs
kubectl logs -n argocd deployment/argocd-server

# Manual refresh
argocd app refresh risk-platform-prod
```

#### 5. Performance Issues
```bash
# Check resource limits
kubectl describe deployment risk-platform -n production

# Scale deployment
kubectl scale deployment risk-platform --replicas=3 -n production

# Check node resources
kubectl describe nodes
```

### Debug Commands

```bash
# Check all resources in namespace
kubectl get all -n production

# Port forward for debugging
kubectl port-forward deployment/risk-platform 8000:8000 -n production

# Exec into pod
kubectl exec -it <pod-name> -n production -- /bin/bash

# Check config maps
kubectl get configmaps -n production

# Check secrets
kubectl get secrets -n production
```

### Health Checks

```bash
# API health
curl -f http://localhost:8000/health

# Kubernetes health
kubectl get pods -n production | grep Running

# ArgoCD health
argocd app list | grep risk-platform-prod

# MLflow health
curl -f http://localhost:5000/health
```

## Production Best Practices

### Security
1. **Use HTTPS** for all production endpoints
2. **Rotate secrets** regularly
3. **Network policies** to restrict traffic
4. **RBAC** for Kubernetes access
5. **Image scanning** for security vulnerabilities

### Monitoring
1. **Set up alerts** for critical metrics
2. **Log aggregation** for centralized logging
3. **Performance monitoring** for response times
4. **Error tracking** for quick issue detection

### Backup and Recovery
1. **Regular backups** of MLflow artifacts
2. **Version control** all configurations
3. **Disaster recovery** plan
4. **Test restore procedures** regularly

### Scaling
1. **Horizontal pod autoscaling** based on metrics
2. **Resource limits** to prevent resource exhaustion
3. **Load testing** before production deployment
4. **Performance monitoring** in production

## Support

For additional support:

1. **Check logs** for error messages
2. **Review this guide** for configuration issues
3. **Consult the documentation** in the repository
4. **Open an issue** on GitHub for bugs
5. **Contact the team** for urgent production issues

---

**Note**: This deployment guide assumes you have the necessary permissions and access to the required services. Adjust configurations based on your specific environment and requirements.
