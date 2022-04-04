import unittest

import mds


# import os, sys
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestDataDownload(unittest.TestCase):
    def test_datadownload_initialization(self):

        test_data = {
            "@id": "ark:99999/valid_owner",
            "@type": "Person",
            "name": "Test Owner",
            "email": "owner@example.org"
        }

        user_cv_as_owner = mds.utils.UserCompactView(
            id=test_data["@id"],
            type=test_data["@type"],
            name=test_data["name"],
            email=test_data["email"]
        )

        test_data = {
            "@id": "ark:99999/valid_user",
            "@type": "Person",
            "name": "Test User",
            "email": "test@example.org"
        }

        user_cv_as_author = mds.utils.UserCompactView(
            id=test_data["@id"],
            type=test_data["@type"],
            name=test_data["name"],
            email=test_data["email"]
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

        mds.DataDownload(
            id="ark:99999/data_download_id",
            name="Action on Data for download",
            type="DataDownload",
            owner=user_cv_as_owner,
            author=user_cv_as_author,
            generatedBy=computation_cv,
            evidencegraph=evidencegraph_cv,
            contentSize="10GB",
            contentUrl="ark:99999/someproject/downloadable_data",
            contentFormat="rdf"
        )


if __name__ == "__main__":
    unittest.main()
