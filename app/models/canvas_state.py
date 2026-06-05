from sqlalchemy import Column, Integer, Text, ForeignKey
from db.database import Base


class CanvasState(Base):
    __tablename__ = "canvas_states"

    id           = Column(Integer, primary_key=True, index=True)
    thumbnail_id = Column(Integer, ForeignKey("thumbnails.id"), unique=True, nullable=False)
    userid       = Column(Integer, ForeignKey("Users.id"), nullable=False)
    lines        = Column(Text, nullable=True)       # JSON array
    shapes       = Column(Text, nullable=True)       # JSON array
    text_items   = Column(Text, nullable=True)       # JSON array
