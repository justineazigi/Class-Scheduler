import pandas as pd
from ortools.sat.python import cp_model


fall_courses = pd.read_csv("/Users/justiineazigi/Documents/Class-Scheduler/Data/fallcourses.csv")
intro_courses = pd.read_csv("/Users/justiineazigi/Documents/Class-Scheduler/Data/intro copy.csv")
timeslot = pd.read_csv("/Users/justiineazigi/Documents/Class-Scheduler/Data/timeslot.csv")
fall_courses.head()
intro_courses.head()
timeslot.head()

model = cp_model.CpModel()
days_of_week = ["Monday", "Tuesday", "wednesday", "Thursday", "Friday"]
schedule_vars = {}

# Decision variable for Introductory Courses and fall courses 
ta_courses = intro_courses[intro_courses["TA_ID"].str.startswith("TA")]
for row in ta_courses.itertuples(index=False):
    course = row.course_code
    credit_hours = row.credit_hours
    meeting_time = row.meeting_time
    assigned_ta = row.TA_ID  

    for ts_row in timeslot.itertuples(index=False):
        if ts_row.Credit_hours == credit_hours and ts_row.meeting_time == meeting_time:
            for day in [day.strip().capitalize() for day in row.Days.split(",")]:
                key = (course, ts_row.TimeSlotID, ts_row.start_time, ts_row.end_time, day, assigned_ta)
                schedule_vars[key] = model.NewBoolVar(f"{course}_{ts_row.TimeSlotID}_{ts_row.start_time}_{ts_row.end_time}_{day}_{assigned_ta}")
        
for row in fall_courses.itertuples(index=False):
    course = row.course_code
    credit_hours = row.credit_hours
    meeting_time = row.meeting_time 
    assigned_instructor = row.instructor_name  

    for ts_row in timeslot.itertuples(index=False):
        if ts_row.Credit_hours == credit_hours and ts_row.meeting_time == meeting_time:
            for day in [day.strip().capitalize() for day in row.Days.split(",")]:
                key = (course, ts_row.TimeSlotID, ts_row.start_time, ts_row.end_time, day, assigned_instructor)
                schedule_vars[key] = model.NewBoolVar(f"{course}_{ts_row.TimeSlotID}_{ts_row.start_time}_{ts_row.end_time}_{day}_{assigned_instructor}")

print("Existing schedule_vars keys:", list(schedule_vars.keys()))
print(f"Total decision variables created: {len(schedule_vars)}")

for key, var in schedule_vars.items():
    print(f"{key}: {var}")

# Constraints: Ensure an instructor/TA is assigned to only one course per time slot

unique_instructors = set(key[5] for key in schedule_vars.keys())
days_of_week = set(key[4] for key in schedule_vars.keys())

for instructor in unique_instructors:
    for day in days_of_week:       
        instructor_schedule = {key: value for key, value in schedule_vars.items() if key[5] == instructor and key[4] == day}               
        unique_time_slots = { (key[1], key[2], key[3]) for key in instructor_schedule.keys() }

        for ts_id, start_time, end_time in unique_time_slots:
            assigned_courses = [
                key for key in instructor_schedule.keys()
                if key[1] == ts_id and key[2] == start_time and key[3] == end_time
            ]
            if assigned_courses:
                model.Add(sum(schedule_vars[key] for key in assigned_courses) <= 1)


#ensures that courses are not scheduled at the same time.checks for the duration of the courses-time overlaps in course durarion 
for instructor in unique_instructors:
    for day in days_of_week:
        instructor_schedule = [
            key for key in schedule_vars.keys() if key[5] == instructor and key[4] == day
        ]
        
        for i in range(len(instructor_schedule)):
            for j in range(i + 1, len(instructor_schedule)): 
                key1 = instructor_schedule[i]
                key2 = instructor_schedule[j]
                
                course1, ts_id1, start1, end1, day1, instructor1 = key1
                course2, ts_id2, start2, end2, day2, instructor2 = key2
                if start1 < end2 and start2 < end1:  # Overlapping condition
                    model.Add(schedule_vars[key1] + schedule_vars[key2] <= 1)



