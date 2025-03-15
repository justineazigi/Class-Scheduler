#If a course meets twice (e.g., Monday & Wednesday) or thrice (e.g., Monday, Tuesday, Friday):The start and end times should be the same on all those days.
for course in unique_courses:
    course_schedule = [
        key for key in schedule_vars.keys() if key[0] == course
    ]
    if len(course_schedule) > 1:  
        # Extract the first scheduled instance of this course to use as reference
        first_instance = course_schedule[0]
        _, ts_id_ref, start_ref, end_ref, day_ref, instructor_ref = first_instance
        # Enforce same start and end time for all instances of this course
        for key in course_schedule:
            _, ts_id, start, end, day, instructor = key
            model.Add(start == start_ref)
            model.Add(end == end_ref)









#  instructors and TAs should not teach more than one course at the same timeslot on the same day.


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

    df_schedule = pd.DataFrame(schedule_output)
    print("Generated Schedule:")
    print(df_schedule)
else:
    print("No feasible solution found!")





for instructor in fall_courses["instructor_name"].unique():
    for day in days_of_week:
        instructor_schedule = [schedule_vars[key] for key in schedule_vars if key[-1] == instructor and key[5] == day]
        if instructor_schedule:
            model.Add(sum(instructor_schedule) <= 1)

for ta in intro_courses["TA_ID"].unique():
    for day in days_of_week:
        ta_schedule = [schedule_vars[key] for key in schedule_vars if key[-1] == ta and key[5] == day]
        if ta_schedule:
            model.Add(sum(ta_schedule) <= 1)

for course in fall_courses["course_code"].unique():
    for day in days_of_week:
        course_schedule = [schedule_vars[key] for key in schedule_vars if key[0] == course and key[5] == day]
        if course_schedule:
            model.Add(sum(course_schedule) == 1) 

for course in intro_courses["course_code"].unique():
    for day in days_of_week:
        course_schedule = [schedule_vars[key] for key in schedule_vars if key[0] == course and key[5] == day]
        if course_schedule:
            model.Add(sum(course_schedule) == 1)


##courses 
for course in fall_courses["course_code"].unique():
    course_schedule = [schedule_vars[key] for key in schedule_vars if key[0] == course]
    if course_schedule:
        model.Add(sum(course_schedule) == 1) 
        
for course in intro_courses["course_code"].unique():
    course_schedule = [schedule_vars[key] for key in schedule_vars if key[0] == course]
    if course_schedule:
        model.Add(sum(course_schedule) == 1) 







for key, var in schedule_vars.items():
    print(f"{key}: {var}")






for constraint in model.Proto().constraints:
    print(constraint)


# ✅ Constraint 1 : No faculty should be booked twice in the same time slot on the same day
for instructor in fall_courses["instructor_name"].unique():  # Loop over all instructors
    for ts_id, start_time, end_time in zip(timeslot["TimeSlotID"], timeslot["start_time"], timeslot["end_time"]):
        for day in days_of_week:
            model.Add(
                sum(
                    schedule_vars[(course, ts_id, start_time, end_time, day, instructor)]
                    for course in fall_courses["course_code"].unique()
                    if (course, ts_id, start_time, end_time, day, instructor) in schedule_vars
                ) <= 1
            )



sample_vars = list(schedule_vars.keys())[:10]
for var in sample_vars:
    print(var, schedule_vars[var])

for key, var in schedule_vars.items():
    print(f"{key}: {var}")



# Extract and print the schedule if a solution is found
# Solve the model
solver = cp_model.CpSolver()
status = solver.Solve(model)

# Extract and print the schedule if a solution is found
if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
    print("\n✅ Solution Found! Here is the schedule:\n")
    
    for key, var in schedule_vars.items():
        if solver.Value(var) == 1:
            print(f"{key}: {var}")
            
else:
    print("No feasible solution found.")


print("Schedule Variables:", schedule_vars)
















for course in fall_courses["course_code"].unique():
    for day in days_of_week:
        model.Add(
            sum(
                schedule_vars[(course, ts_id, start_time, end_time, day, assigned_instructor)]
                for ts_id, start_time, end_time in zip(timeslot["TimeSlotID"], timeslot["start_time"], timeslot["end_time"])
                for instructor in fall_courses["instructor_name"].unique()
                if (course, ts_id, start_time, end_time, day, instructor) in schedule_vars
            ) <= 1
        )

