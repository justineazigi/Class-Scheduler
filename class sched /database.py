import pandas as pd
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, filename="data_loader.log", filemode="a",
                    format="%(asctime)s - %(levelname)s - %(message)s")


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

    def initialize(self):
        try:
            self.load_rooms()
            self.load_meeting_times()
            self.load_instructors()
            self.load_tas()
            self.load_courses()
            self.load_departments()
            self.load_instructor_availability()
        
            logging.info("All data loaded successfully.")
        except Exception as e:
            logging.error(f"An error occurred during data initialization: {e}")
            raise

    def load_rooms(self):
        try:
            rooms_file = "/Users/justiineazigi/Documents/Data/room.xlsx"
            if not os.path.exists(rooms_file):
                raise FileNotFoundError(f"{rooms_file} is missing!")

            rooms_df = pd.read_excel(rooms_file)
            if "RoomNumber" not in rooms_df.columns or "SeatingCapacity" not in rooms_df.columns:
                raise KeyError("Rooms file is missing required columns: RoomNumber or SeatingCapacity")

            for _, row in rooms_df.iterrows():
                if pd.isnull(row["RoomNumber"]) or pd.isnull(row["SeatingCapacity"]):
                    raise ValueError(f"Invalid room data: {row}")
                self._rooms.append(Room(row["RoomNumber"], int(row["SeatingCapacity"])))

            logging.info(f"{len(self._rooms)} rooms loaded successfully.")
        except Exception as e:
            logging.error(f"Error loading rooms: {e}")
            raise

    def load_meeting_times(self):
        try:
            meeting_times_file = "/Users/justiineazigi/Documents/Data/Meeting_times.xlsx"
            if not os.path.exists(meeting_times_file):
                raise FileNotFoundError(f"{meeting_times_file} is missing!")

            meeting_times_df = pd.read_excel(meeting_times_file)
            if "MeetingTimeID" not in meeting_times_df.columns or "TimeSlot" not in meeting_times_df.columns:
                raise KeyError("Meeting times file is missing required columns: MeetingTimeID or TimeSlot")

            for _, row in meeting_times_df.iterrows():
                self._meetingTimes.append(MeetingTime(row["MeetingTimeID"], row["TimeSlot"]))

            logging.info(f"{len(self._meetingTimes)} meeting times loaded successfully.")
        except Exception as e:
            logging.error(f"Error loading meeting times: {e}")
            raise

    def load_instructors(self):
        try:
            instructors_file = "/Users/justiineazigi/Documents/Data/instructors.xlsx"
            if not os.path.exists(instructors_file):
                raise FileNotFoundError(f"{instructors_file} is missing!")

            instructors_df = pd.read_excel(instructors_file)
            if "InstructorID" not in instructors_df.columns or "Name" not in instructors_df.columns:
                raise KeyError("Instructors file is missing required columns: InstructorID or Name")

            for _, row in instructors_df.iterrows():
                self._instructors.append(Instructor(row["InstructorID"], row["Name"]))

            logging.info(f"{len(self._instructors)} instructors loaded successfully.")
        except Exception as e:
            logging.error(f"Error loading instructors: {e}")
            raise

    def load_tas(self):
        try:
            tas_file = "/Users/justiineazigi/Documents/Data/teaching_assistant.xlsx"
            if not os.path.exists(tas_file):
                raise FileNotFoundError(f"{tas_file} is missing!")

            tas_df = pd.read_excel(tas_file)
            if "TAID" not in tas_df.columns or "Name" not in tas_df.columns:
                raise KeyError("Teaching assistants file is missing required columns: TAID or Name")

            for _, row in tas_df.iterrows():
                self._teaching_assistants.append(TeachingAssistant(row["TAID"], row["Name"]))

            logging.info(f"{len(self._teaching_assistants)} teaching assistants loaded successfully.")
        except Exception as e:
            logging.error(f"Error loading teaching assistants: {e}")
            raise

    def load_courses(self):
        try:
            courses_file = "courses.xlsx"
            if not os.path.exists(courses_file):
                raise FileNotFoundError(f"{courses_file} is missing!")

            courses_df = pd.read_excel(courses_file)
            if not all(col in courses_df.columns for col in ["CourseNumber", "CourseName", "MaxStudents", "InstructorIDs"]):
                raise KeyError("Courses file is missing required columns: CourseNumber, CourseName, MaxStudents, InstructorIDs")

            for _, row in courses_df.iterrows():
                course_instructors = [
                    inst for inst in self._instructors if inst.get_id() in row["InstructorIDs"].split(",")
                ]
                self._courses.append(Course(row["CourseNumber"], row["CourseName"], course_instructors, int(row["MaxStudents"])))

            logging.info(f"{len(self._courses)} courses loaded successfully.")
        except Exception as e:
            logging.error(f"Error loading courses: {e}")
            raise

    def load_departments(self):
        try:
            departments_file = "/Users/justiineazigi/Documents/Data/departments.xlsx"
            if not os.path.exists(departments_file):
                raise FileNotFoundError(f"{departments_file} is missing!")

            departments_df = pd.read_excel(departments_file)
            if "DepartmentName" not in departments_df.columns or "CourseNumbers" not in departments_df.columns:
                raise KeyError("Departments file is missing required columns: DepartmentName or CourseNumbers")

            for _, row in departments_df.iterrows():
                course_numbers = row["CourseNumbers"].split(",")
                self._depts.append(Department(row["DepartmentName"], course_numbers))

            logging.info(f"{len(self._depts)} departments loaded successfully.")
        except Exception as e:
            logging.error(f"Error loading departments: {e}")
            raise

    def load_instructor_availability(self):
        try:
            instructor_availability_file = "/Users/justiineazigi/Documents/Data/instructor_availability .xlsx"
            if not os.path.exists(instructor_availability_file):
                raise FileNotFoundError(f"{instructor_availability_file} is missing!")

            instructor_availability_df = pd.read_excel(instructor_availability_file)
            if "InstructorID" not in instructor_availability_df.columns or "AvailableSlots" not in instructor_availability_df.columns:
                raise KeyError("Instructor availability file is missing required columns: InstructorID or AvailableSlots")

            for _, row in instructor_availability_df.iterrows():
                self._instructor_availability[row["InstructorID"]] = row["AvailableSlots"].split(",")

            logging.info("Instructor availability loaded successfully.")
        except Exception as e:
            logging.error(f"Error loading instructor availability: {e}")
            raise

   

try:
    data = Data()
    print("Rooms loaded:", len(data._rooms))  # Number of rooms loaded
    print("Courses loaded:", len(data._courses))  # Number of courses loaded
    print("Departments loaded:", len(data._depts))  # Number of departments loaded
    print("Instructor Availability:", data._instructor_availability)  # Instructor availability dictionary
except Exception as e:
    print("An error occurred:", e)




