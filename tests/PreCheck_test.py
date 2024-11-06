import unittest
from PreCheck import *
from UserSpec import UserSpec

class testPreProcessChecks(unittest.TestCase):
    def setUp(self):
        self.valid_spec = UserSpec("tests/Valid input document.xlsx")
        self.invalid_lecturers_spec = UserSpec("tests/PreProcess Invalid lecturers doc.xlsx")
        self.invalid_rooms_spec = UserSpec("tests/PreProcess Invalid rooms doc.xlsx")
        self.invalid_periods_spec = UserSpec("tests/PreProcess Invalid periods doc.xlsx")
    
    def test_checkFeasibility(self):
        with self.assertRaises(SystemExit) as e:
            checkFeasibility(self.invalid_periods_spec)
            
        self.assertEqual(str(e.exception), "ERROR: There aren't enough periods in a week to run all the sessions for course MECH")
            
        with self.assertRaises(SystemExit) as e:
            checkFeasibility(self.invalid_rooms_spec)
        
        self.assertEqual(str(e.exception), "ERROR: number of people taking module ALG exceeds the space capacity for sessions of type sem")
        
        with self.assertRaises(SystemExit) as e:
            checkFeasibility(self.invalid_lecturers_spec)
        
        self.assertEqual(str(e.exception), "ERROR: number of lec rooms required for a session for module ALG exceeds the number of lecturers available to teach this module")
        
        checkFeasibility(self.valid_spec)