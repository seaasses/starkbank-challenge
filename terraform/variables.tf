variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

variable "app_name" {
  description = "Application name"
  type        = string
  default     = "stark-challenge"
}

variable "domain_name" {
  description = "Domain name for the application"
  type        = string
  default     = "stark-challenge.com"
}

variable "container_port" {
  description = "Port exposed by the docker image"
  type        = number
  default     = 8000
}

variable "container_cpu" {
  description = "CPU units for the container (1024 = 1 CPU)"
  type        = number
  default     = 512
}

variable "container_memory" {
  description = "Memory in MB for the container"
  type        = number
  default     = 1024
}

variable "desired_count" {
  description = "Number of containers to run"
  type        = number
  default     = 1
}

variable "redis_node_type" {
  description = "ElastiCache Redis node type"
  type        = string
  default     = "cache.t4g.micro"
}

variable "redis_num_cache_nodes" {
  description = "Number of cache nodes in the cluster"
  type        = number
  default     = 1
} 