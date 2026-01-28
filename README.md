# Plant Disease Detection

Smart Farming app with Plant Disease Detection using Flutter and FastAPI.

## Features
- Image Upload
- Disease Identification  
- Remedy Suggestion
- Scan History
- Analytics Dashboard

## Tech Stack
- **Frontend:** Flutter
- **Backend:** FastAPI (Python)
- **Database:** SQLite/PostgreSQL
- **ML Model:** CNN (Mock predictions for demo)

## Setup

### Backend
```bash
cd Backend
pip install -r requirements.txt
python main.py
```

### Flutter App
```bash
cd plant
flutter pub get
flutter run
```

## API Endpoints
- `GET /` - Health check
- `POST /predict` - Upload image for disease detection
- `GET /history` - Get scan history
- `GET /analytics` - Get statistics
