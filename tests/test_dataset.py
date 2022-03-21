import unittest

import mds


# import os, sys
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestDataset(unittest.TestCase):
    def test_dataset_initialization(self):
        owner_inst1 = mds.utils.UserCompactView(
            id="ark:99999/testowner1",
            name="test owner1",
            type="Person",
            email="testowner1@example.org"
        )
        self.assertEqual(owner_inst1.id, "ark:99999/testowner1")

        user = mds.utils.UserCompactView(
            id="ark:99999/testuser1",
            name="test user1",
            type="Person",
            email="testuser1@example.org"
        )

        mds.Dataset(
            id="ark:99999/CAMA-users",
            name="A demo dataset",
            type="evi:Dataset",
            owner=owner_inst1,
            #includedInDataCatalog=,
            #sourceOrganization=,
            distribution="csv",
            author=user,
            dateCreated="2022-02-15 09:26:03",
            dateModified="2022-02-15 09:30:03"
        )


if __name__ == "__main__":
    unittest.main()
