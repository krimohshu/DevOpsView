# ========================================
# DevOpsView - Master Makefile
# ========================================
# Convenient commands for development, deployment, and operations

.PHONY: help install-tools setup-local-cluster setup-monitoring deploy-dev deploy-staging deploy-prod \
        test test-unit test-integration test-e2e security-scan lint format clean docs

.DEFAULT_GOAL := help

# ============ Colors for Output ============
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

# ============ Variables ============
PROJECT_NAME := devopsview
AWS_REGION := us-east-1
AWS_ACCOUNT_ID := $(shell aws sts get-caller-identity --query Account --output text 2>/dev/null || echo "not-configured")
CLUSTER_NAME := devopsview-local
NAMESPACE := dev

# Python
PYTHON := python3
VENV := .venv
PIP := $(VENV)/bin/pip
PYTEST := $(VENV)/bin/pytest

# Terraform
TF_DIR := terraform
TF_ENV := dev

# Helm
HELM := helm
HELMFILE := helmfile

# ============ Help ============
help: ## Show this help message
	@echo "$(BLUE)╔═══════════════════════════════════════════════════════════╗$(NC)"
	@echo "$(BLUE)║         DevOpsView - Platform Engineering Suite          ║$(NC)"
	@echo "$(BLUE)╚═══════════════════════════════════════════════════════════╝$(NC)"
	@echo ""
	@echo "$(GREEN)Available targets:$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-30s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(BLUE)Examples:$(NC)"
	@echo "  make install-tools          # Install all required tools"
	@echo "  make setup-local-cluster    # Create local K8s cluster"
	@echo "  make deploy-dev             # Deploy to dev environment"
	@echo "  make test                   # Run all tests"
	@echo "  make security-scan          # Run security scans"
	@echo ""

# ============ Installation & Setup ============
install-tools: ## Install all required tools (kubectl, helm, terraform, etc.)
	@echo "$(BLUE)Installing required tools...$(NC)"
	@bash scripts/setup/install-tools.sh

setup-python: ## Set up Python virtual environment
	@echo "$(BLUE)Setting up Python virtual environment...$(NC)"
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r app/services/task-service/requirements.txt
	$(PIP) install pytest pytest-cov black flake8 mypy bandit
	@echo "$(GREEN)✓ Python environment ready$(NC)"

setup-pre-commit: ## Install pre-commit hooks
	@echo "$(BLUE)Installing pre-commit hooks...$(NC)"
	$(PIP) install pre-commit
	pre-commit install
	@echo "$(GREEN)✓ Pre-commit hooks installed$(NC)"

setup-local-cluster: ## Create local Kubernetes cluster (Kind)
	@echo "$(BLUE)Creating local Kubernetes cluster...$(NC)"
	@bash scripts/setup/setup-k8s-cluster.sh
	@echo "$(GREEN)✓ Local cluster created: $(CLUSTER_NAME)$(NC)"

setup-monitoring: ## Deploy monitoring stack (Prometheus, Grafana, etc.)
	@echo "$(BLUE)Deploying monitoring stack...$(NC)"
	@bash scripts/setup/setup-monitoring.sh
	@echo "$(GREEN)✓ Monitoring stack deployed$(NC)"

setup-vault: ## Deploy and initialize HashiCorp Vault
	@echo "$(BLUE)Setting up HashiCorp Vault...$(NC)"
	@bash scripts/setup/setup-vault.sh
	@echo "$(GREEN)✓ Vault initialized$(NC)"

bootstrap: install-tools setup-python setup-pre-commit setup-local-cluster setup-monitoring ## Complete local environment setup
	@echo "$(GREEN)✓ Environment bootstrap complete!$(NC)"

# ============ Development ============
dev-task-service: ## Run task-service locally
	@echo "$(BLUE)Starting task-service...$(NC)"
	cd app/services/task-service && uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

dev-user-service: ## Run user-service locally
	@echo "$(BLUE)Starting user-service...$(NC)"
	cd app/services/user-service && flask run --host 0.0.0.0 --port 8001

