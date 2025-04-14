import pandas as pd
from ortools.sat.python import cp_model
import ast
from itertools import combinations, product
from datetime import datetime, timedelta
from collections import defaultdict

# Load datasets
fall_courses = pd.read_csv("/Users/justiineazigi/Documents/Class-Scheduler/Data/fallcourses.csv")
intro_courses = pd.read_csv("/Users/justiineazigi/Documents/Class-Scheduler/Data/intro.csv")
timeslot = pd.read_csv("/Users/justiineazigi/Documents/Class-Scheduler/Data/timeslot.csv")

model = cp_model.CpModel()
days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
schedule_vars = {}

# Decision Variables: Intro & Fall Courses
ta_courses = intro_courses[intro_courses["TA_ID"].str.startswith("TA")]
for row in ta_courses.itertuples(index=False):
    for ts_row in timeslot.itertuples(index=False):
        if ts_row.Credit_hours == row.credit_hours and ts_row.meeting_time == row.meeting_time:
            for day in [d.strip().capitalize() for d in row.Days.split(",")]:
                key = (row.course_code, ts_row.TimeSlotID, ts_row.start_time, ts_row.end_time, day, row.TA_ID)
                schedule_vars[key] = model.NewBoolVar(f"{key}")

for row in fall_courses.itertuples(index=False):
    for ts_row in timeslot.itertuples(index=False):
        if ts_row.Credit_hours == row.credit_hours and ts_row.meeting_time == row.meeting_time:
            for day in [d.strip().capitalize() for d in row.Days.split(",")]:
                key = (row.course_code, ts_row.TimeSlotID, ts_row.start_time, ts_row.end_time, day, row.instructor_name)
                schedule_vars[key] = model.NewBoolVar(f"{key}")

print(f"Total decision variables created: {len(schedule_vars)}")


# Constraint 1: Each course meets once per scheduled day
for df in [fall_courses, intro_courses]:
    for row in df.itertuples(index=False):
        for day in [d.strip().capitalize() for d in row.Days.split(",")]:
            model.Add(sum(schedule_vars[key] for key in schedule_vars if key[0] == row.course_code and key[4] == day) == 1)

# Helper function
def times_overlap(start1, end1, start2, end2):
    fmt = "%H:%M"
    s1 = datetime.strptime(start1, fmt)
    e1 = datetime.strptime(end1, fmt)
    s2 = datetime.strptime(start2, fmt)
    e2 = datetime.strptime(end2, fmt)
    return s1 < e2 and s2 < e1

# Constraint 2: Instructor/TA conflict avoidance
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


# Constraint 3: Same time slot across course days
course_day_vars = defaultdict(list)
for key, var in schedule_vars.items():
    course, _, start_time, end_time, day, _ = key
    course_day_vars[(course, day)].append((key, var))

for course in set(k[0] for k in course_day_vars):
    days = [k[1] for k in course_day_vars if k[0] == course]
    for d1, d2 in combinations(days, 2):
        vars_day1 = [v for _, v in course_day_vars[(course, d1)]]
        vars_day2 = [v for _, v in course_day_vars[(course, d2)]]
        for v1, v2 in product(vars_day1, vars_day2):
            model.Add(v1 == v2)

# Constraint 4: No overlaps in specialization required courses
specialization = pd.read_csv("/Users/justiineazigi/Documents/Class-Scheduler/Data/programs_dimension.csv")
specialization.columns = specialization.columns.str.strip()

def safe_eval(val):
    if isinstance(val, str):
        try:
            return ast.literal_eval(val)
        except:
            return [v.strip() for v in val.strip("[]").split(",")]
    return val if isinstance(val, list) else []

specialization["required_courses"] = specialization["Required_courses"].apply(safe_eval)
specialization = specialization[specialization["required_courses"].apply(lambda x: len(x) > 1)]

