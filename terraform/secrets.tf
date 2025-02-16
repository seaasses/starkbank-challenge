resource "aws_secretsmanager_secret" "app_secrets" {
  name = "${var.app_name}-secrets"
}

resource "aws_secretsmanager_secret_version" "app_secrets" {
  secret_id = aws_secretsmanager_secret.app_secrets.id
  secret_string = jsonencode({
    STARK_PROJECT_ID         = ""
    STARKBANK_EC_PARAMETERS  = ""
    STARKBANK_EC_PRIVATE_KEY = ""
  })
} 
