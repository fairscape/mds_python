import os
import sys
import unittest
from mds.utils import *

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestValidateArk(unittest.TestCase):
    def test_validate_ark_missing_ark(self):
        with self.assertRaises(ValueError):
            validate_ark("99999/test-ark")

        with self.assertRaises(ValueError):
            validate_ark("ark99999/test-ark")

        with self.assertRaises(ValueError):
            validate_ark(":99999/test-ark")

    def test_validate_ark_naan_error(self):
        with self.assertRaises(ValueError):
            validate_ark("ark:9999/test-ark")

        with self.assertRaises(ValueError):
            validate_ark("ark:999/test-ark")

        with self.assertRaises(ValueError):
            validate_ark("ark:99/test-ark")

        with self.assertRaises(ValueError):
            validate_ark("ark:9/test-ark")

        with self.assertRaises(ValueError):
            validate_ark("ark:/test-ark")

    def test_validate_ark_postfix_missing(self):
        with self.assertRaises(ValueError):
            validate_ark("ark:99999/")

    def test_missing_slash(self):
        with self.assertRaises(ValueError):
            validate_ark("ark:99999CAMA-test")


class TestValidateEmail(unittest.TestCase):
    def test_validate_email_missing_username(self):
        with self.assertRaises(ValueError):
            validate_email("@example.com")

    def test_validate_email_missing_domain(self):
        with self.assertRaises(ValueError):
            validate_ark("someone@")

    def test_validate_email_missing_at_symbol(self):
        with self.assertRaises(ValueError):
            validate_ark("usernameexample.com")

    def test_validate_email_missing_dot_symbol(self):
        with self.assertRaises(ValueError):
            validate_ark("username@examplecom")

    def test_validate_email_complete(self):
        with self.assertRaises(ValueError):
            validate_ark("lastname.firstname@subdomain.domain.com")


class TestCompactView(unittest.TestCase):
    test_ark = "ark:99999/valid_test"

    def test_compact_vew(self):
        test_data = {
            "@id": "ark:99999/valid_test",
            "@type": "Dataset",
            "name": "Test Dataset"
        }

        cv = FairscapeBaseModel(
            id=test_data["@id"],
            type=test_data["@type"],
            name=test_data["name"]
        )

        self.assertDictEqual(cv.dict(by_alias=True), test_data)


class TestUserCompactView(unittest.TestCase):
    test_data = {
        "@id": "ark:99999/valid_user",
        "@type": "Person",
        "name": "Test User",
        "email": "test@example.org"
    }

    def test_basic(self):
        user_cv = UserCompactView(
            id=self.test_data["@id"],
            type=self.test_data["@type"],
            name=self.test_data["name"],
            email=self.test_data["email"]
        )

        self.assertDictEqual(user_cv.dict(by_alias=True), self.test_data)

    def test_missing(self):
        # If you forget to assign a value it won't default like expected

        cv_default = FairscapeBaseModel(
            id=self.test_data["@id"],
            name=self.test_data["name"],
            email=self.test_data["email"]
        )

        print(cv_default.json(by_alias=True))

        # dicts are not equal
        self.assertDictEqual(cv_default.dict(by_alias=True), self.test_data)

    def test_without_validation(self):
        user_cv = UserCompactView(
            id=self.test_data["@id"],
            type=self.test_data["@type"],
            name=self.test_data["name"],
            email=self.test_data["email"]
        )

        fields_set = user_cv.__fields_set__

        constructed_copy = UserCompactView.construct(_fields_set=fields_set, **user_cv.dict())

        self.assertDictEqual(user_cv.dict(), constructed_copy.dict())


class TestSoftwareCompactView(unittest.TestCase):

    def test_software_compact_view(self):
        test_data = {
            "@id": "ark:99999/valid_user",
            "@type": "evi:Software",
            "name": "Test Software"
        }

        software_cv = SoftwareCompactView(
            id=test_data["@id"],
            type=test_data["@type"],
            name=test_data["name"]
        )

        self.assertDictEqual(software_cv.dict(by_alias=True), test_data)


class TestDatasetCompactView(unittest.TestCase):

    def test_dataset_compact_view(self):
        test_data = {
            "@id": "ark:99999/valid_dataset",
            "@type": "evi:Dataset",
            "name": "Test Dataset"
        }

        dataset_cv = DatasetCompactView(
            id=test_data["@id"],
            type=test_data["@type"],
            name=test_data["name"]
        )

        self.assertDictEqual(dataset_cv.dict(by_alias=True), test_data)


class TestComputationCompactView(unittest.TestCase):

    def test_computation_compact_view(self):
        test_data = {
            "@id": "ark:99999/valid_computation",
            "@type": "evi:Computation",
            "name": "Test Computation"
        }

        computation_cv = ComputationCompactView(
            id=test_data["@id"],
            type=test_data["@type"],
            name=test_data["name"]
        )

        self.assertDictEqual(computation_cv.dict(by_alias=True), test_data)


class TestEvidenceGraphCompactView(unittest.TestCase):

    def test_evidencegraph_compact_view(self):
        test_data = {
            "@id": "ark:99999/valid_evidencegraph",
            "@type": "evi:EvidenceGraph",
            "name": "Test EvidenceGraph"
        }

        evidencegraph_cv = EvidenceGraphCompactView(
            id=test_data["@id"],
            type=test_data["@type"],
            name=test_data["name"]
        )

        self.assertDictEqual(evidencegraph_cv.dict(by_alias=True), test_data)


class TestOrganizationCompactView(unittest.TestCase):

    def test_organization_compact_view(self):
        test_data = {
            "@id": "ark:99999/valid_organization",
            "@type": "Organization",
            "name": "Test Organization"
        }

        organization_cv = OrganizationCompactView(
            id=test_data["@id"],
            type=test_data["@type"],
            name=test_data["name"]
        )

        self.assertDictEqual(organization_cv.dict(by_alias=True), test_data)


class TestProjectCompactView(unittest.TestCase):

    def test_project_compact_view(self):
        test_data = {
            "@id": "ark:99999/valid_project",
            "@type": "Project",
            "name": "Test Project"
        }

        project_cv = ProjectCompactView(
            id=test_data["@id"],
            type=test_data["@type"],
            name=test_data["name"]
        )

        self.assertDictEqual(project_cv.dict(by_alias=True), test_data)


class TestDataDownloadCompactView(unittest.TestCase):

    def test_project_compact_view(self):
        test_data = {
            "@id": "ark:99999/valid_downloadable_data",
            "@type": "DataDownload",
            "name": "A dataset in downloadable form."
        }

        datadownload_cv = DataDownloadCompactView(
            id=test_data["@id"],
            type=test_data["@type"],
            name=test_data["name"]
        )

        self.assertDictEqual(datadownload_cv.dict(by_alias=True), test_data)


if __name__ == "__main__":
    unittest.main()
