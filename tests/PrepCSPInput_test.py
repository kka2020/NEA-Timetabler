import unittest
from PrepCSPInput import ConstraintSystem
from UserSpec import UserSpec
from CSP import ConstraintGraph
import itertools

class testCustConsistCheck(unittest.TestCase):
    def setUp(self) -> None:
        spec = UserSpec("tests/CustConsist test.xlsx")
        self.constr_sys = ConstraintSystem(spec)
        self.period_constr_graph = ConstraintGraph(self.constr_sys.session_vars, self.constr_sys.session_domain, self.constr_sys.conflicts, custom_consist_check=self.constr_sys.lecAndRoomCustConsist)
    
    def test_getSessionVars(self):
        self.assertEqual(self.constr_sys.getSessionVars(), ["lab(0,0)", "lab(1,0)"])
    
    def test_searchRoomCombs(self):
        valid_rooms = {"LAB1", "LAB2", "LAB3"}
        num_taking = 40
        
        expected_output = {("LAB1", "LAB2"), ("LAB1", "LAB3"), ("LAB2", "LAB3")}
        expected_output = {frozenset(val) for val in expected_output.copy()}
        
        self.assertEqual(expected_output, set(frozenset(val) for val in self.constr_sys.searchRoomCombs(valid_rooms, num_taking)))
    
    def test_getRoomDomains(self):
        expected_output = {
            "lab(0,0)" : {("LAB1", "LAB2"), ("LAB1", "LAB3"), ("LAB2", "LAB3")},
            "lab(1,0)" : {("LAB1",), ("LAB2",), ("LAB3",)}
        }
        
        actual_output = {key : domain for (key, domain) in self.constr_sys.getRoomDomains()}
        actual_output["lab(0,0)"] = {tuple(sorted(val)) for val in actual_output["lab(0,0)"].copy()}
        
        self.assertEqual(expected_output, actual_output)
    
    def test_getLecturerDomains(self):
        assignment = {
            "lab(0,0)" : ("LAB1", "LAB2"),
            "lab(1,0)" : ("LAB1",)
        }
        
        expected_output = {
            "lab(0,0)" : {(0, 1)},
            "lab(1,0)" : {(0,)}
        }
        
        self.assertEqual(expected_output, self.constr_sys.getLecturerDomains(assignment))
        
    def test_lecAndRoomCustConsist(self):
        period_assignment = {
            "lab(0,0)" : 0,
            "lab(1,0)" : 0
        }

        self.assertFalse(self.constr_sys.lecAndRoomCustConsist(period_assignment))

        period_assignment = {
            "lab(0,0)" : 0,
            "lab(1,0)" : 1
        }

        self.assertTrue(self.constr_sys.lecAndRoomCustConsist(period_assignment))

        period_assignment = {
            "lab(0,0)" : 1,
            "lab(1,0)" : 1
        }

        self.assertFalse(self.constr_sys.lecAndRoomCustConsist(period_assignment))

        period_assignment = {
            "lab(0,0)" : 0,
            "lab(1,0)" : 0
        }

        self.assertFalse(self.period_constr_graph.consistent(period_assignment))
    
    def test_lecConsist(self):
        period_assignment = {
            "lab(0,0)" : 0,
            "lab(1,0)" : 0
        }

        room_assignment = {
            "lab(0,0)" : ("LAB1", "LAB2"),
            "lab(1,0)" : ("LAB2",)
        }

        self.assertFalse(self.constr_sys.lecConsist(period_assignment, room_assignment))

        room_constr_graph = ConstraintGraph(self.constr_sys.session_vars, self.constr_sys.room_domains, {key : [val] for (key, val) in period_assignment.items()}, custom_domain_vals=lambda room_assignment: self.constr_sys.lecConsist(period_assignment, room_assignment))
        self.assertFalse(room_constr_graph.consistent(room_assignment))

        period_assignment = {
            "lab(0,0)" : 0,
            "lab(1,0)" : 1
        }

        self.assertTrue(self.constr_sys.lecConsist(period_assignment, room_assignment))
