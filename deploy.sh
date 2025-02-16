#!/bin/bash

set -e

echo "Setting up deployment variables..."
AWS_REGION="us-east-1"
APP_NAME="starkbank-challenge"

echo "Getting AWS account ID..."
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

echo "Constructing ECR repository URL..."
ECR_REPO="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${APP_NAME}"

echo "Logging into ECR..."
aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com

echo "Building Docker image..."
docker build -t ${APP_NAME}:latest .

echo "Tagging Docker image..."
docker tag ${APP_NAME}:latest ${ECR_REPO}:latest

echo "Pushing image to ECR..."
docker push ${ECR_REPO}:latest

echo "Deployment complete!"