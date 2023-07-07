from pymongo import MongoClient
from urllib.parse import quote_plus
import os
import minio
import unittest

class TestBackendConnectivity(unittest.TestCase):
  def test_0_mongo(self):
	
    MONGO_PORT = os.environ.get("MONGO_PORT", "27017")
    MONGO_URI = os.environ.get("MONGO_HOST", "localhost")
    MONGO_USER = os.environ.get("MONGO_ACCESS_KEY", "root")
    MONGO_PASS = os.environ.get("MONGO_SECRET_KEY", "example")
    MONGO_DATABASE = os.environ.get("MONGO_DATABASE", "test")
    MONGO_COLLECTION = os.environ.get("MONGO_COLLECTION", "testcol")

    connection_uri = f"mongodb://{quote_plus(MONGO_USER)}:{quote_plus(MONGO_PASS)}@{MONGO_URI}:{MONGO_PORT}"
    mongo_client = MongoClient(connection_uri)

    mongo_db = mongo_client[MONGO_DATABASE]
    mongo_collection = mongo_db["test_col"]

    # insert a test document
    test_doc = {"@id": "test-id", "name": "test document"}
    insert_result = mongo_collection.insert_one(test_doc)
    self.assertIsNotNone(insert_result.inserted_id)

    # find the one test document
    found_doc = mongo_collection.find_one({"@id": "test-id"})
    self.assertDictEqual(test_doc, found_doc)
    
    # delete the test document
    delete_result = mongo_collection.delete_one({"@id": "test-id"})
    self.assertEqual(1, delete_result.deleted_count)


  def test_1_minio(self):
    MINIO_URI = os.environ.get("MINIO_URI", "localhost")
    MINIO_BUCKET = os.environ.get("MINIO_BUCKET", "test")
    MINIO_USER = os.environ.get("MINIO_ACCESS_KEY", "testroot")
    MINIO_PASS = os.environ.get("MINIO_SECRET_KEY" ,"testroot")

    minio_client = minio.Minio( MINIO_URI, 
      access_key= MINIO_USER,
      secret_key= MINIO_PASS)

    self.assertTrue(minio_client.bucket_exists(MINIO_BUCKET))







