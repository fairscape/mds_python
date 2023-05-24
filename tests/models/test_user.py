import path
import unittest

from mds.models.compact import *
from mds.models import *
from mds.database.mongo import MongoConfig


class TestUser(unittest.TestCase):
    maxDiff = None
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
    mongo_client = MongoConfig(
            host_uri = "localhost",
            port = 27017,
            user = "root",
            password = "example"
            ).connect()


    def setUp(self):
        """
        Methods to Run before every test instance
        """

        # create test database

        test_db = self.mongo_client["test"]
        self.test_collection = test_db["testcol"]


    def test_1_model_initialization(self):

        # clear test collection of data
        self.test_collection.delete_many({})

        member = UserCompactView(
            id="ark:99999/testuser1",
            name="test user1",
            email="testuser1@example.org"
        )
        self.assertEqual(member.id, "ark:99999/testuser1")

        # ark prefix missing
        with self.assertRaises(ValueError):
            member = UserCompactView(
                id="99999/testuser1",
                name="test user1",
                email="testuser1@example.org"
            )

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
        

        
        owner_inst3 = UserCompactView(
            **{
                "id":"ark:99999/testowner2",
                "type": "guy",
                "name":"test owner2",
                "email":"testowner2@example.org"

            }
        )

        self.assertEqual(owner_inst3.id, "ark:99999/testowner2")

        # TODO: fix incorrect typing for classes
        self.assertEqual(owner_inst3.type, "guy")
        
        full_user = User(
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

        full_user_missing = User(
            id="ark:99999/testuser1",
            name="test user1",
            type="Person",
            email="testuser1@example.org",
            password="strongpw",
            is_admin=False,
        )

        self.assertDictEqual(full_user.dict(by_alias=True), full_user_missing.dict(by_alias=True))


    def test_2_mongo_create(self):
        test_user = User(**self.user_data)
        create_status = test_user.create(self.test_collection)

        #print(f"UserCreate: {write_success}\tMessage: {message}\tCode: {code}")
        self.assertTrue(create_status.success)
        self.assertEqual(create_status.message, "")
        self.assertEqual(create_status.status_code, 200)

        # try to create the same user and make sure it fails
        test_user = User(**self.user_data)
        duplicate_status = test_user.create(self.test_collection)

        self.assertFalse(duplicate_status.success)
        self.assertEqual(duplicate_status.message, "document already exists")
        self.assertEqual(duplicate_status.status_code, 400)


    def test_3_mongo_read(self):
        find_user = User.construct(id = self.user_data["@id"])
        test_user = User(**self.user_data)
        

        read_status = find_user.read(self.test_collection)

        self.assertTrue(read_status.success)
        self.assertEqual(read_status.message, "")
        self.assertEqual(read_status.status_code, 200)
        self.assertDictEqual(find_user.dict(by_alias=True), test_user.dict(by_alias=True))

        #print(f"UserRead\tSuccess: {result}\tMessage: {message}\tStatusCode: {code}")


    def test_4_mongo_read_not_found(self):
        # try to find a nonexistant user 
        fake_user_id = "ark:99999/notauser"
        nonexistant_user = User.construct(id=fake_user_id)

        not_found = nonexistant_user.read(self.test_collection)

        self.assertFalse(not_found.success)
        self.assertEqual(not_found.message, "No record found")
        self.assertEqual(not_found.status_code, 404)


    def test_5_mongo_delete(self):
        test_user = User.construct(id=self.user_data["@id"])

        delete_status = test_user.delete(self.test_collection)

        self.assertTrue(delete_status.success)
        self.assertEqual(delete_status.message, "")
        self.assertEqual(delete_status.status_code, 200)

  
    def tearDown(self) -> None:
        return super().tearDown()




if __name__ == "__main__":
    unittest.main()
