from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
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

# Create engine
engine = create_engine(DATABASE_URL)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create declarative base
Base = declarative_base()

# Track whether tables have been created
_tables_created = False

def create_tables():
    """Create tables if they haven't been created yet"""
    global _tables_created
    if not _tables_created:
        Base.metadata.create_all(bind=engine)
        _tables_created = True

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
