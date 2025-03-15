import pandas as pd
from ortools.sat.python import cp_model

# Load Data
fall_courses = pd.read_csv("/Users/justiineazigi/Documents/Class-Scheduler/Data/fallcourses.csv")
intro_courses = pd.read_csv("/Users/justiineazigi/Documents/Class-Scheduler/Data/intro copy.csv")
timeslot = pd.read_csv("/Users/justiineazigi/Documents/Class-Scheduler/Data/timeslot.csv")

# Normalize day names
days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

# Initialize Model
model = cp_model.CpModel()
schedule_vars = {}

# Decision Variables
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

print(f"Total decision variables created: {len(schedule_vars)}")

# Constraints: Ensure an instructor/TA is assigned to only one course per time slot
unique_instructors = set(entry[5] for entry in schedule_vars.keys())
days_of_week = set(entry[4] for entry in schedule_vars.keys())

for instructor in unique_instructors:
    for day in days_of_week:       
        instructor_schedule = {key: value for key, value in schedule_vars.items() if key[5] == instructor and key[4] == day}        
        unique_time_slots = set((key[1], key[2], key[3]) for key in instructor_schedule.keys())

        for ts_id, start_time, end_time in unique_time_slots:
            assigned_courses = [
                key for key in instructor_schedule.keys()
                if key[1] == ts_id and key[2] == start_time and key[3] == end_time
            ]
            if assigned_courses:
                model.Add(sum(schedule_vars[key] for key in assigned_courses) <= 1)

# Constraint: Courses should be scheduled only once per day
unique_courses = set(entry[0] for entry in schedule_vars.keys())
unique_time_slots_instructors = set((entry[1], entry[2], entry[3], entry[5]) for entry in schedule_vars.keys())

for course in unique_courses:
    for day in days_of_week:
        relevant_keys = [
            (course, ts_id, start_time, end_time, day, instructor)
            for ts_id, start_time, end_time, instructor in unique_time_slots_instructors
            if (course, ts_id, start_time, end_time, day, instructor) in schedule_vars
        ]
        if relevant_keys:
            model.Add(sum(schedule_vars[key] for key in relevant_keys) <= 1)

# Solve the Model
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 60  # Moved before Solve call
status = solver.Solve(model)

# Display Results
if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
    print("\n✅ Course Schedule Validation:")
    course_schedule = {}
    for key, var in schedule_vars.items():
        if solver.Value(var) == 1:
            course, ts_id, start_time, end_time, day, instructor = key
            if (course, day) not in course_schedule:
                course_schedule[(course, day)] = []
            course_schedule[(course, day)].append((start_time, end_time, instructor))

    for (course, day), times in course_schedule.items():
        print(f"📅 Course {course} | Day: {day} | Scheduled Times: {times}")
        if len(times) > 1:
            print(f"⚠️ Conflict detected: {course} is scheduled more than once on {day}!")
else:
    print("❌ No feasible schedule found!")

# Count Assigned Courses
assigned_count = sum(solver.Value(var) for var in schedule_vars.values())
print(f"Total assigned courses: {assigned_count}")

