from sqlalchemy import Column, Integer, String, ForeignKey

from db.database import Base


class Thumbnail(Base):
    __tablename__ = "thumbnails"

    id = Column(Integer, primary_key=True, index=True)
    userid = Column(Integer, ForeignKey("Users.id"), nullable=False)
    thumbnailpath = Column(String, nullable=False)
