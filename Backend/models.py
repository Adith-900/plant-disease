from sqlalchemy import Column, Integer, String, Float, DateTime
from database import Base
import datetime

class ScanLog(Base):
    __tablename__ = "scan_logs"

    id = Column(Integer, primary_key=True, index=True)
    disease_name = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    remedy = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
