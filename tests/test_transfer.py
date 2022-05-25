import path
from fastapi.testclient import TestClient
import unittest
from mds.app import app
from mds.database.mongo import GetConfig
from mds.database.minio import GetMinioConfig

client = TestClient(app)

test_user = {
		"@id": "ark:99999/test-user1",
		"name": "Test User1",
		"type": "Person",
		"email": "testuser1@example.org",
		"password": "test1",
		"organizations": [],
		"projects": [],
		"datasets": [],
		"software": [],
		"computations": [],
		"evidencegraphs": []
		}

test_dataset = {
	"@id": "ark:99999/test-dataset",
	"@type": "evi:Dataset",
	"name": "test dataset",
	"owner": {
		"@id": "ark:99999/test-user1",
		"@type": "Person",
		"name": "Test User1",
		"email": "testuser1@example.org"
		}
}

test_data_download = {
	"@id": "ark:99999/test-download",
	"name": "test file.txt",
	"@type": "DataDownload",
	"encodingFormat": ".txt",
	"encodesCreativeWork": test_dataset["@id"],
}

files = {'file': ('test file.txt', 'some,data,to,send\nanother,row,to,send\n')}

class TransferTest(unittest.TestCase):

	def test_0_clear_database(self):
		# clear database for all tests
		mongo_client = GetConfig()
		mongo_db = mongo_client["test"]
		mongo_collection = mongo_db["testcol"]
		mongo_collection.delete_many({})
		mongo_client.close()

		# create 
		minio_client = GetMinioConfig()

		if minio_client.bucket_exists("test") != True:	
			minio_client.make_bucket("test")


	def test_0_datadownload_0_create(self):

		# have to create user for dataset owner
		create_user = client.post("/user", json = test_user)
		self.assertEqual(create_user.status_code, 201)

		create_dataset = client.post("/dataset", json= test_dataset)
		self.assertEqual(create_dataset.status_code, 201)


		# test creating download metadata	
		response = client.post(f"/datadownload", json=test_data_download)
		print(response.json())
		self.assertEqual(response.status_code, 201)


	def test_0_datadownload_1_upload_file(self):

		# test upload	
		response = client.post("/datadownload/ark:99999/test-download/upload", files=files)
		print(response.json())
		self.assertEqual(response.status_code, 201)

"""
	def test_0_datadownload_1_get_metadata(self):
		response = client.get(f"/datadownload/{test_data_download['@id']}")
		self.assertEqual(response.status_code, 200)

		download_metadata = response.json()

		self.assertEqual(test_data_download["name"], download_metadata["name"])
		self.assertEqual(test_data_download["encodesCreativeWork"], download_metadata["encodesCreativeWork"])


	def test_0_datadownload_1_get_file(self):
		response = client.get(f"/datadownload/{test_data_download['@id']}?object=1")
		self.assertEqual(response.status_code, 200)
"""

if __name__ == "__main__":
    unittest.main()
