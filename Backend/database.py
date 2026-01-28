from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Use SQLite for development, PostgreSQL for production
# To use PostgreSQL, set DATABASE_URL environment variable
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "sqlite:///./smart_farming.db"  # SQLite for easy local testing
)

# For PostgreSQL use: "postgresql://postgres:1234@localhost:5432/smart_farming"

# Initialize the connection engine
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

# Create a session factory for database operations
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create the Base class for your database models
Base = declarative_base()

# Dependency to get a database session in FastAPI routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()