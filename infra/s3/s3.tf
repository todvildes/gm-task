module "s3_bucket" {
  source  = "terraform-aws-modules/s3-bucket/aws"
  version = "4.8.0"

  bucket = local.bucket_name

  # Allow deletion of non-empty bucket
  #force_destroy = true

  versioning = {
    enabled    = true
    mfa_delete = false
  }

  # S3 bucket-level Public Access Block configuration (by default now AWS has made this default as true for S3 bucket-level block public access)
  # block_public_acls       = true
  # block_public_policy     = true
  # ignore_public_acls      = true
  # restrict_public_buckets = true

  attach_policy                             = true
  policy                                    = data.aws_iam_policy_document.bucket_policy.json
  attach_deny_insecure_transport_policy     = true
  attach_require_latest_tls_policy          = true
  attach_deny_incorrect_encryption_headers  = true
  attach_deny_incorrect_kms_key_sse         = true
  allowed_kms_key_arn                       = aws_kms_key.objects.arn
  attach_deny_unencrypted_object_uploads    = true
  attach_deny_ssec_encrypted_object_uploads = true

#  KMS server-side encryption
  server_side_encryption_configuration = {
    rule = {
      apply_server_side_encryption_by_default = {
        kms_master_key_id = aws_kms_key.objects.arn
        sse_algorithm     = "aws:kms"
      }
    }
  }

  # Example lifecycle rules
  # lifecycle_rule = [
  #   {
  #     id      = "query"
  #     enabled = true
  #
  #     filter = {
  #       tags = {
  #         some    = "value"
  #         another = "value2"
  #       }
  #     }
  #     transition = [
  #       {
  #         days          = 30
  #         storage_class = "ONEZONE_IA"
  #         }, {
  #         days          = 60
  #         storage_class = "GLACIER"
  #       }
  #     ]
  #   },
  #   {
  #     noncurrent_version_transition = [
  #       {
  #         days          = 30
  #         storage_class = "STANDARD_IA"
  #       },
  #       {
  #         days          = 60
  #         storage_class = "ONEZONE_IA"
  #       },
  #       {
  #         days          = 90
  #         storage_class = "GLACIER"
  #       },
  #     ]
  #
  #     noncurrent_version_expiration = {
  #       days = 300
  #     }
  #   },
  #   {
  #     id      = "log2"
  #     enabled = true
  #
  #     filter = {
  #       prefix                   = "query2"
  #       object_size_greater_than = 200000
  #       object_size_less_than    = 500000
  #       tags = {
  #         some    = "value"
  #         another = "value2"
  #       }
  #     }
  #
  #     noncurrent_version_transition = [
  #       {
  #         days          = 30
  #         storage_class = "STANDARD_IA"
  #       },
  #     ]
  #
  #     noncurrent_version_expiration = {
  #       days = 300
  #     }
  #   },
  # ]

  tags = {
    Terraform = "true"
  }
}
