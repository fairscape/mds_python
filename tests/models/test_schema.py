import unittest
import sys
import os 
current_dir = os.path.dirname(__file__)
parent_dir = os.path.join(current_dir, '..', '..', 'src')
sys.path.insert(0, os.path.abspath(parent_dir))
from fairscape_mds.mds.models.schema import *
from fairscape_mds.mds.config import MongoConfig
import pymongo


class TestItem(unittest.TestCase):

    def test_item_initialization(self):
        """
        Runs 2 tests
        1. Sucessful Item creation.
        2. Bad Item creation confirm error is raised.
        """
        # clear test collection of data

        item = Item(
            type = 'number'
        )
        self.assertEqual(item.type, "number")

        # ark prefix missing
        with self.assertRaises(ValueError):
            member = Item(
                type = 'Random Not Allowed Type'
            )

class TestProperty(unittest.TestCase):

    def test_property_initialization(self):
        # Successful Property creation
        prop = Property(
            description="A test property",
            index=0,
            type="string"
        )
        self.assertEqual(prop.description, "A test property")
        self.assertEqual(prop.index, 0)
        self.assertEqual(prop.type, "string")

        prop = Property(
            description="A test property",
            index='1::',
            type="array",
            items = Item(type = 'string')
        )
        self.assertEqual(prop.description, "A test property")
        self.assertEqual(prop.index, '1::')
        self.assertEqual(prop.type, "array")
        self.assertEqual(prop.items.type, 'string')

        # Property with invalid type
        with self.assertRaises(ValueError):
            Property(
                description="Invalid type property",
                index=1,
                type="invalid_type"
            )

        # Property with invalid index
        with self.assertRaises(ValueError):
            Property(
                description="Invalid index property",
                index="invalid_index",
                type="string"
            )

        # Property with invalid items
        with self.assertRaises(ValueError):
            Property(
                description="Invalid index property",
                index="1::",
                type="array",
                items = Item(type = "Not real")
            )


def remove_none_values(d):
    cleaned_dict = {}
    for k, v in d.items():
        if isinstance(v, dict):
            v = remove_none_values(v)  # Recursively clean nested dictionaries
        if v is not None:
            cleaned_dict[k] = v
    return cleaned_dict

class TestSchema(unittest.TestCase):

    maxDiff = None	
    mongo_client = MongoConfig(
            host_uri = "localhost",
            port = "27017",
            user = "mongotestaccess",
            password = "mongotestsecret"
            ).CreateClient()


    def setUp(self):
        """
        Methods to Run before every test instance
        """

        # create test database

        test_db = self.mongo_client["test"]
        self.test_collection = test_db["testcol"]

    def test_schema_initialization(self):
        # Successful Schema creation
        self.test_collection.delete_many({})
        schema = Schema(
            guid = 'ark:99999/fake-id',
            name = 'Test Schema',
            description = 'Fake Schema',
            properties={
                "Test Property": Property(
                    description="A test property",
                    index=0,
                    type="string"
                )
            }
        )
        self.assertEqual(schema.name, 'Test Schema')
        self.assertEqual(schema.properties["Test Property"].description, "A test property")
        self.assertEqual(schema.properties["Test Property"].index, 0)
        self.assertEqual(schema.properties["Test Property"].type, "string")

        # Schema with missing required fields
        with self.assertRaises(ValueError):
            Schema(
                properties={}
            )

        # Schema with invalid property type
        with self.assertRaises(ValueError):
            Schema(
                properties={
                    "Invalid Property": Property(
                        description="Invalid type property",
                        index=1,
                        type="invalid_type"
                    )
                }
            )

    def test_mongo_create(self):

        test_schema = Schema(
            guid = 'ark:99999/fake-id',
            name = 'Test Schema',
            description = 'Fake Schema',
            properties={
                "Test Property": Property(
                    description="A test property",
                    index=0,
                    type="string"
                )
            }
        )
        create_status = test_schema.create(self.test_collection)

        #print(f"UserCreate: {write_success}\tMessage: {message}\tCode: {code}")
        self.assertTrue(create_status.success)
        self.assertEqual(create_status.message, "")
        self.assertEqual(create_status.status_code, 200)

        # try to create the same user and make sure it fails
        test_schema = Schema(
            guid = 'ark:99999/fake-id',
            name = 'Test Schema',
            description = 'Fake Schema',
            properties={
                "Test Property": Property(
                    description="A test property",
                    index=0,
                    type="string"
                )
            }
        )
        duplicate_status = test_schema.create(self.test_collection)

        self.assertFalse(duplicate_status.success)
        self.assertEqual(duplicate_status.message, "document already exists")
        self.assertEqual(duplicate_status.status_code, 400)


    def test_mongo_read(self):
        find_schema = Schema.model_construct(guid = 'ark:99999/fake-id')
        test_schema = Schema(
            guid = 'ark:99999/fake-id',
            name = 'Test Schema',
            description = 'Fake Schema',
            properties={
                "Test Property": Property(
                    description="A test property",
                    index=0,
                    type="string"
                )
            }
        )     

        read_status = find_schema.read(self.test_collection)

        self.assertTrue(read_status.success)
        self.assertEqual(read_status.message, "")
        self.assertEqual(read_status.status_code, 200)

        find_schema_dict = remove_none_values(find_schema.dict(by_alias=True))
        test_schema_dict = remove_none_values(test_schema.dict(by_alias=True))
        # Compare the dictionaries without None values
        self.assertDictEqual(find_schema_dict, test_schema_dict)


    def test_4_mongo_read_not_found(self):
        # try to find a nonexistant user 
        fake_schema_id = "ark:99999/notauser"
        nonexistant_schema = Schema.model_construct(guid=fake_schema_id)

        not_found = nonexistant_schema.read(self.test_collection)

        self.assertFalse(not_found.success)
        self.assertEqual(not_found.message, "No record found")
        self.assertEqual(not_found.status_code, 404)


    def test_5_mongo_delete(self):
        test_schema = Schema(
            guid = 'ark:99999/fake-id',
            name = 'Test Schema',
            description = 'Fake Schema',
            properties={
                "Test Property": Property(
                    description="A test property",
                    index=0,
                    type="string"
                )
            }
        )
        test_schema.create(self.test_collection)
        test_schema = Schema.model_construct(guid = 'ark:99999/fake-id')

        delete_status = test_schema.delete(self.test_collection)

        self.assertTrue(delete_status.success)
        self.assertEqual(delete_status.message, "")
        self.assertEqual(delete_status.status_code, 200)

  
    def tearDown(self) -> None:
        return super().tearDown()




if __name__ == "__main__":
    unittest.main()
