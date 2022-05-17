import unittest
import path
from mds.models import *
from mds import MongoConfig


class TestComputation(unittest.TestCase):
    def test_computation_initialization(self):
        owner_inst1 = UserCompactView(
            id="ark:99999/testowner1",
            name="test owner1",
            email="testowner1@example.org"
        )
        self.assertEqual(owner_inst1.id, "ark:99999/testowner1")

        owner_inst2 = UserCompactView(
            id="ark:99999/testowner2",
            name="test owner2",
            email="testowner2@example.org"
        )
        self.assertEqual(owner_inst2.id, "ark:99999/testowner2")

        software_inst1 = Software(
            id="ark:99999/CAMA-users",
            name="john doe",
            owner=owner_inst1,
            author="author1",
            downloadUrl="ark:99999/downloaddir/thisfile",
            citation="doi://blabla"
        )
        Computation(
            id="ark:99999/CAMA-users",
            name="john doe",
            owner=owner_inst2,
            author="author1",
            dateCreated="2022-02-15",
            dateFinished="2022-02-15",
            usedSoftware=[software_inst1]
        )


if __name__ == "__main__":
    unittest.main()
