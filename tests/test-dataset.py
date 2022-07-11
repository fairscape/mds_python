import path
import unittest
from mds.models import *
from mds.database.mongo import MongoConfig


class TestDataset(unittest.TestCase):
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

    group_data = {
            "@id": "ark:99999/test-group",
            "@type": "Organization",
            "name": "test group",
            "owner": {
                    "@id": "ark:99999/test-user",
                    "@type": "Person",
                    "name": "Test User1",
                    "email": "testuser1@example.org"
                    },
            "members": [{"@id": "ark:99999/test-user2",
            "name": "Test User2",
            "type": "Person",
            "email": "testuser2@example.org"}],
    }

    dataset_data = {
        "@id": "ark:99999/test-dataset",
        "@type": "evi:Dataset",
        "name": "test dataset",
        "owner": {
            "@id": "ark:99999/test-user",
            "@type": "Person",
            "name": "Test User1",
            "email": "testuser1@example.org"
            }
    }

    mongo_client = MongoConfig(
            host_uri = "localhost",
            port = 27017,
            user = "root",
            password = "example"
            ).connect()

    def test_0_setup(self):
        test_db = self.mongo_client["test"]
        test_collection = test_db["testcol"]
        test_collection.delete_many({})

        # create owner user
        test_user = User(**self.user_data)
        create_user = test_user.create(test_collection)
        self.assertTrue(create_user.success)

        # create organization
        #test_organization = Organization(**self.organization_data)
        #create_org = test_organization.create(test_collection)
        #self.assertTrue(create_org.success)

        # create project
        #test_proj= Project(**self.proj_data)
        #create_proj = test_proj.create(test_collection)
        #self.assertTrue(create_proj.success)


    def test_1_dataset_create(self): 
        test_dataset = Dataset(**self.dataset_data)
        create_result = test_dataset.create(self.mongo_client)

        print(f"CREATE: {create_result.success} MESSAGE: {create_result.message}")
        self.assertTrue(create_result.success)
 

    def test_2_dataset_read(self):
        test_db = self.mongo_client["test"]
        test_collection = test_db["testcol"]

        dataset_id = self.dataset_data.get("@id")
        test_dataset = Dataset.construct(id=dataset_id)
        
        read_result = test_dataset.read(test_collection)
        self.assertTrue(read_result.success)

    def test_3_dataset_create_owner_not_found(self):
        pass

    def test_4_dataset_create_organization_not_found(self):
        pass

    def test_5_dataset_update(self):
        pass

    def test_6_dataset_delete(self):
        dataset_id = self.dataset_data.get("@id")
        test_dataset = Dataset.construct(id=dataset_id)
        
        delete_result = test_dataset.delete(self.mongo_client)
        self.assertTrue(delete_result.success) 
