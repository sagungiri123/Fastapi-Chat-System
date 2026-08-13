from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base

class Message(Base):
    __tablename__ = "message"
    
    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable= False)
    user_id = Column(Integer, ForeignKey("users.id"))
    room_id = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User")
    
    
