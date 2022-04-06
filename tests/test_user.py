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

    mongo_client = mds.MongoConfig(
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

        self.test_collection.delete_many({})


    def test_2_mongo_create(self):
        test_user = mds.User(**self.user_data)
        create_status = test_user.create(self.test_collection)

        #print(f"UserCreate: {write_success}\tMessage: {message}\tCode: {code}")
        self.assertTrue(create_status.success)
        self.assertEqual(create_status.message, "")
        self.assertEqual(create_status.status_code, 200)

        # try to create the same user and make sure it fails
        test_user = mds.User(**self.user_data)
        duplicate_status = test_user.create(self.test_collection)

        self.assertFalse(duplicate_status.success)
        self.assertEqual(duplicate_status.message, "document already exists")
        self.assertEqual(duplicate_status.status_code, 400)


    def test_3_mongo_read(self):
        find_user = mds.User.construct(id = self.user_data["@id"])
        test_user = mds.User(**self.user_data)
        

        read_status = find_user.read(self.test_collection)

        self.assertTrue(read_status.success)
        self.assertEqual(read_status.message, "")
        self.assertEqual(read_status.status_code, 200)
        self.assertDictEqual(find_user.dict(by_alias=True), test_user.dict(by_alias=True))

        #print(f"UserRead\tSuccess: {result}\tMessage: {message}\tStatusCode: {code}")


    def test_4_mongo_read_not_found(self):
        # try to find a nonexistant user 
        fake_user_id = "ark:99999/notauser"
        nonexistant_user = mds.User.construct(id=fake_user_id)

        not_found = nonexistant_user.read(self.test_collection)

        self.assertFalse(not_found.success)
        self.assertEqual(not_found.message, "no record found")
        self.assertEqual(not_found.status_code, 404)


    def test_5_mongo_delete(self):
        test_user = mds.User.construct(id=self.user_data["@id"])

        delete_status = test_user.delete(self.test_collection)

        self.assertTrue(delete_status.success)
        self.assertEqual(delete_status.message, "")
        self.assertEqual(delete_status.status_code, 200)


    def test_6a_user_project(self):
        
        test_user = mds.User(**self.user_data)

        create_status = test_user.create(self.test_collection)

        self.assertTrue(create_status.success)
        self.assertEqual(create_status.message, "")
        self.assertEqual(create_status.status_code, 200)

        # add a project to a user
        proj = mds.utils.ProjectCompactView(id="ark:99999/test_proj", name="Test Project")

        add = test_user.addProject(self.test_collection, proj)

        self.assertTrue(add.success)
        self.assertEqual(add.message, "")
        self.assertEqual(add.status_code, 200)

        # check that read updates the existance of the new project
        read_status = test_user.read(self.test_collection)

        self.assertTrue(read_status.success)
        self.assertEqual(read_status.message, "")
        self.assertEqual(read_status.status_code, 200)

        # assert that the new project is in the user model
        self.assertEqual(1, len(test_user.projects))

        # remove the project from the user

        remove_status = test_user.removeProject(self.test_collection, proj)

        self.assertTrue(remove_status.success)
        self.assertEqual(remove_status.message, "")
        self.assertEqual(remove_status.status_code, 200)

        #  check that the updated model has no projects 
        updated_user = mds.User.construct(id=test_user.id)

        read_status = updated_user.read(self.test_collection)

        self.assertTrue(read_status.success)
        self.assertEqual(read_status.message, "")
        self.assertEqual(read_status.status_code, 200)

        self.assertEqual(0, len(updated_user.projects))


    def test_6b_user_dataset(self):

        dataset = mds.utils.ProjectCompactView(id="ark:99999/test_data", name="Test Dataset")

        test_user = mds.User(**self.user_data)
        add = test_user.addDataset(self.test_collection, dataset)

        self.assertTrue(add.success)
        self.assertEqual(add.message, "")
        self.assertEqual(add.status_code, 200)

        # check that read updates the existance of the new project
        read_status = test_user.read(self.test_collection)

        self.assertTrue(read_status.success)
        self.assertEqual(read_status.message, "")
        self.assertEqual(read_status.status_code, 200)
        self.assertEqual(1, len(test_user.datasets))


        remove_status = test_user.removeDataset(self.test_collection, dataset)

        self.assertTrue(remove_status.success)
        self.assertEqual(remove_status.message, "")
        self.assertEqual(remove_status.status_code, 200)


        read_status = test_user.read(self.test_collection)

        self.assertTrue(read_status.success)
        self.assertEqual(read_status.message, "")
        self.assertEqual(read_status.status_code, 200)
        self.assertEqual(0, len(test_user.datasets))


    def test_6c_user_computation(self):
        computation = mds.utils.ComputationCompactView(id="ark:99999/test_comp", name="Test software")


        test_user = mds.User(**self.user_data)
        add = test_user.addComputation(self.test_collection, computation)

        self.assertTrue(add.success)
        self.assertEqual(add.message, "")
        self.assertEqual(add.status_code, 200)

        # check that read updates the existance of the new project
        read_status = test_user.read(self.test_collection)

        self.assertTrue(read_status.success)
        self.assertEqual(read_status.message, "")
        self.assertEqual(read_status.status_code, 200)
        self.assertEqual(1, len(test_user.computations))


        remove_status = test_user.removeComputation(self.test_collection, computation)

        self.assertTrue(remove_status.success)
        self.assertEqual(remove_status.message, "")
        self.assertEqual(remove_status.status_code, 200)


        read_status = test_user.read(self.test_collection)

        self.assertTrue(read_status.success)
        self.assertEqual(read_status.message, "")
        self.assertEqual(read_status.status_code, 200)
        self.assertEqual(0, len(test_user.computations))


    def test_6d_user_software(self):
        software = mds.utils.SoftwareCompactView(id="ark:99999/test_soft", name="Test Software")

        test_user = mds.User(**self.user_data)
        add = test_user.addSoftware(self.test_collection, software)

        self.assertTrue(add.success)
        self.assertEqual(add.message, "")
        self.assertEqual(add.status_code, 200)

        # check that read updates the existance of the new project
        read_status = test_user.read(self.test_collection)

        self.assertTrue(read_status.success)
        self.assertEqual(read_status.message, "")
        self.assertEqual(read_status.status_code, 200)
        self.assertEqual(1, len(test_user.software))


        remove_status = test_user.removeSoftware(self.test_collection, software)

        self.assertTrue(remove_status.success)
        self.assertEqual(remove_status.message, "")
        self.assertEqual(remove_status.status_code, 200)


        read_status = test_user.read(self.test_collection)

        self.assertTrue(read_status.success)
        self.assertEqual(read_status.message, "")
        self.assertEqual(read_status.status_code, 200)
        self.assertEqual(0, len(test_user.software))


    def test_6e_user_organization(self):
        org = mds.utils.OrganizationCompactView(id="ark:99999/test_org", name="Test Org")

        test_user = mds.User(**self.user_data)
        add = test_user.addOrganization(self.test_collection, org)

        self.assertTrue(add.success)
        self.assertEqual(add.message, "")
        self.assertEqual(add.status_code, 200)

        # check that read updates the existance of the new project
        read_status = test_user.read(self.test_collection)

        self.assertTrue(read_status.success)
        self.assertEqual(read_status.message, "")
        self.assertEqual(read_status.status_code, 200)
        self.assertEqual(1, len(test_user.organizations))


        remove_status = test_user.removeOrganization(self.test_collection, org)

        self.assertTrue(remove_status.success)
        self.assertEqual(remove_status.message, "")
        self.assertEqual(remove_status.status_code, 200)


        read_status = test_user.read(self.test_collection)

        self.assertTrue(read_status.success)
        self.assertEqual(read_status.message, "")
        self.assertEqual(read_status.status_code, 200)
        self.assertEqual(0, len(test_user.organizations))

  
    def tearDown(self) -> None:
        return super().tearDown()




if __name__ == "__main__":
    unittest.main()
