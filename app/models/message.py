from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    DateTime,
    Text,
    Index,
    Boolean,
)
from sqlalchemy.dialects.postgresql import TSVECTOR  # <-- ADD THIS
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..core.database import Base


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    room_id = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # --- NEW: Soft delete & edit tracking ---
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Full-text search vector
    search_vector = Column(TSVECTOR, nullable=True)

    user = relationship("User")

    __table_args__ = (
        Index("idx_message_search_vector", search_vector, postgresql_using="gin"),
    )
