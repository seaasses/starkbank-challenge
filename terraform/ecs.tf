# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "${var.app_name}-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

resource "aws_ecs_task_definition" "app" {
  family                   = "${var.app_name}-task"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.container_cpu
  memory                   = var.container_memory
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([
    {
      name      = "${var.app_name}-container"
      image     = "${aws_ecr_repository.api.repository_url}:latest"
      essential = true

      healthCheck = {
        command     = ["CMD-SHELL", "curl -f http://localhost:${var.container_port}/health || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 60
      }

      portMappings = [
        {
          containerPort = var.container_port
          protocol      = "tcp"
        }
      ]

      environment = [
        {
          name  = "ENVIRONMENT"
          value = var.environment
        },
        {
          name  = "REDIS_URL"
          value = "redis://${aws_elasticache_cluster.redis.cache_nodes[0].address}:6379/0"
        },
        {
          name  = "STARK_ENVIRONMENT"
          value = "sandbox"
        },
        {
          name  = "API_EXTERNAL_URL"
          value = "https://${var.domain_name}"
        },
        {
          name  = "RABBITMQ_HOST"
          value = "${var.app_name}-rabbitmq.${var.app_name}-cluster.local"
        },
        {
          name  = "RABBITMQ_PORT"
          value = "5672"
        }
      ]

      secrets = [
        {
          name      = "RABBITMQ_USER"
          valueFrom = "${aws_secretsmanager_secret.rabbitmq.arn}:username::"
        },
        {
          name      = "RABBITMQ_PASS"
          valueFrom = "${aws_secretsmanager_secret.rabbitmq.arn}:password::"
        },
        {
          name      = "STARK_PROJECT_ID"
          valueFrom = "${aws_secretsmanager_secret.app_secrets.arn}:STARK_PROJECT_ID::"
        },
        {
          name      = "STARKBANK_EC_PARAMETERS"
          valueFrom = "${aws_secretsmanager_secret.app_secrets.arn}:STARKBANK_EC_PARAMETERS::"
        },
        {
          name      = "STARKBANK_EC_PRIVATE_KEY"
          valueFrom = "${aws_secretsmanager_secret.app_secrets.arn}:STARKBANK_EC_PRIVATE_KEY::"
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = "/ecs/${var.app_name}"
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "ecs"
        }
      }
    }
  ])
}

resource "aws_ecs_service" "app" {
  name            = "${var.app_name}-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.app.arn
  desired_count   = var.desired_count
  launch_type     = "FARGATE"

  deployment_minimum_healthy_percent = 100
  deployment_maximum_percent         = 200
  health_check_grace_period_seconds  = 30

  enable_execute_command = true # Enables ECS Exec for debugging
  force_new_deployment   = true # Forces new deployment when task definition changes

  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }

  network_configuration {
    security_groups  = [aws_security_group.ecs_tasks.id]
    subnets          = module.vpc.private_subnets
    assign_public_ip = false # Using NAT Gateway instead
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.app.arn
    container_name   = "${var.app_name}-container"
    container_port   = var.container_port
  }

  depends_on = [aws_lb_listener.https, aws_ecs_service.rabbitmq]

  lifecycle {
    create_before_destroy = true
  }
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "app" {
  name              = "/ecs/${var.app_name}"
  retention_in_days = 30
}

# RabbitMQ Server Task Definition
resource "aws_ecs_task_definition" "rabbitmq" {
  family                   = "${var.app_name}-rabbitmq"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = 512
  memory                   = 1024
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([
    {
      name      = "${var.app_name}-rabbitmq"
      image     = "rabbitmq:3"
      essential = true

      portMappings = [
        {
          containerPort = 5672
          protocol      = "tcp"
        }
      ]

      secrets = [
        {
          name      = "RABBITMQ_DEFAULT_USER"
          valueFrom = "${aws_secretsmanager_secret.rabbitmq.arn}:username::"
        },
        {
          name      = "RABBITMQ_DEFAULT_PASS"
          valueFrom = "${aws_secretsmanager_secret.rabbitmq.arn}:password::"
        },
        {
          name      = "RABBITMQ_ERLANG_COOKIE"
          valueFrom = "${aws_secretsmanager_secret.rabbitmq.arn}:erlang_cookie::"
        }
      ]

      linuxParameters = {
        initProcessEnabled = true
      }

      user = "rabbitmq"

      healthCheck = {
        command     = ["CMD", "rabbitmq-diagnostics", "check_running"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 60
      }

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = "/ecs/${var.app_name}"
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "ecs-rabbitmq"
        }
      }
    }
  ])
}

