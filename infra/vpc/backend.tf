terraform {

  backend "s3" {
    bucket         = "galactic-infra-bucket"
    key            = "aws-infra/terraform.tfstate"
    region         = "us-east-1"
    encrypt      = true
    # use_lockfile = true  #new S3 native locking, requires TF version to be at least1.9.0
    dynamodb_table = "aws-infra-state-lock"
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 4.67.0"
    }
  }
  required_version = ">= 1.4.2"
}