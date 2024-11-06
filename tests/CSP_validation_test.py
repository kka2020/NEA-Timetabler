import unittest
import CSP_validation as Validator
from UserSpec import UserSpec

class TestFormatting(unittest.TestCase):
    def setUp(self):
        self.solution1 = [
            {
                "lec(0,0)" : 0,
                "sem(0,0)" : 1,
                "lab(0,0)" : 1,
                "lec(1,0)" : 3,
                "sem(1,0)" : 4
            },
            {
                "lec(0,0)" : ("LEC1",),
                "sem(0,0)" : ("SEM1", "SEM2"),
                "lab(0,0)" : ("LAB1", "LAB2"),
                "lec(1,0)" : ("LEC1",),
                "sem(1,0)" : ("SEM1", "SEM2")
            },
            {
                "lec(0,0)" : (0,),
                "sem(0,0)" : (0, 1),
                "lab(0,0)" : (0, 1),
                "lec(1,0)" : (2,),
                "sem(1,0)" : (2, 3)
            }
        ]
        
        self.spec = UserSpec("tests/Valid input document.xlsx")

    def test_formatTimetable(self):
        expected_output = {
            0 : [["lec(0,0)", ("LEC1",), (0,)]],
            1 : [["sem(0,0)", ("SEM1", "SEM2"), (0, 1)], ["lab(0,0)", ("LAB1", "LAB2"), (0, 1)]],
            3 : [["lec(1,0)", ("LEC1",), (2,)]],
            4 : [["sem(1,0)", ("SEM1", "SEM2"), (2, 3)]]
        }
        
        self.assertEqual(expected_output, Validator.formatTimetable(self.solution1))
    
    def test_getCourseToRoom(self):
        solution = [
            {
                "lec(0,0)" : 0,
                "lec(1,0)" : 1,
                "lec(2,0)" : 2
            },
            {
                "lec(0,0)" : ("sem1", "sem2", "sem3"),
                "lec(1,0)" : ("lec1",),
                "lec(2,0)" : ("lec1",),
            },
            {
                "lec(0,0)" : (0,),
                "lec(1,0)" : (1,),
                "lec(2,0)" : (0,)
            }
        ]
        
        expected_output = {
            "lec(0,0)" : {
                "MECH" : {"sem1" : 30},
                "ELEC" : {"sem2" : 30},
                "BIO" : {"sem3" : 30}
            },
            
            "lec(1,0)" : {
                "MECH" : {"lec1" : 30},
            },
            
            "lec(2,0)" : {
                "ELEC" : {"lec1" : 30},
                "BIO" : {"lec1" : 30}
            }
        }
        
        expected_output = {sess : {course : expected_output[sess][course] for course in expected_output[sess]} for sess in sorted(list(expected_output.keys()))}
        
        actual_output = Validator.getCourseToRoom(Validator.formatTimetable(solution), self.spec)
        actual_output = {sess : {course : actual_output[sess][course] for course in actual_output[sess]} for sess in sorted(list(actual_output.keys()))}
        
        self.assertEqual(actual_output, expected_output)
    
class TestValidation(unittest.TestCase):
    def test_validate(self):
        spec = UserSpec("tests/Valid input document.xlsx")
        
        solution = [
            {
                "lec(0,0)" : 0,
                "sem(0,0)" : 1,
                "lab(0,0)" : 1,
                "lec(1,0)" : 3,
                "sem(1,0)" : 4
            },
            {
                "lec(0,0)" : ("lec1",),
                "sem(0,0)" : ("sem1", "sem2"),
                "lab(0,0)" : ("lab1", "lab2"),
                "lec(1,0)" : ("lec1",),
                "sem(1,0)" : ("sem1", "sem2")
            },
            {
                "lec(0,0)" : (0,),
                "sem(0,0)" : (0, 1),
                "lab(0,0)" : (0, 1),
                "lec(1,0)" : (2,),
                "sem(1,0)" : (2, 3)
            }
        ]

        self.assertFalse(Validator.validate(solution, spec))
        
        solution = [
            {
                "lec(0,0)" : 0,
                "lec(1,0)" : 0,
                "lec(2,0)" : 2
            },
            {
                "lec(0,0)" : ("lec1",),
                "lec(1,0)" : ("lec1",),
                "lec(2,0)" : ("lec1",),
            },
            {
                "lec(0,0)" : (0,),
                "lec(1,0)" : (1,),
                "lec(2,0)" : (0,)
            }
        ]
        
        self.assertFalse(Validator.validate(solution, spec))
        
        solution = [
            {
                "lec(0,0)" : None,
                "lec(1,0)" : 0,
                "lec(2,0)" : 2
            },
            {
                "lec(0,0)" : ("lec1",),
                "lec(1,0)" : ("lec1",),
                "lec(2,0)" : ("lec1",),
            },
            {
                "lec(0,0)" : (0,),
                "lec(1,0)" : (1,),
                "lec(2,0)" : (0,)
            }
        ]
        
        self.assertFalse(Validator.validate(solution, spec))
        
        solution = [
            {
                "lec(0,0)" : 0,
                "sem(0,0)" : 1,
                "lab(0,0)" : 1,
                "lec(1,0)" : 3,
                "sem(1,0)" : 4
            },
            {
                "lec(0,0)" : ("lec1",),
                "sem(0,0)" : ("sem1", "sem2"),
                "lab(0,0)" : ("lab1", "lab2"),
                "lec(1,0)" : ("lec1",),
                "sem(1,0)" : ("sem1", "sem2")
            },
            {
                "lec(0,0)" : (0,),
                "sem(0,0)" : (0,),
                "lab(0,0)" : (0, 1),
                "lec(1,0)" : (2,),
                "sem(1,0)" : (2, 3)
            }
        ]

        self.assertFalse(Validator.validate(solution, spec))
        
        solution = [
            {
                "lec(0,0)" : 0,
                "sem(0,0)" : 1,
                "lab(0,0)" : 1,
                "lec(1,0)" : 3,
                "sem(1,0)" : 4
            },
            {
                "lec(0,0)" : ("lec1",),
                "sem(0,0)" : ("sem1"),
                "lab(0,0)" : ("lab1", "lab2"),
                "lec(1,0)" : ("lec1",),
                "sem(1,0)" : ("sem1", "sem2")
            },
            {
                "lec(0,0)" : (0,),
                "sem(0,0)" : (0),
                "lab(0,0)" : (0, 1),
                "lec(1,0)" : (2,),
                "sem(1,0)" : (2, 3)
            }
        ]

        self.assertFalse(Validator.validate(solution, spec))
        
        solution = [
            {
                "lec(0,0)" : 0,
                "lec(1,0)" : 1,
                "lec(2,0)" : 2
            },
            {
                "lec(0,0)" : ("lab1",),
                "lec(1,0)" : ("lec1",),
                "lec(2,0)" : ("lec1",),
            },
            {
                "lec(0,0)" : (0,),
                "lec(1,0)" : (1,),
                "lec(2,0)" : (0,)
            }
        ]
        
        self.assertFalse(Validator.validate(solution, spec))
        
        solution = [
            {
                "lec(0,0)" : 0,
                "lec(1,0)" : 1,
                "lec(2,0)" : 2
            },
            {
                "lec(0,0)" : ("lec1",),
                "lec(1,0)" : ("lec1",),
                "lec(2,0)" : ("lec1",),
            },
            {
                "lec(0,0)" : (0,),
                "lec(1,0)" : (1,),
                "lec(2,0)" : (0,)
            }
        ]
        
        self.assertTrue(Validator.validate(solution, spec))

        