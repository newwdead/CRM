from sqlalchemy import Column, Integer, String
from .database import Base

class Contact(Base):
    __tablename__ = "contacts"
    id = Column(Integer, primary_key=True, index=True)
    uid = Column(String, unique=True, index=True, nullable=True)
    full_name = Column(String, nullable=True)
    company = Column(String, nullable=True)
    position = Column(String, nullable=True)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    address = Column(String, nullable=True)
    comment = Column(String, nullable=True)
    website = Column(String, nullable=True)
    photo_path = Column(String, nullable=True)
    ocr_raw = Column(String, nullable=True)
