import random as rnd
import prettytable as prettytable
from enum import Enum
import pandas as pd
import os



POPULATION_SIZE = 9
number_of_elite_schedules = 1
mutation_rate = 0.1
tournament_selection_size = 3

class Data:
    def __init__(self):
        self._rooms = []
        self._meetingTimes = []
        self._instructors = []
        self._courses = []
        self._depts = []
        self._teaching_assistants = []
        self._instructor_availability = {}
        self.initialize()

    def load_data(self):
        # Load rooms
        rooms_df = pd.read_excel("rooms.xlsx")
        for _, row in rooms_df.iterrows():
            self._rooms.append(Room(row["RoomNumber"], int(row["SeatingCapacity"])))
        rooms_df.head()

        # Load meeting times
        meeting_times_df = pd.read_excel("meeting_times.xlsx")
        for _, row in meeting_times_df.iterrows():
            self._meetingTimes.append(MeetingTime(row["MeetingTimeID"], row["TimeSlot"]))
        meeting_times_df.head()

        # Load instructors
        instructors_df = pd.read_excel("instructors.xlsx")
        for _, row in instructors_df.iterrows():
            self._instructors.append(Instructor(row["InstructorID"], row["Name"]))
        instructors_df.head()
        
        # Load teaching assistants
        instructors_df = pd.read_excel("teaching_assistants.xlsx")
        for _, row in instructors_df.iterrows():
            self._instructors.append(Instructor(row["TAID"], row["Name"]))
        instructors_df.head()

        # Load courses
        courses_df = pd.read_excel("courses.xlsx")
        for _, row in courses_df.iterrows():
            course_instructors = [
                inst for inst in self._instructors if inst.get_id() in row["InstructorIDs"].split(",")]
        courses_df.head()

        departments_df = pd.read_excel("departments.xlsx")
        for _, row in departments_df.iterrows():
            course_numbers = row["CourseNumbers"].split(",")  # Split course numbers into a list
            self._departments.append(Department(row["DepartmentName"], course_numbers))
        departments_df.head()
        
          # Load INSTRUCTOR_AVAILABILITY
        instructor_availability_df = pd.read_excel("instructor_availability.xlsx")
        for _, row in instructor_availability_df.iterrows():
            self._instructor_availability[row["InstructorID"]] = row["AvailableSlots"].split(",")
        instructor_availability_df.head()
