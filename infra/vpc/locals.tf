locals {

  cidr_block = "10.0.0.0/16"

  region = "us-east-1"

  tags = {
    Name = "galactic devops home task"
  }

  dbname = "galactic-rds-postgres"

  eksname = "galactic-eks"
}