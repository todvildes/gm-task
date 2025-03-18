# DevOps Home Task

This project is designed to test various DevOps skills including AWS, Terraform, Helm, EKS, Docker, and GitHub Actions. It consists of a Python application that can be deployed both as a containerized application in EKS and as a Lambda function behind API Gateway.

## Application Overview

The application is a simple user management API with the following endpoints:

- `GET /healthcheck` - Health check endpoint
- `POST /populate` - Populate database with random user data
- `GET /users` - Read users with filters (name, city, age range)
- `DELETE /users/{user_id}` - Delete a specific user

## Technical Stack

- Python 3.11
- FastAPI
- PostgreSQL
- Docker
- AWS Services (EKS, Lambda, API Gateway)
- Terraform
- Helm

## Environment Variables

### Required Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://postgres:postgres@localhost:5432/users` | Yes |
| `ENVIRONMENT` | Deployment environment (test, dev, prod) | None | Yes |
| `AWS_DEFAULT_REGION` | AWS region | `us-east-1` | Yes for S3 storage |
| `AWS_ACCESS_KEY_ID` | AWS access key | None | Yes for S3 storage |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | None | Yes for S3 storage |
| `S3_BUCKET_NAME` | S3 bucket for storing query results | `user-queries` | Yes for S3 storage |

### Docker-specific Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `AWS_ENDPOINT_URL` | Endpoint URL for localstack | `http://localhost:4566` | Only for local testing with localstack |

### Lambda-specific Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `AWS_LAMBDA_FUNCTION_NAME` | Lambda function name | None | Yes for Lambda |
| `AWS_REGION` | AWS region for Lambda | `us-east-1` | Yes for Lambda |
| `AWS_EXECUTION_ENV` | Lambda execution environment | `AWS_Lambda_python3.11` | Yes for Lambda |
| `AWS_ENDPOINT_URL` | Endpoint URL for localstack | `http://localhost:4566` | Only for local testing with localstack |
| `API_GATEWAY_BASE_PATH` | Base path for API Gateway | `/` | For Lambda with API Gateway |

### Testing Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `PYTEST_CURRENT_TEST` | Set to `True` when running tests | None | Yes for tests |
| `AWS_SECURITY_TOKEN` | AWS security token for testing | `testing` | Only for tests |
| `AWS_SESSION_TOKEN` | AWS session token for testing | `testing` | Only for tests |

## Task Requirements

This task offers two deployment approaches. You may choose **either** the Lambda approach **OR** the EKS approach based on your expertise and preference.

### Option 1: AWS Lambda Approach
If you choose this approach, implement:

1. **Infrastructure as Code (Terraform)**
   - VPC with proper networking setup (public/private subnets, NAT Gateway, Internet Gateway, routing tables)
   - RDS PostgreSQL instance (in private subnets with security groups and backup configuration)
   - Lambda function (with IAM roles, VPC configuration, environment variables)
   - API Gateway (REST API configuration with Lambda integration)
   - S3 bucket for query results storage

2. **CI/CD Pipeline (GitHub Actions)**
   - Test the application
   - Build and package Lambda function
   - Deploy to Lambda and API Gateway
   - Include error handling and notifications

### Option 2: EKS Container Approach
If you choose this approach, implement:

1. **Infrastructure as Code (Terraform)**
   - VPC with proper networking setup (public/private subnets, NAT Gateway, Internet Gateway, routing tables)
   - EKS cluster (node groups, IAM roles/policies, security groups)
   - RDS PostgreSQL instance (in private subnets with security groups and backup configuration)
   - S3 bucket for query results storage

2. **Kubernetes Deployment (Helm)**
   - Deployment configuration (resource limits/requests, health checks, environment variables)
   - Service configuration (service type, port configuration)
   - Ingress configuration (TLS, path routing)
   - Secrets management (database credentials, sensitive information)
   - Horizontal Pod Autoscaling (CPU/Memory based scaling, min/max replicas)

3. **CI/CD Pipeline (GitHub Actions)**
   - Test the application
   - Build and push Docker image
   - Deploy to EKS using Helm
   - Include error handling and notifications

### Requirements for All Code
- Use modular organization
- Implement proper state management (for Terraform)
- Follow security best practices
- Include variables for customization
- Provide comprehensive documentation

**Important**: Please clearly document which approach you've selected in your submission.

## Local Development

1. Set up the environment:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. Set up PostgreSQL and environment variables:
   ```bash
   export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/users"
   export ENVIRONMENT="dev"
   export AWS_DEFAULT_REGION="us-east-1"
   export AWS_ACCESS_KEY_ID="your-access-key"
   export AWS_SECRET_ACCESS_KEY="your-secret-key"
   export S3_BUCKET_NAME="user-queries"
   ```

