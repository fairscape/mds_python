import unittest

import mds


# import os, sys
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestDataset(unittest.TestCase):
    def test_organization_initialization(self):
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

        test_data = {
            "@id": "ark:99999/valid_project",
            "@type": "Project",
            "name": "Test Project"
        }

        project_cv = mds.utils.ProjectCompactView(
            id=test_data["@id"],
            type=test_data["@type"],
            name=test_data["name"]
        )

        mds.Organization(
            id="ark:99999/UVA",
            name="An organization",
            type="Organization",
            owner=owner_inst1,
            projects=[project_cv]
        )


if __name__ == "__main__":
    unittest.main()
