from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.transcript_service import process_transcript
from app.db.student_semesters import get_all_student_semesters

router = APIRouter()

@router.post("/process-transcript")
async def process_transcript_endpoint(
    file: UploadFile = File(...),
    user_id: str = None,
    user_name: str = None
):
    """Process a transcript file and return the analyzed data."""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    if not user_id or not user_name:
        raise HTTPException(status_code=400, detail="user_id and user_name are required")
    
    try:
        # Save the uploaded file temporarily
        file_location = f"temp_{file.filename}"
        with open(file_location, "wb+") as file_object:
            file_object.write(await file.read())
        
        # Process the transcript
        result = process_transcript(file_location, user_id, user_name)
        
        # Clean up the temporary file
        import os
        os.remove(file_location)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/student-semesters")
async def get_student_semesters_endpoint():
    """Get all student semester records."""
    try:
        result = get_all_student_semesters()
        if result is None:
            raise HTTPException(status_code=500, detail="Failed to fetch student semesters")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 