3. Run the application:
   ```bash
   uvicorn app.main:app --reload
   ```

## Docker Build and Run

Build the Docker image:
```bash
docker build -t user-api .
```

Run the Docker container with required environment variables:
```bash
docker run -p 8000:8000 \
  -e DATABASE_URL="postgresql://postgres:postgres@host.docker.internal:5432/users" \
  -e ENVIRONMENT="dev" \
  -e AWS_DEFAULT_REGION="us-east-1" \
  -e AWS_ACCESS_KEY_ID="your-access-key" \
  -e AWS_SECRET_ACCESS_KEY="your-secret-key" \
  -e S3_BUCKET_NAME="user-queries" \
  user-api
```

## Running with Localstack

1. Start localstack and PostgreSQL using docker-compose:
   ```bash
   docker-compose up -d
   ```

2. Create the S3 bucket in localstack:
   ```bash
   aws --endpoint-url=http://localhost:4566 s3 mb s3://user-queries
   ```

3. Run the application with localstack endpoint:
   ```bash
   export AWS_ENDPOINT_URL="http://localhost:4566"
   uvicorn app.main:app --reload
   ```

4. Or run the Docker container with localstack:
   ```bash
   docker run -p 8000:8000 \
     -e DATABASE_URL="postgresql://postgres:postgres@host.docker.internal:5432/users" \
     -e ENVIRONMENT="dev" \
     -e AWS_DEFAULT_REGION="us-east-1" \
     -e AWS_ACCESS_KEY_ID="test" \
     -e AWS_SECRET_ACCESS_KEY="test" \
     -e S3_BUCKET_NAME="user-queries" \
     -e AWS_ENDPOINT_URL="http://host.docker.internal:4566" \
     user-api
   ```

## Lambda Deployment

### Creating a Lambda Deployment Package

This repository includes a script to create a Lambda deployment package that properly bundles the application code with its dependencies for AWS Lambda:

```bash
./create_lambda_package.sh
```

The script performs the following operations:
1. Creates a package directory and copies all Python files from the app directory to the root level
2. Filters the requirements file to exclude packages not needed in Lambda (like localstack and pytest)
3. Installs dependencies with Lambda-specific flags:
   - Uses the manylinux2014_x86_64 platform for compatibility
   - Targets Python 3.11
   - Only includes binary packages
4. Removes unnecessary files to reduce package size (caches, tests, etc.)
5. Creates a ZIP file ready for Lambda deployment

After running the script, you'll have a `lambda_deployment_package.zip` file that can be deployed to AWS Lambda either manually or via Terraform.

### Lambda Handler Configuration

When configuring your Lambda function, use `main.lambda_handler` as the handler. This points to the `lambda_handler` function in the `main.py` file, which is preconfigured to work with API Gateway.

### Required Environment Variables for Lambda

Make sure to set the following environment variables in your Lambda function configuration:

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | Connection string to your RDS instance |
| `ENVIRONMENT` | Deployment environment (dev, prod) |
| `AWS_REGION` | The region where your Lambda is deployed |
| `S3_BUCKET_NAME` | Name of the S3 bucket for storing query results |
| `API_GATEWAY_BASE_PATH` | Base path for API Gateway (e.g., `/dev` for dev stage) |

## Evaluation Criteria

### For Lambda Approach (if selected)
1. Infrastructure as Code (50%):
   - Proper resource organization and modularity
   - Security best practices
   - State management
   - Documentation
   - Resource optimization for Lambda, API Gateway, and RDS
   - VPC configuration and networking

2. CI/CD Pipeline (30%):
   - Proper testing implementation
   - Lambda packaging and deployment
   - API Gateway configuration
   - Error handling and notifications
   - Pipeline efficiency and reliability

3. General (20%):
   - Code quality and organization
   - Documentation quality
   - Security considerations
   - Problem-solving approach
   - Best practices implementation

### For EKS Approach (if selected)
1. Infrastructure as Code (40%):
   - Proper resource organization and modularity
   - Security best practices
   - State management
   - Documentation
   - Resource optimization for EKS and RDS
   - VPC configuration and networking

2. Kubernetes/Helm (40%):
   - Chart organization
   - Resource configuration
   - Security considerations
   - Scalability setup
   - Documentation
   - Secret management

3. CI/CD Pipeline (10%):
   - Docker image building and pushing
   - Helm deployment
   - Error handling and notifications
   - Pipeline efficiency and reliability

4. General (10%):
   - Code quality and organization
   - Documentation quality
   - Security considerations
   - Problem-solving approach
   - Best practices implementation

## Submission Requirements

