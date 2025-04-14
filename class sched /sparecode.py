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
for key, var in schedule_vars.items():
    print(f"{key}: {var}")
print(f"Total decision variables created: {len(schedule_vars)}")

for row in fall_courses.itertuples(index=False):
    course = row.course_code
    model.Add(sum(schedule_vars[key] for key in schedule_vars if key[0] == course) == 1)
for row in intro_courses.itertuples(index=False):
    course = row.course_code
    model.Add(sum(schedule_vars[key] for key in schedule_vars if key[0] == course ) == 1)



#INSTRUCTORS AND TA SHOULD NOT TEACH MORE THAN ONE COURSE AT THE SAME TIMESLOT
constraint_count = 0
for instructor in fall_courses["instructor_name"].unique():
    for day in [d.capitalize() for d in days_of_week]:
     for ts_id, start_time, end_time in zip(timeslot["TimeSlotID"], timeslot["start_time"], timeslot["end_time"]):
            model.Add(
                sum(
                    schedule_vars[(course, ts_id, start_time, end_time, day, instructor)]
                    for course in fall_courses["course_code"].unique()
                    if (course, ts_id, start_time, end_time, day, instructor) in schedule_vars
                ) <= 1
            )
for ta in intro_courses["TA_ID"].unique():
   for day in [d.capitalize() for d in days_of_week]:
     for ts_id, start_time, end_time in zip(timeslot["TimeSlotID"], timeslot["start_time"], timeslot["end_time"]):
            model.Add(
                sum(
                    schedule_vars[(course, section, ts_id, start_time, end_time, day, ta)]
                    for course in intro_courses["course_code"].unique()
                    for section in intro_courses[intro_courses["course_code"] == course]["section"].unique()
                    if (course, section, ts_id, start_time, end_time, day, ta) in schedule_vars
                ) <= 1
            )
            constraint_count += 1
print(f"Total Faculty Load Balancing Constraints: {constraint_count}")

# CONSTRAINT: No Course Overlaps - Each course must be scheduled at most once per  day.
for course in fall_courses["course_code"].unique():
    for day in days_of_week:
        assigned_slots = [
            (start_time, end_time) for start_time, end_time in zip(timeslot["start_time"], timeslot["end_time"])
            for instructor in fall_courses["instructor_name"].unique()
            if (course, start_time, end_time, day, instructor) in schedule_vars
            and solver.Value(schedule_vars[(course, start_time, end_time, day, instructor)]) == 1
        ]
        if len(assigned_slots) > 1:
            print(f" Conflict! Course {course} is scheduled multiple times on {day} at times {assigned_slots}.")
for course in intro_courses["course_code"].unique():
    for day in days_of_week:
        assigned_slots = [
            (start_time, end_time) for start_time, end_time in zip(timeslot["start_time"], timeslot["end_time"])
            for ta in intro_courses["TA_ID"].unique()
            if (course, start_time, end_time, day, ta) in schedule_vars
            and solver.Value(schedule_vars[(course, start_time, end_time, day, ta)]) == 1
        ]
        if len(assigned_slots) > 1:
            print(f" Conflict! Course {course} is scheduled multiple times on {day} at times {assigned_slots}.")




# CONSTRAINT: No Course Overlaps - Each course must be scheduled at most once per  day
constraint_count = 0
for course in fall_courses["course_code"].unique():
    for day in days_of_week:
        model.Add(
            sum(
                schedule_vars[(course, start_time, end_time, day, instructor)]
                for start_time, end_time in zip(timeslot["start_time"], timeslot["end_time"])
                for instructor in fall_courses["instructor_name"].unique()
                if (course, start_time, end_time, day, instructor) in schedule_vars
            ) <= 1
        )

for course in intro_courses["course_code"].unique():
    for day in days_of_week:
        model.Add(
            sum(
                schedule_vars[(course, start_time, end_time, day, ta)]
                for start_time, end_time in zip(timeslot["start_time"], timeslot["end_time"])
                for ta in intro_courses["TA_ID"].unique()
                if (course, start_time, end_time, day, ta) in schedule_vars
            ) <= 1
        )
        constraint_count += 1  
print(f"Total Course Scheduling Constraints (One Course Per Day): {constraint_count}")

##OBEJCTIVE FUNCTION
model.Maximize(sum(schedule_vars[key] for key in schedule_vars))


solver = cp_model.CpSolver()
status = solver.Solve(model)


if status == cp_model.FEASIBLE or status == cp_model.OPTIMAL:
    print("Solution Found!")
else:
    print("No Feasible Solution!")

for key, var in schedule_vars.items():
    print(f"Key: {key}, Value: {solver.Value(var)}")
print(f"Objective Value: {solver.ObjectiveValue()}")
print(f"Total Decision Variables: {len(schedule_vars)}")



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


