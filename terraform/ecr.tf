# ECR Repository for API
resource "aws_ecr_repository" "api" {
  name = "${var.app_name}-api"
  force_delete = true
  image_scanning_configuration {
    scan_on_push = true
  }
}

# ECR Repository for Queue Consumer
resource "aws_ecr_repository" "queue" {
  name = "${var.app_name}-queue"
  force_delete = true
  image_scanning_configuration {
    scan_on_push = true
  }
}