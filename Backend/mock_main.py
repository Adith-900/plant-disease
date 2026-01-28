from fastapi import FastAPI, File, UploadFile
import uvicorn
import asyncio
import random

app = FastAPI()

# A list of fake results to test your UI
MOCK_RESULTS = [
    {"disease_name": "Apple Scab", "remedy": "Prune infected leaves and apply sulfur-based fungicide."},
    {"disease_name": "Tomato Early Blight", "remedy": "Remove lower leaves and apply copper-based spray."},
    {"disease_name": "Healthy Plant", "remedy": "Continue regular watering and monitoring."},
    {"disease_name": "Potato Late Blight", "remedy": "Improve drainage and use resistant varieties."}
]

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    # Simulate the AI 'thinking' for 2 seconds
    await asyncio.sleep(2) 
    
    # Pick a random result from our list
    result = random.choice(MOCK_RESULTS)
    
    return {
        "disease_name": result["disease_name"],
        "confidence": round(random.uniform(85.0, 99.9), 2), # Random confidence score
        "remedy": result["remedy"]
    }

if __name__ == "__main__":
    print("Mock Server is starting...")
    uvicorn.run(app, host="0.0.0.0", port=8000)