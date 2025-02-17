# ECR Repository
resource "aws_ecr_repository" "main" {
  name = var.app_name
  image_scanning_configuration {
    scan_on_push = true
  }
}

# Add lifecycle policy to keep only recent images
resource "aws_ecr_lifecycle_policy" "main" {
  repository = aws_ecr_repository.main.name

  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep last 5 images"
      selection = {
        tagStatus   = "any"
        countType   = "imageCountMoreThan"
        countNumber = 5
      }
      action = {
        type = "expire"
      }
    }]
  })
} 