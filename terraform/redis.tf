resource "aws_elasticache_subnet_group" "redis" {
  name       = "${var.app_name}-redis-subnet-group"
  subnet_ids = module.vpc.private_subnets
}

resource "aws_elasticache_parameter_group" "redis" {
  family = "redis7"
  name   = "${var.app_name}-redis-params"

  parameter {
    name  = "maxmemory-policy"
    value = "allkeys-lru"
  }
}

resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "${var.app_name}-redis"
  engine              = "redis"
  node_type           = var.redis_node_type
  num_cache_nodes     = var.redis_num_cache_nodes
  parameter_group_name = aws_elasticache_parameter_group.redis.name
  port                = 6379
  security_group_ids  = [aws_security_group.redis.id]
  subnet_group_name   = aws_elasticache_subnet_group.redis.name
} 