# ============ Testing ============
test: test-unit test-integration ## Run all tests
	@echo "$(GREEN)✓ All tests passed$(NC)"

test-unit: ## Run unit tests
	@echo "$(BLUE)Running unit tests...$(NC)"
	$(PYTEST) app/services/task-service/tests/unit -v --cov=app/services/task-service/src --cov-report=html --cov-report=term

test-integration: ## Run integration tests
	@echo "$(BLUE)Running integration tests...$(NC)"
	$(PYTEST) app/services/task-service/tests/integration -v

test-e2e: ## Run end-to-end tests
	@echo "$(BLUE)Running E2E tests...$(NC)"
	$(PYTEST) app/services/task-service/tests/e2e -v

test-coverage: ## Generate test coverage report
	@echo "$(BLUE)Generating coverage report...$(NC)"
	$(PYTEST) app/ --cov=app --cov-report=html --cov-report=term-missing
	@echo "$(GREEN)Coverage report: htmlcov/index.html$(NC)"

test-load: ## Run K6 load tests
	@echo "$(BLUE)Running K6 load tests...$(NC)"
	k6 run testing/load-testing/k6/scripts/load-test.js

test-chaos: ## Run chaos engineering tests
	@echo "$(BLUE)Running chaos tests...$(NC)"
	kubectl apply -f testing/chaos-engineering/litmus/experiments/

# ============ Code Quality ============
lint: ## Run linters (flake8, mypy)
	@echo "$(BLUE)Running linters...$(NC)"
	$(VENV)/bin/flake8 app/
	$(VENV)/bin/mypy app/

format: ## Format code with black
	@echo "$(BLUE)Formatting code...$(NC)"
	$(VENV)/bin/black app/

format-check: ## Check code formatting
	@echo "$(BLUE)Checking code format...$(NC)"
	$(VENV)/bin/black --check app/

# ============ Security ============
security-scan: security-scan-sast security-scan-dependencies security-scan-secrets ## Run all security scans

security-scan-sast: ## Run SAST scanning (Bandit)
	@echo "$(BLUE)Running SAST scan...$(NC)"
	$(VENV)/bin/bandit -r app/ -f json -o security-report.json

security-scan-dependencies: ## Scan dependencies (Snyk)
	@echo "$(BLUE)Scanning dependencies...$(NC)"
	@bash scripts/security/scan-dependencies.sh

security-scan-secrets: ## Scan for secrets (Gitleaks)
	@echo "$(BLUE)Scanning for secrets...$(NC)"
	gitleaks detect --source . --verbose

security-scan-containers: ## Scan container images (Trivy)
	@echo "$(BLUE)Scanning container images...$(NC)"
	@bash scripts/security/check-vulnerabilities.sh

# ============ Docker ============
docker-build: ## Build all Docker images
	@echo "$(BLUE)Building Docker images...$(NC)"
	docker build -t task-service:latest app/services/task-service/
	docker build -t user-service:latest app/services/user-service/
	docker build -t auth-service:latest app/services/auth-service/
	@echo "$(GREEN)✓ Images built$(NC)"

docker-push: ## Push images to AWS ECR
	@echo "$(BLUE)Pushing images to ECR...$(NC)"
	@bash scripts/deploy/push-to-ecr.sh

docker-scan: ## Scan Docker images for vulnerabilities
	@echo "$(BLUE)Scanning Docker images...$(NC)"
	trivy image task-service:latest
	trivy image user-service:latest
	trivy image auth-service:latest

# ============ Terraform ============
tf-init: ## Initialize Terraform
	@echo "$(BLUE)Initializing Terraform...$(NC)"
	cd $(TF_DIR)/environments/$(TF_ENV) && terraform init

tf-plan: ## Run Terraform plan
	@echo "$(BLUE)Running Terraform plan...$(NC)"
	cd $(TF_DIR)/environments/$(TF_ENV) && terraform plan -out=plan.tfplan

tf-apply: ## Apply Terraform changes
	@echo "$(BLUE)Applying Terraform changes...$(NC)"
	cd $(TF_DIR)/environments/$(TF_ENV) && terraform apply plan.tfplan

