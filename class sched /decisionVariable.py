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

print("Existing schedule_vars keys:", list(schedule_vars.keys()))
        
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


for instructor in fall_courses["instructor_name"].unique():
    for ts_id, start_time, end_time in zip(timeslot["TimeSlotID"], timeslot["start_time"], timeslot["end_time"]):
        for day in days_of_week:
            instructor_schedule = [schedule_vars[key] for key in schedule_vars if key[-1] == instructor and key[1] == ts_id and key[5] == day]
            if instructor_schedule:
                model.Add(sum(instructor_schedule) <= 1) 


for ta in intro_courses["TA_ID"].unique():
    for ts_id, start_time, end_time in zip(timeslot["TimeSlotID"], timeslot["start_time"], timeslot["end_time"]):
        for day in days_of_week:
            ta_schedule = [schedule_vars[key] for key in schedule_vars if key[-1] == ta and key[2] == ts_id and key[5] == day]
            if ta_schedule:
                model.Add(sum(ta_schedule) <= 1) 

for row in fall_courses.itertuples(index=False):
    course = row.course_code
    days = [day.strip().capitalize() for day in row.Days.split(",")]
    course_schedule = [schedule_vars[key] for key in schedule_vars if key[0] == course and key[5] in days]
    if course_schedule:
        model.Add(sum(course_schedule) == len(days))  # Must be assigned to all days it meets


for row in intro_courses.itertuples(index=False):
    course = row.course_code
    section = row.section
    days = [day.strip().capitalize() for day in row.Days.split(",")]
    course_schedule = [schedule_vars[key] for key in schedule_vars if key[0] == course and key[1] == section and key[5] in days]
    if course_schedule:
        model.Add(sum(course_schedule) == len(days))  # Must be assigned to all listed days


for course in fall_courses["course_code"].unique():
    course_schedule = [schedule_vars[key] for key in schedule_vars if key[0] == course]
    if course_schedule:
        model.Add(sum(course_schedule) == 1) # Each course must be assigned to exactly one slot per day

for course in intro_courses["course_code"].unique():
    course_schedule = [schedule_vars[key] for key in schedule_vars if key[0] == course]
    if course_schedule:
        model.Add(sum(course_schedule) == 1) # Each course must be assigned to exactly one slot per day




solver = cp_model.CpSolver()
status = solver.Solve(model)

if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
    print("\nFinal Course Schedule:")
    for key, var in schedule_vars.items():
        if solver.Value(var) == 1:
            course, *_, day, assigned_person = key
            print(f"Course: {course} | Day: {day} | Assigned to: {assigned_person}")
else:
    print("No feasible schedule found!")



if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
    schedule_output = []
    for key, var in schedule_vars.items():
        if solver.Value(var) == 1:  # Only include assigned courses
            schedule_output.append({
                "Course": key[0],
                "Section": key[1] if isinstance(key[1], int) else "N/A",
                "TimeSlot": key[2],
                "Start Time": key[3],
                "End Time": key[4],
                "Day": key[5],
                "Instructor/TA": key[6]
            })

    # Convert to DataFrame and display
    df_schedule = pd.DataFrame(schedule_output)
    print("Generated Schedule:")
    print(df_schedule)
else:
    print("No feasible solution found!")
for key, var in schedule_vars.items():
    print(f"Key: {key}, Value: {solver.Value(var)}")













