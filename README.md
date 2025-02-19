# Stark Bank Challenge

This project is a solution for the Stark Bank Back End Developer Challenge. It implements a FastAPI application that integrates with Stark Bank's API to handle invoice generation and payment processing.

## Overview

The application performs two main tasks:
1. Automatically generates 8-12 invoices every 3 hours to random people
2. Processes webhook callbacks when invoices are paid, automatically transferring the received amount (minus fees) to a specified Stark Bank account

The application is deployed at: stark-challenge.com

## Features

- **Automated Invoice Generation**: Scheduled job that creates 8-12 invoices every 3 hours using random person data
- **Webhook Processing**: Secure endpoint for receiving invoice payment notifications
- **Automatic Transfers**: Processes paid invoices and transfers funds to the specified account
- **Daily Reconciliation**: Daily job to process any undelivered credited invoices
- **Secure**: Implements webhook signature verification and replay attack prevention
- **Scalable**: Built with Redis for distributed locking and state management
- **Containerized**: Docker and Docker Compose setup for easy deployment

## Tech Stack

- Python 3.9
- FastAPI
- Redis
- Docker
- APScheduler
- Stark Bank SDK
- Pydantic
- Uvicorn


## Setup

1. Clone the repository
2. Create a `.env` file with the following variables:
   ```
    STARK_ENVIRONMENT=sandbox # or production
    STARK_PROJECT_ID=<your-project-id>
    STARKBANK_EC_PARAMETERS=<first part of your private key>
    STARKBANK_EC_PRIVATE_KEY=<last part of your private key>
    API_EXTERNAL_URL=<your-api-url> # must be https, you can use ngrok or similar to test locally
    ENVIRONMENT=development # or production (if running on cloud)

   ```

3. Run with Docker Compose:
   ```bash
   docker-compose up --build
   ```

The development environment includes hot-reloading and debug configurations. The webhook will be created automatically when the container starts.

## API Endpoints

- `POST /api/v1/webhooks/starkbank`: Webhook endpoint for Stark Bank events
- `GET /health`: Health check endpoint

## Scheduled Jobs

1. **Invoice Generation**
   - Runs every 3 hours
   - Creates 8-12 invoices to random people
   - Uses distributed locking to prevent duplicate executions

2. **Undelivered Invoice Processing**
   - Runs daily at 1 AM
   - Processes any undelivered credited invoices
   - Implements retry mechanism for failed transfers

## Infrastructure

The application is containerized and can be deployed to any cloud provider. Terraform configurations are provided for AWS deployment, including:
- Load Balancer
- Redis instance
- ECR repository
- IAM roles and policies

## Security Features

- Webhook signature verification
- Event replay attack prevention
- Distributed locking for scheduled jobs

## Monitoring

The application includes:
- Health check endpoints
- Docker health checks
- Redis connection monitoring
