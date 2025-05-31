from app.services.course_fetcher import fetch_and_update_courses
from app.services.transcript_service import process_transcript

def test_course_fetching():
    """Test the course fetching functionality."""
    print("\n=== Testing Course Fetching ===")
    try:
        success = fetch_and_update_courses()
        if success:
            print("✅ Successfully fetched and updated courses")
        else:
            print("❌ Failed to fetch and update courses")
    except Exception as e:
        print(f"❌ Error during course fetching: {str(e)}")

def test_transcript_processing(pdf_path, user_id=12345, user_name="Test User"):
    """Test the transcript processing functionality.
    
    Args:
        pdf_path (str): Path to the transcript PDF file
        user_id (int): Test user ID (must be a number)
        user_name (str): Test user name
    """
    print("\n=== Testing Transcript Processing ===")
    try:
        result = process_transcript(pdf_path, user_id, user_name)
        if result:
            print("✅ Successfully processed transcript")
            print(f"Processed {len(result)} semesters")
        else:
            print("❌ Failed to process transcript")
    except Exception as e:
        print(f"❌ Error during transcript processing: {str(e)}")

if __name__ == "__main__":
    # Test course fetching
    # test_course_fetching()
    
    # Test transcript processing (uncomment and provide path to test PDF)
    test_transcript_processing("transcript3.pdf")