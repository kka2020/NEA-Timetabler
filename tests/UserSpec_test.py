import unittest
from UserSpec import UserSpec

class testUserSpec(unittest.TestCase):
    def testExceptionHandling(self):
        self.assertRaises(SystemExit, lambda: UserSpec("Non-existent.xlsx"))
        # Have to manually test PermissionError by having file open in Excel whilst trying to use in program
        
        # Tests assertAllModulesUsed validation method
        with self.assertRaises(SystemExit) as e:
            UserSpec("tests/Missing modules in courses.xlsx")
        
        self.assertEqual(str(e.exception), "INPUT ERROR: Modules 'CALC', 'STATS' not used in Courses sheet")
        
        with self.assertRaises(SystemExit) as e:
            UserSpec("tests/Missing modules in lecturers.xlsx")
            
        self.assertEqual(str(e.exception), "INPUT ERROR: Modules 'ALG', 'CALC' not used in Lecturers sheet")
        
        # Tests getValidModulesList validation method
        with self.assertRaises(SystemExit) as e:
            UserSpec("tests/Invalid modules in courses.xlsx")
        
        self.assertEqual(str(e.exception), "INPUT ERROR: The module names 'FAKE1', 'FAKE2' listed in the modules field of row 1 of the table in the Courses sheet are not valid modules")
        
        with self.assertRaises(SystemExit) as e:
            UserSpec("tests/Invalid modules in lecturers.xlsx")
        
        self.assertEqual(str(e.exception), "INPUT ERROR: The module names 'FAKE1', 'FAKE2' listed in the modules field of row 1 of the table in the Lecturers sheet are not valid modules")
        
        # Tests getValidVal validation method
        with self.assertRaises(SystemExit) as e:
            UserSpec("tests/Missing values row type.xlsx")
        
        self.assertEqual(str(e.exception), "INPUT ERROR: No value entered for 'No. students' field of row 1 in the table of sheet Courses")
    
    def testValidExtraction(self):
        spec = UserSpec("tests/Valid Input Document.xlsx")

        self.assertEqual(spec.days, 5)
        self.assertEqual(spec.periods, 10)
        self.assertEqual(spec.rooms, {"lec" : ["lec1", "lec2"], "sem" : ["sem1", "sem2", "sem3"], "lab" : ["lab1", "lab2", "lab3"]})
        self.assertEqual(spec.capacities, {"lec1" : 100, "lec2" : 100, "sem1" : 30, "sem2" : 30, "sem3" : 30, "lab1" : 30, "lab2" : 30, "lab3" : 30})
        self.assertEqual(spec.module_names, ["ALG", "CALC", "STATS"])
        self.assertEqual(spec.module_count, 3)
        self.assertEqual(spec.session_counts, {"lec" : [2, 1, 3], "sem" : [2, 2, 1], "lab" : [1, 2, 1]})
        self.assertEqual(spec.courses, ["MECH", "ELEC", "BIO"])
        self.assertEqual(spec.course_to_modules, {"MECH" : [0, 1], "ELEC" : [0, 2], "BIO" : [2, 0]})
        self.assertEqual(spec.course_student_counts, {"MECH" : 30, "ELEC" : 30, "BIO" : 30})
        self.assertEqual(spec.lecturer_names, ["A", "B", "C"])
        self.assertEqual(spec.lecturer_count, 3)
        self.assertEqual(spec.module_to_lecturers, [[0, 1, 2], [0, 1, 2], [0, 1, 2]])
        self.assertEqual(spec.breaks, True)
        self.assertEqual(spec.max_streak, 3)
        self.assertEqual(spec.spread_sessions, False)
        self.assertEqual(spec.spread_across_lecturers, True)
        self.assertEqual(spec.room_based_ordering, True)
    
    def testEncapsulation(self):
        '''
        Test that attributes are read-only from outside object
        '''
        spec = UserSpec("tests/Valid Input Document.xlsx")
        
        with self.assertRaises(AttributeError):
            spec.days = 4
            spec.periods = 5
            spec.rooms = 0
            spec.capacities = 0
            spec.module_names = 0
            spec.module_count = 0
            spec.session_counts = 0
            spec.courses = 0
            spec.course_to_modules = 0
            spec.course_student_counts = 0
            spec.lecturer_names = 0
            spec.lecturer_count = 0
            spec.module_to_lecturers = 0
            spec.breaks = 0
            spec.max_streak = 0
            spec.spread_sessions = 0
            spec.spread_across_lecturers = 0
            spec.room_based_ordering = 0
        