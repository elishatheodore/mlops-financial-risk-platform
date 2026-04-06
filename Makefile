# MLOps Financial Risk Platform Makefile
# Provides convenient targets for training, serving, testing, and deployment

.PHONY: help train serve docker-build helm-deploy-dev helm-deploy-prod drift-check test clean install lint format

# Default target
.DEFAULT_GOAL := help

# Help target
help: ## Show this help message
	@echo "MLOps Financial Risk Platform - Available targets:"
	@echo ""
	@echo "  train              - Run the full training pipeline"
	@echo "  serve              - Start FastAPI server locally"
	@echo "  docker-build       - Build the Docker image"
	@echo "  helm-deploy-dev    - Deploy to development environment with Helm"
	@echo "  helm-deploy-prod   - Deploy to production environment with Helm"
	@echo "  drift-check        - Run drift detector manually"
	@echo "  test               - Run pytest on test files"
	@echo "  clean              - Clean up temporary files and artifacts"
	@echo "  install            - Install Python dependencies"
	@echo "  lint               - Run code linting"
	@echo "  format             - Format code with black and isort"
	@echo ""

# Installation
install: ## Install Python dependencies
	@echo "Installing Python dependencies..."
	pip install -r requirements.txt
	pip install -r serving/requirements.txt
	pip install -r training/requirements.txt
	pip install -r monitoring/requirements.txt

# Training
train: ## Run the full training pipeline
	@echo "Running training pipeline..."
	cd training && python train.py \
		--mlflow-tracking-uri $(MLFLOW_TRACKING_URI) \
		--experiment-name "financial-risk-experiment" \
		--model-name "financial-risk-model"

# Serving
serve: ## Start FastAPI server locally
	@echo "Starting FastAPI server locally..."
	cd serving && python -m uvicorn app.main:app \
		--host $(HOST) \
		--port $(PORT) \
		--reload \
		--log-level info

# Docker
docker-build: ## Build the Docker image
	@echo "Building Docker image..."
	docker build -t financial-risk-platform:latest -f serving/Dockerfile serving/

docker-push: docker-build ## Build and push Docker image to registry
	@echo "Pushing Docker image to registry..."
	docker tag financial-risk-platform:latest $(DOCKER_REGISTRY)/financial-risk-platform:latest
	docker push $(DOCKER_REGISTRY)/financial-risk-platform:latest

# Helm Deployment
helm-deploy-dev: ## Deploy to development environment with Helm
	@echo "Deploying to development environment..."
	helm upgrade --install risk-platform-dev ./helm/risk-platform \
		--namespace dev \
		--create-namespace \
		--values ./helm/risk-platform/values-dev.yaml \
		--set image.repository=$(DOCKER_REGISTRY)/financial-risk-platform \
		--set image.tag=latest

helm-deploy-prod: ## Deploy to production environment with Helm
	@echo "Deploying to production environment..."
	helm upgrade --install risk-platform-prod ./helm/risk-platform \
		--namespace production \
		--create-namespace \
		--values ./helm/risk-platform/values-prod.yaml \
		--set image.repository=$(DOCKER_REGISTRY)/financial-risk-platform \
		--set image.tag=latest

helm-uninstall-dev: ## Uninstall development deployment
	@echo "Uninstalling development deployment..."
	helm uninstall risk-platform-dev --namespace dev

helm-uninstall-prod: ## Uninstall production deployment
	@echo "Uninstalling production deployment..."
	helm uninstall risk-platform-prod --namespace production

# Drift Detection
drift-check: ## Run drift detector manually
	@echo "Running drift detection..."
	cd monitoring && python drift_detector.py \
		--mlflow-tracking-uri $(MLFLOW_TRACKING_URI) \
		--model-name $(MODEL_NAME) \
		--threshold 0.15

# Testing
test: ## Run pytest on test files
	@echo "Running tests..."
	pytest tests/ -v --cov=. --cov-report=html --cov-report=term-missing

test-unit: ## Run unit tests only
	@echo "Running unit tests..."
	pytest tests/ -v -k "unit" --cov=. --cov-report=term-missing

test-integration: ## Run integration tests only
	@echo "Running integration tests..."
	pytest tests/ -v -k "integration" --cov=. --cov-report=term-missing

# Code Quality
lint: ## Run code linting
	@echo "Running code linting..."
	flake8 serving/ training/ monitoring/ tests/ --max-line-length=88 --extend-ignore=E203,W503
	pylint serving/ training/ monitoring/ --disable=R0903,R0913,R0914,R0915
	mypy serving/ training/ monitoring/ --ignore-missing-imports

