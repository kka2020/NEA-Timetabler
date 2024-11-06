import unittest
import itertools
from SoftConstraints import SoftConstraints 
from UserSpec import UserSpec
from copy import deepcopy

class TestSoftConstraint(unittest.TestCase):
    def setUp(self):
        #self.maxDiff = None
        self.spec = UserSpec("tests/SoftConstraint test input.xlsx")
        self.soft_constraints = SoftConstraints(self.spec)

    def testEnforceBreaks(self):
        assignment = {
            "lec(0,0)" : 0,
            "lec(1,0)" : 1,
            "lec(2,0)" : 2,
            "sem(0,0)" : None,
            "sem(1,0)" : None,
            "sem(2,0)" : None,
            "lab(0,0)" : None,
            "lab(1,0)" : None,
            "lab(2,0)" : None
        }
        
        self.assertEqual({(f"{session}({mod},0)", 3) for (session, mod) in itertools.product(["sem", "lab"], range(3))}, {constraint for constraint in self.soft_constraints.enforceBreaks(assignment)})

        assignment = {
            "lec(0,0)" : 0,
            "lec(1,0)" : 1,
            "lec(2,0)" : None,
            "sem(0,0)" : None,
            "sem(1,0)" : None,
            "sem(2,0)" : None,
            "lab(0,0)" : None,
            "lab(1,0)" : None,
            "lab(2,0)" : None
        }

        self.assertEqual([], [constraint for constraint in self.soft_constraints.enforceBreaks(assignment)])

        assignment = {
            "lec(0,0)" : 0,
            "lec(1,0)" : 1,
            "lec(2,0)" : 2,
            "sem(0,0)" : 5,
            "sem(1,0)" : 6,
            "sem(2,0)" : 7,
            "lab(0,0)" : None,
            "lab(1,0)" : None,
            "lab(2,0)" : None
        }
        
        self.assertEqual({(f"lab({mod},0)", 3) for mod in range(3)} | {(f"lab({mod},0)", 8) for mod in range(3)}, {constraint for constraint in self.soft_constraints.enforceBreaks(assignment)})
    
    def test_transpose(self):
        input_dict = {
            "A" : [0, 1],
            "B" : [1, 2],
            "C" : [0, 2]
        }
        
        expected_output = {
            0 : ["A", "C"],
            1 : ["A", "B"],
            2 : ["B", "C"]
        }
        
        self.assertEqual(self.soft_constraints.transpose(input_dict), expected_output)
    
    def test_getEqualVals(self):
        domain_list = [0, 1, 2, 10, 11, 12, 20, 21, 22]
        func = lambda period : period // 10
        
        expected_output = {dom_type : [[0, 1, 2], [10, 11, 12], [20, 21, 22]] for dom_type in ["hard", "soft"]}
        
        self.assertEqual(expected_output, self.soft_constraints.getEqualVals({"hard" : domain_list, "soft" : domain_list}, func))
    
    def test_enforcePeriodSpreading(self):
        assignment = {
            "lec(0,0)" : 0,
            "lec(1,0)" : 10,
            "lec(2,0)" : 11,
            "sem(0,0)" : 20,
            "sem(1,0)" : 21,
            "sem(2,0)" : 22,
            "lab(0,0)" : None,
            "lab(1,0)" : None,
            "lab(2,0)" : None
        }
        
        domain = set(range(self.spec.days * self.spec.periods)) - {0, 10, 11, 20, 21, 22}
        
        expected_ordered_domain = list(range(30, 50)) + list(range(1, 10)) + list(range(12, 20)) + list(range(23, 30))
        equal_vals = [list(range(30, 50)), list(range(1, 10)), list(range(12, 20)), list(range(23, 30))]
        expected_output = (expected_ordered_domain, expected_ordered_domain, equal_vals, equal_vals)
        self.assertEqual(expected_output, self.soft_constraints.enforcePeriodSpreading(assignment, domain, domain, "lec(0,0)"))
    
    def test_enforceLecturerSharing(self):
        assignment = {
            "lec(0,0)" : (0,),
            "lec(1,0)" : (0,),
            "lec(2,0)" : (2,),
            "sem(0,0)" : None,
            "sem(1,0)" : None,
            "sem(2,0)" : None,
            "lab(0,0)" : None,
            "lab(1,0)" : None,
            "lab(2,0)" : None
        }
        
        domain = {(0,), (1,)}
        
        expected_ordered_domain = [(1,), (0,)]
        equal_vals = [[(1,)], [(0,)]]
        expected_output = (expected_ordered_domain, expected_ordered_domain, equal_vals, equal_vals)
        
        self.assertEqual(expected_output, self.soft_constraints.enforceLecturerSharing(assignment, domain, domain, "lec(0,0)"))
    
    def test_roomBasedOrdering(self):
        assignment = {
            "lec(0,0)" : None,
            "lec(1,0)" : ("lec1",),
            "lec(2,0)" : None,
            "sem(0,0)" : None,
            "sem(1,0)" : None,
            "sem(2,0)" : None,
            "lab(0,0)" : None,
            "lab(1,0)" : None,
            "lab(2,0)" : None
        }
        
        domain = {("sem1", "lec1"), ("sem2", "lec1"), ("sem1", "lec2"), ("sem2", "lec2"), ("lec1",), ("lec2",)}
        
        expected_ordered_domain = [("lec1",), ("lec2",), ("sem1", "lec1"), ("sem2", "lec1"), ("sem1", "lec2"), ("sem2", "lec2")]
        expected_equal_vals = sorted([[("lec1",)], [("lec2",)], [("sem1", "lec1")], [("sem2", "lec1")], [("sem1", "lec2")], [("sem2", "lec2")]])
        
        actual_output = self.soft_constraints.roomBasedOrdering(assignment, domain, domain, "lec(0,0)")
        
        self.assertEqual(expected_ordered_domain, actual_output[0])
        self.assertEqual(expected_equal_vals, sorted(actual_output[2]))
    
    def test_enforceMinRoomsUsedLocal(self):
        assignment = {
            "lec(0,0)" : None,
            "lec(1,0)" : ("lec1",),
            "lec(2,0)" : None,
            "sem(0,0)" : None,
            "sem(1,0)" : None,
            "sem(2,0)" : None,
            "lab(0,0)" : None,
            "lab(1,0)" : None,
            "lab(2,0)" : None
        }
        
        domain = {("sem1", "lec1"), ("sem2", "lec1"), ("sem1", "lec2"), ("sem2", "lec2"), ("lec1",), ("lec2",)}
        
        #expected_ordered_domain = [("lec1",), ("lec2",), ("sem1", "lec1"), ("sem2", "lec1"), ("sem1", "lec2"), ("sem2", "lec2")]
        expected_equal_vals = [{("lec1",), ("lec2",)}, {("sem1", "lec1"), ("sem2", "lec1"), ("sem1", "lec2"), ("sem2", "lec2")}]
        
        actual_output = self.soft_constraints.enforceMinRoomsUsedLocal(domain)
        actual_ordered_domain = actual_output[0]
        actual_equal_vals = actual_output[1]
        
        self.assertIn(actual_ordered_domain[0], [("lec1",), ("lec2",)])
        self.assertIn(actual_ordered_domain[-1], [("sem1", "lec1"), ("sem2", "lec1"), ("sem1", "lec2"), ("sem2", "lec2")])
        self.assertEqual([set(vals) for vals in actual_equal_vals], expected_equal_vals)
    
    def test_enforceMinRoomsUsedGlobal(self):
        assignment = {
            "lec(0,0)" : None,
            "lec(1,0)" : ("lec1",),
            "lec(2,0)" : None,
            "sem(0,0)" : None,
            "sem(1,0)" : None,
            "sem(2,0)" : None,
            "lab(0,0)" : None,
            "lab(1,0)" : None,
            "lab(2,0)" : None
        }
        
        domain = {("lec1",), ("lec2",)}
        
        expected_ordered_domain = [("lec1",), ("lec2",)]
        expected_equal_vals = [[("lec1",)], [("lec2",)]]
        expected_equal_vals.sort()
        
        actual_output = self.soft_constraints.enforceMinRoomsUsedGlobal(domain, assignment)
        
        self.assertEqual(expected_ordered_domain, actual_output[0])
        self.assertEqual(expected_equal_vals, sorted(actual_output[1]))
    
    def test_enforceMinExcessCapacity(self):
        assignment = {
            "lec(0,0)" : None,
            "lec(1,0)" : ("lec1",),
            "lec(2,0)" : None,
            "sem(0,0)" : None,
            "sem(1,0)" : None,
            "sem(2,0)" : None,
            "lab(0,0)" : None,
            "lab(1,0)" : None,
            "lab(2,0)" : None
        }
        
        domain = {("sem1", "lec1"), ("sem2", "lec1"), ("sem1", "lec2"), ("sem2", "lec2"), ("lec1",), ("lec2",)}
        
        expected_ordered_domain = [("lec1",), ("lec2",), ("sem1", "lec1"), ("sem1", "lec2"), ("sem2", "lec1"), ("sem2", "lec2")]
        expected_equal_vals = sorted([{("lec1",), ("lec2",)}, {("sem1", "lec1"), ("sem1", "lec2")}, {("sem2", "lec1"), ("sem2", "lec2")}])
        
        actual_output = self.soft_constraints.enforceMinExcessCapacity(domain, "lec(0,0)")
        
        self.assertEqual(set(expected_ordered_domain[:2]), set(actual_output[0][:2]))
        self.assertEqual(set(expected_ordered_domain[2:4]), set(actual_output[0][2:4]))
        self.assertEqual(set(expected_ordered_domain[4:6]), set(actual_output[0][4:6]))
        
        self.assertEqual(expected_equal_vals, sorted([set(vals) for vals in actual_output[1]]))
        
        domain = {("sem1", "lec1"), ("sem2", "lec1")}
        
        expected_ordered_domain = [("sem1", "lec1"), ("sem2", "lec1")]
        expected_equal_vals = sorted([[("sem2", "lec1")], [("sem1", "lec1")]])
        
        actual_output = self.soft_constraints.enforceMinExcessCapacity(domain, "lec(0,0)")
        self.assertEqual((expected_ordered_domain, expected_equal_vals), (actual_output[0], sorted(actual_output[1])))
    
    def test_subOrder(self):
        assignment = {
            "lec(0,0)" : None,
            "lec(1,0)" : ("lec1",),
            "lec(2,0)" : None,
            "sem(0,0)" : None,
            "sem(1,0)" : None,
            "sem(2,0)" : None,
            "lab(0,0)" : None,
            "lab(1,0)" : None,
            "lab(2,0)" : None
        }
        
        ordered_domain = [("lec1",), ("lec2",), ("sem2", "lec1"), ("sem1", "lec1"), ("sem1", "lec2"), ("sem2", "lec2")]
        unordered_vals = {dom_type : [[("lec1",)], [("lec2",)], [("sem2", "lec1"), ("sem1", "lec1")], [("sem1", "lec2"), ("sem2", "lec2")]] for dom_type in ["hard", "soft"]}

        expected_output = ({dom_type : [("lec1",), ("lec2",), ("sem1", "lec1"), ("sem2", "lec1"), ("sem1", "lec2"), ("sem2", "lec2")] for dom_type in ["hard", "soft"]}, 
                           {dom_type : [[("lec1",)], [("lec2",)], [("sem1", "lec1")], [("sem2", "lec1")], [("sem1", "lec2")], [("sem2", "lec2")]] for dom_type in ["hard", "soft"]})

        self.assertEqual(expected_output, self.soft_constraints.subOrder({dom_type : deepcopy(ordered_domain) for dom_type in ["hard", "soft"]}, unordered_vals, self.soft_constraints.enforceMinExcessCapacity, "lec(0,0)"))
        
        