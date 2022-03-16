import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from typing_extensions import Self
import unittest
import mds


class TestUser(unittest.TestCase):
    def test_user_initialization(self):
        owner_inst1 = mds.utils.UserCompactView(
            id="ark:99999/testowner1",
            name="test owner1",
            type="Person",
            email="testowner1@example.org"
        )
        self.assertEqual(owner_inst1.id, "ark:99999/testowner1")

        owner_inst2 = mds.UserCompactView(
            id="ark:99999/testowner2",
            name="test owner2",
            type="Person",
            email="testowner2@example.org"
        )
        self.assertEqual(owner_inst2.id, "ark:99999/testowner2")
        
        
        full_user = mds.User(
            id="ark:99999/testuser1",
            name="test user1",
            type="Person",
            email="testuser1@example.org",
            password="strongpw",
            is_admin=False,
            datasets=[],
            software=[],
            computations=[],
            organizations=[],
            projects=[],
        )


class TestUserCRUD(unittest.TestCase):
    user_data = {
        "@id": "ark:99999/test-user",
        "name": "Test User",
        "type": "Person",
        "email": "test@example.org",
        "password": "test",
        "is_admin": False,
        "organizations": [],
        "datasets": [],
        "projects": [],
        "software": [],
        "computations": []
        }		


    def setUp(self):
        db_config = mds.MongoConfig(
            host_uri = "localhost",
            port = 27017,
            user = "root",
            password = "example",
            database = "test"
            )
        mongo_client = db_config.connect()
        test_db = mongo_client["test"]
        self.test_collection = test_db["test"]

        # create indexes



    def test_user_create(self):
        test_user = mds.User(**self.user_data)
        write_success, message, code = test_user.create(self.test_collection)
        self.assertTrue(write_success)


    def test_user_read(self):
        test_user = mds.User.construct(
            _fields_set={"id"}, 
            **{"@id": self.user_data["@id"]}
            )

        test_user.read(self.test_collection)


    def test_user_delete(self):
        pass


    def test_user_update(self):
        pass

    
    def tearDown(self) -> None:
        return super().tearDown()

if __name__ == "__main__":
    unittest.main()
