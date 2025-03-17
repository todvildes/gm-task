from fastapi import FastAPI, HTTPException, Query, Depends
from mangum import Mangum
from typing import Optional, List
from datetime import datetime
from .database import SessionLocal, engine
from .models import Base, User
from .schemas import UserCreate, UserResponse, UserQueryResponse
from sqlalchemy.orm import Session
from faker import Faker
import random
import os
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_xray_sdk.core import patch_all
from .s3_utils import S3Handler
import sys

# Initialize AWS Lambda Powertools
logger = Logger()
tracer = Tracer()

# Only patch AWS SDK if running in Lambda environment
if os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
    patch_all()

# Create database tables
Base.metadata.create_all(bind=engine)

# Configure FastAPI app with environment-specific settings
app = FastAPI(
    title="User Management API",
    root_path=os.getenv("API_GATEWAY_BASE_PATH", ""),  # Used by API Gateway in Lambda
    openapi_prefix=os.getenv("API_GATEWAY_BASE_PATH", "")  # Ensures OpenAPI docs work in both environments
)

# Detect if we're running in a test environment
IN_PYTEST = 'pytest' in sys.modules
TESTING = IN_PYTEST or os.getenv('PYTEST_CURRENT_TEST') == 'True' or os.getenv('ENVIRONMENT') == 'test'

fake = Faker()
s3_handler = S3Handler(testing=TESTING)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/healthcheck")
@tracer.capture_method
async def healthcheck():
    environment = "AWS Lambda" if os.getenv("AWS_LAMBDA_FUNCTION_NAME") else "Docker"
    logger.info("Health check requested")
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "environment": environment
    }

@app.post("/populate")
@tracer.capture_method
async def populate_data(count: int = Query(default=10, ge=1, le=100), unique: str = None, db: Session = Depends(get_db)):
    logger.info(f"Populating database with {count} users")
    users = []
    
    try:
        for i in range(count):
            # Use the unique parameter to generate unique email addresses if provided
            email_suffix = f"-{unique}-{i}" if unique else ""
            email = fake.email().replace("@", f"{email_suffix}@")
            
            user = User(
                name=fake.name(),
                email=email,
                age=random.randint(18, 80),
                city=fake.city()
            )
            db.add(user)
            users.append(user)
        
        db.commit()
        logger.info(f"Successfully created {count} users")
        return {"message": f"Created {count} users"}
    except Exception as e:
        logger.error(f"Error populating database: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Error populating database")

@app.get("/users", response_model=UserQueryResponse)
@tracer.capture_method
async def get_users(
    name: Optional[str] = None,
    city: Optional[str] = None,
    min_age: Optional[int] = None,
    max_age: Optional[int] = None,
    db: Session = Depends(get_db)
):
    logger.info(f"Fetching users with filters: name={name}, city={city}, min_age={min_age}, max_age={max_age}")
    query = db.query(User)
    
    if name:
        query = query.filter(User.name.ilike(f"%{name}%"))
    if city:
        query = query.filter(User.city.ilike(f"%{city}%"))
    if min_age is not None:
        query = query.filter(User.age >= min_age)
    if max_age is not None:
        query = query.filter(User.age <= max_age)
    
    try:
        users = query.all()
        logger.info(f"Found {len(users)} users matching the criteria")
        
        # Store query results in S3
        query_params = {
            "name": name,
            "city": city,
            "min_age": min_age,
            "max_age": max_age
        }
        s3_file = s3_handler.store_query_result(query_params, [user.__dict__ for user in users])
        
        return UserQueryResponse(
            users=users,
            count=len(users),
            s3_file=s3_file,
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        logger.error(f"Error fetching users: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching users")

@app.delete("/users/{user_id}")
@tracer.capture_method
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    logger.info(f"Attempting to delete user {user_id}")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        logger.warning(f"User {user_id} not found")
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        db.delete(user)
        db.commit()
        logger.info(f"Successfully deleted user {user_id}")
        return {"message": f"User {user_id} deleted"}
    except Exception as e:
        logger.error(f"Error deleting user {user_id}: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Error deleting user")

# Handler for AWS Lambda
@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event: dict, context: LambdaContext) -> dict:
    # Initialize Mangum handler with custom configurations for Lambda
    asgi_handler = Mangum(app, api_gateway_base_path=os.getenv("API_GATEWAY_BASE_PATH", "/"))
    # Handle the event
    return asgi_handler(event, context)

# This block is used when running the application in Docker
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("ENVIRONMENT", "development") == "development"
    )
