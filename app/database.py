from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

load_dotenv()

# Use test database if running tests
is_testing = os.getenv("TESTING", "false").lower() == "true"
database_name = "users_test" if is_testing else "users"
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"postgresql://postgres:postgres@localhost:5432/{database_name}"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base() 
