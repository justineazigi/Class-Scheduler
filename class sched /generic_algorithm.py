import random as rnd
import prettytable as prettytable
from enum import Enum
import pandas as pd
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, filename="data_loader.log", filemode="a",
                    format="%(asctime)s - %(levelname)s - %(message)s")

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
            required_cols = ["RoomNumber", "SeatingCapacity"]
            for col in required_cols:
                if col not in rooms_df.columns:
                    raise KeyError(f"Rooms file is missing required column: {col}")
            self._rooms = [
                room(row["RoomNumber"], int(row["SeatingCapacity"])) 
                for _, row in rooms_df.iterrows()
                if not pd.isnull(row["RoomNumber"]) and not pd.isnull(row["SeatingCapacity"])
            ]           
            logging.info(f"{len(self._rooms)} rooms loaded successfully.")
        except Exception as e:
            logging.error(f"Error loading rooms: {e}")
            raise
    def get_rooms(self):
        return self._rooms
    

    def load_meeting_times(self):
        try:
            meeting_times_file = "/Users/justiineazigi/Documents/Data/Meeting_times.xlsx"
            if not os.path.exists(meeting_times_file):
                raise FileNotFoundError(f"{meeting_times_file} is missing!")
            meeting_times_df = pd.read_excel(meeting_times_file)
            required_cols = ["MeetingTimeID", "TimeSlot"]
            for col in required_cols:
                if col not in meeting_times_df.columns:
                    raise KeyError(f"Meeting times file is missing required column: {col}")
            self._meetingTimes = [
                meetingTime(row["MeetingTimeID"], row["TimeSlot"])
                for _, row in meeting_times_df.iterrows()
                if not pd.isnull(row["MeetingTimeID"]) and not pd.isnull(row["TimeSlot"])
            ]
            logging.info(f"{len(self._meetingTimes)} meeting times loaded successfully.")
        except Exception as e:
            logging.error(f"Error loading meeting times: {e}")
            raise
    def get_meetingTimes(self):
        return self._meetingTimes

    def load_instructors(self):
        try:
            instructors_file = "/Users/justiineazigi/Documents/Data/instructors.xlsx"
            if not os.path.exists(instructors_file):
                raise FileNotFoundError(f"{instructors_file} is missing!")
            instructors_df = pd.read_excel(instructors_file)
            required_cols = ["InstructorID", "Name"]
            for col in required_cols:
                if col not in instructors_df.columns:
                    raise KeyError(f"Instructors file is missing required column: {col}")
            self._instructors = [
                instructor(row["InstructorID"], row["Name"])
                for _, row in instructors_df.iterrows()
                if not pd.isnull(row["InstructorID"]) and not pd.isnull(row["Name"])
            ]           
            logging.info(f"{len(self._instructors)} instructors loaded successfully.")
        except Exception as e:
            logging.error(f"Error loading instructors: {e}")
            raise
    def get_instructors(self):
        return self._instructors
    

    def load_tas(self):
        try:
            tas_file = "/Users/justiineazigi/Documents/Data/teaching_assistant.xlsx"
            if not os.path.exists(tas_file):
                raise FileNotFoundError(f"{tas_file} is missing!")
            tas_df = pd.read_excel(tas_file)
            required_cols = ["TAID", "Name"]
            for col in required_cols:
                if col not in tas_df.columns:
                    raise KeyError(f"Teaching assistants file is missing required column: {col}")
            self._teaching_assistants = [
                TeachingAssistant(row["TAID"], row["Name"])
                for _, row in tas_df.iterrows()
                if not pd.isnull(row["TAID"]) and not pd.isnull(row["Name"])
            ]           
            logging.info(f"{len(self._teaching_assistants)} teaching assistants loaded successfully.")
        except Exception as e:
            logging.error(f"Error loading teaching assistants: {e}")
            raise
    def get_tas(self):
        return self._teaching_assistants
       

    def load_courses(self):
        try:
            courses_file = "/Users/justiineazigi/Documents/Data/courses.xlsx"
            if not os.path.exists(courses_file):
                raise FileNotFoundError(f"{courses_file} is missing!")
            courses_df = pd.read_excel(courses_file)
            required_cols = ["CourseNumber", "CourseName", "MaxStudents", "InstructorID"]
            for col in required_cols:
                if col not in courses_df.columns:
                    raise KeyError(f"Courses file is missing required column: {col}")
            self._courses = [
                course(row["CourseNumber"], row["CourseName"], row["InstructorID"], int(row["MaxStudents"]), None)
                for _, row in courses_df.iterrows()
                if not pd.isnull(row["CourseNumber"]) and not pd.isnull(row["CourseName"]) and not pd.isnull(row["InstructorID"]) and not pd.isnull(row["MaxStudents"])
            ]                       
            logging.info(f"{len(self._courses)} courses loaded successfully.")
        except Exception as e:
            logging.error(f"Error loading courses: {e}")
            raise
    def get_courses(self):
        return self._courses

    def load_departments(self):
        try:
            departments_file = "/Users/justiineazigi/Documents/Data/departments.xlsx"
            if not os.path.exists(departments_file):
                raise FileNotFoundError(f"{departments_file} is missing!")
            departments_df = pd.read_excel(departments_file)
            required_cols = ["DepartmentName", "CourseNumbers"]
            for col in required_cols:
                if col not in departments_df.columns:
                    raise KeyError(f"Departments file is missing required column: {col}")
            self._depts = [
                department(row["DepartmentName"], row["CourseNumbers"])
                for _, row in departments_df.iterrows()
                if not pd.isnull(row["DepartmentName"]) and not pd.isnull(row["CourseNumbers"])
            ]         
            logging.info(f"{len(self._depts)} departments loaded successfully.")
        except Exception as e:
            logging.error(f"Error loading departments: {e}")
            raise
    def get_depts(self):
        return self._depts
    

    def load_instructor_availability(self):
        try:
            instructor_availability_file = "/Users/justiineazigi/Documents/Data/instructor_availability .xlsx"
            if not os.path.exists(instructor_availability_file):
                raise FileNotFoundError(f"{instructor_availability_file} is missing!")           
            instructor_availability_df = pd.read_excel(instructor_availability_file)
            required_cols = ["InstructorID", "AvailableSlots"]
            for col in required_cols:
                if col not in instructor_availability_df.columns:
                    raise KeyError(f"Instructor availability file is missing required column: {col}")
            self._instructor_availability = {
                row["InstructorID"]: row["AvailableSlots"].split(",")
                for _, row in instructor_availability_df.iterrows()
                if not pd.isnull(row["InstructorID"]) and not pd.isnull(row["AvailableSlots"])
            }
            logging.info("Instructor availability loaded successfully.")
        except Exception as e:
            logging.error(f"Error loading instructor availability: {e}")
            raise
    def get_instructor_availability(self):
        return self._instructor_availability
    ''''''
