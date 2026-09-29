def generate_recommendation(student):
    if student['math'] < 40:
        return "Improve Math"
    elif student['science'] < 40:
        return "Focus on Science"
    elif student['english'] < 40:
        return "Work on English"
    elif student['attendance'] < 60:
        return "Improve Attendance"
    else:
        return "Performing Well"