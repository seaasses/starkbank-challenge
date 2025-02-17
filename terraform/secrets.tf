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
