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

# Constraint: No Course Overlaps (Each course can only be scheduled once per time slot per day)
for course in fall_courses["course_code"].unique():
    for ts_id, start_time, end_time in zip(timeslot["TimeSlotID"], timeslot["start_time"], timeslot["end_time"]):
        for day in days_of_week:
            model.Add(
                sum(
                    schedule_vars[(course, ts_id, start_time, end_time, day, instructor)]
                    for instructor in fall_courses["instructor_name"].unique()
                    if (course, ts_id, start_time, end_time, day, instructor) in schedule_vars
                ) <= 1
            )
for course in intro_courses["course_code"].unique():
    for ts_id, start_time, end_time in zip(timeslot["TimeSlotID"], timeslot["start_time"], timeslot["end_time"]):
        for day in days_of_week:
            model.Add(
                sum(
                    schedule_vars[(course, ts_id, start_time, end_time, day, ta)]
                    for ta in intro_courses["TA_ID"].unique()
                    if (course, ts_id, start_time, end_time, day, ta) in schedule_vars
                ) <= 1
            )

# Constraint: Faculty Load Balancing (Each faculty and TA  can only teach one course per timeslot per day)
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
                    schedule_vars[(course, ts_id, start_time, end_time, day, ta)]
                    for course in intro_courses["course_code"].unique()
                    if (course,ts_id, start_time, end_time, day, ta) in schedule_vars
                ) <= 1
            )

# Objective Function: Maximize the number of scheduled courses - this will tell the solver to schedule as much courses while satisfyint the constraints 
model.Maximize(sum(schedule_vars[key] for key in schedule_vars))

# Solve the model
solver = cp_model.CpSolver()
status = solver.Solve(model)

# Check if a feasible solution was found
if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
    print("\n=== Generated Class Schedule ===\n")
    
    schedule_list = []
    
    for key in schedule_vars:
        if solver.Value(schedule_vars[key]) == 1:  # If the course is scheduled
            course, ts_id, start_time, end_time, day, instructor = key
            schedule_list.append([course, ts_id, start_time, end_time, day, instructor])
    
    # Sort the schedule list by time slot and day for better readability
    schedule_list.sort(key=lambda x: (x[1], x[4]))  # Sorting by TimeSlotID and Day
    
    # Print the schedule in a clean list format
    for entry in schedule_list:
        course, ts_id, start_time, end_time, day, instructor = entry
        print(f"Course: {course} | Time Slot: {ts_id} ({start_time} - {end_time}) | Day: {day} | Instructor: {instructor}")

else:
    print("No feasible schedule found.")
