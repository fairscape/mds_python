import unittest
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



        test_data = {
            "@id": "ark:99999/valid_dataset",
            "@type": "evi:Dataset",
            "name": "Test Dataset"
        }

        dataset_cv = mds.utils.DatasetCompactView(
            id=test_data["@id"],
            type=test_data["@type"],
            name=test_data["name"]
        )

        test_data = {
            "@id": "ark:99999/valid_user",
            "@type": "evi:Software",
            "name": "Test Software"
        }

        software_cv = mds.utils.SoftwareCompactView(
            id=test_data["@id"],
            type=test_data["@type"],
            name=test_data["name"]
        )

        test_data = {
            "@id": "ark:99999/valid_computation",
            "@type": "evi:Computation",
            "name": "Test Computation"
        }

        computation_cv = mds.utils.ComputationCompactView(
            id=test_data["@id"],
            type=test_data["@type"],
            name=test_data["name"]
        )

        test_data = {
            "@id": "ark:99999/valid_evidencegraph",
            "@type": "evi:EvidenceGraph",
            "name": "Test EvidenceGraph"
        }

        evidencegraph_cv = mds.utils.EvidenceGraphCompactView(
            id=test_data["@id"],
            type=test_data["@type"],
            name=test_data["name"]
        )


        mds.Project(
            id="ark:99999/Fairscape",
            name="Fairscepe project",
            type="Project",
            owner=owner_inst1,
            datasets=[dataset_cv],
            computations=[computation_cv],
            software=[software_cv],
            evidencegraphs=[evidencegraph_cv]
        )



if __name__ == "__main__":
    unittest.main()
