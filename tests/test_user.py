import unittest
import mds


class TestUser(unittest.TestCase):
    def test_user_initialization(self):
        owner_inst1 = mds.UserView(
            id="ark:99999/testowner1",
            name="test owner1",
            email="testowner1@example.org"
        )
        self.assertEqual(owner_inst1.id, "ark:99999/testowner1")

        owner_inst2 = mds.UserView(
            id="ark:99999/testowner2",
            name="test owner2",
            email="testowner2@example.org"
        )
        self.assertEqual(owner_inst2.id, "ark:99999/testowner2")
        software_inst1 = mds.Software(
            id="ark:99999/CAMA-users",
            name="john doe",
            owner=owner_inst1,
            author="author1",
            downloadUrl="ark:99999/downloaddir/thisfile",
            citation="doi://blabla"
        )
        computation_inst1 = mds.Computation(
            id="ark:99999/CAMA-users",
            name="john doe",
            owner=owner_inst2,
            author="author1",
            dateCreated="2022-02-15",
            dateFinished="2022-02-15",
            usedSoftware=[software_inst1]
        )
        mds.User(
            id="ark:99999/testuser1",
            name="test user1",
            email="testuser1@example.org",
            password="strongpw",
            is_admin=False,
            software=[software_inst1],
            computations=[computation_inst1]
        )


if __name__ == "__main__":
    unittest.main()
