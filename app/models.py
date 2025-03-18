from sqlalchemy import Column, Integer, String, DateTime
import datetime

# Smart import system that works in all environments
try:
    # First try relative imports (works in Docker)
    from .database import Base
except (ImportError, ValueError):
    try:
        # Then try absolute imports with 'app' prefix (works in tests)
        from app.database import Base
    except ImportError:
        # Finally try direct imports (works in Lambda)
        from database import Base

class User(Base):
    __tablename__ = "users"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    age = Column(Integer)
    city = Column(String)
