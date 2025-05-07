# The RDS db-credentials previously created and stored in AWS Secrets Manager
data "aws_secretsmanager_secret" "galactic-db" {
  #secret_id = data.aws_secretsmanager_secret.galactic-db.id
  name = "galactic-db"
}

data "aws_secretsmanager_secret_version" "galactic-db" {
  secret_id = data.aws_secretsmanager_secret.galactic-db.id
}

