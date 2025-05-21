from pypdf import PdfReader
import re

def parse_transcript(text):
    # Split text into semesters
    semesters = {}
    current_semester = None
    
    # Regular expression to match semester headers
    semester_pattern = r'(Fall|Spring|Summer)\s+(\d{4})'
    
    # Regular expression to match course lines with optional GenEd designators
    # Made the title pattern more flexible to handle special characters including hyphens
    course_pattern = r'^\s*([A-Z]{4}\d{3}\w?)\s+([A-Za-z0-9\s&\-]+)\s+([A-Z][+-]?)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)(?:\s+([A-Z,]+))?'
    # work in progress on future courses
    upcoming_course_pattern = r'^\s*([A-Z]{4}\d{3}\w?)\s+(\d{4})\s+(\d+\.\d+)\s+'
    
    lines = text.split('\n')
    for line in lines:
        # Check for semester header
        semester_match = re.search(semester_pattern, line)
        if semester_match:
            # gets current semester e.g. "Fall 2024"
            current_semester = f"{semester_match.group(1)} {semester_match.group(2)}"
            semesters[current_semester] = []
            continue
            
        # Check for course line
        if current_semester:
            course_match = re.search(course_pattern, line)
            if course_match:
                course = {
                    'code': course_match.group(1).strip(),
                    'title': course_match.group(2).strip(),
                    'grade': course_match.group(3),
                    'credits_attempted': float(course_match.group(4)),
                    'credits_earned': float(course_match.group(5)),
                    'quality_points': float(course_match.group(6)),
                    'gened': course_match.group(7).strip() if course_match.group(7) else None
                }
                semesters[current_semester].append(course)
    
    return semesters

# Read the PDF
reader = PdfReader("transcript1.pdf")
full_text = ""

# Extract text from all pages
for page in reader.pages:
    full_text += page.extract_text()

# Parse the transcript
semesters = parse_transcript(full_text)

# Print the results
for semester, courses in semesters.items():
    print(f"\n{semester}:")
    for course in courses:
        gened_str = f" - GenEd: {course['gened']}" if course['gened'] else ""
        print(f"{course['code']}: {course['title']} - Grade: {course['grade']} ({course['credits_earned']} credits){gened_str}")