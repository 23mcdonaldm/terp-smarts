import pdfplumber
import re
from supabase import create_client, Client
import os
from dotenv import load_dotenv
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
import numpy as np
import pandas as pd

def parse_transcript(text, courses_taken_list):
    # Split text into semesters
    semesters = {}
    current_semester = None

    present_semester = "Spring 2025"
    upcoming_semester = "Fall 2025"
    
    # Regular expression to match semester headers
    semester_pattern = r'(Fall|Spring|Summer)\s+(\d{4})'
    
    # Regular expression to match course lines with optional GenEd designators
    # Made the title pattern more flexible to handle special characters including hyphens
    course_pattern = r'^\s*([A-Z]{4}\d{3}\w?)\s+([A-Za-z0-9\s&\-]+)\s+([A-Z][+-]?|NG|W)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)(?:\s+([A-Z,]+))?'
    # work in progress on future courses
    upcoming_course_pattern = r'^\s*([A-Z]{4}\d{3}\w?)\s+(\d{4})\s+(\d+\.\d+)\s+REG\s+([AD])\s+(\d{2}/\d{2}/\d{2})(?:\s+(\d{2}/\d{2}/\d{2})\s+(\d{2}/\d{2}/\d{2}))?(?:\s+([A-Z,]+))?'
    
    lines = text.split('\n')
    for line in lines:
        # Check for semester header
        semester_match = re.search(semester_pattern, line)
        if semester_match:
            # gets currently being searched semester e.g. "Fall 2024"
            current_semester = f"{semester_match.group(1)} {semester_match.group(2)}"
            semesters[current_semester] = []
            continue
        
        # Skip if no semester is currently being processed
        if not current_semester:
            continue

        # Handle present and upcoming semester courses
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
                    'is_upcoming': True  # Add flag to identify upcoming courses
                }
                semesters[current_semester].append(course)
                courses_taken_list.append(course['code'])
        # Handle historical courses
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
                    'is_upcoming': False  # Add flag to identify historical courses
                }
                semesters[current_semester].append(course)
                courses_taken_list.append(course['code'])
    
    return semesters



def get_course_gpas(course_codes):
    try:
        result = supabase.table('courses').select('course_id, average_gpa').in_('course_id', course_codes).execute()
        course_gpas = {row['course_id']: row['average_gpa'] for row in result.data}
        return course_gpas
    except Exception as e:
        print(f"Error getting course gpas: {e}")
        return None

def get_student_semesters():
    try:
        result = supabase.table('student_semesters').select('*').execute()
        return result
    except Exception as e:
        print(f"Error getting student semester data: {e}")
        return None

# get all course average_gpas from database
load_dotenv()
db_url: str = os.getenv("SUPABASE_URL")
db_key: str = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(db_url, db_key)

curr_user_id = "123"
curr_user_name = "John Doe"


# Read the PDF
with pdfplumber.open("transcript3.pdf") as pdf:
    full_text = ""
    for page in pdf.pages:
        full_text += page.extract_text()


courses_taken_list = []
semesters = parse_transcript(full_text, courses_taken_list)

average_gpas = get_course_gpas(courses_taken_list)

# Print the results
for semester, courses in semesters.items():
    print(f"\n{semester}:")
    for course in courses:
        gened_str = f" - GenEd: {course['gened']}" if course.get('gened') else ""
        if course.get('is_upcoming', False):  # Check if it's an upcoming course
            print(f"{course['code']}: Section {course['section']} - Credits: {course['credits']} - Add/Drop: {course['addDrop']}{gened_str}")
        else:  # Historical course
            print(f"{course['code']}: {course['title']} - Grade: {course['grade']} ({course['credits_earned']} credits){gened_str}")


print("--------------------------------")
# getting a user object

gpa_map = {
    'A+': 4.0, 'A': 4.0, 'A-': 3.7,
    'B+': 3.3, 'B': 3.0, 'B-': 2.7,
    'C+': 2.3, 'C': 2.0, 'C-': 1.7,
    'D+': 1.3, 'D': 1.0, 'D-': 0.7,
    'F': 0.0, 'NG': 0.0, 'W': 0.0
}

def grade_to_gpa(grade):
  return gpa_map.get(grade)

user_courses = {}
all_deltas = []
count = 0
for semester, courses in semesters.items():
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
        gpa = grade_to_gpa(course['grade'])
        semester_difficulty += expected_course_gpa * course['credits_earned']
        # figure out how to handle W and NG
        curr_semester["courses"].append({
            'class': course['code'],
            'grade': gpa,
            'credits': course['credits_earned'],
        })
        curr_semester["gpa"] += grade_to_gpa(course['grade']) * course['credits_earned']
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

user_courses.pop("Fall 2025", None)
user_courses.pop("Spring 2025", None)

print(user_courses)

# users: {
#     'Fall 2023': {
#         gpa: 0,
#         credits: 0,
#         courses: [    
#           {class: "CS 101", grade: 4.0, credits: 3},
#           {class: "MATH 101", grade: 4.0, credits: 3},
#         ]
#     },
#     'Spring 2024': {
#         
#     }
# }

print("--------------------------------")



mean_delta = np.mean(all_deltas)
std_delta = np.std(all_deltas)

# adds Sigmoid-normalized score to each semester
for semester in user_courses.values():
    z = (semester["delta_gpa"] - mean_delta) / std_delta if std_delta != 0 else 0
    score = 1 / (1 + np.exp(-z))
    semester["score"] = score

# adding curr user's data to database
db_semesters = []
for semester in user_courses.values():
    db_semesters.append({
        "student_id": curr_user_id,
        "name": curr_user_name,
        "semester": semester["semester"],
        "gpa": semester["gpa"],
        "credits": semester["credits"],
        "difficulty": semester["semester_difficulty"],
        "delta_gpa": semester["delta_gpa"],
        "score": semester["score"],
        "created_at": pd.Timestamp.now().isoformat(),
    })

supabase.table('student_semesters').upsert(db_semesters, on_conflict='student_id, semester').execute()

# getting all semester data from the database
student_semesters = get_student_semesters()

print("Student Semesters: ", student_semesters)

# scoring model predicting user performance
# 0 - worst student, 0.5 - student performing as expected, 1 - best student
# goal: identify
# A student with a 4.0 GPA in easy classes gets a modest score.

# A student with a 3.7 GPA in hard classes, heavy course load, and tough grading can score higher.

# It accounts for difficulty, load, and performance variance — a multidimensional quality metric.

X = []
y = []


for semester in student_semesters:
    X.append([semester["semester"], semester["gpa"], semester["credits"], semester["semester_difficulty"], semester["delta_gpa"]])
    y.append(semester["score"])

X = np.array(X)
y = np.array(y)

# X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.33, random_state=42)


regressor = RandomForestRegressor(n_estimators=10, random_state=42, oob_score=True)
regressor.fit(X, y)

oob_score = regressor.oob_score_
print(f'Out-of-Bag Score: {oob_score}')

predictions = regressor.predict(X)

mse = mean_squared_error(y, predictions)
print(f'Mean Squared Error: {mse}')

r2 = r2_score(y, predictions)
print(f'R-squared: {r2}')


