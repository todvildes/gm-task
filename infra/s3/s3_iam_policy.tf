data "aws_iam_policy_document" "bucket_policy" {
  statement {
    principals {
      type        = "AWS"
      identifiers = [aws_iam_role.this.arn]
    }

    actions = [
      "s3:ListBucket",
      "s3:Delete*",
      "s3:Get*",
      "s3:*Upload*",
      "s3:Put*"
    ]

    resources = [
      "arn:aws:s3:::${local.bucket_name}",
    ]
  }
}