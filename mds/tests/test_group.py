import unittest
import json
import test_path
from mds.models import *
from mds import MongoConfig


class TestGroup(unittest.TestCase):
    maxDiff = None
    context = {"@vocab": "https://schema.org/", "evi": "https://w3id.org/EVI#"}

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


    def test_2_group_create(self):
        pass

    def test_3_group_delete(self):
        pass
    
    def test_4_group_add_user(self):
        pass

    def test_5_group_remove_user(self):
        pass


if __name__ == "__main__":
    unittest.main()