# Constraint 2: An instructor should not have overlapping classes in the same time slot
for instructor in fall_courses["instructor_name"].unique():
    for ts_id, start_time, end_time in zip(timeslot["TimeSlotID"], timeslot["start_time"], timeslot["end_time"]):
        for day in days_of_week:
            model.Add(
                sum(
                    schedule_vars[(course, section, ts_id, start_time, end_time, day, instructor)]
                    for course in fall_courses["course_code"].unique()
                    for section in fall_courses[fall_courses["course_code"] == course]["section"].unique()
                    if (course, section, ts_id, start_time, end_time, day, instructor) in schedule_vars
                ) <= 1
            )


print("Existing schedule_vars keys:", list(schedule_vars.keys()))




  if ts_credit_hours == credit_hours and ts_meeting_time == meeting_time:
            for day in [day.strip().capitalize() for day in row.Days.split(",")]:
                schedule_vars[(course, section, ts_id, ts_start_time, ts_end_time, day, assigned_ta)] = model.NewBoolVar(
                    f"{course}_Sec{section}_{ts_id}_{ts_start_time}_{ts_end_time}_{day}_{assigned_ta}"
                )

##CHECKING FOR MISSING KEYS
for instructor in fall_courses["instructor_name"].unique():
    print(f"Instructor: {instructor}, Available Time Slots: {timeslot['TimeSlotID'].tolist()}")

for ta in intro_courses["TA_ID"].unique():
    print(f"TA: {ta}, Available Time Slots: {timeslot['TimeSlotID'].tolist()}")

for instructor in fall_courses["instructor_name"].unique():
    for course in fall_courses["course_code"].unique():
        for ts_id, start_time, end_time in zip(timeslot["TimeSlotID"], timeslot["start_time"], timeslot["end_time"]):
            for day in days_of_week:
                key = (course, ts_id, start_time, end_time, day, instructor)
                if key not in schedule_vars:
                    print("Missing key for instructor constraint:", key)





for instructor in unique_instructors:
    for day in days_of_week:
        # Step 3: Identify all unique time slots for the instructor on that day
        instructor_schedule = {key: value for key, value in schedule_vars.items() if key[5] == instructor and key[4] == day}
        unique_time_slots = set((key[1], key[2], key[3]) for key in instructor_schedule.keys())
        for ts_id, start_time, end_time in unique_time_slots:
            # Step 4: Collect all courses assigned to the instructor for this day and time slot
            assigned_courses = [
                key[0] for key in instructor_schedule.keys()
                if key[1] == ts_id and key[2] == start_time and key[3] == end_time
            ]
            # Step 5: Constraint to ensure an instructor teaches only one course at a time
            constraint = {
                "Instructor": instructor,
                "Day": day,
                "TS_ID": ts_id,
                "Start Time": start_time,
                "End Time": end_time,
                "Assigned Courses": assigned_courses,
                "Max Courses": 1  
            }

            constraints.append(constraint)



for instructors in set(key[5] for key in schedule_vars.keys()):
    for day in days_of_week:
        for ts_id in set(key[1] for key in schedule_vars.keys() if key[5] == instructors):
            assigned_courses = [
                schedule_vars[key]
                for key in schedule_vars
                if key[5] == instructors and key[1] == ts_id and key[4] == day
            ]
            if assigned_courses:
                model.Add(sum(assigned_courses) <= 1)







schedule_results = []
if status in (cp_model.FEASIBLE, cp_model.OPTIMAL):
    for key, var in schedule_vars.items():
        if solver.Value(var) == 1:  # If the course is scheduled
            course, ts_id, start_time, end_time, day, instructor = key
            schedule_results.append((course, day, start_time, end_time, instructor))

    # Convert results to a DataFrame for better visualization
    import pandas as pd
    schedule_df = pd.DataFrame(schedule_results, columns=["Course", "Day", "Start Time", "End Time", "Instructor"])
    
    # Display the schedule
    import ace_tools as tools
    tools.display_dataframe_to_user(name="Course Schedule", dataframe=schedule_df)



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


            
assigned_count = sum(solver.Value(var) for var in schedule_vars.values())
print(f"Total assigned courses: {assigned_count}")
print(f"Total decision variables created: {len(schedule_vars)}")


for key in list(schedule_vars.keys())[:10]:  # Print first 10 keys
    print(key)



for instructor in unique_instructors:
    for day in days_of_week:
        instructor_schedule = [
            key for key in schedule_vars.keys() if key[5] == instructor and key[4] == day
        ]
        for key1 in instructor_schedule:
            course1, ts_id1, start1, end1, day1, instructor1 = key1
            for key2 in instructor_schedule:
                if key1 == key2:
                    continue  # Skip if it's the same course
                course2, ts_id2, start2, end2, day2, instructor2 = key2
                if (start1 < end2 and start2 < end1):  # Overlapping condition
                    model.Add(schedule_vars[key1] + schedule_vars[key2] <= 1)