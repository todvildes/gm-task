terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 4.67.0"
    }
  }
  required_version = ">= 1.4.2"
}

resource "aws_s3_bucket" "state_bucket" {
  bucket = "galactic-infra-bucket"
}

resource "aws_s3_bucket_versioning" "state_bucket_versioning" {
  bucket = aws_s3_bucket.state_bucket.id
  versioning_configuration {
    status = "Enabled"
  }
}
# Old way of managing DynamoDB-based locking
resource "aws_dynamodb_table" "statelock" {
  name         = "aws-infra-state-lock"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }
}