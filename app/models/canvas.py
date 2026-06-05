from sqlalchemy import Column, Integer, String, ForeignKey
from db.database import Base


class Canvas(Base):
    __tablename__ = "canvas"

    id = Column(Integer, primary_key=True, index=True)
    userid = Column(Integer, ForeignKey("Users.id"), nullable=False)
    thumbnail_id = Column(Integer, ForeignKey("thumbnails.id"), nullable=False, unique=True)
    canvaspath = Column(String, nullable=False)
