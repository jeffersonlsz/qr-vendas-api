# Cloud Run Deployment Script
# Usage: ./deploy.sh [project-id] [region]

#!/bin/bash

set -e

PROJECT_ID=${1:-$(gcloud config get-value project)}
REGION=${2:-us-central1}
SERVICE_NAME="sist-vendas-uber"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "🚀 Deploying ${SERVICE_NAME} to Cloud Run..."
echo "📦 Project: ${PROJECT_ID}"
echo "🌍 Region: ${REGION}"

# Build and push Docker image
echo "🔨 Building Docker image..."
docker build -t ${IMAGE_NAME} -f deploy/Dockerfile .

echo "📤 Pushing image to Container Registry..."
docker push ${IMAGE_NAME}

# Deploy to Cloud Run
echo "☁️ Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE_NAME} \
    --platform managed \
    --region ${REGION} \
    --allow-unauthenticated \
    --set-env-vars ENVIRONMENT=production,LOG_LEVEL=INFO \
    --memory 512Mi \
    --cpu 1 \
    --min-instances 1 \
    --max-instances 10

echo "✅ Deployment complete!"
echo "🔗 Service URL: $(gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format 'value(status.url)')"
