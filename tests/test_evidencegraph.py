import unittest

import mds


# import os, sys
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestEvidenceGraph(unittest.TestCase):
    def test_evidencegraph_initialization(self):
        owner_inst1 = mds.utils.UserCompactView(
            id="ark:99999/testowner1",
            name="test owner1",
            type="Person",
            email="testowner1@example.org"
        )
        self.assertEqual(owner_inst1.id, "ark:99999/testowner1")
        eg = mds.EvidenceGraph(
            id="ark:99999/CAMA-users",
            name="a demo evidencegraph",
            type="evi:EvidenceGraph",
            owner=owner_inst1,
            graph=""
        )


if __name__ == "__main__":
    unittest.main()
