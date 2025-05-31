from fastapi import APIRouter, HTTPException
from app.services.course_fetcher import fetch_and_update_courses

router = APIRouter()

@router.post("/fetch-courses")
async def fetch_courses_endpoint():
    """Trigger the course fetching and updating process."""
    try:
        success = fetch_and_update_courses()
        if success:
            return {"message": "Successfully fetched and updated courses"}
        else:
            raise HTTPException(status_code=500, detail="Failed to fetch and update courses")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 