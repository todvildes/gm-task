import pytest
import os
import sys
import docker
import boto3
import time
import traceback
from pathlib import Path
from typing import Generator
import requests

# Add the project root directory to sys.path
# This will allow imports to work without 'app.' prefix
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    # Also add the app directory directly to handle imports like 'from database import Base'
    sys.path.insert(0, os.path.join(project_root, 'app'))

# Now import the modules (these will use the modified sys.path)
from sqlalchemy import create_engine, text, MetaData
from sqlalchemy.orm import Session
from app.database import Base
from app.models import User
from moto import mock_aws
from app.s3_utils import S3Handler
import platform

# Test database URL from environment or default
TEST_DB_URL = os.getenv('DATABASE_URL', "postgresql://postgres:postgres@localhost:5432/users_test")

@pytest.fixture(scope="session")
def docker_client():
    try:
        # Print Docker environment variables
        print(f"DOCKER_HOST: {os.environ.get('DOCKER_HOST')}")
        
        # Try to connect to Docker using the correct socket path for macOS
        if platform.system() == 'Darwin':
            socket_path = os.path.expanduser('~/.docker/run/docker.sock')
            if os.path.exists(socket_path):
                print(f"Using Docker socket at: {socket_path}")
                return docker.DockerClient(base_url=f'unix://{socket_path}')
        
        # Default approach
        client = docker.from_env()
        # Test the connection
        client.ping()
        return client
    except Exception as e:
        print(f"Docker connection error: {str(e)}")
        print(f"Error type: {type(e)}")
        traceback.print_exc()
        pytest.skip(f"Docker not available: {e}")

@pytest.fixture(scope="session")
def docker_compose_file(pytestconfig) -> Path:
    return Path("docker-compose.yml")

@pytest.fixture(scope="session")
def postgres_container(docker_client):
    container = docker_client.containers.run(
        "postgres:15",
        environment={
            "POSTGRES_PASSWORD": "postgres",
            "POSTGRES_USER": "postgres",
            "POSTGRES_DB": "postgres"
        },
        ports={"5432/tcp": 5432},
        detach=True,
        remove=True
    )
    
    # Wait for PostgreSQL to be ready
    time.sleep(3)
    
    # Create test database
    import psycopg2
    try:
        conn = psycopg2.connect(
            dbname="postgres",
            user="postgres",
            password="postgres",
            host="localhost"
        )
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute("DROP DATABASE IF EXISTS users_test")
        cur.execute("CREATE DATABASE users_test")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error creating test database: {e}")
    
    yield container
    
    container.stop()

@pytest.fixture(scope="session")
def test_db_engine():
    """Create a test database engine with a separate metadata instance"""
    # Import here to avoid import loops
    from app.database import Base
    from sqlalchemy import MetaData
    
    # Create a new engine for tests
    database_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/users_test")
    engine = create_engine(database_url)
    
    # Create a new metadata for tests to avoid conflicts
    test_metadata = MetaData()
    for table in Base.metadata.tables.values():
        table.to_metadata(test_metadata)
    
    # Create tables using test metadata
    test_metadata.create_all(bind=engine)
    
    yield engine
    
    # Optionally drop tables after tests
    # test_metadata.drop_all(bind=engine)

@pytest.fixture
def db_session(test_db_engine) -> Generator[Session, None, None]:
    """Create a new database session for a test"""
    connection = test_db_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="session")
def docker_api_url(docker_client):
    # Build and run the application container
    docker_client.images.build(path=".", tag="user-api:test")
    container = docker_client.containers.run(
        "user-api:test",
        environment={
            "DATABASE_URL": TEST_DB_URL.replace("localhost", "host.docker.internal"),
            "ENVIRONMENT": "test",
            "AWS_ENDPOINT_URL": "http://host.docker.internal:4566",
            "AWS_ACCESS_KEY_ID": "test",
            "AWS_SECRET_ACCESS_KEY": "test",
            "AWS_DEFAULT_REGION": "us-east-1",
            "S3_BUCKET_NAME": "user-queries"
        },
        ports={"8000/tcp": 8000},
        extra_hosts={"host.docker.internal": "host-gateway"},
        detach=True,
        remove=True
    )
    
    # Wait for the application to start
    time.sleep(3)
    
    yield "http://localhost:8000"
    
    container.stop()

@pytest.fixture(scope="session")
def docker_services(docker_compose_file, docker_compose_project_name):
    """Start docker services defined in docker-compose.yml"""
    os.system(f"docker-compose -f {docker_compose_file} -p {docker_compose_project_name} up -d")
    time.sleep(5)  # Give services time to start
    yield
    os.system(f"docker-compose -f {docker_compose_file} -p {docker_compose_project_name} down")

@pytest.fixture(scope="session")
def localstack_endpoint(docker_services):
    """Get the endpoint URL for localstack"""
    return "http://localhost:4566"

@pytest.fixture(scope="session")
def lambda_client(localstack_endpoint):
    """Create a boto3 Lambda client for localstack"""
    return boto3.client(
        'lambda',
        endpoint_url=localstack_endpoint,
        region_name='us-east-1',
        aws_access_key_id='test',
        aws_secret_access_key='test'
    )

@pytest.fixture
def mock_s3_bucket(monkeypatch):
    """Create a mock S3 bucket for testing"""
    # Set environment variables for testing
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_SECURITY_TOKEN", "testing")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "testing")
    monkeypatch.setenv("PYTEST_CURRENT_TEST", "True")
    
    # Check if we're using localstack
    using_localstack = os.getenv('AWS_ENDPOINT_URL') is not None
    
    if using_localstack:
        # Use localstack for S3
        print("Using localstack for S3 operations")
        s3 = boto3.client(
            's3',
            endpoint_url=os.getenv('AWS_ENDPOINT_URL'),
            region_name='us-east-1',
            aws_access_key_id='test',
            aws_secret_access_key='test'
        )
        
        # Create bucket if it doesn't exist
        try:
            s3.head_bucket(Bucket='user-queries')
            print("Bucket already exists in localstack")
        except Exception:
            try:
                s3.create_bucket(
                    Bucket='user-queries',
                    CreateBucketConfiguration={
                        'LocationConstraint': os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
                    }
                )
                print("Created bucket in localstack")
            except Exception as e:
                print(f"Error creating bucket in localstack: {str(e)}")
        
        yield s3
    else:
        # Use moto for S3
        print("Using moto for S3 operations")
        with mock_aws():
            s3 = boto3.client(
                's3',
                region_name='us-east-1'
            )
            s3.create_bucket(Bucket='user-queries')
            yield s3

@pytest.fixture
def s3_handler():
    """Create an S3 handler instance for testing"""
    return S3Handler() 
