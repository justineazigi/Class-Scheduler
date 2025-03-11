import pandas as pd
from ortools.sat.python import cp_model


fall_courses = pd.read_csv("/Users/justiineazigi/Downloads/Data/fallcourses.csv")
intro_courses = pd.read_csv("/Users/justiineazigi/Downloads/Data/intro.csv")
timeslot = pd.read_csv("/Users/justiineazigi/Downloads/Data/timeslot.csv")
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
    section = row.section
    credit_hours = row.credit_hours
    meeting_time = row.meeting_time
    assigned_ta = row.TA_ID  

    for ts_row in timeslot.itertuples(index=False):
        ts_id = ts_row.TimeSlotID
        ts_meeting_time = ts_row.meeting_time
        ts_start_time = ts_row.start_time
        ts_end_time = ts_row.end_time
        ts_credit_hours = ts_row.Credit_hours

        if ts_credit_hours == credit_hours and ts_meeting_time == meeting_time:
            for day in [day.strip().capitalize() for day in row.Days.split(",")]:
                key = (course, section, ts_id, ts_start_time, ts_end_time, day, assigned_ta)
                schedule_vars[key] = model.NewBoolVar(f"{course}_Sec{section}_{ts_id}_{ts_start_time}_{ts_end_time}_{day}_{assigned_ta}")
        
for row in fall_courses.itertuples(index=False):
    course = row.course_code
    credit_hours = row.credit_hours
    meeting_time = row.meeting_time 
    assigned_instructor = row.instructor_name  

    for ts_row in timeslot.itertuples(index=False):
        ts_id = ts_row.TimeSlotID
        ts_meeting_time = ts_row.meeting_time
        ts_start_time = ts_row.start_time
        ts_end_time = ts_row.end_time
        ts_credit_hours = ts_row.Credit_hours

        if ts_credit_hours == credit_hours and ts_meeting_time == meeting_time:
            for day in [day.strip().capitalize() for day in row.Days.split(",")]:
                key = (course, ts_id, ts_start_time, ts_end_time, day, assigned_instructor)
                schedule_vars[key] = model.NewBoolVar(f"{course}_{ts_id}_{ts_start_time}_{ts_end_time}_{day}_{assigned_instructor}")
                #print(f"Created Variable for {course}: {key}")

print("Existing schedule_vars keys:", list(schedule_vars.keys()))


#  instructors and TAs should not teach more than one course at the same timeslot 
for instructor in fall_courses["instructor_name"].unique():
    for ts_id, start_time, end_time in zip(timeslot["TimeSlotID"], timeslot["start_time"], timeslot["end_time"]):
        for day in days_of_week:
            model.Add(
                sum(
                    schedule_vars[(course, ts_id, start_time, end_time, day, instructor)]
                    for course in fall_courses["course_code"].unique()
                    if (course, ts_id, start_time, end_time, day, instructor) in schedule_vars
                ) <= 1
            )
for ta in intro_courses["TA_ID"].unique():
    for ts_id, start_time, end_time in zip(timeslot["TimeSlotID"], timeslot["start_time"], timeslot["end_time"]):
        for day in [d.capitalize() for d in days_of_week]:  
            model.Add(
                sum(
                    schedule_vars[(course, section, ts_id, start_time, end_time, day, ta)]
                    for course in intro_courses["course_code"].unique()
                    for section in intro_courses[intro_courses["course_code"] == course]["section"].unique()
                    if (course, section, ts_id, start_time, end_time, day, ta) in schedule_vars
                ) <= 1
            )

#  courses should be assigned to their specific meetind days
for row in fall_courses.itertuples(index=False):
    course = row.course_code
    days = [day.strip().capitalize() for day in row.Days.split(",")]
    course_schedule = [schedule_vars[key] for key in schedule_vars if key[0] == course and key[4] in days]
    print(f"Course: {course}, Required Days: {days}, Scheduled Variables: {course_schedule}")
    if course_schedule:
        model.Add(sum(course_schedule) == len(days))

for row in intro_courses.itertuples(index=False):
    course = row.course_code
    section = row.section
    days = [day.strip().capitalize() for day in row.Days.split(",")]
    course_schedule = [schedule_vars[key] for key in schedule_vars if key[0] == course and key[1] == section and key[5] in days]
    if course_schedule:
        model.Add(sum(course_schedule) == len(days))   


solver = cp_model.CpSolver()
status = solver.Solve(model)
for key, var in schedule_vars.items():
    print(f"Key: {key}, Value: {solver.Value(var)}")
if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
    print("\nFinal Course Schedule:")
    for key, var in schedule_vars.items():
        if solver.Value(var) == 1:
            course, *_, start_time, end_time, day, assigned_person = key
            print(f"Course: {course} | Start Time: {start_time} | End Time: {end_time} | Day: {day} | Assigned to: {assigned_person}")
else:
    print("No feasible schedule found!")




#  checking the value of monday in the slover
for key, var in schedule_vars.items():
    if key[0] == "STAT 4640":  # Filter only STAT 4640
        print(f"Key: {key}, Assigned Value: {solver.Value(var)}")


##monday do not seem to asigned to any of the days 
for key in schedule_vars.keys():
    if key[0] == "STAT 4640":
        print("Generated Variable:", key)
        print("\nChecking Assigned Variables for STAT 4640:")


