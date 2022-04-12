import unittest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import mds


class TestGroup(unittest.TestCase):

    def test_0_group_initilization(self):
        owner = mds.utils.UserCompactView(
            id="ark:99999/testowner",
            name="test owner",
            email="testowner@example.org"
        )

        member = mds.utils.UserCompactView(
            id="ark:99999/testuser1",
            name="test user1",
            email="testuser1@example.org"
        )

        grp = mds.Group(
            id="ark:99999/CAMA-users",
            name="Cama Users",
            owner=owner,
            members=[member]
        )

    
    def test_1_group_json(self):
        pass

    def test_2_group_create(self):
        pass

    def test_3_group_delete(self):
        pass
    
    def test_4_group_user(self):
        pass



if __name__ == "__main__":
    unittest.main()