tf-destroy: ## Destroy Terraform infrastructure
	@echo "$(RED)WARNING: This will destroy infrastructure!$(NC)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		cd $(TF_DIR)/environments/$(TF_ENV) && terraform destroy; \
	fi

tf-validate: ## Validate Terraform configuration
	@echo "$(BLUE)Validating Terraform...$(NC)"
	cd $(TF_DIR)/environments/$(TF_ENV) && terraform validate

tf-fmt: ## Format Terraform files
	@echo "$(BLUE)Formatting Terraform files...$(NC)"
	terraform fmt -recursive $(TF_DIR)/

# ============ Helm ============
helm-lint: ## Lint Helm charts
	@echo "$(BLUE)Linting Helm charts...$(NC)"
	$(HELM) lint helm/charts/task-service/
	$(HELM) lint helm/charts/user-service/
	$(HELM) lint helm/charts/auth-service/

helm-template: ## Generate Helm templates
	@echo "$(BLUE)Generating Helm templates...$(NC)"
	$(HELM) template helm/charts/task-service/ --values helm/charts/task-service/values-dev.yaml

helm-upgrade-all: ## Upgrade all Helm releases
	@echo "$(BLUE)Upgrading all Helm releases...$(NC)"
	@bash scripts/helm/upgrade-all.sh

helm-diff: ## Show Helm chart differences
	@echo "$(BLUE)Showing Helm differences...$(NC)"
	@bash scripts/helm/diff-charts.sh

helmfile-sync: ## Sync all services with Helmfile
	@echo "$(BLUE)Syncing Helmfile...$(NC)"
	$(HELMFILE) sync

# ============ Deployment ============
deploy-dev: ## Deploy to dev environment
	@echo "$(BLUE)Deploying to dev environment...$(NC)"
	$(HELM) upgrade --install task-service helm/charts/task-service/ \
		--namespace dev --create-namespace \
		--values helm/charts/task-service/values-dev.yaml
	@echo "$(GREEN)✓ Deployed to dev$(NC)"

deploy-staging: ## Deploy to staging environment
	@echo "$(BLUE)Deploying to staging environment...$(NC)"
	$(HELM) upgrade --install task-service helm/charts/task-service/ \
		--namespace staging --create-namespace \
		--values helm/charts/task-service/values-staging.yaml
	@echo "$(GREEN)✓ Deployed to staging$(NC)"

deploy-prod: ## Deploy to production environment
	@echo "$(YELLOW)WARNING: Deploying to PRODUCTION!$(NC)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		$(HELM) upgrade --install task-service helm/charts/task-service/ \
			--namespace prod --create-namespace \
			--values helm/charts/task-service/values-prod.yaml; \
		echo "$(GREEN)✓ Deployed to production$(NC)"; \
	fi

# ============ ArgoCD ============
argocd-install: ## Install ArgoCD
	@echo "$(BLUE)Installing ArgoCD...$(NC)"
	kubectl create namespace argocd || true
	kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
	@echo "$(GREEN)✓ ArgoCD installed$(NC)"

argocd-login: ## Get ArgoCD admin password
	@echo "$(BLUE)ArgoCD Admin Password:$(NC)"
	@kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d && echo

argocd-sync: ## Sync ArgoCD applications
	@echo "$(BLUE)Syncing ArgoCD applications...$(NC)"
	argocd app sync --all

# ============ Monitoring ============
port-forward-grafana: ## Port-forward Grafana
	@echo "$(BLUE)Port-forwarding Grafana (http://localhost:3000)...$(NC)"
	kubectl port-forward -n monitoring svc/grafana 3000:80

port-forward-prometheus: ## Port-forward Prometheus
	@echo "$(BLUE)Port-forwarding Prometheus (http://localhost:9090)...$(NC)"
	kubectl port-forward -n monitoring svc/prometheus 9090:9090

port-forward-backstage: ## Port-forward Backstage
	@echo "$(BLUE)Port-forwarding Backstage (http://localhost:7000)...$(NC)"
	kubectl port-forward -n platform svc/backstage 7000:80

