import openpyxl
import StructTools
from StructTools import deepCopy

class UserSpec():
    def __init__(self, xl_doc):
        # Tries to open excel file
        # Catches any errors that may arise from this process
        try:
            workbook = openpyxl.load_workbook(filename=xl_doc)
        except FileNotFoundError:
            raise SystemExit("FILE ERROR: Could not find excel file")
        except PermissionError:
            raise SystemExit("FILE ERROR: Invalid permissions. Make sure excel file is not open in another app")
        
        # Extracts all the data from the excel file
        # Defines as private attributes with getter methods (makes them read-only)
        self.__days, self.__periods = self.getDaysAndPeriods(workbook)
        self.__rooms, self.__capacities = self.getRooms(workbook)
        self.__module_names, self.__module_count, self.__session_counts = self.getModules(workbook)
        self.__courses, self.__course_to_modules, self.__course_student_counts = self.getCourses(workbook)
        self.__lecturer_names, self.__lecturer_count, self.__module_to_lecturers = self.getLecturers(workbook)
        self.__breaks, self.__max_streak, self.__spread_sessions, self.__spread_across_lecturers, self.__room_based_ordering = self.getConstraints(workbook)
    
    '''
    Getter methods
    Allow private attributes to be accessed like normal attributes, but still can't be edited
    '''
    @property
    def days(self):
        return self.__days
    
    @property
    def periods(self):
        return self.__periods
    
    @property
    def rooms(self):
        return deepCopy(self.__rooms)
    
    @property
    def capacities(self):
        return self.__capacities.copy()
    
    @property
    def module_names(self):
        return self.__module_names.copy()
    
    @property
    def module_count(self):
        return self.__module_count
    
    @property
    def session_counts(self):
        return self.__session_counts.copy()
    
    @property
    def courses(self):
        return self.__courses.copy()
    
    @property
    def course_to_modules(self):
        return deepCopy(self.__course_to_modules)
    
    @property
    def course_student_counts(self):
        return self.__course_student_counts.copy()
    
    @property
    def lecturer_names(self):
        return self.__lecturer_names.copy()
    
    @property
    def lecturer_count(self):
        return self.__lecturer_count
    
    @property
    def module_to_lecturers(self):
        return deepCopy(self.__module_to_lecturers)
    
    @property
    def breaks(self):
        return self.__breaks
    
    @property
    def max_streak(self):
        return self.__max_streak
    
    @property
    def spread_sessions(self):
        return self.__spread_sessions
    
    @property
    def spread_across_lecturers(self):
        return self.__spread_across_lecturers
    
    @property
    def room_based_ordering(self):
        return self.__room_based_ordering
    
    def getDaysAndPeriods(self, workbook:openpyxl.Workbook) -> tuple[int]:
        """
        Gets the number of days in a week and the number of periods per day

        Args:
            workbook (openpyxl.Workbook): Object representing excel workbook

        Returns:
            tuple[int]: (no. days, no. periods)
        
        Raises:
            SystemExit: Quits program and displays useful error message when data inputted incorrectly
        """           
        general_sheet = workbook["Days & Periods"]
        
        return (int(self.getValidVal(general_sheet, "B1", "days", "General", False)), 
                int(self.getValidVal(general_sheet, "B2", "periods", "General", False)))
    
    def getRooms(self, workbook: openpyxl.Workbook) -> tuple[dict]:
        """
        Gets the names of each room, their types and their capactities.

        Args:
            workbook (openpyxl.Workbook): Object representing excel workbook

        Returns:
            tuple[dict]: (dict of lists of room names organised by type, dict mapping room names to capactities)
        """        
        rooms = {"lec" : [], "sem" : [], "lab" : []}
        capacities = dict()
        
        room_sheet = workbook["Rooms"]
        
        # Reads every row until row with an empty first cell
        valid = True
        i = 2
        
        
        while valid:
            room_type = str(self.getValidVal(room_sheet, f"B{i}", 'Lecturer, lab or seminar', "Rooms")).lower()[:3]
            room_name = str(self.getValidVal(room_sheet, f"A{i}", "Room name", "Rooms"))
            rooms[room_type].append(room_name)
            
            capacities[room_name] = int(self.getValidVal(room_sheet, f"C{i}", "Capacity", "Rooms"))
            
            i += 1
            valid = room_sheet[f"A{i}"].value is not None
        
        return rooms, capacities
    
    def getModules(self, workbook: openpyxl.Workbook) -> tuple[list, int, dict[list]]:
        """
        Gets each module's name and the number of lecture, seminar
        and lab sessions each has in a week

        Args:
            workbook (openpyxl.Workbook): Object representing excel workbook

        Returns:
           list: The names of each module, where the index = the modules ID
           int: The total number of modules
           dict[list]: Store the number of lectures, seminars and labs for each module
        """        
        module_names = []
        session_counts = {"lec" : [], "sem" : [], "lab" : []}
        
        modules_sheet = workbook["Modules"]
        valid = True
        i = 2
        
        while valid:
            module_names.append(str(self.getValidVal(modules_sheet, f"A{i}", "Module names", "Modules")))
            
            session_counts["lec"].append(int(self.getValidVal(modules_sheet, f"B{i}", "No. lectures per week", "Modules")))
            session_counts["sem"].append(int(self.getValidVal(modules_sheet, f"C{i}", "No. seminars per week", "Modules")))
            session_counts["lab"].append(int(self.getValidVal(modules_sheet, f"D{i}", "No. labs per week", "Modules")))
            
            i += 1
            valid = modules_sheet[f"A{i}"].value is not None
        
        module_count = len(module_names)
        
        return module_names, module_count, session_counts
            
    
    def getCourses(self, workbook):
        courses = []
        course_to_module = dict()
        course_student_counts = dict()
        
        courses_sheet = workbook["Courses"]
        valid = True
        i = 2
        
        while valid:
            courses.append(str(self.getValidVal(courses_sheet, f"A{i}", "Course", "Courses")))
            course_to_module[courses[-1]] = [self.module_names.index(mod) for mod in self.getValidModulesList(courses_sheet, f"B{i}", "Courses")]
            course_student_counts[courses[-1]] = int(self.getValidVal(courses_sheet, f"C{i}", "No. students", "Courses"))
            
            i += 1
            valid = courses_sheet[f"A{i}"].value is not None
            
        self.assertAllModulesUsed(course_to_module.values(), "Courses")
        
        return courses, course_to_module, course_student_counts
    
    def getValidModulesList(self, sheet, cell, sheet_name):
        modules = str(self.getValidVal(sheet, cell, "Modules", sheet_name)).split(',')
        modules = [mod.strip() for mod in modules]
        
        diff = set(modules) - set(self.module_names)
        
        if diff == set():
            return modules
        
        raise SystemExit(f"INPUT ERROR: The module names {repr(StructTools.quickSort(list(diff))).strip('[]')} listed in the modules field of row {int(cell[1]) - 1} of the table in the {sheet_name} sheet are not valid modules")
    
        
    def getLecturers(self, workbook):
        lecturer_names = []
        
        lecturer_to_modules = []
        
        lecturers_sheet = workbook["Lecturers"]
        valid = True
        i = 2
        
        while valid:
            lecturer_names.append(str(self.getValidVal(lecturers_sheet, f"A{i}", "Lecturer", "Lecturers")))
            lecturer_to_modules.append(list(map(self.module_names.index, self.getValidModulesList(lecturers_sheet, f"B{i}", "Lecturers"))))
            i += 1
            valid = lecturers_sheet[f"A{i}"].value is not None
        
        lecturer_count = len(lecturer_names)
        
        self.assertAllModulesUsed(lecturer_to_modules, "Lecturers")
        
        module_to_lecturers = [[] for i in range(self.module_count)]
        for (lec, mod_list) in enumerate(lecturer_to_modules):
            for mod in mod_list:
                module_to_lecturers[mod].append(lec)
        
        return lecturer_names, lecturer_count, module_to_lecturers
    
    def assertAllModulesUsed(self, modules_iter, sheet_name):
        modules_used = set()
        for mod in StructTools.chain(*modules_iter):
            modules_used.add(mod)
        
        diff = set(self.module_names) - set(map(lambda m: self.module_names[m], modules_used))
        
        if diff == set():
            return
        
        raise SystemExit(f"INPUT ERROR: Modules {repr(StructTools.quickSort(list(diff))).strip('[]')} not used in {sheet_name} sheet")
    
    def getConstraints(self, workbook):
        constraints_sheet = workbook["Constraints"]
        
        breaks = str(self.getValidVal(constraints_sheet, "B2", "Break periods?", "Constraints", False)) == "Yes"
        max_streak = int(self.getValidVal(constraints_sheet, "B3", "Max no. lessons before break", "Constraints", False))
        spread_sessions = str(self.getValidVal(constraints_sheet, "B4", "Spread lessons throughout week?", "Constraints", False)) == "Yes"
        spread_across_lecturers = str(self.getValidVal(constraints_sheet, "B7", "Spread sessions between lecturers?", "Constraints", False)) == "Yes"
        room_based_ordering = str(self.getValidVal(constraints_sheet, "B10", "Minimse no. rooms used and spare capacity?", "Constraints", False)) == "Yes"
        
        return breaks, max_streak, spread_sessions, spread_across_lecturers, room_based_ordering

    def getValidVal(self, sheet, cell, col_name, sheet_name, isTable=True):
        val = sheet[cell].value
        
        if val is None:
            if isTable:
                raise SystemExit(f"INPUT ERROR: No value entered for '{col_name}' field of row {int(cell[1]) - 1} in the table of sheet {sheet_name}")
            else:
                raise SystemExit(f"INPUT ERROR: No value entered for '{col_name}' field in sheet {sheet_name}")
        
        return val
