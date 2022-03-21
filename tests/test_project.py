import unittest
from datetime import datetime
import mds


# import os, sys
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import tests.test_computation


class TestProject(unittest.TestCase):
    def test_project_initialization(self):
        owner_inst1 = mds.utils.UserCompactView(
            id="ark:99999/testowner1",
            name="test owner1",
            type="Person",
            email="testowner1@example.org"
        )
        self.assertEqual(owner_inst1.id, "ark:99999/testowner1")

        owner_inst2 = mds.utils.UserCompactView(
            id="ark:99999/testowner2",
            name="test owner2",
            type="Person",
            email="testowner2@example.org"
        )
        self.assertEqual(owner_inst2.id, "ark:99999/testowner2")

        software_inst1 = mds.Software(
            id="ark:99999/CAMA-users",
            name="john doe",
            type="evi:Software",
            owner=owner_inst1,
            author="author1",
            downloadUrl="ark:99999/downloaddir/thisfile",
            citation="doi://blabla",
            usedBy=[]
        )
        computation = mds.Computation(
            id="ark:99999/CAMA-users",
            name="john doe",
            type="evi:Computation",
            owner=owner_inst2,
            author="author1",
            dateCreated=datetime(2022, 2, 15, 9, 26, 30, 342380),
            dateFinished=datetime(2022, 2, 15, 9, 30, 3, 342380),
            associatedWith=[],
            usedSoftware=[software_inst1],
            usedDataset=[]
        )

        user = mds.utils.UserCompactView(
            id="ark:99999/testuser1",
            name="test user1",
            type="Person",
            email="testuser1@example.org"
        )

        ds = mds.Dataset(
            id="ark:99999/CAMA-users",
            name="A demo dataset",
            type="evi:Dataset",
            owner=owner_inst1,
            #includedInDataCatalog=,
            #sourceOrganization=,
            distribution="csv",
            author=user,
            dateCreated=datetime(2022, 2, 15, 9, 26, 30),
            dateModified=datetime(2022, 2, 16, 9, 26, 30, 342380),
        )
        eg = mds.EvidenceGraph(
            id="ark:99999/CAMA-users",
            name="a demo evidencegraph",
            type="evi:EvidenceGraph",
            owner=owner_inst1,
            graph=""
        )
        mds.Project(
            id="ark:99999/Fairscape",
            name="Fairscepe project",
            type="Project",
            owner=owner_inst1,
            datasets=[ds],
            computations=[computation],
            software=[software_inst1],
            evidencegraphs=[eg]
        )



if __name__ == "__main__":
    unittest.main()
