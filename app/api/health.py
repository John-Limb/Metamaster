"""Health check endpoints"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("/")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "message": "Application is running",
    }


@router.get("/db")
async def database_health(db: Session = Depends(get_db)):
    """Database health check endpoint"""
    try:
        # Simple query to check database connection
        db.execute("SELECT 1")
        return {
            "status": "healthy",
            "message": "Database connection is working",
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"Database connection failed: {str(e)}",
        }
