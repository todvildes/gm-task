from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

class UserBase(BaseModel):
    name: str
    email: str
    age: int
    city: str

class UserCreate(UserBase):
    pass

class UserResponse(UserBase):
    id: int
    
    model_config = ConfigDict(from_attributes=True)

class UserQueryResponse(BaseModel):
    users: List[UserResponse]
    count: int
    s3_file: str
    timestamp: datetime
    
    model_config = ConfigDict(from_attributes=True) 
