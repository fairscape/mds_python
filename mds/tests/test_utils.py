import test_path
import unittest
from mds.models import *
from mds import MongoConfig

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


class TestFairscapeBaseModel(unittest.TestCase):
    test_ark = "ark:99999/valid_test"
    test_data = {
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
    mongo_client = MongoConfig(
            host_uri = "localhost",
            port = 27017,
            user = "root",
            password = "example"
            ).connect()

    def setUp(self):
        test_db = self.mongo_client["test"]
        self.test_collection = test_db["basemodel"]


    def test_0_parse_success(self):

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

        validated_dict = cv.dict(by_alias=True)

        validated_dict.pop("@context", None)

        self.assertDictEqual(validated_dict, test_data)


    def test_1_mongo_0_create(self):

        test_base_model = FairscapeBaseModel(**self.test_data)
        res = test_base_model.create(self.test_collection)
        self.assertTrue(res.success)
        self.assertEqual(res.message, "")
        self.assertEqual(res.status_code, 200)


    def test_1_mongo_1_read(self):

        identifier = self.test_data["@id"]

        read_test = User.construct(id=identifier)
        test_base_model = FairscapeBaseModel(**self.test_data)

        read_status = read_test.read(self.test_collection)


        self.assertTrue(read_status.success)
        self.assertEqual(read_status.message, "")
        self.assertEqual(read_status.status_code, 200)

        validated = test_base_model.dict(by_alias=True)
        self.assertDictEqual(validated, read_test.dict(by_alias=True))


    def test_1_mongo_2_delete(self):
        identifier = self.test_data["@id"]

        delete_test = User.construct(id=identifier)

        del_status = delete_test.delete(self.test_collection)
        self.assertTrue(del_status.success)
        self.assertEqual(del_status.message, "")
        self.assertEqual(del_status.status_code, 200)

        read_status = delete_test.read(self.test_collection)
        self.assertFalse(read_status.success)
        self.assertEqual(read_status.status_code, 404)


    def test_2_mongo_3_update(self):
        pass

 
    def test_2_user_compact_view(self):
        test_data = {
            "@id": "ark:99999/valid_user",
            "@type": "Person",
            "name": "Test User",
            "email": "test@example.org"
        }

        user_cv = UserCompactView(**test_data)
        validated_user_cv = user_cv.dict(by_alias=True)
        validated_user_cv.pop("@context", None)
        self.assertDictEqual(validated_user_cv, test_data)

        cv_default = UserCompactView(
            id    = test_data["@id"],
            name  = test_data["name"],
            email = test_data["email"]
        )

        cv_dict = cv_default.dict(by_alias=True)
        cv_dict.pop("@context", None)
        self.assertDictEqual(cv_dict, test_data)

        user_cv = UserCompactView(**test_data)

        fields_set = user_cv.__fields_set__
        constructed_copy = UserCompactView.construct(_fields_set=fields_set, **user_cv.dict())


        self.assertDictEqual(user_cv.dict(), constructed_copy.dict())


    def test_3_software_compact_view(self):

        test_data = {
            "@id": "ark:99999/valid_user",
            "@type": "evi:Software",
            "name": "Test Software"
        }

        software_cv = SoftwareCompactView(**test_data)

        validated_software_cv = software_cv.dict(by_alias=True)
        validated_software_cv.pop("@context", None)
        self.assertDictEqual(validated_software_cv, test_data)


    def test_4_dataset_compact_view(self):

        test_data = {
            "@id": "ark:99999/valid_dataset",
            "@type": "evi:Dataset",
            "name": "Test Dataset"
        }

        dataset_cv = DatasetCompactView(**test_data)
        validated_dataset_cv = dataset_cv.dict(by_alias=True)
        validated_dataset_cv.pop("@context", None)

        self.assertDictEqual(validated_dataset_cv, test_data)



if __name__ == "__main__":
    unittest.main()