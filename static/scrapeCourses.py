import pickle
import json

courses = {}

with open("courses.json") as json_file:
    data = json.load(json_file)

    for row in data:
        course = row["classes"][0]
        subject = course["catalogSubject"]
        number = course["courseNumber"]

        if subject not in courses:
            courses[subject] = [number]
        else:
            courses[subject].append(number)

    for nums in courses.values():
        nums.sort()

subjects = sorted(courses.keys())

pickle.dump(courses, open( "courses.p", "wb"))
pickle.dump(subjects, open( "subjects.p", "wb"))

