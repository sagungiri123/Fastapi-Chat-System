from pydantic import BaseModel
from datetime import datetime

class MessageCreate(BaseModel):
    content: str
    room_id: str
    
class MessageOut(BaseModel):
    id: int
    content: str
    user_id: int
    room_id: str
    created_at: datetime
    
    class Config:
        from_attributes = True
        
        