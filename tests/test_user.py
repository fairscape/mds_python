import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from typing_extensions import Self
import unittest
import mds


class TestUser(unittest.TestCase):
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




    def test_user_crud(self):
        test_user = mds.User(**self.user_data)
        write_success, message, code = test_user.create(self.test_collection)

        #print(f"UserCreate: {write_success}\tMessage: {message}\tCode: {code}")
        self.assertTrue(write_success)
        self.assertEqual(message, "")
        self.assertEqual(code, 200)

        # try to create the same user and make sure it fails
        test_user = mds.User(**self.user_data)
        write_success, message, code = test_user.create(self.test_collection)

        self.assertFalse(write_success)
        self.assertEqual(message, "document already exists")
        self.assertEqual(code, 400)



    #def test_user_read(self):
        find_user = mds.User.construct(id = self.user_data["@id"])
        test_user = mds.User(**self.user_data)
        

        result, message, code = find_user.read(self.test_collection)

        self.assertTrue(result)
        self.assertEqual(message, "")
        self.assertEqual(code, 200)
        self.assertDictEqual(find_user.dict(by_alias=True), test_user.dict(by_alias=True))

        #print(f"UserRead\tSuccess: {result}\tMessage: {message}\tStatusCode: {code}")


    


    #def test_user_read_not_found(self):
        # try to find a nonexistant user 
        fake_user_id = "ark:99999/notauser"
        nonexistant_user = mds.User.construct(id=fake_user_id)

        result, message , code = nonexistant_user.read(self.test_collection)

        self.assertFalse(result)
        self.assertEqual(message, "no record found")
        self.assertEqual(code, 404)


    #def test_user_delete(self):
        test_user = mds.User.construct(id=self.user_data["@id"])

        result, message, code = test_user.delete(self.test_collection)

        self.assertTrue(result)
        self.assertEqual(message, "")
        self.assertEqual(code, 200)


    #def test_user_update(self):
        pass

    
    def tearDown(self) -> None:

        self.test_collection.drop() 
        return super().tearDown()

    

if __name__ == "__main__":
    unittest.main()