format: ## Format code with black and isort
	@echo "Formatting code..."
	black serving/ training/ monitoring/ tests/
	isort serving/ training/ monitoring/ tests/

format-check: ## Check code formatting
	@echo "Checking code formatting..."
	black --check serving/ training/ monitoring/ tests/
	isort --check-only serving/ training/ monitoring/ tests/

# Data Setup
download-data: ## Download Kaggle dataset
	@echo "Downloading Kaggle dataset..."
	kaggle datasets download -d mlg-ulb/creditcardfraud --unzip
	mv creditcard.csv data/

setup-env: ## Setup environment file from example
	@echo "Setting up environment file..."
	if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "Created .env from .env.example - please update with your values"; \
	else \
		echo ".env already exists"; \
	fi

# Monitoring
monitor-logs: ## Monitor application logs
	@echo "Monitoring application logs..."
	kubectl logs -f deployment/risk-platform -n $(NAMESPACE) --tail=100

monitor-metrics: ## Access metrics dashboard
	@echo "Opening metrics dashboard..."
	kubectl port-forward svc/prometheus-operator-grafana 3000:3000 -n monitoring &
	@echo "Grafana dashboard available at http://localhost:3000"
	@echo "Username: admin"
	@echo "Password: admin123"

# Cleanup
clean: ## Clean up temporary files and artifacts
	@echo "Cleaning up..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type f -name ".coverage" -delete
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type f -name "*.log" -delete
	rm -rf build/
	rm -rf dist/
	rm -rf .coverage
	rm -rf htmlcov/

clean-data: ## Clean up data files
	@echo "Cleaning up data files..."
	rm -f data/*.csv
	rm -rf data/raw/
	rm -rf data/processed/

clean-models: ## Clean up model artifacts
	@echo "Cleaning up model artifacts..."
	rm -rf models/
	rm -rf mlruns/

# Development helpers
dev-setup: install download-data setup-env ## Complete development setup
	@echo "Development setup complete!"
	@echo "Next steps:"
	@echo "1. Update .env with your configuration"
	@echo "2. Run 'make train' to train the model"
	@echo "3. Run 'make serve' to start the API server"

dev-test: format lint test ## Run all development checks
	@echo "All development checks completed!"

# CI/CD helpers
ci-test: ## Run tests in CI environment
	@echo "Running tests in CI environment..."
	pytest tests/ -v --cov=. --cov-report=xml --cov-report=term-missing --junitxml=test-results.xml

ci-build: ## Build for CI environment
	@echo "Building for CI environment..."
	docker build -t financial-risk-platform:$(BUILD_NUMBER) -f serving/Dockerfile serving/

# Production helpers
prod-deploy: test docker-build helm-deploy-prod ## Complete production deployment
	@echo "Production deployment complete!"

prod-rollback: ## Rollback production deployment
	@echo "Rolling back production deployment..."
	helm rollback risk-platform-prod -n production

# Documentation
docs-serve: ## Serve documentation locally
	@echo "Serving documentation..."
	cd serving && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 & \
	sleep 2 && xdg-open http://localhost:8000/docs

docs-build: ## Build documentation
	@echo "Building documentation..."
	@echo "Documentation available at: serving/app/docs"

# Environment variables setup
check-env: ## Check required environment variables
	@echo "Checking environment variables..."
	@echo "MLFLOW_TRACKING_URI: $(MLFLOW_TRACKING_URI)"
	@echo "MODEL_NAME: $(MODEL_NAME)"
	@echo "DOCKER_REGISTRY: $(DOCKER_REGISTRY)"
	@echo "HOST: $(HOST)"
	@echo "PORT: $(PORT)"
	@echo "NAMESPACE: $(NAMESPACE)"

# Quick start
quickstart: ## Quick start for new users
	@echo "=== MLOps Financial Risk Platform Quick Start ==="
	@echo ""
	@echo "1. Setting up environment..."
	$(MAKE) setup-env
	@echo ""
	@echo "2. Installing dependencies..."
	$(MAKE) install
	@echo ""
	@echo "3. Downloading data..."
	$(MAKE) download-data
	@echo ""
	@echo "4. Training model..."
	$(MAKE) train
	@echo ""
	@echo "5. Starting server..."
	$(MAKE) serve
	@echo ""
	@echo "Quick start complete! API available at http://$(HOST):$(PORT)"
	@echo "Documentation available at http://$(HOST):$(PORT)/docs"