# ============ Backup & Recovery ============
backup-create: ## Create Velero backup
	@echo "$(BLUE)Creating backup...$(NC)"
	velero backup create backup-$(shell date +%Y%m%d-%H%M%S) --include-namespaces dev,staging,prod

backup-restore: ## Restore from latest backup
	@echo "$(BLUE)Restoring from backup...$(NC)"
	@bash scripts/backup/restore-from-backup.sh

# ============ Logs ============
logs-task-service: ## View task-service logs
	kubectl logs -n $(NAMESPACE) -l app=task-service --tail=100 -f

logs-user-service: ## View user-service logs
	kubectl logs -n $(NAMESPACE) -l app=user-service --tail=100 -f

# ============ Kafka ============
kafka-create-topics: ## Create Kafka topics
	@echo "$(BLUE)Creating Kafka topics...$(NC)"
	@bash scripts/kafka/create-topics.sh

kafka-monitor-lag: ## Monitor Kafka consumer lag
	@echo "$(BLUE)Monitoring Kafka lag...$(NC)"
	@bash scripts/kafka/monitor-lag.sh

# ============ Documentation ============
docs: ## Generate documentation
	@echo "$(BLUE)Generating documentation...$(NC)"
	mkdocs build

docs-serve: ## Serve documentation locally
	@echo "$(BLUE)Serving documentation at http://localhost:8000...$(NC)"
	mkdocs serve

# ============ Cleanup ============
clean: ## Clean up local artifacts
	@echo "$(BLUE)Cleaning up...$(NC)"
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.log" -delete
	rm -rf htmlcov/ .coverage .pytest_cache/ .mypy_cache/
	rm -rf $(VENV)
	@echo "$(GREEN)✓ Cleanup complete$(NC)"

clean-cluster: ## Delete local Kubernetes cluster
	@echo "$(RED)Deleting local cluster...$(NC)"
	kind delete cluster --name $(CLUSTER_NAME)

clean-all: clean clean-cluster ## Clean everything including cluster
	@echo "$(GREEN)✓ Complete cleanup done$(NC)"

# ============ Information ============
info: ## Show environment information
	@echo "$(BLUE)╔═══════════════════════════════════════════════════════════╗$(NC)"
	@echo "$(BLUE)║              Environment Information                      ║$(NC)"
	@echo "$(BLUE)╚═══════════════════════════════════════════════════════════╝$(NC)"
	@echo ""
	@echo "$(YELLOW)AWS:$(NC)"
	@echo "  Region:       $(AWS_REGION)"
	@echo "  Account ID:   $(AWS_ACCOUNT_ID)"
	@echo ""
	@echo "$(YELLOW)Kubernetes:$(NC)"
	@echo "  Context:      $$(kubectl config current-context 2>/dev/null || echo 'Not configured')"
	@echo "  Cluster:      $(CLUSTER_NAME)"
	@echo "  Namespace:    $(NAMESPACE)"
	@echo ""
	@echo "$(YELLOW)Tools:$(NC)"
	@echo "  Python:       $$(python3 --version 2>/dev/null || echo 'Not installed')"
	@echo "  Terraform:    $$(terraform version -json 2>/dev/null | jq -r '.terraform_version' || echo 'Not installed')"
	@echo "  Helm:         $$(helm version --short 2>/dev/null || echo 'Not installed')"
	@echo "  kubectl:      $$(kubectl version --client -o json 2>/dev/null | jq -r '.clientVersion.gitVersion' || echo 'Not installed')"
	@echo ""

# ============ CI/CD ============
ci-build: ## CI: Build stage
	@echo "$(BLUE)CI: Running build...$(NC)"
	$(MAKE) docker-build

ci-test: ## CI: Test stage
	@echo "$(BLUE)CI: Running tests...$(NC)"
	$(MAKE) test lint security-scan

ci-deploy: ## CI: Deploy stage
	@echo "$(BLUE)CI: Running deploy...$(NC)"
	$(MAKE) deploy-dev
