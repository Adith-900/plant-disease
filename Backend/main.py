import io
import os
import json
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

USE_MOCK = False
model = None
device = None

# Try to load PyTorch model
MODEL_PATH = os.path.join(os.path.dirname(__file__), "plant_disease_model.pth")
CLASSES_PATH = os.path.join(os.path.dirname(__file__), "classes.json")

try:
    import torch
    import torch.nn as nn
    from torchvision import models as tv_models, transforms
    
    if os.path.exists(MODEL_PATH) and os.path.exists(CLASSES_PATH):
        # Load class names and remedies
        with open(CLASSES_PATH, 'r') as f:
            classes_data = json.load(f)
        
        CLASS_NAMES = classes_data['class_names']  # Dict with int keys as strings
        REMEDIES = classes_data['remedies']
        
        # Load model
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model = tv_models.resnet18(weights=None)
        model.fc = nn.Linear(model.fc.in_features, len(CLASS_NAMES))
        
        checkpoint = torch.load(MODEL_PATH, map_location=device, weights_only=False)
        model.load_state_dict(checkpoint['model_state_dict'])
        model = model.to(device)
        model.eval()
        
        # Image transform
        transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])
        
        print(f"✅ Model loaded successfully with {len(CLASS_NAMES)} classes")
        print(f"   Device: {device}")
    else:
        print(f"⚠️ Model file not found at {MODEL_PATH}")
        USE_MOCK = True
except ImportError:
    print("⚠️ PyTorch not installed - using mock predictions")
    USE_MOCK = True
except Exception as e:
    print(f"⚠️ Error loading model: {e}")
    USE_MOCK = True

# Fallback class names and remedies for mock mode
if USE_MOCK:
    CLASS_NAMES = {
        "0": "Apple_Scab", "1": "Apple_Black_Rot", "2": "Apple_Cedar_Rust",
        "3": "Apple_Healthy", "4": "Blueberry_Healthy", "5": "Cherry_Powdery_Mildew"
    }
    REMEDIES = {
        "Apple_Scab": "Apply fungicide sprays. Remove fallen leaves.",
        "Apple_Black_Rot": "Prune infected branches. Apply copper fungicide.",
        "Apple_Cedar_Rust": "Remove nearby juniper trees. Apply fungicide.",
        "Apple_Healthy": "No treatment needed. Continue regular care.",
        "Blueberry_Healthy": "No treatment needed. Maintain watering.",
        "Cherry_Powdery_Mildew": "Apply sulfur-based fungicide."
    }
    print("⚠️ Using mock predictions")

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

        if USE_MOCK or model is None:
            # Mock prediction for testing
            class_names_list = list(CLASS_NAMES.values())
            predicted_class = random.choice(class_names_list)
            confidence = round(random.uniform(85.0, 99.9), 2)
        else:
            # Real PyTorch prediction
            img_tensor = transform(image).unsqueeze(0).to(device)
            
            with torch.no_grad():
                outputs = model(img_tensor)
                probabilities = torch.nn.functional.softmax(outputs, dim=1)
                confidence_val, predicted_idx = torch.max(probabilities, 1)
                
            predicted_class = CLASS_NAMES[str(predicted_idx.item())]
            confidence = round(confidence_val.item() * 100, 2)

        remedy_text = REMEDIES.get(predicted_class, "Consult an agronomist for proper treatment.")

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
