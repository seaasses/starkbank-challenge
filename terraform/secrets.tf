resource "aws_secretsmanager_secret" "app_secrets" {
  name = "${var.app_name}-application-secrets"

  lifecycle {
    prevent_destroy = false
  }
  recovery_window_in_days = 0
}

resource "aws_secretsmanager_secret_version" "app_secrets" {
  secret_id = aws_secretsmanager_secret.app_secrets.id
  secret_string = jsonencode({
    STARK_PROJECT_ID         = ""
    STARKBANK_EC_PARAMETERS  = ""
    STARKBANK_EC_PRIVATE_KEY = ""
  })
}

resource "random_password" "rabbitmq" {
  length           = 32
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

resource "random_password" "rabbitmq_erlang_cookie" {
  length           = 20
  special          = false
  override_special = ""
}

resource "aws_secretsmanager_secret" "rabbitmq" {
  name = "${var.app_name}-rabbitmq-credentials"
}

resource "aws_secretsmanager_secret_version" "rabbitmq" {
  secret_id = aws_secretsmanager_secret.rabbitmq.id
  secret_string = jsonencode({
    username      = "user"
    password      = random_password.rabbitmq.result
    erlang_cookie = random_password.rabbitmq_erlang_cookie.result
  })
}
