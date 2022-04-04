import unittest
from datetime import datetime

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

        test_data = {
            "@id": "ark:99999/valid_user",
            "@type": "evi:Software",
            "name": "Test Software"
        }

        software_cv = mds.utils.SoftwareCompactView(
            id=test_data["@id"],
            type=test_data["@type"],
            name=test_data["name"]
        )

        mds.Computation(
            id="ark:99999/CAMA-users",
            name="john doe",
            type="evi:Computation",
            owner=owner_inst1,
            author="author1",
            dateCreated=datetime(2022, 2, 15, 9, 26, 3),
            dateFinished=datetime(2022, 2, 15, 9, 30, 3),
            associatedWith=[],
            usedSoftware=[software_cv],
            usedDataset=[]
        )


if __name__ == "__main__":
    unittest.main()
