from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    username: str
    email: EmailStr   # or str if you removed EmailStr
    password: str     # ← now lowercase 'password'
    
class UserOut(BaseModel):
    id: int
    username: str
    email: str
    
    class Config:
        from_attributes = True
        