1. Fork this repository
2. Implement the required infrastructure code
3. Document your solution
4. Create a pull request with your implementation

## Testing Strategy

The project includes several types of tests:

### Docker Tests

Tests the application running in a Docker container:

```bash
# Run with localstack
AWS_ENDPOINT_URL=http://localhost:4566 pytest tests/test_docker.py -v
```

These tests verify that the API endpoints work correctly when the application is running in a Docker container.

### Lambda Tests

Tests the application running as an AWS Lambda function:

```bash
# Run with localstack and Lambda environment variables
AWS_ENDPOINT_URL=http://localhost:4566 \
AWS_LAMBDA_FUNCTION_NAME=test-function \
AWS_REGION=us-east-1 \
AWS_EXECUTION_ENV=AWS_Lambda_python3.11 \
pytest tests/test_lambda.py -v
```

Our Lambda testing approach:

1. **Direct Lambda Tests**: We invoke the Lambda handler function directly with API Gateway-like event payloads. This approach completely bypasses the need for API Gateway while still testing the Lambda function's behavior with realistic inputs.

2. **Lambda Environment Simulation**: We set the necessary AWS Lambda environment variables (`AWS_LAMBDA_FUNCTION_NAME`, `AWS_REGION`, `AWS_EXECUTION_ENV`) to simulate the Lambda execution environment.

3. **S3 Integration**: We use localstack's S3 implementation for testing the S3 storage functionality, ensuring that our Lambda function correctly interacts with S3.

#### Why We Don't Use API Gateway for Testing

We've intentionally removed API Gateway from our testing strategy for several reasons:

- Localstack's API Gateway implementation has significant limitations
- Direct Lambda invocation provides more reliable and consistent test results
- The tests run faster without the API Gateway overhead
- We get the same code coverage with direct Lambda invocation

By directly invoking the Lambda handler with API Gateway-like event payloads, we get:

- More reliable tests
- Faster test execution
- Consistent behavior across environments
- The same code coverage as API Gateway tests

### Running Tests

Before running tests, make sure you have the test database set up:

```bash
# Create the test database
docker exec -it home-task-postgres-1 psql -U postgres -c 'CREATE DATABASE users_test;'
```

To run all Lambda tests:

```bash
AWS_ENDPOINT_URL=http://localhost:4566 \
AWS_LAMBDA_FUNCTION_NAME=test-function \
AWS_REGION=us-east-1 \
AWS_EXECUTION_ENV=AWS_Lambda_python3.11 \
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/users_test \
pytest tests/test_lambda.py -v
```

To run Docker tests, you need to ensure port 8000 is available. If you're running the application with docker-compose, you'll need to stop it first or modify the test port:

```bash
# Stop the running containers if they're using port 8000
docker compose stop app

# Run Docker tests
AWS_ENDPOINT_URL=http://localhost:4566 \
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/users_test \
pytest tests/test_docker.py -v
```

For local testing with all components:

```bash
# Start all services using docker-compose
docker compose up -d

# Create the test database if it doesn't exist
docker exec -it home-task-postgres-1 psql -U postgres -c 'CREATE DATABASE users_test;'

# Run all tests
AWS_ENDPOINT_URL=http://localhost:4566 \
AWS_LAMBDA_FUNCTION_NAME=test-function \
AWS_REGION=us-east-1 \
AWS_EXECUTION_ENV=AWS_Lambda_python3.11 \
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/users_test \
pytest
```

This will start PostgreSQL and localstack containers, then run all tests against them.

> **Note**: If you're using docker-compose, the test database will be created automatically by the init-db.sh script. If you're running PostgreSQL separately, you'll need to create the test database manually as shown above.

> **Troubleshooting**: If you encounter port conflicts with the Docker tests, ensure that no other application is using port 8000, or modify the port mapping in the test configuration.

## API Documentation

Once running, visit `/docs` for the Swagger UI documentation of all endpoints. 

### Endpoints

- `GET /healthcheck` - Health check endpoint
  - Returns status information and environment details
  - No parameters required

- `POST /populate` - Populate database with random user data
  - Optional `count` parameter to specify the number of users to create (default: 10)
  - Optional `unique` parameter to ensure unique email addresses (useful for testing)
  - Returns the number of users created

- `GET /users` - Read users with filters (name, city, age range)
  - Supports partial matching for `name` and `city` filters (e.g., "New" will match "New York" and "New Jersey")
  - Supports range filtering for `age` with `min_age` and `max_age` parameters
  - Results are stored in S3 and the S3 object URL is returned

- `DELETE /users/{user_id}` - Delete a specific user
  - Returns 204 No Content on success
  - Returns 404 Not Found if the user doesn't exist
