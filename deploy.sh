#!/bin/bash

# Deployment script for Google Cloud Run
# Usage: ./deploy.sh your-project-id

set -e

if [ -z "$1" ]; then
    echo "Usage: ./deploy.sh PROJECT_ID [REGION] [SERVICE_NAME]"
    echo "Example: ./deploy.sh my-project us-central1 python-executor"
    exit 1
fi

PROJECT_ID=$1
REGION=${2:-us-central1}
SERVICE_NAME=${3:-python-executor}

echo "==================================="
echo "Deploying to Google Cloud Run"
echo "==================================="
echo "Project ID: $PROJECT_ID"
echo "Region: $REGION"
echo "Service Name: $SERVICE_NAME"
echo "==================================="

# Set the project
echo "Setting GCP project..."
gcloud config set project $PROJECT_ID

# Build and submit to Google Cloud Build
echo "Building Docker image..."
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME

# Deploy to Cloud Run
echo "Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --timeout 60 \
  --max-instances 10

# Get the service URL
echo "==================================="
echo "Deployment complete!"
echo "==================================="
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)')
echo "Service URL: $SERVICE_URL"
echo "==================================="

# Test the deployment
echo "Testing the deployment..."
curl -X POST $SERVICE_URL/execute \
  -H "Content-Type: application/json" \
  -d '{
    "script": "def main():\n    return {\"message\": \"Deployment successful!\", \"status\": \"ok\"}"
  }'

echo ""
echo "==================================="
echo "Example cURL command:"
echo "==================================="
echo "curl -X POST $SERVICE_URL/execute \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -d '{"
echo "    \"script\": \"def main():\\n    return {\\\"result\\\": 42}\""
echo "  }'"
echo "==================================="