import unittest
import path
from mds.models import *
from mds.models.compact import UserCompactView
from mds import MongoConfig


class TestComputation(unittest.TestCase):
    test_user = UserCompactView(
        id="ark:99999/test-owner",
        name="test owner1",
        email="testowner1@example.org"
    )

    test_software = Software(
        id="ark:99999/test-software",
        owner=owner_inst1,
        citation="doi://blabla"
    )

    test_software_download = DataDownload()

    test_dataset = Dataset()
    
    test_dataset_download = DataDownload()
    
    test_computation  =  Computation(
            id="ark:99999/test-comp",
            name="",
            owner=self.test_user,
            author="author1",
            dateCreated="2022-02-15",
            dateFinished="2022-02-15",
            usedSoftware=[software_inst1]
        )


if __name__ == "__main__":
    unittest.main()
