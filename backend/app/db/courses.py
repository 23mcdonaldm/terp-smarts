from app.db.client import supabase
import pandas as pd

def get_course_gpas(course_codes):
    """Get average GPAs for a list of course codes."""
    try:
        result = supabase.table('courses').select('course_id, average_gpa').in_('course_id', course_codes).execute()
        course_gpas = {row['course_id']: row['average_gpa'] for row in result.data}
        return course_gpas
    except Exception as e:
        print(f"Error getting course gpas: {e}")
        return None

def bulk_upsert_courses(courses_data):
    """Bulk upsert course records into the database.
    
    Args:
        courses_data (list): List of course dictionaries from PlanetTerp API
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Convert to DataFrame and clean data
        df = pd.DataFrame(courses_data)
        df.columns = df.columns.str.strip()
        df_filtered = df[df['average_gpa'].notna()]
        
        # Prepare records for database
        records = df_filtered[['name', 'title', 'description', 'credits', 'average_gpa']].copy()
        records['last_updated'] = pd.Timestamp.now().isoformat()
        records = records.rename(columns={'name': 'course_id'})
        
        # Convert credits to integers and handle NaN values
        records['credits'] = records['credits'].fillna(0).astype(int)
        records = records.replace({float('nan'): None})
        records_list = records.to_dict('records')
        
        # Insert records in batches
        batch_size = 1000
        for i in range(0, len(records_list), batch_size):
            batch = records_list[i:i + batch_size]
            result = supabase.table('courses').upsert(batch, on_conflict='course_id').execute()
            print(f"Upserted batch {i//batch_size + 1} of {(len(records_list) + batch_size - 1)//batch_size}")
        
        return True
    except Exception as e:
        print(f"Error during bulk upsert: {e}")
        return False 