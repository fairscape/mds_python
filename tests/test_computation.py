import unittest
import mds


# import os, sys
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestComputation(unittest.TestCase):
    def test_computation_initialization(self):
        owner_inst1 = mds.utils.UserCompactView(
            id="ark:99999/testowner1",
            name="test owner1",
            type="Person",
            email="testowner1@example.org"
        )
        self.assertEqual(owner_inst1.id, "ark:99999/testowner1")

        owner_inst2 = mds.utils.UserCompactView(
            id="ark:99999/testowner2",
            name="test owner2",
            type="Person",
            email="testowner2@example.org"
        )
        self.assertEqual(owner_inst2.id, "ark:99999/testowner2")

        software_inst1 = mds.Software(
            id="ark:99999/CAMA-users",
            name="john doe",
            type="evi:Software",
            owner=owner_inst1,
            author="author1",
            downloadUrl="ark:99999/downloaddir/thisfile",
            citation="doi://blabla",
            usedBy=[]
        )
        comp = mds.Computation(
            id="ark:99999/CAMA-users",
            name="john doe",
            type="evi:Computation",
            owner=owner_inst2,
            author="author1",
            dateCreated="2022-02-15 09:26:03",
            dateFinished="2022-02-15 09:30:03",
            associatedWith=[],
            usedSoftware=[software_inst1],
            usedDataset=[]
        )


if __name__ == "__main__":
    unittest.main()
