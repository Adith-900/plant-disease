import io
import os
import uvicorn
import numpy as np
from PIL import Image
from typing import List
import random

from fastapi import FastAPI, File, UploadFile, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func

import database
import models
import schemas

# -------------------- APP INITIALIZATION --------------------

app = FastAPI(title="Smart Farming - Plant Disease Detection API")

# Enable CORS (Required for Flutter frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create database tables on startup
models.Base.metadata.create_all(bind=database.engine)

# -------------------- LOAD ML MODEL --------------------

USE_MOCK = True
model = None

# TensorFlow loading is disabled for now - using mock predictions
# To enable: Install TensorFlow compatible with your Python version
# and place plant_disease_model.h5 in the Backend folder
print("⚠️ Using mock predictions (TensorFlow not loaded)")

# Class labels
CLASS_NAMES = ["Healthy", "Powdery Mildew", "Leaf Rust", "Apple Scab", "Tomato Early Blight"]

# Remedies for detected diseases
REMEDIES = {
    "Healthy": "No treatment needed. Maintain regular watering and monitoring.",
    "Powdery Mildew": "Apply organic fungicide and improve air circulation.",
    "Leaf Rust": "Remove infected leaves and apply copper-based spray.",
    "Apple Scab": "Prune infected leaves and apply sulfur-based fungicide.",
    "Tomato Early Blight": "Remove lower leaves and apply copper-based spray.",
}

# -------------------- HEALTH CHECK --------------------

@app.get("/")
async def health_check():
    return {
        "status": "healthy",
        "message": "Smart Farming API is running",
        "ml_model": "loaded" if not USE_MOCK else "mock"
    }

# -------------------- PREDICTION ENDPOINT --------------------

@app.post("/predict", response_model=schemas.PredictionResponse)
async def predict(
    file: UploadFile = File(...),
    db: Session = Depends(database.get_db)
):
    try:
        # Read image bytes
        image_data = await file.read()
        image = Image.open(io.BytesIO(image_data)).convert("RGB")
        image = image.resize((224, 224))

        if USE_MOCK or model is None:
            # Mock prediction for testing
            predicted_class = random.choice(CLASS_NAMES)
            confidence = round(random.uniform(85.0, 99.9), 2)
        else:
            # Real ML prediction (requires TensorFlow)
            img_array = np.array(image) / 255.0
            img_array = np.expand_dims(img_array, axis=0)
            predictions = model.predict(img_array)
            predicted_class = CLASS_NAMES[np.argmax(predictions[0])]
            confidence = float(np.max(predictions[0]) * 100)

        remedy_text = REMEDIES.get(predicted_class, "Consult an agronomist.")

        # Save to database
        new_log = models.ScanLog(
            disease_name=predicted_class,
            confidence=confidence,
            remedy=remedy_text
        )
        db.add(new_log)
        db.commit()

        return {
            "disease_name": predicted_class,
            "confidence": confidence,
            "remedy": remedy_text
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

# -------------------- HISTORY ENDPOINT --------------------

@app.get("/history", response_model=List[schemas.PredictionHistoryResponse])
async def get_history(limit: int = 50, db: Session = Depends(database.get_db)):
    return db.query(models.ScanLog).order_by(
        models.ScanLog.timestamp.desc()
    ).limit(limit).all()

# -------------------- ANALYTICS ENDPOINT --------------------

@app.get("/analytics", response_model=schemas.AnalyticsResponse)
async def get_analytics(db: Session = Depends(database.get_db)):
    total_scans = db.query(models.ScanLog).count()
    
    if total_scans == 0:
        return {
            "total_scans": 0,
            "disease_distribution": [],
            "most_common_disease": None,
            "average_confidence": 0.0
        }
    
    disease_counts = db.query(
        models.ScanLog.disease_name,
        func.count(models.ScanLog.id).label('count')
    ).group_by(models.ScanLog.disease_name).all()
    
    disease_distribution = [
        schemas.DiseaseStats(
            disease_name=d.disease_name,
            count=d.count,
            percentage=round((d.count / total_scans) * 100, 2)
        )
        for d in disease_counts
    ]
    
    most_common = max(disease_counts, key=lambda x: x.count) if disease_counts else None
    avg_confidence = db.query(func.avg(models.ScanLog.confidence)).scalar() or 0.0
    
    return {
        "total_scans": total_scans,
        "disease_distribution": disease_distribution,
        "most_common_disease": most_common.disease_name if most_common else None,
        "average_confidence": round(float(avg_confidence), 2)
    }

# -------------------- SERVER START --------------------

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