##nstructor conflict 
    for instructor in fall_courses['instructor_name'].unique():
    for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]:
        for ts_row in timeslot.itertuples(index=False):
            start_time = ts_row.start_time
            end_time = ts_row.end_time
            model.Add(
                sum(
                    schedule_vars[key]
                    for key in schedule_vars
                    if key[4] == day and key[5] == instructor and key[2] == start_time and key[3] == end_time
                ) <= 1
            )

# TA conflict constraint
for ta in intro_courses['TA_ID'].unique():
    for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]:
        for ts_row in timeslot.itertuples(index=False):
            start_time = ts_row.start_time
            end_time = ts_row.end_time
            model.Add(
                sum(
                    schedule_vars[key]
                    for key in schedule_vars
                    if key[4] == day and key[5] == ta and key[2] == start_time and key[3] == end_time
                ) <= 1
            )


##generating an initial schedule without constraints
model = cp_model.CpModel()
solver = cp_model.CpSolver()
def print_schedule():
    print("\nGenerated Schedule:")
    for key, var in schedule_vars.items():
        value = solver.Value(var)  # Correct way to get the binary value
        if value == 1:  
            course, ts_id, start, end, day, instructor = key
            print(f"{course} -> {day}, {start}-{end} ({instructor})")

status = solver.Solve(model)

if status in (cp_model.FEASIBLE, cp_model.OPTIMAL):
    print_schedule()
else:
    print("No feasible schedule found.")

status = solver.Solve(model)
print(f"Solver Status: {status}")  # Should return an "OPTIMAL" or "FEASIBLE" solution even if it's arbitrary

for key, var in schedule_vars.items():
    print(f"{key}: {solver.Value(var)}")  # Check how OR-Tools randomly assigns them


for key, var in schedule_vars.items():
    print(f"{key}: {var}")






#  check for time conflicts for required courses conflicting 
def has_time_conflict(course1, course2, schedule_df):
    df1 = schedule_df[schedule_df['course_code'] == course1]
    df2 = schedule_df[schedule_df['course_code'] == course2]
    
    for _, row1 in df1.iterrows():
        for _, row2 in df2.iterrows():
            if row1['day'] == row2['day']:  # Same day
                if not (row1['end_time'] <= row2['start_time'] or row2['end_time'] <= row1['start_time']):
                    return True  # Overlapping time
    return False

# Check conflicts for each specialization
conflicts = []

for _, row in specialization.iterrows():
    required_courses = row['required_courses']
    program_code = row['program_code']
    
    # Compare all pairs of required courses
    for course1, course2 in combinations(required_courses, 2):
        if has_time_conflict(course1, course2, schedule_df):
            conflicts.append((program_code, course1, course2))

# Display conflicts
if conflicts:
    print("Conflicting Required Courses:")
    for conflict in conflicts:
        print(f"Specialization {conflict[0]}: {conflict[1]} conflicts with {conflict[2]}")
else:
    print("No conflicts found!")


#  checking the value of monday in the slover
for key, var in schedule_vars.items():
    if key[0] == "STAT 2600":  # Filter only STAT 4640
        print(f"Key: {key}, Assigned Value: {solver.Value(var)}")

for key, var in schedule_vars.items():
    if key[0] == "STAT 4640":  # Filter only STAT 4640
        print(f"Key: {key}, Assigned Value: {solver.Value(var)}")



##monday do not seem to asigned to any of the days in stat 4640 
for key in schedule_vars.keys():
    if key[0] == "STAT 4640":
        print("Generated Variable:", key)
        print("\nChecking Assigned Variables for STAT 4640:")




###	4. No overlap between required courses in the same program
specialization = pd.read_csv("/Users/justiineazigi/Documents/Class-Scheduler/Data/programs_dimension.csv")
specialization.columns = specialization.columns.str.strip()

specialization['Required_courses'] = specialization['Required_courses'].apply(lambda x: [] if pd.isna(x) else x)

def safe_eval(course_list): #convert string lists to actual lists
    if isinstance(course_list, str):  # only if its a string
        try:
            return ast.literal_eval(course_list)
        except (SyntaxError, ValueError):
            return [course.strip() for course in course_list.strip("[]").split(", ") if course]
    return course_list  
specialization.loc[:, 'required_courses'] = specialization['Required_courses'].apply(safe_eval)
print(specialization[['program_code', 'required_courses']].head())

for _, row in specialization.iterrows():
    required_courses = row['required_courses']
    if not required_courses:  # Skip if the list is empty
        continue
    # Compare all pairs of required courses
    for course1, course2 in combinations(required_courses, 2):
        for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]:
            relevant_vars_course1 = [key for key in schedule_vars if key[0] == course1 and key[4] == day]
            relevant_vars_course2 = [key for key in schedule_vars if key[0] == course2 and key[4] == day]
            for k1 in relevant_vars_course1:
                for k2 in relevant_vars_course2:
                    if times_overlap(k1[2], k1[3], k2[2], k2[3]):
                        model.Add(schedule_vars[k1] + schedule_vars[k2] <= 1)


print(specialization['required_courses'].apply(type).unique())