class schedule:
    def __init__(self):
        self.data = Data()
        self.classes = []
        self._numbOfConflicts = 0
        self._fitness = -1
        self._classNumb = 0
        self._isFitnessChanged = True
    
    def inintialize (self):
        depts = self.data.get_depts()
        for depts in depts:
            for courses in depts.get_courses():
                newClass = Class(self._classNumb, depts, courses)
                self._classNumb += 1
                newClass.set_meetingTime(rnd.choice(Data.get_meetingTimes()))
                newClass.set_room(rnd.choice(Data.get_rooms()))
                newClass.set_instructor(rnd.choice(Data.get_instructors()))
                self.classes.append(newClass)
        return self
    
    def calculate_fitness(self):
        for i, class1 in enumerate(self.classes):
            if (class1.get_room().get_seatingCapacity() < class1.get_course().get_maxNumbOfStudents()):
                self._numbOfConflicts += 1
            for class2 in self.classes[i+1:]:
                    if (class1.get_meetingTime() == class2.get_meetingTime() and class1.get_id() != class2.get_id()):
                        if (class1.get_room() == class2.get_room()): self._numbOfConflicts += 1
                        if (class1.get_instructor() == class2.get_instructor()): self._numbOfConflicts += 1

        self._fitness = 1 / (1.0 * self._numbOfConflicts + 1)
        self._isFitnessChanged = False
        return self._fitness
    ''''''

