import unittest
import StructTools

class TestIterTools(unittest.TestCase):
    def testCombinations(self):        
        self.assertRaises(TypeError, lambda: [comb for comb in StructTools.combinations("ABC", "Should raise TypeError")])
        self.assertEqual([(0, 1, 2), (0, 1, 3), (0, 2, 3), (1, 2, 3)], [comb for comb in StructTools.combinations(range(4), 3)])
        self.assertEqual([('A', 'B'), ('A', 'C'), ('A', 'D'), ('B', 'C'), ('B', 'D'), ('C', 'D')], [comb for comb in StructTools.combinations('ABCD', 2)])
    
    def testChain(self):
        self.assertEqual([0, 1, 2, 'A', 'B', 'C', True, False], [elem for elem in StructTools.chain(range(3), "ABC", [True, False])])
    
class TestDataStructTools(unittest.TestCase):
    def testQuickSort(self):
        self.assertEqual(list(range(10)), StructTools.quickSort([1, 3, 4, 2, 7, 8, 5, 9, 6, 0]))
        self.assertEqual([1, 1, 1, 1], StructTools.quickSort([1, 1, 1, 1]))
        self.assertEqual(list(range(10)) + [9], StructTools.quickSort([1, 3, 4, 2, 7, 8, 5, 9, 6, 0, 9]))
        self.assertEqual(list(map(str, range(10))), StructTools.quickSort(['0', '2', '3', '1', '5', '4', '9', '7', '6', '8'], int))
    
    def testDeepCopy(self):
        self.assertEqual([[0, 1, 2], [3, 4, 5], [6, 7, [8]]], StructTools.deepCopy([[0, 1, 2], [3, 4, 5], [6, 7, [8]]]))
        self.assertEqual({'A' : [0, 1, 2], 'B' : [2, 3, 4], 'C' : [5, 6, 7]}, StructTools.deepCopy({'A' : [0, 1, 2], 'B' : [2, 3, 4], 'C' : [5, 6, 7]}))
        self.assertEqual({'A' : {(0), (1, 2)}, 'B' : {(3), (4, 5)}, 'C' : {(6), (7, 8)}}, StructTools.deepCopy({'A' : {(0), (1, 2)}, 'B' : {(3), (4, 5)}, 'C' : {(6), (7, 8)}}))