# Constraint: Courses should be scheduled only once per day
unique_courses = set(key[0] for key in schedule_vars.keys())
days_of_week = set(key[4] for key in schedule_vars.keys())
for course in unique_courses:
    for day in days_of_week:
        course_schedule = [
            key for key in schedule_vars.keys()
            if key[0] == course and key[4] == day
        ]
        if course_schedule:
            model.Add(sum(schedule_vars[key] for key in course_schedule) == 1)




# Faculty preferences
faculty_preferences = pd.read_csv("/Users/justiineazigi/Documents/Class-Scheduler/Data/fall preferences.csv")
faculty_preferences.head
faculty_prefs_dict = faculty_preferences.set_index("instructor_name")[["preferred_time", "breaks_between_session"]].to_dict("index")

morning_start, morning_end = 8 * 60, 11 * 60 + 59      # 8:00 AM - 11:59 AM
afternoon_start, afternoon_end = 12 * 60, 15 * 60 + 59 # 12:00 PM - 3:59 PM
evening_start, evening_end = 16 * 60, 19 * 60 + 50     # 4:00 PM - 7:50 PM

# Helper function to convert HH:MM string to minutes
def time_to_minutes(time_str):
    hours, minutes = map(int, time_str.split(":"))
    return hours * 60 + minutes  # Convert hours to minutes and add minutes

for instructor, prefs in faculty_prefs_dict.items():
    preferred_time = prefs["preferred_time"]
    break_time = prefs["breaks_between_session"]

    # Map preferred time slots to minutes
    if preferred_time == "morning":
        time_range = (morning_start, morning_end)
    elif preferred_time == "afternoon":
        time_range = (afternoon_start, afternoon_end)
    elif preferred_time == "evening":
        time_range = (evening_start, evening_end)  
    else:
        time_range = None  

    for day in days_of_week:
        instructor_schedule = [
            key for key in schedule_vars.keys() if key[5] == instructor and key[4] == day
        ]

        # Apply preferred teaching time constraint
        if time_range:
            for key in instructor_schedule:
                _, _, start, end, _, _ = key
                start = time_to_minutes(start)  # Convert to minutes
                end = time_to_minutes(end)      # Convert to minutes
                
                model.Add(start >= time_range[0])
                model.Add(end <= time_range[1])

        # Apply break preference constraint (for instructors teaching multiple courses in a day)
        for i in range(len(instructor_schedule)):
            for j in range(i + 1, len(instructor_schedule)):
                key1 = instructor_schedule[i]
                key2 = instructor_schedule[j]
                _, _, start1, end1, _, _ = key1
                _, _, start2, end2, _, _ = key2

                start1 = time_to_minutes(start1)
                end1 = time_to_minutes(end1)
                start2 = time_to_minutes(start2)
                end2 = time_to_minutes(end2)

                if break_time == 0:  # No break → back-to-back classes
                    model.Add(start2 == end1)
                elif break_time == 60:  # 1-hour break → At least 60 min gap
                    model.Add(start2 >= end1 + 60)



solver = cp_model.CpSolver()
status = solver.Solve(model)

if status == cp_model.FEASIBLE or status == cp_model.OPTIMAL:
    print("Solution Found!")
else:
    print("No Feasible Solution!")



if status in (cp_model.FEASIBLE, cp_model.OPTIMAL):
    print("\nFinal Schedule:\n" + "-" * 50)
    for key, var in schedule_vars.items():
        if solver.Value(var) == 1:  # If the course is scheduled
            course, ts_id, start_time, end_time, day, instructor = key
            print(f"Course: {course} | Start Time: {start_time} | End Time: {end_time} | Day: {day} | Assigned to: {instructor}")
else:
    print("No feasible solution found.")






