class population:
    def __init__(self, size):
        self._size = size
        self._data = Data()
        self._schedules = []
        for i in range(size):
            self._schedules.append(schedule().initialize())
    ''''''
class genetic_algorithm:
    def evolve(self, population):
        return self._mutate_population(self._crossover_population(population))
    
    def _crossover_population(self, population):
        crossoverPopulation = population(0)
        for i in range(number_of_elite_schedules):
            crossoverPopulation.get_schedules().append(population.get_schedules()[i])
        for i in range(number_of_elite_schedules, POPULATION_SIZE):
            parent1 = self._select_tournament_population(population)
            parent2 = self._select_tournament_population(population)
            crossoverPopulation.get_schedules().append(self._crossover_schedule(parent1, parent2))
        return crossoverPopulation
    
    
    def _mutate_population(self, population):
        for i in range(number_of_elite_schedules), len(population.get_schedules()):
            self._mutate_schedule(population.get_schedules()[i])
        return population
    
    def _crossover_schedule(self, schedule1, schedule2):
        child = schedule1.initialize()
        for i in range(len(child.get_classes())):
            if (rnd.random() > 0.5):
                child.get_classes()[i] = schedule1.get_classes()[i]
            else:
                child.get_classes()[i] = schedule2.get_classes()[i]
        return child
    
    def _mutate_schedule(self, mutateSchedule):
        for class_obj in schedule.get_classes():
            if rnd.random() < mutation_rate:
                class_obj.set_meetingTime(rnd.choice(Data.get_meetingTimes()))
                class_obj.set_room(rnd.choice(Data.get_rooms()))
                class_obj.set_instructor(rnd.choice(Data.get_instructors()))
        return mutateSchedule

    def _select_tournament_population(self, population):
        tournamentPopulation = population(tournament_selection_size)
        for _ in range(tournament_selection_size):
            tournamentPopulation.get_schedules().append(
                rnd.choice(population.get_schedules())
            )
                
        tournamentPopulation.get_schedules().sort(key = lambda s: s.calculate_fitness(), reverse = True)
        return tournamentPopulation.get_schedules()[0]
    
    ''''''
class course:
    def __init__(self, courseNumber, courseName, InstructorID, maxStudents, meetingTime):
         self.courseNumber = courseNumber
         self.courseName = courseName
         self.instructorID = InstructorID
         self.maxStudents = maxStudents
         self.meetingTime = meetingTime
    def get_courseNumber(self):
        return self.courseNumber
    def get_courseName(self):
        return self.courseName
    def get_instructorID(self):
        return self.instructorID
    def get_maxStudents(self):
        return self.maxStudents
    def get_meetingTime(self):
        return self.meetingTime
    def __str__(self):
        return self.courseNumber + " " + self.courseName
    ''''''
class room:
    def __init__(self, number, seatingCapacity):
        self.number = number
        self.seatingCapacity = seatingCapacity
    def get_number(self):
        return self.number
    def get_seatingCapacity(self):
        return self.seatingCapacity
    ''''''
class instructor:
    def __init__(self, id, name):
        self.id = id
        self.name = name
    def get_id(self):
        return self.id
    def get_name(self):
        return self.name
    ''''''
class meetingTime:
    def __init__(self, id, time):
        self.id = id
        self.time = time
    def get_id(self):
        return self.id
    def get_time(self):
        return self.time
    ''''''
class department:
    def __init__(self, name, courses):
        self.name = name
        self.courses = courses
    def get_name(self):
        return self.name
    def get_courses(self):
        return self.courses
    
    ''''''
