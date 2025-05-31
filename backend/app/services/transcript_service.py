import pdfplumber
import re
import numpy as np
import pandas as pd
from app.db.student_semesters import upsert_student_semesters
from app.db.courses import get_course_gpas

def parse_transcript(text, courses_taken_list):
    # Split text into semesters
    semesters = {}
    current_semester = None

    present_semester = "Spring 2025"
    upcoming_semester = "Fall 2025"
    
    # Regular expression to match semester headers
    semester_pattern = r'(Fall|Spring|Summer)\s+(\d{4})'
    
    # Regular expression to match course lines with optional GenEd designators
    course_pattern = r'^\s*([A-Z]{4}\d{3}\w?)\s+([A-Za-z0-9\s&\-]+)\s+([A-Z][+-]?|NG|W)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)(?:\s+([A-Z,]+))?'
    upcoming_course_pattern = r'^\s*([A-Z]{4}\d{3}\w?)\s+(\d{4})\s+(\d+\.\d+)\s+REG\s+([AD])\s+(\d{2}/\d{2}/\d{2})(?:\s+(\d{2}/\d{2}/\d{2})\s+(\d{2}/\d{2}/\d{2}))?(?:\s+([A-Z,]+))?'
    
    lines = text.split('\n')
    for line in lines:
        semester_match = re.search(semester_pattern, line)
        if semester_match:
            current_semester = f"{semester_match.group(1)} {semester_match.group(2)}"
            semesters[current_semester] = []
            continue
        
        if not current_semester:
            continue

        if current_semester in [present_semester, upcoming_semester]:
            course_match = re.search(upcoming_course_pattern, line)
            if course_match:
                course = {
                    'code': course_match.group(1).strip(),
                    'section': course_match.group(2).strip(),
                    'credits': float(course_match.group(3)),
                    'addDrop': course_match.group(4),
                    'add_date': course_match.group(5),
                    'drop_date': course_match.group(6) if course_match.group(6) else None,
                    'modified_date': course_match.group(7) if course_match.group(7) else None,
                    'gened': course_match.group(8).strip() if course_match.group(8) else None,
                    'is_upcoming': True
                }
                semesters[current_semester].append(course)
                courses_taken_list.append(course['code'])
        else:
            course_match = re.search(course_pattern, line)
            if course_match:
                course = {
                    'code': course_match.group(1).strip(),
                    'title': course_match.group(2).strip(),
                    'grade': course_match.group(3),
                    'credits_attempted': float(course_match.group(4)),
                    'credits_earned': float(course_match.group(5)),
                    'quality_points': float(course_match.group(6)),
                    'gened': course_match.group(7).strip() if course_match.group(7) else None,
                    'is_upcoming': False
                }
                semesters[current_semester].append(course)
                courses_taken_list.append(course['code'])
    
    return semesters

def process_transcript(transcript_file, user_id, user_name):
    """Process a transcript file and return the analyzed data."""
    # Read the PDF
    with pdfplumber.open(transcript_file) as pdf:
        full_text = ""
        for page in pdf.pages:
            full_text += page.extract_text()

    courses_taken_list = []
    semesters = parse_transcript(full_text, courses_taken_list)
    average_gpas = get_course_gpas(courses_taken_list)

    gpa_map = {
        'A+': 4.0, 'A': 4.0, 'A-': 3.7,
        'B+': 3.3, 'B': 3.0, 'B-': 2.7,
        'C+': 2.3, 'C': 2.0, 'C-': 1.7,
        'D+': 1.3, 'D': 1.0, 'D-': 0.7,
        'F': 0.0, 'NG': 0.0, 'W': 0.0
    }

    user_courses = {}
    all_deltas = []
    count = 0

    for semester, courses in semesters.items():
        if semester in ["Fall 2025", "Spring 2025"]:
            continue

        curr_semester = {
            "gpa": 0,
            "credits": 0,
            "courses": [],
        }
        semester_difficulty = 0.0

        for course in courses:
            if course.get('is_upcoming', True):
                continue
            expected_course_gpa = average_gpas.get(course['code'], 0)
            gpa = gpa_map.get(course['grade'], 0)
            semester_difficulty += expected_course_gpa * course['credits_earned']
            
            curr_semester["courses"].append({
                'class': course['code'],
                'grade': gpa,
                'credits': course['credits_earned'],
            })
            curr_semester["gpa"] += gpa * course['credits_earned']
            curr_semester["credits"] += course['credits_earned']

        curr_semester["semester"] = count
        count += 1

        if curr_semester["credits"] > 0:
            curr_semester["gpa"] = curr_semester["gpa"] / curr_semester["credits"]
            curr_semester["semester_difficulty"] = semester_difficulty / curr_semester["credits"]
        else:
            curr_semester["gpa"] = 0
            curr_semester["semester_difficulty"] = 0

        curr_semester["delta_gpa"] = curr_semester["gpa"] - curr_semester["semester_difficulty"]
        all_deltas.append(curr_semester["delta_gpa"])
        user_courses[semester] = curr_semester

    # Calculate scores
    mean_delta = np.mean(all_deltas)
    std_delta = np.std(all_deltas)

    for semester in user_courses.values():
        z = (semester["delta_gpa"] - mean_delta) / std_delta if std_delta != 0 else 0
        score = 1 / (1 + np.exp(-z))
        semester["score"] = score

    # Prepare data for database
    db_semesters = []
    for semester in user_courses.values():
        db_semesters.append({
            "student_id": user_id,
            "name": user_name,
            "semester": semester["semester"],
            "gpa": semester["gpa"],
            "credits": semester["credits"],
            "difficulty": semester["semester_difficulty"],
            "delta_gpa": semester["delta_gpa"],
            "score": semester["score"],
            "created_at": pd.Timestamp.now().isoformat(),
        })

    # Save to database
    upsert_student_semesters(db_semesters)

    return user_courses 