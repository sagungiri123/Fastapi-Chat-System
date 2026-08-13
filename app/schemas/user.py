from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    Password: str
    
class UserOut(BaseModel):
    id: int
    username: str
    email: str
    
    class Config:
        from_attributes = True
        