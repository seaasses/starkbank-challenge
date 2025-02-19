#!/bin/bash

set -e

echo "Setting up deployment variables..."
AWS_REGION="us-east-1"
APP_NAME="starkbank-challenge"

echo "Getting AWS account ID..."
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

echo "Constructing ECR repository URLs..."
API_ECR_REPO="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${APP_NAME}-api"
QUEUE_ECR_REPO="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${APP_NAME}-queue"

echo "Logging into ECR..."
aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com

echo "Building and pushing API Docker image..."
docker build -t ${APP_NAME}-api:latest ./api/
docker tag ${APP_NAME}-api:latest ${API_ECR_REPO}:latest
docker push ${API_ECR_REPO}:latest

echo "Building and pushing Queue Consumer Docker image..."
docker build -t ${APP_NAME}-queue:latest ./queue/
docker tag ${APP_NAME}-queue:latest ${QUEUE_ECR_REPO}:latest
docker push ${QUEUE_ECR_REPO}:latest

echo "Images pushed successfully!"

echo "Forcing new deployment of ECS services..."
aws ecs update-service --cluster ${APP_NAME}-cluster \
    --service ${APP_NAME}-service \
    --force-new-deployment \
    --region ${AWS_REGION} \
    --no-cli-pager > /dev/null 2>&1 &

aws ecs update-service --cluster ${APP_NAME}-cluster \
    --service ${APP_NAME}-queue-consumer \
    --force-new-deployment \
    --region ${AWS_REGION} \
    --no-cli-pager > /dev/null 2>&1 &

echo "Force deployment initiated successfully!" 