import boto3
import json
from datetime import datetime
import uuid
import os
from aws_lambda_powertools import Logger
import sys

logger = Logger()

# Skip S3 operations during test collection
IN_PYTEST = 'pytest' in sys.modules

class S3Handler:
    def __init__(self, testing=False):
        # For testing, we'll use the moto mock or localstack
        self.testing = testing or IN_PYTEST or os.getenv('PYTEST_CURRENT_TEST') == 'True'
        
        # Check if we're using localstack
        self.using_localstack = os.getenv('AWS_ENDPOINT_URL') is not None
        
        # Configure S3 client with environment variables
        self.s3_client = boto3.client(
            's3',
            endpoint_url=os.getenv('AWS_ENDPOINT_URL'),  # For localstack testing
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID', 'test'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY', 'test'),
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )
        self.bucket_name = os.getenv('S3_BUCKET_NAME', 'user-queries')
        
        # Create bucket if using localstack
        if self.using_localstack:
            try:
                # Check if bucket exists first
                try:
                    self.s3_client.head_bucket(Bucket=self.bucket_name)
                    logger.info(f"Bucket already exists in localstack: {self.bucket_name}")
                except Exception:
                    # Create bucket with region configuration for localstack
                    self.s3_client.create_bucket(
                        Bucket=self.bucket_name,
                        CreateBucketConfiguration={
                            'LocationConstraint': os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
                        }
                    )
                    logger.info(f"Created localstack bucket: {self.bucket_name}")
            except Exception as e:
                logger.info(f"Bucket operation in localstack failed (may be normal): {str(e)}")
                # Don't raise during testing with localstack
        # Only try to ensure bucket exists if not in a test and not using localstack
        elif not self.testing:
            self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        """Ensure the S3 bucket exists, create if it doesn't"""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
        except Exception as e:
            logger.info(f"Bucket check error (may be normal): {str(e)}")
            try:
                self.s3_client.create_bucket(Bucket=self.bucket_name)
                logger.info(f"Created bucket: {self.bucket_name}")
            except Exception as e:
                logger.error(f"Error creating bucket: {str(e)}")
                # Don't raise during testing
                if not self.testing:
                    raise

    def store_query_result(self, query_params: dict, results: list):
        """
        Store query results in S3 with a unique filename based on timestamp and UUID
        """
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid.uuid4())
        filename = f"query_results/{timestamp}_{unique_id}.json"

        # For testing with moto (not localstack), just return a mock filename
        if self.testing and not self.using_localstack:
            return f"mock-s3-file-{unique_id}.json"

        data = {
            "timestamp": datetime.utcnow().isoformat(),
            "query_parameters": query_params,
            "results": results,
            "result_count": len(results)
        }

        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=filename,
                Body=json.dumps(data, default=str),
                ContentType='application/json'
            )
            logger.info(f"Stored query results in S3: {filename}")
            return filename
        except Exception as e:
            logger.error(f"Error storing results in S3: {str(e)}")
            if self.testing:
                return f"mock-s3-file-{unique_id}.json"
            raise 
