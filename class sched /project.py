
import pandas as pd
from ortools.sat.python import cp_model
import ast
from itertools import combinations
from datetime import datetime
from datetime import datetime, timedelta
from collections import defaultdict

fall_courses = pd.read_csv("/Users/justiineazigi/Documents/Class-Scheduler/Data/fallcourses.csv")
intro_courses = pd.read_csv("/Users/justiineazigi/Documents/Class-Scheduler/Data/intro.csv")
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

for key, var in schedule_vars.items():
    print(f"{key}: {var}")
print(f"Total decision variables created: {len(schedule_vars)}")


# 1. Constraint to ensure that each course is scheduled for exactly one timeslot per day
for row in fall_courses.itertuples(index=False):
    course = row.course_code
    for day in [day.strip().capitalize() for day in row.Days.split(",")]:
        model.Add(sum(schedule_vars[key] for key in schedule_vars 
                      if key[0] == course and key[4] == day) == 1)

for row in intro_courses.itertuples(index=False):
    course = row.course_code
    for day in [day.strip().capitalize() for day in row.Days.split(",")]:
        model.Add(sum(schedule_vars[key] for key in schedule_vars 
                      if key[0] == course and key[4] == day) == 1)

# 2. Constraint to ensure that each instructor/TA is assigned to only one course per time slot

# Helper Function 
def times_overlap(start1, end1, start2, end2):
    fmt = "%H:%M"
    s1 = datetime.strptime(start1, fmt)
    e1 = datetime.strptime(end1, fmt)
    s2 = datetime.strptime(start2, fmt)
    e2 = datetime.strptime(end2, fmt)
    return s1 < e2 and s2 < e1

# Instructor conflict constraint (handling time overlaps!)
for instructor in fall_courses['instructor_name'].unique():
    for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]:
        relevant_vars = [key for key in schedule_vars if key[4] == day and key[5] == instructor]
        for i in range(len(relevant_vars)):
            for j in range(i + 1, len(relevant_vars)):
                k1 = relevant_vars[i]
                k2 = relevant_vars[j]
                if times_overlap(k1[2], k1[3], k2[2], k2[3]):
                    model.Add(schedule_vars[k1] + schedule_vars[k2] <= 1)

# TA conflict constraint (handling  time overlaps!)
for ta in intro_courses['TA_ID'].unique():
    for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]:
        relevant_vars = [key for key in schedule_vars if key[4] == day and key[5] == ta]
        for i in range(len(relevant_vars)):
            for j in range(i + 1, len(relevant_vars)):
                k1 = relevant_vars[i]
                k2 = relevant_vars[j]
                if times_overlap(k1[2], k1[3], k2[2], k2[3]):
                    model.Add(schedule_vars[k1] + schedule_vars[k2] <= 1)


##3. from the solver we want The time slot (start and end time) to be the same across all days the course meets
course_day_vars = defaultdict(list)  
for key, var in schedule_vars.items():
    course, timeslot_id, start_time, end_time, day, instructor_or_ta = key
    course_day_vars[(course, day)].append((key, var))

for course in set([key[0] for key in schedule_vars]):
    course_days = [key[1] for key in course_day_vars if key[0] == course] 
    for i in range(len(course_days)):
        for j in range(i + 1, len(course_days)):
            day_i = course_days[i]
            day_j = course_days[j]
            vars_day_i = [v for k, v in course_day_vars[(course, day_i)]]
            vars_day_j = [v for k, v in course_day_vars[(course, day_j)]]
            for var_i, var_j in zip(vars_day_i, vars_day_j):
                model.Add(var_i == var_j)

##. course overlaps within various specializarion
specialization = pd.read_csv("/Users/justiineazigi/Documents/Class-Scheduler/Data/programs_dimension.csv")
specialization.columns = specialization.columns.str.strip()

def safe_eval(course_list):
    if isinstance(course_list, str):
        try:
            return ast.literal_eval(course_list)
        except (SyntaxError, ValueError):
            return [course.strip() for course in course_list.strip("[]").split(", ") if course]
    return course_list if isinstance(course_list, list) else []


#4. No overlap between required courses in the same program specialization
specialization['required_courses'] = specialization['Required_courses'].apply(safe_eval)
specialization = specialization[specialization['required_courses'].apply(lambda x: isinstance(x, list) and len(x) > 1)] # Filter out Nan rows

