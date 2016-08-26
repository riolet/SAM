import dbaccess
import unittest

class dbaccessTest(unittest.TestCase):
    def determineRange_test(self):
        self.assertEqual(dbaccess.determineRange(), (0x00000000, 0xffffffff, 0x1000000), "dbaccess.determineRange() failed")
        self.assertEqual(dbaccess.determineRange(12), (0xc000000, 0xcffffff, 0x10000), "dbaccess.determineRange(12) failed")
        self.assertEqual(dbaccess.determineRange(12, 8), (0xc080000, 0xc08ffff, 0x100), "dbaccess.determineRange(12, 8) failed")
        self.assertEqual(dbaccess.determineRange(12, 8, 192), (0xc08c000, 0xc08c0ff, 0x1), "dbaccess.determineRange(12, 8, 192) failed")
        self.assertEqual(dbaccess.determineRange(12, 8, 192, 127), (0xc08c07f, 0xc08c07f, 0x1), "dbaccess.determineRange(12, 8, 192, 127) failed")

    def getNodes_test(self):
        self.assertEqual(len(dbaccess.getNodes()), 8, "dbaccess.getNodes() failed")
        self.assertEqual(len(dbaccess.getNodes(21)), 1, "dbaccess.getNodes(21) failed")
        self.assertEqual(len(dbaccess.getNodes(21, 66)), 80, "dbaccess.getNodes(21, 66) failed")
        self.assertEqual(len(dbaccess.getNodes(21, 66, 1)), 5, "dbaccess.getNodes(21, 66, 1) failed")
        self.assertEqual(len(dbaccess.getNodes(52)), 0, "dbaccess.getNodes(52) failed")
