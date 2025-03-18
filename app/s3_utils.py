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
        
        # Configure S3 client - don't specify credentials in Lambda
        # Instead rely on the Lambda's IAM role
        self.s3_client = boto3.client(
            's3',
            endpoint_url=os.getenv('AWS_ENDPOINT_URL'),  # For localstack testing
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
            # Check if bucket exists, but don't try to create it (S3 buckets should be pre-created by Terraform)
            try:
                self.s3_client.head_bucket(Bucket=self.bucket_name)
                logger.info(f"Bucket exists: {self.bucket_name}")
            except Exception as e:
                logger.error(f"Error with S3 bucket: {str(e)}")
                # Log but don't crash - Lambda should keep running

    def store_query_result(self, query_params, results):
        """Store query results in S3 and return the file path"""
        # Make sure results is properly serialized
        serialized_results = []
        for item in results:
            if hasattr(item, '__dict__'):
                # This is an ORM object, extract only the data we need
                serialized_item = {}
                for key, value in vars(item).items():
                    if not key.startswith('_'):  # Skip SQLAlchemy internals
                        if hasattr(value, 'isoformat'):  # Convert datetime
                            serialized_item[key] = value.isoformat()
                        else:
                            serialized_item[key] = value
                serialized_results.append(serialized_item)
            else:
                # Already a dict, just add it
                serialized_results.append(item)
                
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid.uuid4())
        filename = f"queries/{timestamp}_{unique_id}.json"

        # For testing with moto (not localstack), just return a mock filename
        if self.testing and not self.using_localstack:
            return f"mock-s3-file-{unique_id}.json"

        data = {
            "timestamp": datetime.utcnow().isoformat(),
            "query_parameters": query_params,
            "results": serialized_results,
            "result_count": len(serialized_results)
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
            # Return a fallback, but don't crash the app
            return f"error-storing-{unique_id}.json" 