for _, row in specialization.iterrows():
    required_courses = set(row['required_courses']) 
    for course1, course2 in combinations(required_courses, 2):
        for day in days_of_week:
            relevant_vars_course1 = [key for key in schedule_vars if key[0] == course1 and key[4] == day]
            relevant_vars_course2 = [key for key in schedule_vars if key[0] == course2 and key[4] == day]
            for k1 in relevant_vars_course1:
                for k2 in relevant_vars_course2:
                    if times_overlap(k1[2], k1[3], k2[2], k2[3]):
                        model.Add(schedule_vars[k1] + schedule_vars[k2] <= 1)


##5  Elective vs Required Course Conflict Implementation(soft constraint)
specialization['elective_courses'] = specialization['Elective_courses'].apply(safe_eval)
specialization = specialization[specialization['elective_courses'].apply(lambda x: isinstance(x, list) and len(x) > 1)] #filter out nan  rows

overlap_penalties = []  
for _, row in specialization.iterrows():
    required_courses = set(row['required_courses'])
    elective_courses = set(row['elective_courses'])
    for req_course in required_courses:
        for elec_course in elective_courses:
            for day in days_of_week:
                relevant_vars_req = [key for key in schedule_vars if key[0] == req_course and key[4] == day]
                relevant_vars_elec = [key for key in schedule_vars if key[0] == elec_course and key[4] == day]
                
                for k1 in relevant_vars_req:
                    for k2 in relevant_vars_elec:
                        if times_overlap(k1[2], k1[3], k2[2], k2[3]):
                            penalty_var = model.NewBoolVar(f"overlap_{k1}_{k2}")
                            model.Add(schedule_vars[k1] + schedule_vars[k2] <= 1 + penalty_var)
                            overlap_penalties.append(penalty_var)
model.Minimize(sum(overlap_penalties))


#STAT courses do not overlap with the predefined External (CS courses and maths courses )
specialization["External_courses"] = specialization["External_courses"].apply(safe_eval)

external_courses = pd.read_csv("/Users/justiineazigi/Documents/Class-Scheduler/Data/external.csv")
external_courses.columns = external_courses.columns.str.strip()
external_courses["Day"] = external_courses["Day"].fillna("").astype(str)
external_courses["Day"] = external_courses["Day"].apply(lambda x: [day.strip().capitalize() for day in x.split(",") if day.strip()])
external_courses["Start_Time"] = external_courses["Start_Time"].astype(str)
external_courses["End_Time"] = external_courses["End_Time"].astype(str)


external_course_times = {}
for row in external_courses.itertuples(index=False):
    course = row.external_courses
    for day in row.Day:
        external_course_times[(course, day)] = (row.Start_Time, row.End_Time)


def times_overlap(start1, end1, start2, end2, buffer_minutes=30): #added 30 mins buffer to help transitioning from one class to the other 
    s1 = datetime.strptime(start1, "%H:%M")
    e1 = datetime.strptime(end1, "%H:%M")
    s2 = datetime.strptime(start2, "%H:%M")
    e2 = datetime.strptime(end2, "%H:%M")
    buffer = timedelta(minutes=buffer_minutes)
    return s1 < e2 + buffer and s2 < e1 + buffer

# Loop through each specialization to apply constraints
for _, row in specialization.iterrows():
    required_courses = row["Required_courses"]
    external_courses = row["External_courses"]
    for req_course in required_courses:
        for ext_course in external_courses:
            for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]:
                if (ext_course, day) in external_course_times:
                    ext_start, ext_end = external_course_times[(ext_course, day)]
                    for key in schedule_vars:
                        if key[0] == req_course and key[4] == day:
                            req_start, req_end = key[2], key[3]
                            if times_overlap(req_start, req_end, ext_start, ext_end):
                                model.Add(schedule_vars[key] == 0)

#Faculty Preferences
# Define time ranges for each session type
faculty_preferences = pd.read_csv("/Users/justiineazigi/Documents/Class-Scheduler/Data/instructor_preferences.csv")
faculty_preferences.head()

morning_range = ("08:00", "11:59")
afternoon_range = ("12:00", "15:59")
evening_range = ("16:00", "19:50")