# RabbitMQ Service
resource "aws_service_discovery_private_dns_namespace" "main" {
  name        = "${var.app_name}-cluster.local"
  description = "Private DNS namespace for ECS services"
  vpc         = module.vpc.vpc_id
}

resource "aws_service_discovery_service" "rabbitmq" {
  name = "${var.app_name}-rabbitmq"

  dns_config {
    namespace_id = aws_service_discovery_private_dns_namespace.main.id

    dns_records {
      ttl  = 10
      type = "A"
    }

    routing_policy = "MULTIVALUE"
  }

  health_check_custom_config {
    failure_threshold = 1
  }
}

resource "aws_ecs_service" "rabbitmq" {
  name            = "${var.app_name}-rabbitmq"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.rabbitmq.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    security_groups  = [aws_security_group.ecs_tasks.id]
    subnets          = module.vpc.private_subnets
    assign_public_ip = false
  }

  service_registries {
    registry_arn = aws_service_discovery_service.rabbitmq.arn
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Queue Consumer Task Definition
resource "aws_ecs_task_definition" "queue_consumer" {
  family                   = "${var.app_name}-queue-consumer"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = 512
  memory                   = 1024
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([
    {
      name      = "${var.app_name}-queue-consumer"
      image     = "${aws_ecr_repository.queue.repository_url}:latest"
      essential = true

      environment = [
        {
          name  = "RABBITMQ_HOST"
          value = "${var.app_name}-rabbitmq.${var.app_name}-cluster.local"
        },
        {
          name  = "RABBITMQ_PORT"
          value = "5672"
        },
        {
          name  = "NUM_CONSUMERS_PER_INSTANCE"
          value = "50"
        },
        {
          name  = "QUEUE_NAME"
          value = "starkbank-queue"
        }
      ]

      secrets = [
        {
          name      = "RABBITMQ_USER"
          valueFrom = "${aws_secretsmanager_secret.rabbitmq.arn}:username::"
        },
        {
          name      = "RABBITMQ_PASS"
          valueFrom = "${aws_secretsmanager_secret.rabbitmq.arn}:password::"
        },
        {
          name      = "STARK_PROJECT_ID"
          valueFrom = "${aws_secretsmanager_secret.app_secrets.arn}:STARK_PROJECT_ID::"
        },
        {
          name      = "STARKBANK_EC_PARAMETERS"
          valueFrom = "${aws_secretsmanager_secret.app_secrets.arn}:STARKBANK_EC_PARAMETERS::"
        },
        {
          name      = "STARKBANK_EC_PRIVATE_KEY"
          valueFrom = "${aws_secretsmanager_secret.app_secrets.arn}:STARKBANK_EC_PRIVATE_KEY::"
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = "/ecs/${var.app_name}"
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "ecs-consumer"
        }
      }
    }
  ])
}

# Queue Consumer Service
resource "aws_ecs_service" "queue_consumer" {
  name            = "${var.app_name}-queue-consumer"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.queue_consumer.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    security_groups  = [aws_security_group.ecs_tasks.id]
    subnets          = module.vpc.private_subnets
    assign_public_ip = false
  }

  depends_on = [aws_ecs_service.rabbitmq]

  lifecycle {
    create_before_destroy = true
  }
}
