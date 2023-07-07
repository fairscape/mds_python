import path
import unittest
from mds.models import *
from mds.database.mongo import MongoConfig


class TestSoftware(unittest.TestCase):


    def test_0_software_initialization(self):
        owner_inst1 = UserCompactView(
            id="ark:99999/testowner1",
            name="test owner1",
            email="testowner1@example.org"
        )
        self.assertEqual(owner_inst1.id, "ark:99999/testowner1")
        
        Software(
            id="ark:99999/CAMA-users",
            name="john doe",
            owner=owner_inst1,
            author="author1",
            downloadUrl="ark:99999/downloaddir/thisfile",
            citation="doi://blabla"
        )

    def test_1_create(self):
        pass

    def test_2_read(self):
        pass

    def test_3_update(self):
        pass

    def test_4_delete(self):
        pass

if __name__ == "__main__":
    unittest.main()