class Class:
    def __init__(self, id, dept, course):
        self.id = id
        self.dept = dept
        self.course = course
        self.meetingTime = None
        self.room = None
    def get_id(self):
        return self.id
    def get_dept(self):
        return self.dept
    def get_course(self):
        return self.course
    def get_meetingTime(self):
        return self.meetingTime
    def get_room(self):
        return self.room
    def set_meetingTime(self, meetingTime): 
        self.meetingTime = meetingTime
    def set_room(self, room):
        self.room = room
    def __str__(self):
        return self.dept.get_name() + " " + self.course.get_number() + " " + \
            str(self.room.get_number()) + " " + str(self._instructor.get_id()) + " " + str(self.meetingTime.get_id())
        

    ''''''
class TeachingAssistant:
    def __init__(self, id, name):
        self.id = id
        self.name = name
    def get_id(self):
        return self.id
    def get_name(self):
        return self.name
    ''''''
class conflict:
    class conflictType(Enum):
        INSTRUCTOR_BOOKING=1
        SAME_ROOM = 1
        ROOM_BOOKING = 2
        INSTRUCTOR_AVAILABILITY = 4
    def __init__(self, conflictType, conflictBetweenClasses):
        self.conflictType = conflictType
        self.conflictBetweenClasses = conflictBetweenClasses
        def get_conflictType(self):
            return self.conflictType
        def get_conflictBetweenClasses(self):
            return self.conflictBetweenClasses
class Displaymanager:
    def __init__(self, data):
        self.data = data

    def print_available_data(self):
        print("> All Available Data")
        self.print_depts()
        self.print_course()
        self.print_instructor()
        self.print_room()
        self.print_meetingTime()
        
    def print_depts(self):
        print("departments:")
        for department in self.data.get_depts():
            print("name: ", department.get_name(), " courses: ", department.get_courses())
        print("")
        
    def print_course(self):
        print("courses:")
        for course in self.data.get_courses():           
            instructors = [instructor.get_name() for instructor in course.get_instructors()]
            print(f"-{course.get_number()}: {course.get_name()}"
                  f" (max # of students: {course.get_maxNumbOfStudents()}, instructors: {','.join (instructors)})")
        print("")
        
    def print_instructor(self):
        print("instructors:")
        for instructor in self.data.get_instructors():
            print(f"-{instructor.get_id()}: {instructor.get_name()}")
        print("")

    def print_room(self):
        print("rooms:")
        for room in self.data.get_rooms():
            print(f"-{room.get_number()}: {room.get_seatingCapacity()}")
        print("")

    def print_meetingTime(self):
        print("meeting times:")
        for meetingTime in self.data.get_meetingTimes():
            print(f"-{meetingTime.get_id()}: {meetingTime.get_time()}")
        print("")
  
    def print_generation(self,generation_number,population):
        print(f"\n> Generation # {generation_number}")
        print("schedules:")
        for i, schedule in enumerate(population.get_schedules()):
            print(f"schedule #{i+1}: Fitness= {schedule.calculate_fitness():.4f}")
        print("")

    
    def print_schedule_as_table(self, schedule):
        classes = schedule.get_classes()
        table = prettytable.PrettyTable(['Class #', 'Dept', 'Course (number, max # of students)', 'Room (Capacity)', 'Instructor (ID)', 'Meeting Time (ID)'])
        for i in range(len(classes)):
            table.add_row([str(i), classes[i].get_dept().get_name(), classes[i].get_course().__str__(), \
                classes[i].get_room().get_number() + " (" + str(classes[i].get_room().get_seatingCapacity()) + ")", \
                classes[i].get_instructor().get_id(), classes[i].get_meetingTime().get_id() + " (" + classes[i].get_meetingTime().get_time() + ")"])
        print(table)


    def print_final_solution(self, population):
        
        best_schedule = max(population.get_schedules(), key=lambda s: s.calculate_fitness())
        print("Final Solution (Best Schedule):")
        self.print_schedule_as_table(best_schedule)


if __name__ == "__main__":
    data = Data()
    display_manager = Displaymanager(data)
    display_manager.print_available_data()
    generation_number = 0
    population = population(POPULATION_SIZE)  
    display_manager.print_generation(generation_number, population)
    display_manager.print_final_solution(population)




