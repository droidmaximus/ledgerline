#!/bin/bash

# Deploy to AWS EKS cluster
# Prerequisites: AWS CLI configured, kubectl installed, Terraform applied

set -e

CLUSTER_NAME="${CLUSTER_NAME:-pageindex-cluster}"
REGION="${AWS_REGION:-us-east-1}"
NAMESPACE="${NAMESPACE:-default}"

echo "=========================================="
echo "PageIndex EKS Deployment"
echo "=========================================="
echo ""

# Check prerequisites
echo "Checking prerequisites..."

if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not found"
    exit 1
fi

if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl not found"
    exit 1
fi

echo "✓ Prerequisites found"
echo ""

# Configure kubectl
echo "Configuring kubectl for cluster: $CLUSTER_NAME"
aws eks update-kubeconfig --name $CLUSTER_NAME --region $REGION
echo "✓ kubectl configured"
echo ""

# Check cluster connectivity
echo "Checking cluster connectivity..."
kubectl get nodes || {
    echo "❌ Cannot connect to cluster"
    exit 1
}
echo "✓ Connected to cluster"
echo ""

# Build and push Docker images
echo "=========================================="
echo "Building and Pushing Docker Images"
echo "=========================================="
echo ""

ECR_REGISTRY=$(aws ecr describe-registry --region $REGION | jq -r '.registryId').dkr.ecr.$REGION.amazonaws.com

for service in ingestion-service parser-service cache-service api-gateway; do
    echo "Building $service..."
    docker build -t $ECR_REGISTRY/pageindex-$service:latest services/$service/
    
    echo "Pushing to ECR..."
    aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ECR_REGISTRY
    docker push $ECR_REGISTRY/pageindex-$service:latest
    echo "✓ Pushed $service"
done

echo ""
echo "=========================================="
echo "Deploying to EKS"
echo "=========================================="
echo ""

# Deploy base resources
echo "Deploying base resources..."
kubectl apply -k kubernetes/base/ || echo "Note: Some base resources may already exist"

# Deploy production overlay
echo "Deploying production configuration..."
kubectl apply -k kubernetes/overlays/prod/ || echo "Note: Some resources may already exist"

# Deploy observability stack (if Helm available)
if command -v helm &> /dev/null; then
    echo "Deploying observability stack..."
    helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
    helm repo update
    helm upgrade --install prometheus prometheus-community/kube-prometheus-stack \
        --namespace monitoring \
        --create-namespace \
        --values kubernetes/base/observability/prometheus/values.yaml \
        --wait || echo "⚠ Prometheus installation skipped"
fi

echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""

echo "Check deployment status:"
echo "  kubectl get pods -A"
echo ""

echo "Get external IP:"
echo "  kubectl get service api-gateway"
echo ""

echo "View logs:"
echo "  kubectl logs -f deployment/api-gateway"
echo ""

echo "Scale a service:"
echo "  kubectl scale deployment api-gateway --replicas=5"
echo ""
