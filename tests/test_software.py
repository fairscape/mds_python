import unittest

import mds


# import os, sys
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestSoftware(unittest.TestCase):
    def test_software_initialization(self):
        owner_inst1 = mds.utils.UserCompactView(
            id="ark:99999/testowner1",
            name="test owner1",
            type="Person",
            email="testowner1@example.org"
        )
        self.assertEqual(owner_inst1.id, "ark:99999/testowner1")
        mds.Software(
            id="ark:99999/CAMA-users",
            name="john doe",
            type="evi:Software",
            owner=owner_inst1,
            author="author1",
            downloadUrl="ark:99999/downloaddir/thisfile",
            citation="doi://blabla",
            usedBy=[]
        )


if __name__ == "__main__":
    unittest.main()
