import unittest
import json
import path
from mds.models import *
from mds import MongoConfig


class TestGroup(unittest.TestCase):
    maxDiff = None
    context = {"@vocab": "https://schema.org/", "evi": "https://w3id.org/EVI#"}

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
            "name": "Test User", 
            "email": "test@example.org" 
            },
        "members": [],
    }

    mongo_client = MongoConfig(
            host_uri = "localhost",
            port = 27017,
            user = "root",
            password = "example"
            ).connect()

    def test_0_group_initilization(self):

        owner = UserCompactView(
            id="ark:99999/testowner",
            name="test owner",
            email="testowner@example.org"
        )

        member = UserCompactView(
            id="ark:99999/testuser1",
            name="test user1",
            email="testuser1@example.org"
        )

        grp = Group(
            id="ark:99999/CAMA-users",
            name="Cama Users",
            owner=owner,
            members=[member]
        )

        grp_dict = grp.dict(by_alias=True)

        expected = {
            "@context": self.context,
            "@id": "ark:99999/CAMA-users",
            "@type": "Organization",
            "name": "Cama Users",
            "owner": owner.dict(by_alias=True),
            "members": [ member.dict(by_alias=True)]
        }

        self.assertDictEqual(grp_dict, expected)

    
    def test_1_group_json(self):

        owner = UserCompactView(
            id="ark:99999/testowner",
            name="test owner",
            email="testowner@example.org"
        )

        member = UserCompactView(
            id="ark:99999/testuser1",
            name="test user1",
            email="testuser1@example.org"
        )

        grp = Group(
            id="ark:99999/CAMA-users",
            name="Cama Users",
            owner=owner,
            members=[member]
        )

        grp_json = grp.json(by_alias=True)
        expected = json.dumps({
            "@context": self.context,
            "@id": "ark:99999/CAMA-users",
            "@type": "Organization",
            "name": "Cama Users",
            "owner": owner.dict(by_alias=True),
            "members": [ member.dict(by_alias=True)]
        })

        self.assertDictEqual(json.loads(grp_json), json.loads(expected))


    def test_2_group_create_0(self):
        
        test_db = self.mongo_client["test"]
        self.test_collection = test_db["testcol"]

        # clear test collection of data
        self.test_collection.delete_many({})

        # create a user
        test_user = User(**self.user_data)
        create_user_status = test_user.create(self.test_collection)
        self.assertTrue(create_user_status.success)

        # create a group
        test_group = Group(**self.group_data)
        create_group_status = test_group.create(self.test_collection)

        self.assertTrue(create_group_status.success)


    def test_2_group_create_1_group_exists(self):
        
        test_db = self.mongo_client["test"]
        test_collection = test_db["testcol"]

        test_user = User(**self.user_data)
        test_group = Group(**self.group_data)
        create_group_status = test_group.create(test_collection)

        self.assertFalse(create_group_status.success)


    def test_2_group_create_2_owner_doesnt_exist(self):
        
        test_db = self.mongo_client["test"]
        test_collection = test_db["testcol"]

        not_a_user = User(**self.user_data)
        not_a_user.id = "ark:99999/not-a-user"

        test_group = Group(**self.group_data)

        test_group.id = "ark:99999/group-no-owner"
        test_group.owner = UserCompactView(
            id=not_a_user.id, 
            name=not_a_user.name,
            email= not_a_user.email
            )

        group_create = test_group.create(test_collection)

        self.assertFalse(group_create.success)


    def test_2_group_create_3_member_doesnt_exist(self):
        pass

    def test_3_group_read_0(self):
        pass


    def test_3_group_read_1_doesnt_exist(self):
        pass

    
    def test_3_group_read_2_data_doesnt_validate(self):
        pass


    def test_4_group_delete_0(self):
        test_group = Group(**self.group_data)


    def test_4_group_delete_1_doesnt_exist(self):
        pass


    def test_5_group_add_user(self):
        pass


    def test_6_group_remove_user(self):
        pass


if __name__ == "__main__":
    unittest.main()