for _, row in specialization.iterrows():
    for c1, c2 in combinations(set(row["required_courses"]), 2):
        for day in days_of_week:
            for k1 in [k for k in schedule_vars if k[0] == c1 and k[4] == day]:
                for k2 in [k for k in schedule_vars if k[0] == c2 and k[4] == day]:
                    if times_overlap(k1[2], k1[3], k2[2], k2[3]):
                        model.Add(schedule_vars[k1] + schedule_vars[k2] <= 1)

# Constraint 5: Required vs Elective conflict (soft)
specialization["elective_courses"] = specialization["Elective_courses"].apply(safe_eval)
specialization = specialization[specialization["elective_courses"].apply(lambda x: len(x) > 1)]
overlap_penalties = []

for _, row in specialization.iterrows():
    for req, elec in product(set(row["required_courses"]), set(row["elective_courses"])):
        for day in days_of_week:
            for k1 in [k for k in schedule_vars if k[0] == req and k[4] == day]:
                for k2 in [k for k in schedule_vars if k[0] == elec and k[4] == day]:
                    if times_overlap(k1[2], k1[3], k2[2], k2[3]):
                        penalty_var = model.NewBoolVar(f"penalty_{k1}_{k2}")
                        model.Add(schedule_vars[k1] + schedule_vars[k2] <= 1 + penalty_var)
                        overlap_penalties.append(penalty_var)

# Constraint 6: External course conflict
external_courses = pd.read_csv("/Users/justiineazigi/Documents/Class-Scheduler/Data/external.csv")
external_courses.columns = external_courses.columns.str.strip()
external_courses["Day"] = external_courses["Day"].fillna("").apply(lambda x: [d.strip().capitalize() for d in x.split(",") if d.strip()])
external_courses["Start_Time"] = external_courses["Start_Time"].astype(str)
external_courses["End_Time"] = external_courses["End_Time"].astype(str)

external_dict = {}
for row in external_courses.itertuples(index=False):
    for day in row.Day:
        external_dict[(row.external_courses, day)] = (row.Start_Time, row.End_Time)

specialization["External_courses"] = specialization["External_courses"].apply(safe_eval)

for _, row in specialization.iterrows():
    for ext in row["External_courses"]:
        for req in row["Required_courses"]:
            for day in days_of_week:
                if (ext, day) in external_dict:
                    ext_start, ext_end = external_dict[(ext, day)]
                    for key in schedule_vars:
                        if key[0] == req and key[4] == day and times_overlap(key[2], key[3], ext_start, ext_end, buffer_minutes=10):
                            model.Add(schedule_vars[key] == 0)

# Constraint 7: Faculty time preference (hard)
faculty_preferences = pd.read_csv("/Users/justiineazigi/Documents/Class-Scheduler/Data/instructor_preferences.csv")

time_blocks = {
    "morning": ("08:00", "11:59"),
    "afternoon": ("12:00", "15:59"),
    "evening": ("16:00", "19:50")
}

for _, row in faculty_preferences.iterrows():
    pref = str(row["preferred_time"]).strip().lower()
    if pref in time_blocks:
        start_pref, end_pref = time_blocks[pref]
        for key in schedule_vars:
            if key[5] == row["instructor_name"]:
                if not times_overlap(key[2], key[3], start_pref, end_pref):
                    model.Add(schedule_vars[key] == 0)

# Constraint 8: Breaks between sessions (soft)
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



# Objective function
model.Maximize(sum(schedule_vars[k] for k in schedule_vars))

# Solve
solver = cp_model.CpSolver()
status = solver.Solve(model)


if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
    print("\n📅 Final Scheduled Assignments:\n")
    for key, var in schedule_vars.items():
        if solver.Value(var) == 1:
            course, timeslot_id, start_time, end_time, day, instructor_or_ta = key
            print(f"{course} assigned to {instructor_or_ta} on {day} from {start_time} to {end_time} (Slot {timeslot_id})")
else:
    print("❌ No feasible solution found.")