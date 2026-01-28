from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class PredictionResponse(BaseModel):
    disease_name: str
    confidence: float
    remedy: str

class PredictionHistoryResponse(BaseModel):
    id: int
    disease_name: str
    confidence: float
    remedy: str
    timestamp: datetime

    class Config:
        from_attributes = True

class DiseaseStats(BaseModel):
    disease_name: str
    count: int
    percentage: float

class AnalyticsResponse(BaseModel):
    total_scans: int
    disease_distribution: List[DiseaseStats]
    most_common_disease: Optional[str]
    average_confidence: float
