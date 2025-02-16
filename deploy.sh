#!/bin/bash

set -e

AWS_REGION="us-east-1"
APP_NAME="starkbank-challenge"

AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

ECR_REPO="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${APP_NAME}"

aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com

docker build -t ${APP_NAME}:latest .

docker tag ${APP_NAME}:latest ${ECR_REPO}:latest

docker push ${ECR_REPO}:latest