import unittest
import CSP
from SoftConstraints import *

class TestConstraintGraph(unittest.TestCase):
    def setUp(self) -> None:
        self.csp = CSP.ConstraintGraph(
            ["a", "b", "c", "d"],
            set(range(3)),
            {
               "a" : [2, 4, 8],
               "b" : [3, 4, 6],
               "c" : [2, 3, 5],
               "d" : [1, 8, 3]
            },
            hard_unary_constraints=[("a", 0)],
            soft_unary_constraints=lambda x: [("b", 1)] if x["a"] == 4 else [("c", 2)]
        )

    def test_init(self):
        csp = CSP.ConstraintGraph(["a", "b"], set(range(3)), {"a" : [1, 2, 3], "b" : [3, 4, 5]}, hard_unary_constraints=[("a", 0)], soft_unary_constraints= lambda x: [("b", 1)], solution={"a" : 5})
        self.assertEqual(csp._ConstraintGraph__hard_unary_constraints, [("a", 0)])
        self.assertEqual(csp._ConstraintGraph__soft_unary_constraints(None), [("b", 1)])
        self.assertEqual(set(csp._ConstraintGraph__conflicts), {("a", "b"), ("b", "a")})
        self.assertEqual(csp._ConstraintGraph__hard_domains, {"a" : {0, 1, 2}, "b" : {0, 1, 2}})
        self.assertEqual(csp._ConstraintGraph__soft_domains, {"a" : {0, 1, 2}, "b" : {0, 1, 2}})
        self.assertEqual(csp._ConstraintGraph__solution, {"a" : 5})
    
    def test_makeNodeConsistentHard(self):
        self.csp.makeNodeConsistent()
        self.assertEqual(self.csp._ConstraintGraph__hard_domains["a"], {1, 2})
    
    def test_makeNodeConsistentSoft(self):
        self.csp.makeNodeConsistent({"a" : 4}, hard=False)
        self.assertEqual(self.csp._ConstraintGraph__soft_domains["b"], {0, 2})
        self.csp.makeNodeConsistent({"a" : 3}, hard=False)
        self.assertEqual(self.csp._ConstraintGraph__soft_domains["c"], {0, 1})
    
    def test_getConflicts(self):
        self.assertEqual(set(self.csp._ConstraintGraph__conflicts), {("a", "c"), ("c", "a"), ("a", "b"), ("b", "a"), ("a", "d"), ("d", "a"), ("b", "c"), ("c", "b"), ("b", "d"), ("d", "b"), ("c", "d"), ("d", "c")})
    
    def test_revise(self):
        csp = CSP.ConstraintGraph(["a", "b"], set(range(3)), {"a" : [1, 2, 3], "b" : [3, 4, 5]}, [("a", 0)])
        csp._ConstraintGraph__hard_domains["a"] = {0}
        csp._ConstraintGraph__soft_domains["a"] = {0}
        csp.revise("b", "a")
        self.assertEqual(csp._ConstraintGraph__hard_domains["b"], {1, 2})
        csp.revise("b", "a", False)
        self.assertEqual(csp._ConstraintGraph__soft_domains["b"], {1, 2})
    
    def test_AC3(self):
        csp = CSP.ConstraintGraph(["a", "b", "c"], set(range(3)), {"a" : [1, 2, 3], "b" : [3, 4, 5], "c" : [1, 4, 7]}, [("a", 0)])
        csp._ConstraintGraph__hard_domains.update({"a" : {0}, "b" : {0, 1}})
        csp.AC3()
        self.assertEqual(csp._ConstraintGraph__hard_domains, {"a" : {0}, "b" : {1}, "c" : {2}})
        self.assertEqual(csp._ConstraintGraph__soft_domains, {key : set(range(3)) for key in "abc"})
        csp._ConstraintGraph__soft_domains.update({"a" : {0}, "b" : {0, 1}})
        csp.AC3(hard=False)
        self.assertEqual(csp._ConstraintGraph__hard_domains, {"a" : {0}, "b" : {1}, "c" : {2}})
        self.assertEqual(csp._ConstraintGraph__soft_domains, {"a" : {0}, "b" : {1}, "c" : {2}})
        
    def test_neighbours(self):
        csp = CSP.ConstraintGraph(["a", "b", "c"], set(range(3)), {"a" : [1, 2, 3], "b" : [3, 4, 5], "c" : [1, 4, 7]}, [("a", 0)])
        self.assertEqual(csp.neighbours("c"), {"a", "b"})

    def test_inferences(self):
        csp = CSP.ConstraintGraph(["a", "b"], set(range(3)), {"a" : [1, 2, 3], "b" : [3, 4, 5]}, [("a", 0)])
        assignment = {"a" : 0, "b" : None}
        csp._ConstraintGraph__hard_domains["b"] = {0, 1}
        self.assertEqual(csp.inference(assignment, "a", True), {"b" : 1})
    
    def test_complete(self):
        self.assertFalse(self.csp.complete({"a" : 0, "b" : None}))
        self.assertTrue(self.csp.complete({"a" : 0, "b" : 1}))
    
    def test_consistent(self):
        csp = CSP.ConstraintGraph(["a", "b"], set(range(3)), {"a" : [1, 2, 3], "b" : [3, 4, 5]}, [("a", 0)])
        self.assertTrue(csp.consistent({"a" : 0, "b" : 1}))
        self.assertFalse(csp.consistent({"a" : 1, "b" : 1}))
    
    def test_domainVals(self):
        self.csp._ConstraintGraph__hard_domains["a"] = {0, 2}
        #self.csp._ConstraintGraph__soft_domains["a"] = {0, 2}
        self.assertEqual(self.csp.domainVals("c", {key : None for key in "abcd"}), [(0, True), (1, True), (2, True), (1, False), (0, False), (2, False)])
        self.assertEqual(self.csp.domainVals("d", {key : None for key in "abcd"}), [(0, True), (1, True), (2, True), (1, False), (0, False), (2, False)])
        self.assertEqual(self.csp.domainVals("b", {key : None for key in "abcd"}), [(0, True), (1, True), (2, True), (1, False), (0, False), (2, False)])
        self.assertEqual(self.csp.domainVals("a", {key : None for key in "abcd"}), [(0, True), (1, True), (2, True), (0, False), (2, False)])
        self.assertEqual(self.csp.domainVals("c", {"a" : 0, "b" : None, "c" : None, "d" : None}), [(0, True), (1, True), (2, True), (0, False), (1, False), (2, False)])
    
    def test_selectUnassignedVar(self):
        csp = CSP.ConstraintGraph(["a", "b", "c"], set(range(3)), {"a" : [1, 2, 3], "b" : [3, 4, 5], "c" : [1, 4, 7]}, [("a", 0)])
        self.assertEqual(csp.selectUnassignedVar({"a" : 0, "b" : None, "c" : None}, True), "b")
        self.assertEqual(csp.selectUnassignedVar({"a" : None, "b" : 0, "c" : None}, True), "a")
        
        csp._ConstraintGraph__hard_domains["c"] = {0, 1}
        self.assertEqual(csp.selectUnassignedVar({"a" : None, "b" : None, "c" : None}, True), "c")


if __name__ == "__main__":
    unittest.main()
    
    