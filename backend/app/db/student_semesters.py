from app.db.client import supabase

def get_all_student_semesters():
    """Get all student semester records from the database."""
    try:
        result = supabase.table('student_semesters').select('*').execute()
        return result.data
    except Exception as e:
        print(f"Error getting student semester data: {e}")
        return None

def upsert_student_semesters(semesters_data):
    """Upsert student semester records into the database."""
    try:
        result = supabase.table('student_semesters').upsert(
            semesters_data, 
            on_conflict='student_id, semester'
        ).execute()
        return result.data
    except Exception as e:
        print(f"Error upserting student semester data: {e}")
        return None 