for _, row in faculty_preferences.iterrows():
    instructor = row["instructor_name"]
    preferred_time = row["preferred_time"]
    if pd.isna(preferred_time):
        continue
    preferred_time = preferred_time.strip().lower()
    if preferred_time == "morning":
        preferred_start, preferred_end = morning_range
    elif preferred_time == "afternoon":
        preferred_start, preferred_end = afternoon_range
    elif preferred_time == "evening":
        preferred_start, preferred_end = evening_range
    else:
        # If "Any" or unrecognized, skip constraint
        continue
    for key in schedule_vars:
        if key[5] == instructor:
            slot_start = key[2]
            slot_end = key[3]
            if not times_overlap(slot_start, slot_end, preferred_start, preferred_end):
                model.Add(schedule_vars[key] == 0)


# Faculty preferences for breaks between sessions
penalties = []
for _, row in faculty_preferences.iterrows():
    instructor = row["instructor_name"]
    min_break = row["breaks_between_session"]
    if pd.isna(min_break) or min_break < 0:
        continue
    for day in days_of_week:
        rel_keys = [k for k in schedule_vars if k[5] == instructor and k[4] == day]
        for i in range(len(rel_keys)):
            for j in range(i + 1, len(rel_keys)):
                k1, k2 = rel_keys[i], rel_keys[j]
                s1, e1 = datetime.strptime(k1[2], "%H:%M"), datetime.strptime(k1[3], "%H:%M")
                s2, e2 = datetime.strptime(k2[2], "%H:%M"), datetime.strptime(k2[3], "%H:%M")
                gap = abs((s2 - e1).total_seconds() / 60)
                if 0 <= gap < min_break:
                    v = model.NewBoolVar(f"break_violation_{k1}_{k2}")
                    model.Add(schedule_vars[k1] + schedule_vars[k2] == 2).OnlyEnforceIf(v)
                    model.Add(schedule_vars[k1] + schedule_vars[k2] < 2).OnlyEnforceIf(v.Not())
                    penalties.append(v)



# Objective Function
model.Maximize(sum(schedule_vars[key] for key in schedule_vars))


solver = cp_model.CpSolver()
status = solver.Solve(model)

#final schedule in a list format
final_schedule = []

if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
    print("\n📋 Final Schedule as a List:\n")
    for key, var in schedule_vars.items():
        if solver.Value(var) == 1:
            course, timeslot_id, start_time, end_time, day, instructor_or_ta = key  
            final_schedule.append((course,timeslot_id,start_time, end_time, day, instructor_or_ta))
    
    print("self.schedule = [")
    for entry in final_schedule:
        print(f"    {entry},")
    print("]")
else:
    print("❌ No feasible solution found.")



# Save the final schedule to a CSV file
if scheduled_assignments:
    df_schedule = pd.DataFrame(scheduled_assignments)
df_schedule.to_csv("final_schedule.csv", index=False)



#Conflicting courses 
timeslot_map = timeslot.groupby(['Credit_hours', 'meeting_time'])[['start_time', 'end_time']].apply(
    lambda df: list(zip(df['start_time'], df['end_time']))
).to_dict()

conflict_list = []

specialization['Required_courses'] = specialization['Required_courses'].apply(safe_eval)
for _, row in specialization.iterrows():
    required_courses = row['Required_courses']
    for i, course in enumerate(required_courses):
        conflicting_courses = required_courses[:i] + required_courses[i+1:]

        course_row = fall_courses[fall_courses['course_code'] == course]
        if course_row.empty:
            course_row = intro_courses[intro_courses['course_code'] == course]
        if course_row.empty:
            continue  # Skip unknown course
        course_row = course_row.iloc[0]
        days_allowed = [[d.strip().capitalize() for d in str(course_row['Days']).split(',') if d.strip()]]
        credit_hours = int(course_row['credit_hours'])
        meeting_time = int(course_row['meeting_time'])

        time_slots_allowed = timeslot_map.get((credit_hours, meeting_time), [])

        conflict_list.append({
            "course": course,
            "conflicting_courses": conflicting_courses,
            "days_allowed": days_allowed,
            "time_slots_allowed": time_slots_allowed
        })


# Print the conflict list
for conflict in conflict_list:
    print(f"Course: {conflict['course']}")
    print(f"Conflicting Courses: {', '.join(conflict['conflicting_courses'])}")
    print(f"Days Allowed: {', '.join(conflict['days_allowed'][0])}")  # Print first element of the list
    print(f"Time Slots Allowed: {', '.join([f'{start} - {end}' for start, end in conflict['time_slots_allowed']])}")
    print()

import json
print(json.dumps(conflict_list, indent=4))












